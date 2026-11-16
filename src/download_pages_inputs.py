#!/usr/bin/env python3
"""Download existing published multilingual dictionary assets directly from
repository GitHub Releases (not GitHub API), verify SHA-256 and build inputs
for the static Pages index. No source is downloaded from its upstream.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import hashlib
import json
import pathlib
import re
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

REPO="https://github.com/danilfg/dicts"
MAIN_CATALOG=REPO+"/releases/latest"
CORE={"en-ru","ru-en","en-es","es-en","en-de","de-en"}

def fetch(url,path,expected=None):
    headers={"User-Agent":"danilfg-dicts-pages-index/1.0","Accept-Encoding":"identity"}
    for n in range(4):
        try:
            request=urllib.request.Request(url,headers=headers)
            h=hashlib.sha256()
            with urllib.request.urlopen(request,timeout=120) as response,path.open("wb") as out:
                for block in iter(lambda:response.read(1<<20),b""):
                    out.write(block);h.update(block)
            if expected and h.hexdigest()!=expected:
                raise ValueError("Checksum mismatch: "+path.name)
            return
        except (TimeoutError,ConnectionError,urllib.error.URLError) as err:
            path.unlink(missing_ok=True)
            if n==3:raise
            print(f"Retry {n+1} {path.name}: {err}",flush=True)
            time.sleep(5*(n+1))

def choose(name):
    if name.startswith("koreader--") and name.endswith(".zip"):
        return True
    if name.startswith(("enrichment--","enrichments-extra--")) and name.endswith((".json.gz",".zip")):
        return True
    match=re.fullmatch(r"(?:freedict|wikdict)--([a-z0-9]+-[a-z0-9]+)\.zip",name)
    return bool(match and match.group(1) in CORE)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--dir",type=pathlib.Path,default=pathlib.Path("downloads"))
    args=parser.parse_args()
    args.dir.mkdir(exist_ok=True,parents=True)
    # GitHub's public HTML redirect, not the rate-limited GitHub REST API.
    with urllib.request.urlopen(urllib.request.Request(MAIN_CATALOG,headers={
        "User-Agent":"danilfg-dicts-pages-index/1.0"}),timeout=90) as response:
        target=response.geturl()
    match=re.search(r"/releases/tag/(data-[A-Za-z0-9-]+)",target)
    if not match:raise ValueError("Could not determine latest published dictionary release: "+target)
    tag=match.group(1)
    url=REPO+"/releases/download/"+tag+"/"
    manifest=args.dir/"manifest.json"
    fetch(url+"manifest.json",manifest)
    catalog=json.loads(manifest.read_text())
    assets=[x for x in catalog.get("assets",[]) if choose(x["name"])]
    if len(assets)<120:
        raise ValueError("Found fewer than 120 source dictionaries/enrichment archives")
    print("Latest dictionary release",tag,"with",len(assets),"selected assets",flush=True)
    def pull(asset):
        path=args.dir/asset["name"]
        fetch(url+asset["name"],path,asset["sha256"])
        if path.stat().st_size!=asset.get("bytes"):raise ValueError("Size mismatch: "+path.name)
        return asset["name"],path.stat().st_size
    total=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,(name,amount) in enumerate(pool.map(pull,assets),1):
            total+=amount
            if i%25==0 or i==len(assets):
                print(f"Downloaded {i}/{len(assets)} verified assets ({total//1_000_000} MB)",flush=True)
    (args.dir/".release-tag").write_text(tag)
    print("READY:",len(assets),"assets",total,"bytes",flush=True)

if __name__=="__main__":main()
