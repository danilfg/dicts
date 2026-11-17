"""Refresh or safely retain a complete, previously published source family."""
import argparse
import json
import subprocess
import tempfile
import time
import os
from pathlib import Path
from unified_release import REPO, inventory, digest, release, gh, upload

def belongs(name, source):
    return name.startswith(source+"--") or (source=="oewn" and name.startswith("lexicon--oewn-"))

def stage(tag, previous, source):
    script="mirror_raw.py" if source in ("kaikki","tatoeba") else "sync_lexical.py"
    previous_assets=inventory(previous)
    prior=[n for n in previous_assets if belongs(n,source)]
    try:
        proc=subprocess.run(["python",str(Path(__file__).with_name(script)),"--source",source],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,env=dict(os.environ,UNIFIED_RELEASE_TAG=tag))
        print(proc.stdout,flush=True)
        if proc.returncode:raise ValueError(" ".join(proc.stdout.splitlines()[-4:])[-350:])
        current=inventory(tag)
        if source=="conceptnet" and "conceptnet--assertions-5.7.0.csv.gz" not in current:
            raise ValueError("Official CSV unavailable; retain prior CSV for normalization")
        return
    except (subprocess.CalledProcessError, ValueError) as exc:
        if not prior:raise
        reason=str(exc)[:350]
        print(f"::warning::{source}: refresh failed; retaining {previous}: {reason}",flush=True)
    # Delete incomplete assets of this source only. Never edit prior release.
    for name,asset in inventory(tag).items():
        if belongs(name,source):
            gh("api","--method","DELETE",f"repos/{REPO}/releases/assets/{asset['id']}")
    with tempfile.TemporaryDirectory() as tmp:
        folder=Path(tmp)
        for start in range(0,len(prior),3):
            batch=prior[start:start+3]
            cmd=["gh","release","download",previous,"-R",REPO,"--dir",tmp]
            for name in batch:cmd+=["--pattern",name]
            subprocess.run(cmd,check=True)
            import hashlib
            for name in batch:
                path=folder/name
                with path.open("rb") as f:h=hashlib.file_digest(f,"sha256").hexdigest()
                if h!=digest(previous_assets[name]) or path.stat().st_size!=previous_assets[name]["size"]:
                    raise ValueError("Retained source checksum mismatch "+name)
            upload(tag,[folder/name for name in batch])
            for name in batch:(folder/name).unlink()
        note=folder/f"retained--{source}.json"
        note.write_text(json.dumps({"source":source,"previous_release":previous,"retained":True,"reason":reason})+"\n")
        upload(tag,[note])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--tag",required=True);p.add_argument("--previous",required=True)
    p.add_argument("--source",choices=["kaikki","tatoeba","oewn","omw","conceptnet"],required=True)
    a=p.parse_args();stage(a.tag,a.previous,a.source)
