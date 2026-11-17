#!/usr/bin/env python3
"""Read the public Dicts catalog and install exactly one language direction."""
import argparse
import gzip
import hashlib
import json
import re
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path
from io import BytesIO

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from public_client import REGISTRY, public_blob

BASE="https://github.com/danilfg/dicts/releases/"
TAG=re.compile(r"v\d{4}\.\d{2}\.\d{2}\.\d+\.\d+")
def fetch_json(url):
    with urllib.request.urlopen(url,timeout=120) as r:
        return r.read()
def verify(data,meta):
    if len(data)!=meta["bytes"] or hashlib.sha256(data).hexdigest()!=meta["sha256"]:
        raise ValueError("Size or SHA-256 mismatch")
    return data
def normalize(word):
    return " ".join(word.casefold().strip().split())
def shard_path(word,folder,buckets):
    n=hashlib.sha256(word.encode("utf-8")).digest()[0]%buckets
    return f"{folder}/{n:02x}.json.gz"
def units(index,pair):
    p=index["pairs"][pair]
    for group,desc in sorted(index["groups"].items()):
        if pair in desc["pairs"]:
            yield group,"pairs",pair,desc["pairs"][pair]
        for lang in dict.fromkeys((p["from"],p["to"])):
            if lang in desc["languages"]:
                yield group,"languages",lang,desc["languages"][lang]
class Client:
    def __init__(self,cache=".dicts-cache",version=None):
        self.cache=Path(cache)
        if version and not TAG.fullmatch(version):raise ValueError("Invalid release tag")
        p=self.cache/"catalogs"/version/"PAIR-INDEX.json" if version else None
        if p and p.exists():
            master=json.loads((p.parent/"LEXICAL-INDEX.json").read_bytes())
            data=verify(p.read_bytes(),master["pair_index"])
        else:
            master=json.loads(fetch_json(BASE+(f"download/{version}/" if version else "latest/download/")+"LEXICAL-INDEX.json"))
            if master.get("format")!="oci-pair-v1":raise ValueError("No OCI pair release published yet")
            tag=master["version"]
            if not TAG.fullmatch(tag) or (version and version!=tag):raise ValueError("Invalid release version")
            if master["registry"]!=REGISTRY or master["download_base"]!=BASE+f"download/{tag}/":raise ValueError("Unexpected transport")
            data=verify(fetch_json(master["download_base"]+"PAIR-INDEX.json"),master["pair_index"])
            p=self.cache/"catalogs"/tag/"PAIR-INDEX.json"
            p.parent.mkdir(parents=True,exist_ok=True)
            (p.parent/"LEXICAL-INDEX.json").write_text(json.dumps(master))
            p.write_bytes(data)
        self.index=json.loads(data)
        if (self.index["schema"],self.index["format"],self.index["registry"],self.index["version"])!=(1,"oci-pair-v1",REGISTRY,master["version"]):
            raise ValueError("Incompatible catalog")
    def block(self,meta):
        key=meta["sha256"]
        if not re.fullmatch(r"[0-9a-f]{64}",key):raise ValueError("Invalid digest")
        path=self.cache/"blobs"/(key+".zip")
        if path.is_file():
            try:return verify(path.read_bytes(),meta)
            except ValueError:pass
        data=public_blob(REGISTRY,meta)
        path.parent.mkdir(parents=True,exist_ok=True)
        tmp=path.with_suffix(".partial")
        tmp.write_bytes(data);tmp.replace(path)
        return data
    def install(self,pair):
        result=[]
        for group,scope,key,blocks in units(self.index,pair):
            for block in blocks:self.block(block)
            result.append({"group":group,"scope":scope,"id":key,"blocks":len(blocks),
                           "bytes":sum(b["bytes"] for b in blocks)})
        return result
    def lookup(self,pair,query):
        word=normalize(query);output=[]
        for group,scope,key,blocks in units(self.index,pair):
            # UNIT.json is in exactly one block of this unit.
            files={};meta=None
            for block in blocks:
                with zipfile.ZipFile(BytesIO(self.block(block))) as z:
                    for name in z.namelist():
                        if name in files:raise ValueError("Duplicate unit member")
                        files[name]=block
                    if "UNIT.json" in z.namelist():meta=json.loads(z.read("UNIT.json"))
            if not meta or (meta["group"],meta["scope"],meta["id"],meta["schema"])!=(group,scope,key,1):
                raise ValueError("Wrong unit descriptor")
            if meta["kind"]=="bilingual":
                paths=[shard_path(word,"data/"+key,meta["descriptor"]["buckets"])]
            elif meta["kind"]=="links":
                paths=[shard_path(word,meta["path"],meta["buckets"])]
            elif meta["kind"]=="lexical":
                paths=[shard_path(word,d["path"],d["buckets"]) for d in meta["descriptors"]]
            else:
                # Unknown source groups may use known kinds; future kinds are
                # installed unchanged, but need an explicit lookup adapter.
                continue
            for path in paths:
                if path not in files:continue
                with zipfile.ZipFile(BytesIO(self.block(files[path]))) as z:
                    shard=json.loads(gzip.decompress(z.read(path)))
                entry=shard["words"].get(word)
                if entry is not None:output.append({"group":group,"scope":scope,"id":key,"member":path,"entry":entry,"unit":meta})
        return output
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("word",nargs="?");p.add_argument("--pair",default="en-ru")
    p.add_argument("--version");p.add_argument("--cache",default=".dicts-cache")
    p.add_argument("--list",action="store_true");p.add_argument("--install",action="store_true")
    a=p.parse_args();client=Client(a.cache,a.version)
    if a.list:print(json.dumps(client.index["pairs"],ensure_ascii=False,indent=2));return
    if a.pair not in client.index["pairs"]:p.error("Unknown direction; use --list")
    if a.install:result=client.install(a.pair)
    elif a.word:result=client.lookup(a.pair,a.word)
    else:p.error("Provide a word, --list or --install")
    print(json.dumps({"version":client.index["version"],"pair":a.pair,"results":result},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
