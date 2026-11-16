#!/usr/bin/env python3
"""Build a fully static, source-labelled dictionary search index for GitHub Pages.

All bilingual entries come from the published StarDict ZIPs. Published study
enrichments add available definitions/examples without replacing original
translations. Shard requests are deterministic and browser-loadable via gzip.
"""
from __future__ import annotations
import argparse
import collections
import datetime as dt
import gzip
import hashlib
import html
import io
import json
import math
import re
import shutil
import struct
import zipfile
from pathlib import Path

SOURCES=("koreader","freedict","wikdict")
PAIRS_RE=re.compile(r"^(koreader|freedict|wikdict)--([a-z0-9]+-[a-z0-9]+)\.zip$")
COMPRESSED=re.compile(r"^enrichment--([a-z0-9]+-[a-z0-9]+)\.json\.gz$")
MAX_SITE_BYTES=945_000_000
MAX_ARCHIVE_BYTES=250_000_000

def normalize(word: str) -> str:
    return " ".join(word.casefold().strip().split())

def bucket(word: str, count: int) -> int:
    return hashlib.sha256(word.encode("utf-8")).digest()[0] % count

def clean_text(blob: bytes) -> str:
    """Preserve all readable dictionary content, without exposing unsafe HTML."""
    decoded=blob.decode("utf-8","replace").replace("\x00","\n")
    decoded=re.sub(r"<(?:br|/p|/div|/li)\b[^>]*>", "\n", decoded,flags=re.I)
    decoded=re.sub(r"<[^>]+>"," ",decoded)
    decoded=html.unescape(decoded).replace("\r","\n")
    return re.sub(r"[ \t]+"," ",decoded).strip()

def extract_stardict(path: Path):
    """Yield complete text entries. Supports 32/64-bit .idx offset fields."""
    with zipfile.ZipFile(path) as pack:
        if pack.testzip():raise ValueError("Corrupt ZIP: "+str(path))
        names=[n for n in pack.namelist() if not n.endswith("/")]
        candidates=[n for n in names if n.endswith(".idx")]
        if not candidates:raise ValueError("Missing .idx: "+path.name)
        for indexname in candidates:
            stem=indexname[:-4]
            dataname=next((n for n in (stem+".dict",stem+".dict.dz",stem+".dict.gz") if n in names),None)
            if dataname is None:continue
            info=next((n for n in (stem+".ifo",) if n in names),None)
            ifobytes=pack.read(info) if info else b""
            use64=b"idxoffsetbits=64" in ifobytes
            field_width=12 if use64 else 8
            index=pack.read(indexname)
            data=pack.read(dataname)
            if dataname.endswith((".gz",".dz")):data=gzip.decompress(data)
            position=0
            while position<len(index):
                end=index.find(b"\0",position)
                if end<0 or end+1+field_width>len(index):break
                label=normalize(index[position:end].decode("utf-8","replace"))
                start,count=struct.unpack(">QI" if use64 else ">II",index[end+1:end+1+field_width])
                position=end+1+field_width
                if not label or not count or start+count>len(data):continue
                meaning=clean_text(data[start:start+count])
                if meaning:yield label, meaning

def write_gzip(path: Path,obj) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("wb") as out:
        with gzip.GzipFile(fileobj=out,filename="",mtime=0,mode="wb",compresslevel=9) as z:
            # JSONEncoder yields tiny tokens, sometimes millions. Buffer them so
            # gzip gets large chunks instead of one syscall per token.
            pieces=[]
            characters=0
            for piece in json.JSONEncoder(ensure_ascii=False,separators=(",",":")).iterencode(obj):
                pieces.append(piece)
                characters+=len(piece)
                if characters>=1_000_000:
                    z.write("".join(pieces).encode("utf-8"))
                    pieces=[]
                    characters=0
            if pieces:z.write("".join(pieces).encode("utf-8"))

def enrich_records(words:dict, data:dict):
    if data.get("schema")!=1 or not isinstance(data.get("words"),dict):
        raise ValueError("Invalid enrichment schema")
    for label,values in data["words"].items():
        key=normalize(label)
        if not key or not isinstance(values,dict):continue
        row=words.setdefault(key,{"translations":{},"meanings":[],"examples":[]})
        # Raw StarDict output always takes precedence over short excerpt indexes.
        for item in values.get("translations",[]):
            source=item.get("source")
            meaning=item.get("text","")
            if source not in SOURCES or not meaning:continue
            if source not in row["translations"]:
                row["translations"][source]=[meaning]
        for category in ("meanings","examples"):
            for item in values.get(category,[]):
                if isinstance(item,dict) and item.get("text"):
                    # Preserve license/source URL and sentence author from original.
                    if item not in row[category]:row[category].append(item)

