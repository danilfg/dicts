#!/usr/bin/env python3
"""Consolidate, verify and publish one versioned release for all eight sources."""
import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
import urllib.request
from release_changes import diff_plan, confirm_zip_changes
from normalized_pack import GROUPS
from pathlib import Path
REPO="danilfg/dicts"
OLD={"main":"data-20261116-093517","kaikki":"raw-kaikki-20261116-090335",
     "tatoeba":"raw-tatoeba-20261116-090344","oewn":"lex-oewn-2025-edition-v1",
     "omw":"lex-omw-v2.0-v1","conceptnet":"lex-conceptnet-5.7.0-v1"}
RAW=("SOURCE-MANIFEST.json","ATTRIBUTION-AND-LICENSE.txt")
LEX=("LEXICAL-MANIFEST.json","THIRD-PARTY-LEXICAL-NOTICES.md")
def gh(*args):
    return subprocess.check_output(["gh",*args],text=True).strip()
def release(tag):
    # A draft can exist before its git tag does; the authenticated release
    # list includes drafts, unlike the published-release-by-tag endpoint.
    if tag.startswith("v"):
        pages=json.loads(gh("api","--paginate","--slurp",f"repos/{REPO}/releases?per_page=100"))
        return next(r for page in pages for r in page if r["tag_name"]==tag)
    return json.loads(gh("api",f"repos/{REPO}/releases/tags/{tag}"))
def inventory(tag):
    rel=release(tag)
    # The release response includes the assets; use pagination if the
    # response looks capped, and always validate completeness afterwards.
    pages=json.loads(gh("api","--paginate","--slurp",f"repos/{REPO}/releases/{rel['id']}/assets?per_page=100"))
    rows=[a for page in pages for a in page]
    assert len({a["name"] for a in rows})==len(rows)
    return {a["name"]:a for a in rows}
def digest(a):
    d=a.get("digest") or ""
    if not re.fullmatch(r"sha256:[0-9a-f]{64}",d) or not 0<a["size"]<2**31:
        raise ValueError("Invalid release asset: "+a["name"])
    return d[7:]
def rename(source,name):
    return source+"--"+name if source!="main" and name in RAW+LEX else name
def upload(tag,paths):
    subprocess.run(["gh","release","upload",tag,*map(str,paths),"-R",REPO],check=True)
def download(a,path):
    url=a["browser_download_url"]
    if not url.startswith("https://github.com/"+REPO+"/releases/download/"):raise ValueError("Foreign asset")
    for retry in range(4):
        try:
            h=hashlib.sha256()
            req=urllib.request.Request(url,headers={"User-Agent":"DictsUnified/1.0"})
            with urllib.request.urlopen(req,timeout=180) as r,path.open("wb") as f:
                for b in iter(lambda:r.read(1<<20),b""):
                    f.write(b);h.update(b)
            if h.hexdigest()!=digest(a) or path.stat().st_size!=a["size"]:raise ValueError("Asset integrity mismatch: "+a["name"])
            return path
        except (OSError,TimeoutError):
            path.unlink(missing_ok=True)
            if retry==3:raise
            time.sleep(5*(retry+1))
def migrate(tag,source,part,parts):
    if not release(tag)["draft"]:raise ValueError("Destination is not a draft")
    old=inventory(OLD[source])
    names=sorted(n for n in old if n!="SHA256SUMS.txt")[part::parts]
    if not names:raise ValueError("Empty source")
    for i in range(0,len(names),250):
        with tempfile.TemporaryDirectory() as tmp:
            def fetch(n):return download(old[n],Path(tmp)/rename(source,n))
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
                files=list(pool.map(fetch,names[i:i+250]))
            upload(tag,files)
        print(source,part,min(i+250,len(names)),len(names),flush=True)
