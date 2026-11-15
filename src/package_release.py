#!/usr/bin/env python3
"""Build one non-relicensed aggregate ZIP from independently licensed assets."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

MAX_BYTES=1_900_000_000

def sha256(file):
    h=hashlib.sha256()
    with file.open("rb") as f:
        for data in iter(lambda:f.read(1024*1024),b""):
            h.update(data)
    return h.hexdigest()

def build(dist):
    manifest=json.loads((dist/"manifest.json").read_text())
    assets=sorted(x["name"] for x in manifest["assets"])
    expected=set(assets+["manifest.json","THIRD-PARTY-NOTICES.md"])
    for name in expected:
        if not (dist/name).is_file():raise FileNotFoundError(name)
    bundle=dist/"dicts-all.zip"
    with zipfile.ZipFile(bundle,"w",compression=zipfile.ZIP_STORED,allowZip64=True) as z:
        for name in sorted(expected):
            z.write(dist/name,arcname="dicts/"+name)
    if bundle.stat().st_size>=MAX_BYTES:raise ValueError("Aggregate archive exceeds safe GitHub size limit")
    with zipfile.ZipFile(bundle) as z:
        if {p.removeprefix("dicts/") for p in z.namelist()}!=expected:
            raise ValueError("Aggregate archive missing assets")
        if z.testzip():raise ValueError("Aggregate ZIP checksum error")
    checksum_file=dist/"SHA256SUMS.txt"
    with checksum_file.open("w") as f:
        for x in sorted(dist.iterdir()):
            if x.is_file() and x.name!=checksum_file.name:
                f.write(sha256(x)+"  "+x.name+"\n")
    print("Bundle built:",bundle.name,"bytes",bundle.stat().st_size,
          "files",len(expected),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--dist",default="dist")
    build(Path(p.parse_args().dist))
