#!/usr/bin/env python3
"""Mirror all available *text* dictionary editions without truncating source corpora.

Data always land on the distributor's GitHub Releases, not in the Git history.
Only publisher rights/data text are redistributed; audio, media and external
software are excluded. Every asset is chunked below GitHub's 2-GiB per-file cap.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

MAX_CHUNK=1_450_000_000
UA="danilfg-dicts-archive-mirror/1.0 (https://github.com/danilfg/dicts)"
KAikki_INDEX="https://kaikki.org/dictionary/rawdata.html"
TATOEBA_INDEX="https://downloads.tatoeba.org/exports/"
EXPLICIT_TATOEBA=[
    "sentences.tar.bz2","sentences_detailed.tar.bz2",
    "sentences_CC0.tar.bz2","links.tar.bz2","sentences_base.tar.bz2"
]

class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            url=dict(attrs).get("href")
            if url:self.links.append(url)

def get_page(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=90) as response:
        return response.read(1_000_000).decode("utf-8","replace")

def discover(source,html=None):
    homepage=KAikki_INDEX if source=="kaikki" else TATOEBA_INDEX
    parser=Links();parser.feed(html if html is not None else get_page(homepage))
    found={}
    for href in parser.links:
        url=urljoin(homepage,href)
        if source=="kaikki":
            if url.endswith("/raw-wiktextract-data.jsonl.gz"):
                edition="en"
            else:
                match=re.search(r"/downloads/([a-z0-9_-]+)/([a-z0-9_-]+)-extract\.jsonl\.gz$",url)
                if not match or match.group(1)!=match.group(2):continue
                edition=match.group(1)
            found[edition]=url
        else:
            name=url.rsplit("/",1)[-1]
            if name in EXPLICIT_TATOEBA:found[name]=url
    if not found:
        raise ValueError("No verified text archives found in source index")
    if source=="kaikki" and "en" not in found:
        raise ValueError("English Wiktionary source dump was not discovered")
    if source=="tatoeba" and not set(EXPLICIT_TATOEBA).issubset(found):
        raise ValueError("Incomplete Tatoeba text corpus index")
    return dict(sorted(found.items()))

def gh(*args):
    return subprocess.run(["gh",*args],check=True,capture_output=True,text=True).stdout.strip()

def rights(source):
    if source=="kaikki":return {
        "license":"CC-BY-SA-4.0 for eligible Wiktionary text (third-party exceptions require separate review)",
        "authors":"Wiktionary contributors; machine-readable extraction by Tatu Ylonen (Wiktextract/Kaikki)",
        "license_url":"https://creativecommons.org/licenses/by-sa/4.0/",
        "modification":"Compressed upstream dump split into sequential byte ranges; original content otherwise unchanged"
    }
    return {
        "license":"CC-BY-2.0-FR for attributed Tatoeba text, with specifically marked CC0 records; check record terms",
        "authors":"Individual sentence authors / Tatoeba community",
        "license_url":"https://creativecommons.org/licenses/by/2.0/fr/",
        "modification":"Upstream original text-export archives split if they exceed the per-asset limit; no audio included"
    }

def mirror_one_once(url,prefix,tag,manifest):
    request=urllib.request.Request(url,headers={"User-Agent":UA})
    pieces=[]
    index=0;size=0;hasher=None;dest=None;file=None
    def start_part():
        nonlocal index,size,hasher,dest,file
        index+=1;size=0;hasher=hashlib.sha256()
        dest=Path(tempfile.gettempdir())/f"{prefix}.part{index:03d}"
        file=dest.open("wb")
    def finalize():
        nonlocal size,file
        if file is None or size==0:return
        file.close();file=None
        hashval=hasher.hexdigest()
        gh("release","upload",tag,str(dest),"-R",os.environ["GITHUB_REPOSITORY"],"--clobber")
        pieces.append({"asset":dest.name,"bytes":size,"sha256":hashval,"index":index})
        print(f"Published {dest.name}: {size} bytes",flush=True)
        dest.unlink(missing_ok=True)
    start_part()
    try:
        with urllib.request.urlopen(request,timeout=180) as response:
            while data:=response.read(1024*1024):
                pos=0
                while pos<len(data):
                    if size==MAX_CHUNK:
                        finalize();start_part()
                    amount=min(len(data)-pos,MAX_CHUNK-size)
                    block=data[pos:pos+amount]
                    file.write(block);hasher.update(block)
                    size+=len(block);pos+=amount
        finalize()
    finally:
        if file and not file.closed:file.close()
        if dest:dest.unlink(missing_ok=True)
    if not pieces:raise ValueError("Zero-length upstream download: "+url)
    manifest.append({"original_url":url,"parts":pieces,
        "reassembly":"Join parts by numeric index without altering bytes.",
        "original_bytes":sum(x["bytes"] for x in pieces)})
    return pieces

def mirror_one(url,prefix,tag,manifest):
    for attempt in range(3):
        try:return mirror_one_once(url,prefix,tag,manifest)
        except (OSError, TimeoutError):
            if attempt==2:raise
            print(f"Retrying {prefix} after network error, attempt {attempt+2}",flush=True)
            time.sleep(5*(attempt+1))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",choices=["kaikki","tatoeba"],required=True)
    args=p.parse_args()
    source=args.source
    owner=os.getenv("GITHUB_REPOSITORY","")
    if owner!="danilfg/dicts":raise ValueError("Refusing to publish to a foreign repository")
    discovered=discover(source)
    tag=os.environ["UNIFIED_RELEASE_TAG"]
    report={"schema":1,"source":source,"created":dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_index":KAikki_INDEX if source=="kaikki" else TATOEBA_INDEX,
        "full_text_archive":True,"excluded":["media","audio","template dumps","non-dictionary logs"],
        "discovered":len(discovered),"licenses":rights(source),"sources":[],"status":"in_progress"}
    with tempfile.TemporaryDirectory() as d:
        for key,url in discovered.items():
            label="kaikki--"+key if source=="kaikki" else "tatoeba--"+key.replace(".tar.bz2","")
            print("Downloading",key,url,flush=True)
            mirror_one(url,label,tag,report["sources"])
        report["status"]="complete" if len(report["sources"])==len(discovered) else "incomplete"
        if report["status"]!="complete":raise ValueError("Not all discovered files were mirrored")
        doc=Path(d)/(source+"--SOURCE-MANIFEST.json")
        doc.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
        legal=Path(d)/(source+"--ATTRIBUTION-AND-LICENSE.txt")
        legal.write_text(json.dumps(report["licenses"],ensure_ascii=False,indent=2)+
            "\nOriginal URLs and SHA-256: SOURCE-MANIFEST.json\n"+
            "No guarantee of translation quality or content correctness.\n")
        gh("release","upload",tag,str(doc),str(legal),"-R",owner,"--clobber")
    print(f"RAW SOURCE COMPLETE: https://github.com/{owner}/releases/tag/{tag}",flush=True)

if __name__=="__main__":main()
