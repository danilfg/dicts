#!/usr/bin/env python3
"""Mirror and index three additional independently licensed lexical datasets.

GitHub Actions is the sole upstream downloader. End users download all resulting
assets from danilfg/dicts GitHub Releases. Original files are preserved.
"""
from __future__ import annotations
import argparse
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
import tomllib
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

REPO = "danilfg/dicts"
MAX_ASSET = 1_850_000_000
UA = "danilfg-dicts-lexical-mirror/1.0 (https://github.com/danilfg/dicts)"
CONCEPTNET_SOURCE = "https://s3.amazonaws.com/conceptnet/downloads/2019/edges/conceptnet-assertions-5.7.0.csv.gz"
SOURCES = {
 "oewn": {"repo":"globalwordnet/english-wordnet","license":"CC-BY-4.0",
          "license_url":"https://creativecommons.org/licenses/by/4.0/",
          "credit":"Open English Wordnet Community; Princeton WordNet; individual contributors"},
 "omw":{"repo":"omwn/omw-data","license":"PER-COMPONENT; see upstream index.toml and original archives",
        "license_url":"https://omwn.org/omw1.html",
        "credit":"Francis Bond, Ryan Foster, and all individual WordNet contributors"},
 "conceptnet":{"repo":"commonsense/conceptnet5","license":"CC-BY-SA-4.0; per-edge metadata may add source obligations",
        "license_url":"https://creativecommons.org/licenses/by-sa/4.0/",
        "credit":"ConceptNet / Robyn Speer, Luminoso, and upstream crowdsourced contributors"}
}
def gh(*args):
    p=subprocess.run(["gh",*args],capture_output=True,text=True)
    if p.returncode:raise RuntimeError("gh "+repr(args)+": "+p.stderr[-800:])
    return p.stdout.strip()
def api(url):
    headers={"User-Agent":UA,"Accept":"application/vnd.github+json"}
    token=os.getenv("GH_TOKEN")
    if token:headers["Authorization"]="Bearer "+token
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=90) as r:return json.load(r)
def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for data in iter(lambda:f.read(1<<20),b""):h.update(data)
    return h.hexdigest()
def download(url,path,limit=MAX_ASSET):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    length=0
    for retry in range(3):
        try:
            with urllib.request.urlopen(req,timeout=180) as resp, path.open("wb") as dst:
                while buf:=resp.read(1<<20):
                    length+=len(buf)
                    if length>limit:raise ValueError("Input exceeds release asset size cap: "+url)
                    dst.write(buf)
            break
        except (TimeoutError,ConnectionError,urllib.error.URLError) as e:
            path.unlink(missing_ok=True)
            length=0
            if retry==2:raise
            time.sleep(2**retry)
    if length<10:raise ValueError("Download empty "+url)
    return sha256(path)
def verify(file,asset):
    if file.stat().st_size!=asset["size"]:raise ValueError("Wrong download size "+asset["name"])
    digest=asset.get("digest") or ""
    if digest.startswith("sha256:") and sha256(file)!=digest[7:]:
        raise ValueError("Upstream SHA-256 mismatch "+asset["name"])
def upstream_release(repo):
    return api("https://api.github.com/repos/"+repo+"/releases/latest")
def local(node):
    return node.tag.split("}",1)[-1]
def normalize_wordnet_xml(path,out):
    """WN-LMF synset definitions, synonyms and relations, for browser adaptation."""
    with gzip.open(path,"rb") as f:tree=ET.parse(f)
    root=tree.getroot()
    synsets={}
    for e in root.iter():
        if local(e)=="Synset":
            sid=e.attrib.get("id","")
            defs=[" ".join("".join(x.itertext()).split()) for x in e if local(x)=="Definition"]
            rel=[{"type":x.attrib.get("relType",""),"target":x.attrib.get("target","")}
                 for x in e if local(x)=="SynsetRelation" and x.attrib.get("target")]
            if sid:synsets[sid]={"definition":defs[:4],"relation":rel}
    terms=defaultdict(set)
    entries=defaultdict(list)
    for e in root.iter():
        if local(e)!="LexicalEntry":continue
        lemma=next((x.attrib.get("writtenForm","") for x in e if local(x)=="Lemma"),"").strip()
        if not lemma:continue
        name=lemma.lower()
        for sense in e.iter():
            if local(sense)!="Sense":continue
            sid=sense.attrib.get("synset","")
            if sid:
                terms[sid].add(lemma)
                entries[name].append(sid)
    words={}
    for word,sids in entries.items():
        defs=[];synonyms=set();relations=[]
        for sid in dict.fromkeys(sids):
            data=synsets.get(sid,{})
            defs.extend(data.get("definition",[]))
            synonyms.update(term for term in terms.get(sid,set()) if term.lower()!=word)
            for item in data.get("relation",[])[:15]:
                if item.get("type") in ("hypernym","hyponym","similar","antonym"):
                    relations.append(item)
        words[word]={"definitions":list(dict.fromkeys(defs))[:8],
                     "synonyms":sorted(synonyms)[:25],"relations":relations[:20],
                     "source":"oewn"}
    if len(words)<10_000:raise ValueError("Suspiciously small Open English Wordnet XML index")
    payload={"schema":1,"language":"en","source":"oewn",
             "license":"CC-BY-4.0","attribution":SOURCES["oewn"]["credit"],
             "words":words}
    with out.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw,filename="",mode="wb",mtime=0,compresslevel=7) as z:
            z.write(json.dumps(payload,ensure_ascii=False,separators=(",",":")).encode())
    return len(words)
