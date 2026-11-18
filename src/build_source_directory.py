"""Build a compact public source directory from one pinned release's metadata."""
import json
import tempfile
from pathlib import Path

from unified_release import physical_inventory,release
from normalized_pack import pull

def directory(tag,published,legal,main,other,report):
    rows=[]
    for source in legal["families"]:
        key=source["id"]
        if key=="aggregate":continue
        if key in ("koreader","freedict","wikdict"):
            items=[a for a in main["assets"] if a.get("source")==key and a["name"].endswith(".zip")]
            packages=[{"pair":a.get("pair",""),"name":a["name"],"version":a.get("version") or None} for a in items]
            versions=sorted({p["version"] for p in packages if p["version"] and p["version"]!="source version: online directory"})
            snapshot=None
        else:
            m=other[key]
            packages=[]
            if key in ("kaikki","tatoeba"):
                packages=[{"name":a["original_url"].rsplit("/",1)[-1],"version":None} for a in m.get("sources",[])]
                snapshot=m.get("created")
            else:
                packages=[{"name":a["name"],"version":a.get("version") or m.get("version")} for a in m.get("assets",[])]
                snapshot=m.get("generated_at")
            versions=sorted({p["version"] for p in packages if p.get("version")})
            if m.get("version") and m["version"] not in versions:versions.append(m["version"])
        state=report["sources"].get(key,{})
        for p in packages:
            if p.get("version")=="source version: online directory":p["version"]=None
        rows.append({"id":key,"name":source["name"],"description":source.get("modification",""),
                     "license":source.get("license"),"license_url":source.get("license_url"),
                     "source_url":source.get("source_url"),"versions":versions,
                     "snapshot_date":snapshot,"package_count":len(packages),
                     "packages":sorted(packages,key=lambda p:(p.get("pair") or p["name"],p["name"])),
                     "status":state.get("status"),"previous_release":report.get("previous_release")})
    return {"schema":1,"release_tag":tag,"published_at":published,"sources":rows}

def run(tag,site):
    rel=release(tag)
    if rel["draft"]:raise ValueError("Cannot deploy an unpublished release")
    assets=physical_inventory(tag)
    names={"kaikki":"kaikki--SOURCE-MANIFEST.json","tatoeba":"tatoeba--SOURCE-MANIFEST.json",
           "oewn":"oewn--LEXICAL-MANIFEST.json","omw":"omw--LEXICAL-MANIFEST.json",
           "conceptnet":"conceptnet--LEXICAL-MANIFEST.json"}
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)
        pull(tag,["SOURCES.json","manifest.json","REFRESH-REPORT.json",*names.values()],p,assets)
        def read(n):return json.loads((p/n).read_text())
        doc=directory(tag,rel.get("published_at"),read("SOURCES.json"),read("manifest.json"),
                      {k:read(v) for k,v in names.items()},read("REFRESH-REPORT.json"))
    output=site/"data"/"sources.json"
    output.write_text(json.dumps(doc,ensure_ascii=False,separators=(",",":"))+"\n")
    print("Public source directory ready:",len(doc["sources"]),"sources",flush=True)