def validate(tag,assets,folder):
    def check(name,expected=None,size=None):
        a=assets[name]; h=digest(a)
        if expected is not None and h!=expected:raise ValueError("Hash mismatch: "+name)
        if size is not None and a["size"]!=size:raise ValueError("Size mismatch: "+name)
    def doc(name):
        check(name)
        subprocess.run(["gh","release","download",tag,"-R",REPO,"--pattern",name,"--dir",str(folder)],check=True)
        data=(folder/name).read_bytes()
        if hashlib.sha256(data).hexdigest()!=digest(assets[name]):raise ValueError("Metadata checksum mismatch "+name)
        return json.loads(data)
    m=doc("manifest.json"); bundles=doc("BUNDLE-PARTS.json")
    names=set()
    for a in m["assets"]:
        check(a["name"],a["sha256"],a["bytes"]);names.add(a["name"])
    for source in ("koreader","freedict","wikdict","kaikki","tatoeba"):
        if m["source_status"][source]["status"]!="included":raise ValueError("Incomplete main source "+source)
        if source in ("freedict","wikdict"):
            state=m["source_status"][source]
            if state["included"]!=state["discovered"]:raise ValueError("Skipped pairs "+source)
    members=[n for p in bundles["parts"] for n in p["members"]]
    if len(members)!=len(names) or set(members)!=names:raise ValueError("Bundle coverage mismatch")
    for p in bundles["parts"]:
        check(p["file"],p["sha256"],p["bytes"]);names.add(p["file"])
    names|={"manifest.json","BUNDLE-PARTS.json","THIRD-PARTY-NOTICES.md"}
    groups={"main":{"assets":sorted(names),"manifest":"manifest.json"}}
    for source in tuple(OLD)[1:]:
        raw=source in ("kaikki","tatoeba")
        a,b=[rename(source,n) for n in (RAW if raw else LEX)]
        m=doc(a);check(b)
        if m["source"]!=source or m["status"]!="complete":raise ValueError("Incomplete "+source)
        group={a,b}
        if raw:
            if not m["sources"] or len(m["sources"])!=m["discovered"]:raise ValueError("Raw inventory mismatch")
            for s in m["sources"]:
                ps=s["parts"]
                if [p["index"] for p in ps]!=list(range(1,len(ps)+1)) or sum(p["bytes"] for p in ps)!=s["original_bytes"]:raise ValueError("Raw parts mismatch")
                for p in ps:check(p["asset"],p["sha256"],p["bytes"]);group.add(p["asset"])
        else:
            if not m["assets"]:raise ValueError("Empty lexical inventory")
            for p in m["assets"]:check(p["name"],p["sha256"],p["bytes"]);group.add(p["name"])
        if names&group:raise ValueError("Filename collision")
        names|=group
        groups[source]={"manifest":a,"assets":sorted(group),"version":m.get("version")}
    # All non-source metadata is explicitly inventoried and checked.
    if "REFRESH-REPORT.json" in assets:
        report=doc("REFRESH-REPORT.json")
        if report.get("version")!=tag:raise ValueError("Refresh report version mismatch")
        names.add("REFRESH-REPORT.json")
        notes=sorted(n for n in assets if n.startswith("retained--") and n.endswith(".json"))
        for n in notes:
            row=doc(n)
            if not row.get("retained") or not row.get("reason"):raise ValueError("Bad retention record")
            names.add(n)
        groups["refresh"]={"assets":["REFRESH-REPORT.json"]+notes,"manifest":"REFRESH-REPORT.json"}
    for group in GROUPS:
        name=f"normalized--{group}-index.json"
        if name not in assets:continue
        index=doc(name)
        if index["schema"]!=1 or index["group"]!=group or not index["members"]:raise ValueError("Invalid normalized group "+group)
        group_names={name}
        packs={p["name"]:p for p in index["packages"]}
        if not packs:raise ValueError("Missing normalized packages "+group)
        for n,p in packs.items():
            if not n.startswith(f"normalized--{group}-") or not n.endswith(".zip"):raise ValueError("Invalid pack name")
            check(n,p["sha256"],p["bytes"]);group_names.add(n)
        for member,row in index["members"].items():
            if member.startswith("/") or ".." in Path(member).parts or row["pack"] not in packs or row["bytes"]<=0 or not re.fullmatch(r"[0-9a-f]{64}",row["sha256"]):
                raise ValueError("Invalid normalized member "+member)
        if names&group_names:raise ValueError("Normalized name collision")
        names|=group_names
        groups["normalized-"+group]={"assets":sorted(group_names),"manifest":name}
    if "LEXICAL-INDEX.json" in assets:
        idx=doc("LEXICAL-INDEX.json")
        if idx["version"]!=tag or set(idx["groups"])!=set(GROUPS):raise ValueError("Invalid master normalized index")
        for group,item in idx["groups"].items():
            check(item["index"],item["sha256"],item["bytes"])
        names.add("LEXICAL-INDEX.json")
    if names!=set(assets)-{"SHA256SUMS.txt","RELEASE-MANIFEST.json"}:
        raise ValueError("Unexpected/missing files: "+repr(sorted(names^(set(assets)-{"SHA256SUMS.txt","RELEASE-MANIFEST.json"}))[:20]))
    for name in names:check(name)
    return groups
