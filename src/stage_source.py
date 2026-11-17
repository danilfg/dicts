"""Refresh or safely retain a complete, previously published source family."""
import argparse
import json
import subprocess
import tempfile
import time
import os
from pathlib import Path
from unified_release import REPO, inventory, digest, release, gh, upload
from upstream_cache import matching_digest

def belongs(name, source):
    return name.startswith(source+"--") or (source=="oewn" and name.startswith("lexicon--oewn-"))

def copy_source(previous,tag,previous_assets,prior):
    from normalized_pack import pull
    from storage import link
    linked=[n for n in prior if previous_assets[n].get("oci")]
    if linked:link(tag,previous_assets,linked)
    prior=[n for n in prior if n not in set(linked)]
    for start in range(0,len(prior),3):
        batch=prior[start:start+3]
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            pull(previous,batch,folder,previous_assets)
            upload(tag,[folder/name for name in batch])

def upstream_unchanged(source,previous_assets):
    # GitHub's authoritative asset SHA-256 allows skipping unchanged upstream archives.
    from sync_lexical import SOURCES,upstream_release
    if source not in ("oewn","omw"):return False
    rel=upstream_release(SOURCES[source]["repo"])
    upstream=[a for a in rel["assets"] if (a["name"].endswith((".zip",".gz")) if source=="oewn" else a["name"].endswith(".tar.xz") or a["name"]=="index.toml")]
    originals={n for n in previous_assets if n.startswith(source+"--") and
               (n.endswith((".zip",".gz")) if source=="oewn" else n.endswith(".tar.xz") or n=="omw--index.toml")}
    return bool(upstream) and originals=={source+"--"+a["name"] for a in upstream} and all(
        matching_digest(previous_assets[source+"--"+a["name"]],a) for a in upstream)

def stage(tag, previous, source):
    script="mirror_raw.py" if source in ("kaikki","tatoeba") else "sync_lexical.py"
    previous_assets=inventory(previous)
    prior=[n for n in previous_assets if belongs(n,source)]
    try:
        if prior and upstream_unchanged(source,previous_assets):
            copy_source(previous,tag,previous_assets,prior)
            print("Reused unchanged verified "+source,flush=True)
            return
        proc=subprocess.run(["python",str(Path(__file__).with_name(script)),"--source",source],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,env=dict(os.environ,UNIFIED_RELEASE_TAG=tag))
        print(proc.stdout,flush=True)
        if proc.returncode:raise ValueError(" ".join(proc.stdout.splitlines()[-4:])[-350:])
        current=inventory(tag)
        if source in ("kaikki","tatoeba"):
            # A retried transfer may previously have uploaded longer trailing parts.
            from normalized_pack import pull
            with tempfile.TemporaryDirectory() as tmp:
                manifest=source+"--SOURCE-MANIFEST.json"
                pull(tag,[manifest],Path(tmp),current)
                report=json.loads((Path(tmp)/manifest).read_text())
                expected={p["asset"] for item in report["sources"] for p in item["parts"]}
                expected|={manifest,source+"--ATTRIBUTION-AND-LICENSE.txt"}
                from storage import remove
                remove(tag,[name for name in current if belongs(name,source) and name not in expected])
        if source=="conceptnet" and "conceptnet--assertions-5.7.0.csv.gz" not in current:
            raise ValueError("Official CSV unavailable; retain prior CSV for normalization")
        return
    except (subprocess.CalledProcessError,ValueError,OSError) as exc:
        if not prior:raise
        reason=str(exc)[:350]
        print(f"::warning::{source}: refresh failed; retaining {previous}: {reason}",flush=True)
    # Delete incomplete assets of this source only. Never edit prior release.
    from storage import remove
    remove(tag,[name for name in inventory(tag) if belongs(name,source)])
    copy_source(previous,tag,previous_assets,prior)
    with tempfile.TemporaryDirectory() as tmp:
        folder=Path(tmp)
        note=folder/f"retained--{source}.json"
        note.write_text(json.dumps({"source":source,"previous_release":previous,"retained":True,"reason":reason})+"\n")
        upload(tag,[note])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--tag",required=True);p.add_argument("--previous",required=True)
    p.add_argument("--source",choices=["kaikki","tatoeba","oewn","omw","conceptnet"],required=True)
    a=p.parse_args();stage(a.tag,a.previous,a.source)
