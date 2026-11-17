"""Compare verified candidate with its immutable baseline; record all refresh outcomes."""
import argparse
import json
import os
import tempfile
from pathlib import Path
from unified_release import REPO,inventory,validate,upload
from release_changes import diff_plan,confirm_zip_changes,source_assets

SOURCES=("koreader","freedict","wikdict","kaikki","tatoeba","oewn","omw","conceptnet")
def plan(old,new,changed,retained,version,previous):
    families={s:{"added":[],"updated":[],"removed":[],"retained":[]} for s in SOURCES}
    a,b=source_assets(old),source_assets(new)
    for n in sorted(changed):
        src=n.split("--",1)[0]
        if src not in families:continue
        key="added" if n not in a else "removed" if n not in b else "updated"
        families[src][key].append(n)
    for name,row in sorted(retained.items()):
        src=row["source"]
        if src in families:families[src]["retained"].append(dict(row,file=name))
    for s,row in families.items():
        modifies=any(row[k] for k in ("added","updated","removed"))
        row["status"]="updated_with_stale_data" if modifies and row["retained"] else "updated" if modifies else "retained" if row["retained"] else "unchanged"
    bootstrap="LEXICAL-INDEX.json" not in old
    return {"schema":1,"version":version,"previous_release":previous,"publish":bool(changed or bootstrap),
            "normalization_bootstrap":bootstrap,"sources":families}

def release_notes(report):
    lines=["","## Source update report","",f"Baseline: `{report['previous_release']}`","",
           "| Source | Result | Added | Updated | Removed | Retained / unavailable |",
           "|---|---|---:|---:|---:|---:|"]
    for src,row in report["sources"].items():
        lines.append(f"| {src} | {row['status']} | {len(row['added'])} | {len(row['updated'])} | {len(row['removed'])} | {len(row['retained'])} |")
    for src,row in report["sources"].items():
        if any(row[k] for k in ("added","updated","removed","retained")):
            lines+=["",f"### {src}"]
            for k in ("added","updated","removed"):
                if row[k]:
                    lines.append(f"- {k.title()}: "+", ".join("`"+n+"`" for n in row[k][:12])+(f" (+{len(row[k])-12} more; see REFRESH-REPORT.json)" if len(row[k])>12 else ""))
            for item in row["retained"][:12]:
                reason=item["reason"].replace("\n"," ").replace("\r"," ")
                state="kept previous verified file" if item["retained"] else "new file unavailable; no prior copy"
                lines.append(f"- `{item['file']}`: {state}; {reason}")
            if len(row["retained"])>12:lines.append("- Further retained/unavailable files: see REFRESH-REPORT.json.")
    if report["normalization_bootstrap"]:lines+=["","First release with normalized application packages."]
    lines+=["","Changes describe source files, not invented per-entry linguistic diffs. Original licenses remain in force.",""]
    return "\n".join(lines)

def run(tag,previous):
    old,new=inventory(previous),inventory(tag)
    with tempfile.TemporaryDirectory() as tmp:
        folder=Path(tmp)
        # Retention markers are produced before the report; validate after adding it.
        from normalized_pack import pull
        raw_reports=[s+"--SOURCE-MANIFEST.json" for s in ("kaikki","tatoeba")]
        pull(tag,["manifest.json"]+raw_reports+[n for n in new if n.startswith("retained--")],folder,new)
        data=json.loads((folder/"manifest.json").read_text())
        retained=dict(data.get("fallbacks",{}))
        for name in raw_reports:
            doc=json.loads((folder/name).read_text())
            # A whole-family fallback has its own marker; avoid stale historical failure records.
            marker="retained--"+doc["source"]+".json"
            if marker not in new:retained.update(doc.get("fallbacks",{}))
        for n in new:
            if n.startswith("retained--"):
                retained[n]=json.loads((folder/n).read_text())
        changed,zips=diff_plan(old,new)
        changed+=confirm_zip_changes(previous,tag,zips,REPO)
        report=plan(old,new,changed,retained,tag,previous)
        p=folder/"REFRESH-REPORT.json";p.write_text(json.dumps(report,indent=2)+"\n")
        upload(tag,[p])
    with tempfile.TemporaryDirectory() as tmp:
        validate(tag,inventory(tag),Path(tmp))
    print(release_notes(report),flush=True)
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"],"a") as f:f.write(release_notes(report))
    if os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"],"a") as f:f.write("changed="+str(report["publish"]).lower()+"\n")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--tag",required=True);p.add_argument("--previous",required=True)
    a=p.parse_args();run(a.tag,a.previous)
