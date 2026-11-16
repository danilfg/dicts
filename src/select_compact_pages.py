#!/usr/bin/env python3
"""Fit the public multilingual index into GitHub Pages without losing any
published *language direction*: keep original KOReader ZIPs only where
compact lexical enrichments for the same direction do not exist.

This changes ONLY which text copies are embedded in Pages. Every original
dictionary remains fully downloadable in the main GitHub release.
"""
import argparse
import collections
import pathlib
import re
import shutil
import zipfile

CORE={"en-ru","ru-en","en-es","es-en","en-de","de-en"}
ENRICH_RE=re.compile(r"enrichment--([a-z0-9]+-[a-z0-9]+)\.json\.gz$")
KOREADER_RE=re.compile(r"koreader--([a-z0-9]+-[a-z0-9]+)\.zip$")

def all_enrichments(downloads:pathlib.Path)->set[str]:
    result=set()
    for file in downloads.glob("enrichment--*.json.gz"):
        found=ENRICH_RE.fullmatch(file.name)
        if found:result.add(found.group(1))
    for path in downloads.glob("enrichments-extra--*.zip"):
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                found=ENRICH_RE.fullmatch(pathlib.PurePosixPath(name).name)
                if found:result.add(found.group(1))
    return result

def select_compact(downloads:pathlib.Path,skipped:pathlib.Path):
    enriched=all_enrichments(downloads)
    if len(enriched)<400:
        raise ValueError(f"Too few compact language-pair indexes: {len(enriched)}")
    skipped.mkdir(parents=True,exist_ok=True)
    retained=[];omitted=[]
    for file in sorted(downloads.glob("koreader--*.zip")):
        match=KOREADER_RE.fullmatch(file.name)
        if not match:continue
        pair=match.group(1)
        if pair in enriched and pair not in CORE:
            shutil.move(str(file),str(skipped/file.name))
            omitted.append(pair)
        else:retained.append(pair)
    if len(retained)+len(omitted)<74:
        raise ValueError("Not all expected KOReader packages were inspected")
    print("COMPACT-PAGES-PLAN:",len(enriched),"enriched pairs",
          len(retained),"retained original KOReader pairs",
          len(omitted),"redundant KOReader pairs kept only in Releases",flush=True)
    return {"enriched":len(enriched),"retained":retained,"omitted":omitted}

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--downloads",type=pathlib.Path,default=pathlib.Path("downloads"))
    cli.add_argument("--skipped",type=pathlib.Path,default=pathlib.Path("excluded-pages-zips"))
    args=cli.parse_args()
    select_compact(args.downloads,args.skipped)

if __name__=="__main__":main()
