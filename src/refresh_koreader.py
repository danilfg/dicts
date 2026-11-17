"""Download only changed KOReader ZIPs; retain verified previous copies on a per-file outage."""
import argparse
import json
import subprocess
from pathlib import Path
from normalized_pack import pull,sha
from unified_release import inventory,gh,REPO
from upstream_cache import matching_digest
UPSTREAM="DanielGregorini/koreader-dicts"

def latest():
    return json.loads(gh("api",f"repos/{UPSTREAM}/releases/latest"))

def run(previous,output):
    output.mkdir(parents=True,exist_ok=True)
    old=inventory(previous)
    last=latest()
    pages=json.loads(gh("api","--paginate","--slurp",f"repos/{UPSTREAM}/releases/{last['id']}/assets?per_page=100"))
    upstream=[x for page in pages for x in page if x["name"].endswith(".zip")]
    if len(upstream)<74:raise ValueError("Unexpectedly incomplete KOReader catalog")
    seen=set()
    fallbacks={}
    for a in upstream:
        name=a["name"];target=output/name;oldname="koreader--"+name
        if Path(name).name!=name or name in seen:raise ValueError("Invalid upstream name")
        seen.add(name)
        prior=old.get(oldname)
        if prior and matching_digest(prior,a):
            pull(previous,[oldname],output,old)
            (output/oldname).rename(target)
            continue
        try:
            subprocess.run(["gh","release","download",last["tag_name"],"-R",UPSTREAM,"--pattern",name,"--dir",str(output),"--clobber"],check=True)
            if target.stat().st_size!=a["size"] or (a.get("digest") and "sha256:"+sha(target)!=a["digest"]):
                raise ValueError("KOReader upstream integrity mismatch")
        except (subprocess.CalledProcessError,OSError,ValueError) as exc:
            target.unlink(missing_ok=True)
            fallbacks[oldname]={"source":"koreader","previous_release":previous,"retained":bool(prior),"reason":str(exc)[:350]}
            if prior:
                pull(previous,[oldname],output,old)
                (output/oldname).rename(target)
    count=len(list(output.glob("*.zip")))
    if count<74:raise ValueError("Too few verified KOReader archives")
    (output/"SOURCE_INFO.json").write_text(json.dumps({"repository":UPSTREAM,"tag":last["tag_name"],"expected":count,"fallbacks":fallbacks}))
    print(f"Verified KOReader archives: {count}, unavailable: {len(fallbacks)}",flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--previous",required=True);p.add_argument("--out",default="upstream")
    a=p.parse_args();run(a.previous,Path(a.out))
