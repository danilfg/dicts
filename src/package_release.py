#!/usr/bin/env python3
"""Reproducible sharded bundles; no GitHub release asset >= 2 GiB."""
import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

MAX_BYTES=1_600_000_000
COMMON=("manifest.json","THIRD-PARTY-NOTICES.md")

def sha256(file):
    h=hashlib.sha256()
    with file.open("rb") as f:
        while data:=f.read(1024*1024):h.update(data)
    return h.hexdigest()

def one_zip(dest,files,root):
    with zipfile.ZipFile(dest,"w",compression=zipfile.ZIP_STORED,allowZip64=True) as z:
        for name in files:
            info=zipfile.ZipInfo("dicts/"+name,date_time=(1980,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_STORED
            info.external_attr=0o644<<16
            with z.open(info,"w",force_zip64=True) as output,(root/name).open("rb") as source:
                shutil.copyfileobj(source,output,1024*1024)
    if dest.stat().st_size>MAX_BYTES:raise ValueError("Oversized distribution part: "+dest.name)
    with zipfile.ZipFile(dest) as z:
        if z.testzip():raise ValueError("Corrupted output ZIP: "+dest.name)
        if set(z.namelist())!=set("dicts/"+n for n in files):raise ValueError("Missing bundle member")

def build(dist):
    source=json.loads((dist/"manifest.json").read_text())
    names=sorted(a["name"] for a in source["assets"])
    for name in names+list(COMMON):
        if not (dist/name).is_file():raise FileNotFoundError(name)
        if (dist/name).stat().st_size>=MAX_BYTES:raise ValueError("Individual asset requires further splitting: "+name)
    groups=[];current=[];total=sum((dist/n).stat().st_size for n in COMMON)
    for name in names:
        size=(dist/name).stat().st_size+160
        if current and total+size>=MAX_BYTES:
            groups.append(current);current=[];total=sum((dist/n).stat().st_size for n in COMMON)
        current.append(name);total+=size
    if current:groups.append(current)
    parts=[]
    for i,group in enumerate(groups,1):
        # Preserve single-file installation for smaller distributions.
        name="dicts-all.zip" if len(groups)==1 else "dicts-part-%03d.zip"%i
        dest=dist/name
        members=sorted(group+list(COMMON))
        one_zip(dest,members,dist)
        parts.append({"file":name,"bytes":dest.stat().st_size,
                      "sha256":sha256(dest),"members":group})
    (dist/"BUNDLE-PARTS.json").write_text(json.dumps({
        "schema":1,"description":"Collection is split to respect GitHub's per-asset 2-GiB limit. Download all parts for a complete snapshot.",
        "parts":parts,"source_asset_count":len(names),
        "notes":"Each nested original dictionary retains its own LICENSE and ATTRIBUTION."
    },ensure_ascii=False,indent=2)+"\n")
    with (dist/"SHA256SUMS.txt").open("w") as f:
        for entry in sorted(dist.iterdir()):
            if entry.is_file() and entry.name!="SHA256SUMS.txt":
                f.write(sha256(entry)+"  "+entry.name+"\n")
    print("Bundle parts:",len(parts),"source assets:",len(names),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--dist",default="dist")
    build(Path(p.parse_args().dist))