def add_asset(state,path,source,upstream_url,license,attribution,modified=False,version=""):
    if not path.is_file() or not license or not attribution:raise ValueError("Missing file or legal provenance")
    entry={"name":path.name,"bytes":path.stat().st_size,"sha256":sha256(path),
           "source":source,"source_url":upstream_url,"license":license,
           "license_url":SOURCES[source]["license_url"],"attribution":attribution,
           "version":version,"modified":modified}
    state["assets"].append(entry)
    return entry
def build_oewn(directory,state):
    source=SOURCES["oewn"];rel=upstream_release(source["repo"])
    assets=[a for a in rel["assets"] if a["name"].endswith((".zip",".gz"))]
    if len(assets)<6:raise ValueError("Missing official Open English Wordnet downloads")
    for a in assets:
        target=directory/("oewn--"+a["name"])
        download(a["browser_download_url"],target)
        verify(target,a)
        add_asset(state,target,"oewn",a["browser_download_url"],source["license"],source["credit"],
                  version=rel["tag_name"])
    xml=next((directory/("oewn--"+a["name"]) for a in assets
             if re.search(r"-plus\.xml\.gz$",a["name"])),None)
    if xml is None:xml=next((directory/("oewn--"+a["name"]) for a in assets if a["name"].endswith(".xml.gz")),None)
    if xml is None:raise ValueError("OEWN WN-LMF input not found")
    out=directory/"lexicon--oewn-en.json.gz"
    count=normalize_wordnet_xml(xml,out)
    add_asset(state,out,"oewn",f"https://github.com/{source['repo']}/releases/tag/{rel['tag_name']}",
              source["license"],source["credit"],True,rel["tag_name"])
    state["counts"]={"upstream_files":len(assets),"indexed_english_lemmas":count}
    state["version"]=rel["tag_name"]
def build_omw(directory,state):
    source=SOURCES["omw"];rel=upstream_release(source["repo"])
    assets=[a for a in rel["assets"] if a["name"].endswith(".tar.xz") or a["name"]=="index.toml"]
    if len(assets)<25:raise ValueError("OMW release incomplete")
    toml_asset=next((a for a in assets if a["name"]=="index.toml"),None)
    if not toml_asset:raise ValueError("OMW index.toml not available")
    indexpath=directory/"omw--index.toml"
    download(toml_asset["browser_download_url"],indexpath)
    verify(indexpath,toml_asset)
    index=tomllib.loads(indexpath.read_text())
    # Release index.toml uses top-level [omw-lang] sections; source-code
    # index.toml uses [packages.omw-lang]. Support both upstream layouts.
    packages=index.get("packages") or {k:v for k,v in index.items() if k.startswith("omw-") and isinstance(v,dict)}
    included=0;licenses={}
    for a in assets:
        if a["name"]=="index.toml":continue
        target=directory/("omw--"+a["name"])
        pkg=a["name"].removesuffix("-"+rel["tag_name"].lstrip("v")+".tar.xz")
        info=packages.get(pkg,{})
        if pkg=="omw":
            license="PER-COMPONENT; read each included wordnet license in upstream sources"
            attribution=index.get("citation",source["credit"])
        else:
            license=info.get("license")
            attribution=info.get("citation") or info.get("label")
            if not license or not attribution:raise ValueError("OMW component missing license/citation: "+pkg)
        download(a["browser_download_url"],target)
        verify(target,a)
        with tarfile.open(target,"r:xz") as archive:
            if not any(m.isfile() and m.name.endswith(".xml") for m in archive):raise ValueError("No WN-LMF XML in "+a["name"])
        add_asset(state,target,"omw",a["browser_download_url"],str(license),str(attribution),
                  version=rel["tag_name"])
        licenses[a["name"]]={"license":license,"citation":attribution,
                             "language":info.get("language","mul")}
        included+=1
    add_asset(state,indexpath,"omw",toml_asset["browser_download_url"],source["license"],source["credit"],version=rel["tag_name"])
    (directory/"omw--PER-PACKAGE-LICENSES.json").write_text(json.dumps(licenses,ensure_ascii=False,indent=2))
    add_asset(state,directory/"omw--PER-PACKAGE-LICENSES.json","omw",
              f"https://github.com/{source['repo']}/releases/tag/{rel['tag_name']}",
              source["license"],source["credit"],True,rel["tag_name"])
    state["counts"]={"upstream_files":included,"individual_licenses":len(licenses),
                      "languages":len(set(info["language"] for info in licenses.values()))}
    state["version"]=rel["tag_name"]