def index_pair(pair:str,files:list[tuple[str,Path]],enrichment:Path|None,site:Path,manifest:dict):
    words={}
    sources=[]
    for source,path in files:
        count=0
        for label,value in extract_stardict(path):
            row=words.setdefault(label,{"translations":{},"meanings":[],"examples":[]})
            group=row["translations"].setdefault(source,[])
            if value not in group:group.append(value)
            count+=1
        sources.append({"id":source,"records":count})
        print("Indexed",pair,source,count,flush=True)
    if enrichment and enrichment.is_file():
        with gzip.open(enrichment,"rt",encoding="utf-8") as f:
            enrich_records(words,json.load(f))
    if not words:return None
    num=len(words)
    count=1 if num<10000 else 4 if num<50000 else 16 if num<250000 else 32
    shards=[{} for _ in range(count)]
    for word,entry in words.items():
        shards[bucket(word,count)][word]=entry
    folder=site/"data"/pair
    total=0
    for i,entries in enumerate(shards):
        # Publish even empty buckets so an unknown word yields a clean
        # "not found" response, not an HTTP 404 and a broken UI.
        output=folder/("%02x.json.gz"%i)
        write_gzip(output,{"schema":1,"pair":pair,"words":entries})
        total+=output.stat().st_size
    result={"pair":pair,"from":pair.split("-")[0],"to":pair.split("-")[1],
            "entries":num,"sources":sources,"buckets":count,"compressed_bytes":total}
    print("Pair complete:",pair,num,"entries",total,"bytes",flush=True)
    return result

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--download-dir",default="downloads")
    cli.add_argument("--site-dir",default="site")
    cli.add_argument("--manifest",default="downloads/manifest.json")
    cli.add_argument("--release-tag",default="")
    args=cli.parse_args()
    downloads=Path(args.download_dir)
    site=Path(args.site_dir)
    (site/"data").mkdir(parents=True,exist_ok=True)
    m=json.loads(Path(args.manifest).read_text())
    assets={v["name"]:v for v in m["assets"]}
    grouped=collections.defaultdict(list)
    for path in downloads.glob("*.zip"):
        match=PAIRS_RE.match(path.name)
        if match:
            source,pair=match.groups()
            info=assets.get(path.name)
            if not info:raise ValueError("Published package missing from manifest: "+path.name)
            if path.stat().st_size!=info["bytes"]:
                raise ValueError("Incomplete archive download: "+path.name)
            grouped[pair].append((source,path))
    if not grouped:raise ValueError("No dictionary ZIPs downloaded")
    for pair,group in grouped.items():
        group.sort(key=lambda q:SOURCES.index(q[0]))
    enrichments={}
    for f in downloads.glob("enrichment--*.json.gz"):
        match=COMPRESSED.match(f.name)
        if match:enrichments[match.group(1)]=f
    # Extra enrichment ZIPs contain only enrichment--pair.json.gz plus notices.
    for pack in downloads.glob("enrichments-extra--*.zip"):
        with zipfile.ZipFile(pack) as z:
            for name in z.namelist():
                match=COMPRESSED.match(Path(name).name)
                if not match:continue
                pair=match.group(1)
                if pair in enrichments:continue
                dest=downloads/"extracted-enrichment"/Path(name).name
                dest.parent.mkdir(exist_ok=True)
                with z.open(name) as src,dest.open("wb") as out:shutil.copyfileobj(src,out)
                enrichments[pair]=dest
    for pair in enrichments:grouped.setdefault(pair,[])
    catalog=[]
    for pair in sorted(grouped):
        data=index_pair(pair,grouped[pair],enrichments.get(pair),site,m)
        if data:catalog.append(data)
    if not catalog:raise ValueError("No searchable dictionary entries generated")
    published={}
    for item in m["assets"]:
        match=PAIRS_RE.match(item["name"])
        if not match:continue
        source,pair=match.groups()
        published.setdefault(pair,{})[source]={
            "download_url":"https://github.com/danilfg/dicts/releases/download/"+
                (args.release_tag or m.get("tag",""))+"/"+item["name"],
            "license":item.get("license","See original archive"),
            "attribution":item.get("attribution","See original archive"),
            "source_url":item.get("source_url",""),
            "license_url":item.get("license_url","")}
    stats={"schema":1,"title":"Dicts searchable dictionary index",
           "release_tag":args.release_tag or m.get("tag",""),
           "updated":dt.datetime.now(dt.timezone.utc).isoformat(),
           "pairs":catalog,"provenance":published,
           "notice":"A source package may have its own license. The aggregator does not guarantee linguistic quality."}
    (site/"data"/"catalog.json").write_text(json.dumps(stats,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    (site/".nojekyll").write_text("")
    size=sum(p.stat().st_size for p in site.rglob("*") if p.is_file())
    if size>MAX_SITE_BYTES:
        raise ValueError("Pages index exceeds GitHub Pages 1 GB limit: "+str(size)+
          ". Data must be moved to a separate indexed release/CDN before deploying.")
    print("PAGES INDEX READY",len(catalog),"pairs; bytes",size,flush=True)

if __name__=="__main__":main()
