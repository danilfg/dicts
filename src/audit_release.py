#!/usr/bin/env python3
"""Audit ACTUAL published GitHub Releases (not just build-stage log messages).

Checks every release asset SHA-256 against GitHub's independently reported
digest, the downloaded SHA256SUMS, and the generated manifest. Verifies all
bundles cover each source asset exactly once, audits raw corpus inventories,
and opens samples of KOReader/FreeDict/WikDict and EN-RU enrichment.
"""
import collections
import gzip
import hashlib
import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path
from urllib.request import Request,urlopen

REPO=os.environ.get("GITHUB_REPOSITORY","danilfg/dicts")
TOKEN=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
if REPO!="danilfg/dicts":raise SystemExit("Unsafe repo: "+REPO)
if not TOKEN:raise SystemExit("GH_TOKEN is not configured")
HEADERS={"Authorization":"Bearer "+TOKEN,"Accept":"application/vnd.github+json","User-Agent":"Dicts-Audit/1.0"}
OUTPUT=[]

def api(route):
    r=Request("https://api.github.com/"+route,headers=HEADERS)
    with urlopen(r,timeout=60) as response:return json.load(response)

def assets(release):
    output=[];page=1
    while True:
        batch=api(f"repos/{REPO}/releases/{release['id']}/assets?per_page=100&page={page}")
        output+=batch
        if len(batch)<100:break
        page+=1
        if page>40:raise ValueError("Too many pages of release assets")
    return {x["name"]:x for x in output}

def gh_download(tag,name,directory):
    subprocess.run(["gh","release","download",tag,"-R",REPO,"--pattern",name,
        "--dir",str(directory),"--clobber"],check=True)
    path=directory/name
    if not path.is_file():raise ValueError(f"Download missing: {tag}/{name}")
    return path

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        while block:=f.read(1024*1024):h.update(block)
    return h.hexdigest()

def checked(name,asset,digest):
    if not asset:raise ValueError("Missing published release asset "+name)
    actual=asset.get("digest")
    if actual!="sha256:"+digest:raise ValueError("SHA256 mismatch: "+name)
    if asset["size"]<=0:raise ValueError("Empty release asset "+name)
    if asset["size"]>1_999_000_000:raise ValueError("GitHub asset size limit exceeded: "+name)

def sample_archive(tag,filename,dir):
    f=gh_download(tag,filename,dir)
    with zipfile.ZipFile(f) as archive:
        if archive.testzip():raise ValueError("Invalid ZIP "+filename)
        names=[Path(n).name.lower() for n in archive.namelist()]
        if not any(x.endswith(".idx") for x in names):
            raise ValueError("No StarDict index: "+filename)
        if not any(x.endswith((".dict",".dict.dz")) for x in names):
            raise ValueError("No StarDict data: "+filename)
        if filename.startswith("koreader--"):
            if not ("license" in names and "attribution" in names):
                raise ValueError("KOReader original notices missing")
        else:
            if not ("license-source.txt" in names and "attribution.txt" in names):
                raise ValueError("Converted source notices missing")
            if filename.startswith("freedict--") and "original-source.tar.xz" not in names:
                raise ValueError("FreeDict original TEI source missing")
    return f.stat().st_size