def hf_tree(path=""):
    """Discover the publisher's community conversion without assuming file names."""
    suffix="/"+path if path else ""
    url="https://huggingface.co/api/datasets/CleverThis/conceptnet/tree/main"+suffix+"?recursive=true"
    headers={"User-Agent":UA,"Accept":"application/json"}
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=90) as resp:
        return json.load(resp)
def build_conceptnet(directory,state):
    """Mirror original assertions when online; otherwise a clearly marked HF
    redistribution of ConceptNet. Never label converted Parquet as original CSV.
    """
    src=SOURCES["conceptnet"]
    path=directory/"conceptnet--assertions-5.7.0.csv.gz"
    source_url=CONCEPTNET_SOURCE
    try:
        download(CONCEPTNET_SOURCE,path)
    except urllib.error.HTTPError as e:
        if e.code not in (403,404,410):raise
        print("WARNING: official ConceptNet 5.7.0 assertions unavailable (HTTP "+str(e.code)+
              "); discovering CC BY-SA attributed community Parquet mirror",flush=True)
        path.unlink(missing_ok=True)
        files=hf_tree()
        flat=[x for x in files if x.get("path","").endswith(".parquet") and x.get("type")=="file"]
        if not flat:
            files=hf_tree("data")
            flat=[x for x in files if x.get("path","").endswith(".parquet") and x.get("type")=="file"]
        if not flat:raise ValueError("No downloadable ConceptNet Parquet mirror assets found")
        mirrored=0
        for file in flat:
            rel=file["path"]
            name="conceptnet--"+rel.replace("/","--")
            dest=directory/name
            url="https://huggingface.co/datasets/CleverThis/conceptnet/resolve/main/"+rel+"?download=true"
            download(url,dest)
            with dest.open("rb") as stream:
                if stream.read(4)!=b"PAR1":raise ValueError("Not a valid Parquet header: "+rel)
                stream.seek(-4,2)
                if stream.read(4)!=b"PAR1":raise ValueError("Not a valid Parquet footer: "+rel)
            digest=file.get("lfs",{}).get("oid")
            if digest and sha256(dest)!=digest:raise ValueError("HuggingFace mirror checksum mismatch "+rel)
            add_asset(state,dest,"conceptnet",url,"CC-BY-SA-4.0; community converted RDF Parquet",
                      src["credit"]+"; converted by CleverThis / CleverErnie",version="5.7.0",modified=True)
            mirrored+=1
        readme_url="https://huggingface.co/datasets/CleverThis/conceptnet/raw/main/README.md"
        readme=directory/"conceptnet--COMMUNITY-MIRROR-README.md"
        download(readme_url,readme,limit=2_000_000)
        add_asset(state,readme,"conceptnet",readme_url,src["license"],src["credit"]+"; CleverThis conversion",True,"5.7.0")
        state["version"]="5.7.0-community-parquet"
        state["counts"]={"mirror_format":"converted RDF Parquet","upstream_files":mirrored,
            "note":"Official CSV URL returned 403/404; files rehosted from CC BY-SA 4.0 CleverThis dataset. Per-edge CSV metadata cannot be assumed to be present."}
        return
    with path.open("rb") as f:
        if f.read(2)!=b"\x1f\x8b":raise ValueError("Official ConceptNet file is not gzipped")
    lines=0;languages=set();license_types=set()
    with gzip.open(path,"rt",encoding="utf8",errors="replace") as f:
        for row in f:
            lines+=1
            if lines<=10_000 or lines%5000==0:
                cols=row.split("\t")
                if len(cols)>4:
                    for col in (cols[2],cols[3]):
                        parts=col.split("/")
                        if len(parts)>2 and parts[1]=="c":languages.add(parts[2])
                    try:license_types.add(json.loads(cols[4]).get("license",""))
                    except Exception:pass
    if lines<1_000_000:raise ValueError("ConceptNet assertions suspiciously small: "+str(lines))
    add_asset(state,path,"conceptnet",CONCEPTNET_SOURCE,src["license"],src["credit"],version="5.7.0")
    state["counts"]={"assertion_rows":lines,"sampled_language_codes":len(languages),
                     "sampled_edge_licenses":sorted(license_types)}
    state["version"]="5.7.0"
    for name,url in [
       ("conceptnet--LICENSE.txt","https://raw.githubusercontent.com/commonsense/conceptnet5/master/LICENSE.txt"),
       ("conceptnet--DATA-CREDITS.txt","https://raw.githubusercontent.com/commonsense/conceptnet5/master/DATA-CREDITS.txt")]:
        target=directory/name
        download(url,target,limit=20_000_000)
        add_asset(state,target,"conceptnet",url,src["license"],src["credit"],version="5.7.0")
