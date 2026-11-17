"""Deploy the pre-normalized compact website indexes without parsing dictionaries."""
import argparse
import json
import shutil
import tempfile
from pathlib import Path
from normalized_pack import pull,unpack
from unified_release import inventory

def run(tag,site):
    assets=inventory(tag)
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)
        for group in ("pages","pages-lexical"):
            name=f"normalized--{group}-index.json"
            pull(tag,[name],p,assets)
            doc=json.loads((p/name).read_text())
            pull(tag,[x["name"] for x in doc["packages"]],p,assets)
            unpack(p,doc,site)
            for x in doc["packages"]:(p/x["name"]).unlink()
    (site/".nojekyll").write_text("")
    pair=site/"data/catalog.json"
    lexical=site/"data/lexical/catalog.json"
    if not pair.is_file() or not lexical.is_file():raise ValueError("Missing public indexes")
    size=sum(p.stat().st_size for p in site.rglob("*") if p.is_file())
    if size>=1_000_000_000:raise ValueError("Pages deployment exceeds 1 GB")
    if not json.loads(pair.read_text())["pairs"]:raise ValueError("Empty pair catalog")
    if not all(json.loads(lexical.read_text())["sources"][s]["languages"] for s in ("oewn","omw","conceptnet")):raise ValueError("Incomplete lexical Pages catalog")
    print("Normalized Pages ready:",size,"bytes",flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--tag",required=True);p.add_argument("--site-dir",default="site")
    a=p.parse_args();run(a.tag,Path(a.site_dir))