def audit_main(directory):
    latest=api(f"repos/{REPO}/releases/latest")
    if latest["draft"]:raise ValueError("Latest release is a draft")
    tag=latest["tag_name"]
    published=assets(latest)
    for name in published:
        if not published[name].get("digest","").startswith("sha256:"):
            raise ValueError("Missing GitHub checksum: "+name)
    manifest=json.loads(gh_download(tag,"manifest.json",directory).read_text())
    checks=gh_download(tag,"SHA256SUMS.txt",directory)
    parts=json.loads(gh_download(tag,"BUNDLE-PARTS.json",directory).read_text())
    notices=gh_download(tag,"THIRD-PARTY-NOTICES.md",directory)
    rows={}
    for line in checks.read_text().splitlines():
        digest,name=line.split("  ",1)
        if name in rows:raise ValueError("Duplicate checksum for "+name)
        rows[name]=digest
    if set(rows)!=(set(published)-{"SHA256SUMS.txt"}):
        raise ValueError("Checksum coverage differs from actual release assets")
    for name,digest in rows.items():checked(name,published.get(name),digest)
    for name in ("manifest.json","SHA256SUMS.txt","BUNDLE-PARTS.json","THIRD-PARTY-NOTICES.md"):
        file=directory/name
        if file.stat().st_size!=published[name]["size"] or sha(file)!=published[name]["digest"].split(":",1)[1]:
            raise ValueError("Downloaded metadata mismatch: "+name)
    source_assets=manifest["assets"]
    by_name={x["name"]:x for x in source_assets}
    if len(by_name)!=len(source_assets):raise ValueError("Duplicate names in manifest")
    for name,item in by_name.items():
        checked(name,published.get(name),item["sha256"])
        if item.get("license") is None or not item.get("attribution") or not item.get("source_url"):
            raise ValueError("Missing attribution/source for "+name)
    bundle_parts=parts["parts"]
    bundled=[n for p in bundle_parts for n in p["members"]]
    if len(bundled)!=len(set(bundled)) or set(bundled)!=set(by_name):
        raise ValueError("Bundled source names do not match manifest")
    for part in bundle_parts:checked(part["file"],published.get(part["file"]),part["sha256"])
    statuses=manifest["source_status"]
    counts=collections.Counter(a["source"] for a in source_assets)
    for family in ("koreader","freedict","wikdict"):
        state=statuses[family]
        if state.get("status")!="included":raise ValueError(f"{family} incomplete: {state}")
    for family in ("freedict","wikdict"):
        if statuses[family]["included"]!=statuses[family]["discovered"]:
            raise ValueError(f"{family}: catalog discovery and published packages differ")
        if counts[family]!=statuses[family]["included"]:
            raise ValueError(f"{family}: manifest count and source status differ")
    if counts["koreader"]!=statuses["koreader"]["archives"]:
        raise ValueError("KOReader count mismatch")
    for source in ("kaikki","tatoeba"):
        if statuses[source]["status"]!="included":
            raise ValueError(f"{source} browser enrichment missing")
    # Check real StarDict structure, attribution and EN-RU enrichment data.
    for prefix in ("koreader","freedict","wikdict"):
        name=f"{prefix}--en-ru.zip"
        if name not in published:raise ValueError("Missing EN-RU "+prefix)
        sample_archive(tag,name,directory)
    enrich=gh_download(tag,"enrichment--en-ru.json.gz",directory)
    with gzip.open(enrich,"rt",encoding="utf8") as f:
        words=json.load(f)
    if words.get("schema")!=1 or words.get("pair")!="en-ru" or not words.get("words"):
        raise ValueError("EN-RU enrichment missing records")
    source_types={r.get("source") for e in words["words"].values()
                  for field in ("translations","meanings","examples")
                  for r in e.get(field,[])}
    for source in ("freedict","wikdict","kaikki","tatoeba"):
        if source not in source_types:
            raise ValueError("EN-RU index missing source: "+source)
    OUTPUT.append(f"**Main release:** [{tag}](https://github.com/{REPO}/releases/tag/{tag}), {len(published)} files")
    OUTPUT.append("**Main packages:** "+", ".join(f"{k} {counts[k]}" for k in ("koreader","freedict","wikdict","aggregate")))
    OUTPUT.append("**EN-RU:** checked original ZIP notices and StarDict structures; enrichment includes FreeDict, WikDict, Kaikki, Tatoeba.")
    OUTPUT.append("**Hashes:** all GitHub asset SHA-256 digests agree with both manifest and SHA256SUMS.")
    OUTPUT.append(f"**Bundle coverage:** {len(bundle_parts)} part(s), {len(bundled)} distinct source files.")

def audit_raw(directory):
    releases=api(f"repos/{REPO}/releases?per_page=100")
    for source in ("kaikki","tatoeba"):
        candidates=[x for x in releases if x["tag_name"].startswith("raw-"+source+"-") and not x["draft"]]
        if not candidates:raise ValueError("No published complete raw "+source+" release")
        release=candidates[0]
        tag=release["tag_name"]
        items=assets(release)
        dest=directory/source
        dest.mkdir()
        p=gh_download(tag,"SOURCE-MANIFEST.json",dest)
        legal=gh_download(tag,"ATTRIBUTION-AND-LICENSE.txt",dest)
        doc=json.loads(p.read_text())
        if doc.get("status")!="complete" or len(doc.get("sources",[]))!=doc.get("discovered"):
            raise ValueError("Incomplete raw source manifest "+tag)
        all_part_names=[]
        for upstream in doc["sources"]:
            chunks=upstream["parts"]
            if not chunks:raise ValueError("Empty original archive source")
            if sum(x["bytes"] for x in chunks)!=upstream["original_bytes"]:
                raise ValueError("Raw original archive byte count mismatch")
            if [x["index"] for x in chunks]!=list(range(1,len(chunks)+1)):
                raise ValueError("Nonsequential chunk indices")
            for chunk in chunks:
                checked(chunk["asset"],items.get(chunk["asset"]),chunk["sha256"])
                all_part_names.append(chunk["asset"])
        if len(all_part_names)!=len(set(all_part_names)):
            raise ValueError("Duplicate raw chunks")
        if len(all_part_names)+2!=len(items):
            raise ValueError("Unaccounted source files in "+tag)
        if not legal.read_text().strip():raise ValueError("Missing raw licensing evidence")
        OUTPUT.append(f"**Raw {source}:** [{tag}](https://github.com/{REPO}/releases/tag/{tag}), {len(doc['sources'])} source archives, {len(all_part_names)} chunks. All hashes checked.")

def main():
    with tempfile.TemporaryDirectory() as temp:
        directory=Path(temp)
        audit_main(directory)
        latest=api(f"repos/{REPO}/releases/latest")
        if latest["tag_name"].startswith("v"):
            from unified_release import inventory, validate
            with tempfile.TemporaryDirectory() as check:
                validate(latest["tag_name"],inventory(latest["tag_name"]),Path(check))
            OUTPUT.append("All eight unified release source inventories validated.")
        else:
            audit_raw(directory)
    print("\n".join(OUTPUT),flush=True)
    summary=os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary,"a") as f:
            f.write("## Dicts published release audit\n\n"+"\n\n".join(OUTPUT)+"\n")

if __name__=="__main__":main()