def finalize(tag):
    if not release(tag)["draft"]:raise ValueError("Do not modify published version")
    assets=inventory(tag)
    with tempfile.TemporaryDirectory() as tmp:
        folder=Path(tmp);groups=validate(tag,assets,folder)
        report=json.loads((folder/"REFRESH-REPORT.json").read_text())
        if not report.get("publish"):raise ValueError("Refusing unchanged draft")
        groups_expected={"normalized-"+g for g in GROUPS}
        if not groups_expected.issubset(groups):raise ValueError("Missing normalized groups")
        idx={"schema":1,"version":tag,"groups":{},"format":"gzip-json-shards","download_base":f"https://github.com/{REPO}/releases/download/{tag}/"}
        for group in GROUPS:
            name=f"normalized--{group}-index.json"
            idx["groups"][group]={"index":name,"bytes":assets[name]["size"],"sha256":digest(assets[name])}
        idxfile=folder/"LEXICAL-INDEX.json"
        idxfile.write_text(json.dumps(idx,indent=2)+"\n")
        upload(tag,[idxfile])
        assets=inventory(tag)
        # Use a fresh directory because validate downloads manifests.
        with tempfile.TemporaryDirectory() as fresh:
            groups=validate(tag,assets,Path(fresh))
        entries=[{"name":n,"bytes":assets[n]["size"],"sha256":digest(assets[n])} for n in sorted(assets)]
        if len(entries)+2>1000:raise ValueError("Asset limit exceeded")
        master=folder/"RELEASE-MANIFEST.json"
        master.write_text(json.dumps({"schema":1,"version":tag,"sources":["koreader","freedict","wikdict",*tuple(OLD)[1:]],"groups":groups,"assets":entries,"download_base":f"https://github.com/{REPO}/releases/download/{tag}/"},indent=2)+"\n")
        checks=folder/"SHA256SUMS.txt"
        checks.write_text("".join(a["sha256"]+"  "+a["name"]+"\n" for a in entries)+hashlib.sha256(master.read_bytes()).hexdigest()+"  "+master.name+"\n")
        upload(tag,[master,checks])
        final=inventory(tag)
        if set(final)!=set(assets)|{master.name,checks.name}:raise ValueError("Final file inventory mismatch")
        for a in entries:
            if digest(final[a["name"]])!=a["sha256"]:raise ValueError("Final digest mismatch")
        for f in (master,checks):
            if digest(final[f.name])!=hashlib.sha256(f.read_bytes()).hexdigest():raise ValueError("Manifest digest mismatch")
        notes=f"""## Complete dictionary collection — {tag}
All eight source families in a single version: KOReader, FreeDict, WikDict, Kaikki/Wiktionary, Tatoeba, Open English WordNet, Open Multilingual Wordnet and ConceptNet.

**{len(final)} assets · {sum(a['size'] for a in final.values())/1e9:.2f} GB** (including convenience bundles).

- [Online dictionary](https://danilfg.github.io/dicts/)
- [Complete file inventory](https://github.com/{REPO}/releases/download/{tag}/RELEASE-MANIFEST.json)
- [SHA-256 verification](https://github.com/{REPO}/releases/download/{tag}/SHA256SUMS.txt)
- Bilingual ZIPs and compact indexes: individual files or BUNDLE-PARTS.json.
- Full text corpora: kaikki-- and tatoeba--; join numbered parts in order.
- WordNet and ConceptNet: oewn--, omw--, conceptnet-- and lexicon-- files.
- [Normalized application indexes](https://github.com/{REPO}/releases/download/{tag}/LEXICAL-INDEX.json) (all eight sources; compact corpus/graph subsets).
- [Source refresh report](https://github.com/{REPO}/releases/download/{tag}/REFRESH-REPORT.json) (exact changed assets and retained sources).
- Preserve original licenses and source-specific attribution. Third-party data are not covered by the project MIT license.
"""
        from release_plan import release_notes
        notes+=release_notes(report)
        gh("release","edit",tag,"-R",REPO,"--draft=false","--latest","--title","Dicts "+tag,"--notes",notes)
        print("PUBLISHED",tag,len(final),"verified assets",flush=True)
def main():
    p=argparse.ArgumentParser();p.add_argument("action",choices=["migrate","finalize"]);p.add_argument("--tag",required=True);p.add_argument("--source",choices=tuple(OLD));p.add_argument("--partition",type=int,default=0);p.add_argument("--partitions",type=int,default=1)
    a=p.parse_args()
    if os.getenv("GITHUB_REPOSITORY")!=REPO or not re.fullmatch(r"v\d{4}\.\d{2}\.\d{2}\.\d+\.\d+",a.tag):raise ValueError("Invalid destination")
    if a.action=="migrate":migrate(a.tag,a.source,a.partition,a.partitions)
    else:finalize(a.tag)
if __name__=="__main__":main()