def finish(dir,state):
    if not state["assets"]:raise ValueError("No verified source assets")
    files=dir/"LEXICAL-MANIFEST.json"
    files.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    notices=dir/"THIRD-PARTY-LEXICAL-NOTICES.md"
    lines=["# Lexical source attribution",
           "No underlying dictionary, graph or corpus is owned by danilfg.",
           "Original upstream licenses, credits and per-component requirements remain in force.",
           "Independent aggregation does not guarantee linguistic accuracy or fitness.",""]
    for a in state["assets"]:
        lines+=["## "+a["name"],"Source: "+a["source_url"],
                "License: "+a["license"],"Attribution: "+a["attribution"],
                "Modified: "+str(a["modified"]),"SHA-256: "+a["sha256"],""]
    notices.write_text("\n".join(lines),encoding="utf8")
def publish(dir,state,tag):
    if os.environ.get("GITHUB_REPOSITORY")!=REPO:raise ValueError("Refusing foreign repo")
    title=f"{state['source']} lexical snapshot — {state['version']}"
    body="Third-party dictionary/graph resources. Read LEXICAL-MANIFEST.json and THIRD-PARTY-LEXICAL-NOTICES.md; license terms differ among data sources."
    gh("release","create",tag,"-R",REPO,"--draft","--latest=false","--title",title,"--notes",body)
    names=[p for p in sorted(dir.iterdir()) if p.is_file()]
    if len(names)>1000:raise ValueError("GitHub release asset limit exceeded")
    for i in range(0,len(names),10):
        gh("release","upload",tag,*map(str,names[i:i+10]),"-R",REPO,"--clobber")
    listed=json.loads(gh("release","view",tag,"-R",REPO,"--json","assets"))
    if len(listed["assets"])!=len(names):raise ValueError("Release asset count mismatch")
    gh("release","edit",tag,"-R",REPO,"--draft=false","--latest=false")
    print("PUBLISHED "+f"https://github.com/{REPO}/releases/tag/{tag}",flush=True)
def main():
    p=argparse.ArgumentParser();p.add_argument("--source",choices=tuple(SOURCES),required=True)
    args=p.parse_args()
    if os.getenv("GITHUB_REPOSITORY")!=REPO:raise ValueError("Expected GitHub repository "+REPO)
    version=upstream_release(SOURCES[args.source]["repo"])["tag_name"] if args.source!="conceptnet" else "5.7.0"
    tag=f"lex-{args.source}-{version}-v1"
    try:
        previous=json.loads(gh("release","view",tag,"-R",REPO,"--json","isDraft,assets"))
        if not previous.get("isDraft") and any(a["name"]=="LEXICAL-MANIFEST.json" for a in previous.get("assets",[])):
            print("UP-TO-DATE "+tag+" (existing verified publication)",flush=True);return
    except RuntimeError:pass
    state={"schema":1,"source":args.source,"publisher":REPO,
            "generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),
            "assets":[],"versions":{},"license_registry":SOURCES,"status":"complete"}
    with tempfile.TemporaryDirectory() as tmp:
        directory=Path(tmp)
        if args.source=="oewn":build_oewn(directory,state)
        elif args.source=="omw":build_omw(directory,state)
        else:build_conceptnet(directory,state)
        finish(directory,state)
        publish(directory,state,tag)
if __name__=="__main__":main()
