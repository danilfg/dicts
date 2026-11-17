"""Publish only the catalog artifact of an already published OCI release.

No source downloads, normalization, or changes to the GitHub Release.
Both public aliases refer to the same verified catalog manifest.
"""
import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

from storage import REGISTRY, SOURCE, FORMAT, metadata
from unified_release import REPO, gh, release, physical_inventory, digest
from normalized_pack import pull
from public_client import public_blob

ARTIFACT="application/vnd.danilfg.dicts.catalog.v1"
TAG=re.compile(r"v\d{4}\.\d{2}\.\d{2}\.\d+\.\d+")
FILES=("LEXICAL-INDEX.json","PAIR-INDEX.json","RELEASE-MANIFEST.json",
       "SHA256SUMS.txt","REFRESH-REPORT.json","SOURCES.json","NOTICE.md",
       "LICENSE","THIRD-PARTY-NOTICES.md")

def latest_version():
    return gh("release","view","-R",REPO,"--json","tagName","--jq",".tagName")

def check_catalog(tag,folder,assets):
    rows={n:metadata(folder/n) for n in FILES}
    for n,row in rows.items():
        if row["bytes"]!=assets[n]["size"] or row["sha256"]!=digest(assets[n]):
            raise ValueError("Release metadata mismatch: "+n)
    lexical=json.loads((folder/"LEXICAL-INDEX.json").read_text())
    pair=json.loads((folder/"PAIR-INDEX.json").read_text())
    manifest=json.loads((folder/"RELEASE-MANIFEST.json").read_text())
    for index in (lexical,pair):
        if (index.get("schema"),index.get("format"),index.get("version"),index.get("registry"))!=(1,FORMAT,tag,REGISTRY):
            raise ValueError("Unsupported or mismatched catalog")
    if not pair.get("pairs") or not pair.get("groups"):
        raise ValueError("Empty pair catalog")
    if manifest.get("version")!=tag:raise ValueError("Release manifest version mismatch")
    if lexical.get("pair_index")!=rows["PAIR-INDEX.json"]:
        raise ValueError("Pair index descriptor mismatch")
    checks={}
    for line in (folder/"SHA256SUMS.txt").read_text().splitlines():
        key,name=line.split("  ",1)
        if name in checks:raise ValueError("Duplicate checksum "+name)
        checks[name]=key
    for n,row in rows.items():
        if n!="SHA256SUMS.txt" and checks.get(n)!=row["sha256"]:
            raise ValueError("Release checksum mismatch: "+n)
    return rows

def validate_manifest(doc,rows,tag):
    if doc.get("artifactType")!=ARTIFACT:raise ValueError("Unexpected OCI artifact type")
    ann=doc.get("annotations",{})
    if ann.get("org.opencontainers.image.version")!=tag or ann.get("org.opencontainers.image.source")!=SOURCE:
        raise ValueError("Unexpected OCI version or source")
    layers=doc["layers"]
    actual={layer.get("annotations",{}).get("org.opencontainers.image.title"):
            (layer["size"],layer["digest"]) for layer in layers}
    desired={n:(r["bytes"],"sha256:"+r["sha256"]) for n,r in rows.items()}
    if len(layers)!=len(desired) or actual!=desired:
        raise ValueError("OCI catalog layer mismatch")

def oras_json(*args,**kwargs):
    return json.loads(subprocess.check_output(["oras",*args],text=True,**kwargs))

def publish_catalog(tag):
    if not TAG.fullmatch(tag):raise ValueError("Invalid release tag")
    if release(tag)["draft"] or latest_version()!=tag:
        raise ValueError("Only the latest published release can be promoted")
    assets=physical_inventory(tag)
    with tempfile.TemporaryDirectory() as tmp:
        folder=Path(tmp)
        pull(tag,FILES,folder,assets)
        rows=check_catalog(tag,folder,assets)
        ref=REGISTRY+":"+tag
        # Reuse an existing immutable dated manifest only if every layer matches.
        result=subprocess.run(["oras","manifest","fetch","--descriptor",ref],
                              capture_output=True,text=True)
        if result.returncode==0:
            descriptor=json.loads(result.stdout)
        elif re.search(r"(?i)not found|manifest unknown|MANIFEST_UNKNOWN|404",result.stderr):
            descriptor=oras_json("push","--artifact-type",ARTIFACT,
                "--annotation","org.opencontainers.image.source="+SOURCE,
                "--annotation","org.opencontainers.image.version="+tag,
                "--annotation","org.opencontainers.image.title=Dicts complete collection",
                "--annotation","org.opencontainers.image.description=Versioned multilingual dictionary catalog; select only required language pairs. Original data licenses apply.",
                "--format","json",ref,*[n+":application/octet-stream" for n in FILES],cwd=folder)
        else:
            raise RuntimeError("Cannot check dated artifact: "+result.stderr)
        manifest_digest=descriptor["digest"]
        if not re.fullmatch(r"sha256:[0-9a-f]{64}",manifest_digest):
            raise ValueError("Invalid manifest digest")
        pinned=REGISTRY+"@"+manifest_digest
        anonymous=folder/"anonymous.json"
        anonymous.write_text('{"auths":{}}')
        doc=oras_json("manifest","fetch","--registry-config",str(anonymous),pinned)
        validate_manifest(doc,rows,tag)
        # Actually read the catalog from the public blob endpoint.
        if public_blob(REGISTRY,rows["PAIR-INDEX.json"])!=(folder/"PAIR-INDEX.json").read_bytes():
            raise ValueError("Anonymous catalog content mismatch")
        if latest_version()!=tag:raise ValueError("Latest release changed during promotion")
        subprocess.run(["oras","tag",pinned,"latest"],check=True)
        for alias in (tag,"latest"):
            actual=oras_json("manifest","fetch","--descriptor","--registry-config",
                             str(anonymous),REGISTRY+":"+alias)
            if actual["digest"]!=manifest_digest:raise ValueError("Alias digest mismatch: "+alias)
        print(f"VERIFIED CATALOG {tag}: {manifest_digest}",flush=True)
        print(f"{REGISTRY}:{tag} and {REGISTRY}:latest",flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tag")
    args=p.parse_args()
    publish_catalog(args.tag or latest_version())
