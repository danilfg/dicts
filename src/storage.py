"""Content-addressed GHCR storage; Releases carry metadata and one receipt per producer.

The package is data, not a runnable Docker image. Every layer is one original
file or independently installable normalized block. No per-file release assets.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import urllib.request
from pathlib import Path

REGISTRY="ghcr.io/danilfg/dicts-data"
REPOSITORY="danilfg/dicts-data"
SOURCE="https://github.com/danilfg/dicts"
RECEIPT=re.compile(r"oci--([a-z0-9-]+)\.json")
HEX=re.compile(r"[0-9a-f]{64}")
FILE=re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
FORMAT="oci-pair-v1"
ARTIFACT="application/vnd.danilfg.dicts.files.v1"
BATCH=48

def sha(path):
    with path.open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()

def metadata(path):
    return {"name":path.name,"bytes":path.stat().st_size,"sha256":sha(path)}

def scope_of(name):
    if name.startswith("unit--"):return "normalized-"+name.split("--")[1]
    if name.startswith("normalized--"):return "normalized-"+name[len("normalized--"):].rsplit("-",1)[0]
    for source in ("kaikki","tatoeba","oewn","omw","conceptnet"):
        if name.startswith(source+"--") or source=="oewn" and name.startswith("lexicon--oewn-"):return source
    return "main"

def is_control(name):
    return (name in {"LEXICAL-INDEX.json","PAIR-INDEX.json","REFRESH-REPORT.json","RELEASE-MANIFEST.json","SHA256SUMS.txt","SOURCES.json","NOTICE.md","LICENSE","manifest.json","BUNDLE-PARTS.json","THIRD-PARTY-NOTICES.md"}
        or name.endswith(("--SOURCE-MANIFEST.json","--ATTRIBUTION-AND-LICENSE.txt","--LEXICAL-MANIFEST.json","--THIRD-PARTY-LEXICAL-NOTICES.md","--PER-PACKAGE-LICENSES.json"))
        or name.startswith("retained--") or name.startswith("normalized--") and name.endswith("-index.json"))

def record_ok(row):
    return (bool(FILE.fullmatch(row["name"])) and HEX.fullmatch(row["sha256"]) and
            0<row["bytes"]<2**31 and row["registry"]==REGISTRY and
            re.fullmatch(r"sha256:[0-9a-f]{64}",row["manifest"]))

def push_batch(tag,scope,paths):
    paths=[Path(p).resolve() for p in paths]; rows=[metadata(p) for p in paths]
    if not rows or any(not FILE.fullmatch(r["name"]) or not 0<r["bytes"]<2**31 for r in rows):
        raise ValueError("Invalid registry input")
    if len({p.parent for p in paths})!=1 or len({r["name"] for r in rows})!=len(rows):
        raise ValueError("Registry batch requires one directory and unique names")
    identity=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()[:24]
    ref=f"{REGISTRY}:{tag}-{scope}-{identity}"
    args=["oras","push","--artifact-type",ARTIFACT,"--annotation","org.opencontainers.image.source="+SOURCE,
          "--annotation","org.opencontainers.image.description=Independent dictionary files; original data licenses apply",
          "--concurrency","6","--format","json",ref]+[p.name+":application/octet-stream" for p in paths]
    output=subprocess.check_output(args,cwd=paths[0].parent,text=True)
    desc=json.loads(output)
    digest=desc["digest"]
    if not re.fullmatch(r"sha256:[0-9a-f]{64}",digest):raise ValueError("Invalid OCI manifest digest")
    manifest=json.loads(subprocess.check_output(["oras","manifest","fetch",REGISTRY+"@"+digest],text=True))
    layers={l.get("annotations",{}).get("org.opencontainers.image.title"):l for l in manifest["layers"]}
    for row in rows:
        layer=layers[row["name"]]
        if layer["size"]!=row["bytes"] or layer["digest"]!="sha256:"+row["sha256"]:raise ValueError("Registry layer mismatch")
        row.update(registry=REGISTRY,manifest=digest)
    return rows

def physical(tag):
    from unified_release import physical_inventory
    return physical_inventory(tag)

def upload_release(tag,paths,clobber=False):
    from unified_release import REPO
    cmd=["gh","release","upload",tag,*map(str,paths),"-R",REPO]
    if clobber:cmd.append("--clobber")
    subprocess.run(cmd,check=True)

def read_receipts(tag,assets=None):
    from unified_release import REPO,digest
    assets=assets if assets is not None else physical(tag)
    names=sorted(n for n in assets if RECEIPT.fullmatch(n))
    result={}
    if not names:return result
    with tempfile.TemporaryDirectory() as tmp:
        from normalized_pack import pull
        pull(tag,names,Path(tmp),assets)
        for n in names:
            path=Path(tmp)/n
            if path.stat().st_size!=assets[n]["size"] or sha(path)!=digest(assets[n]):raise ValueError("Receipt integrity mismatch "+n)
            doc=json.loads(path.read_text())
            scope=RECEIPT.fullmatch(n)[1]
            if doc["schema"]!=1 or doc["version"]!=tag or doc["scope"]!=scope:raise ValueError("Wrong receipt "+n)
            rows=doc["files"]
            if len(rows)!=len({r["name"] for r in rows}) or any(not record_ok(r) or scope_of(r["name"])!=scope for r in rows):
                raise ValueError("Invalid receipt "+n)
            result[scope]={r["name"]:r for r in rows}
    return result

def write_receipt(tag,scope,rows):
    if not rows:return
    if any(scope_of(n)!=scope or n!=r["name"] or not record_ok(r) for n,r in rows.items()):raise ValueError("Invalid scoped records")
    with tempfile.TemporaryDirectory() as t:
        p=Path(t)/f"oci--{scope}.json"
        p.write_text(json.dumps({"schema":1,"version":tag,"scope":scope,"files":[rows[n] for n in sorted(rows)]},separators=(",",":"))+"\n")
        upload_release(tag,[p],clobber=True)

def publish(tag,paths):
    """One writer per scope (enforced by the workflow matrix)."""
    controls=[];scopes={}
    for path in map(Path,paths):
        if is_control(path.name):controls.append(path)
        else:scopes.setdefault(scope_of(path.name),[]).append(path)
    if controls:upload_release(tag,controls,clobber=True)
    if not scopes:return
    for scope,files in scopes.items():
        name=f"oci--{scope}.json"
        actual=physical(tag)
        existing=read_receipts(tag,{name:actual[name]} if name in actual else {})
        rows=existing.get(scope,{})
        for i in range(0,len(files),BATCH):
            new=push_batch(tag,scope,files[i:i+BATCH])
            rows.update({r["name"]:r for r in new})
            print(f"OCI {scope}: staged {min(i+BATCH,len(files))}/{len(files)} files",flush=True)
        # Commit one receipt per scope, not one REST upload per batch.
        write_receipt(tag,scope,rows)

def link(tag,assets,names):
    """Reuse registry manifests by digest, without uploading unchanged bytes."""
    touched={scope_of(n) for n in names}
    actual=physical(tag)
    receipts=read_receipts(tag,{n:r for n,r in actual.items() if RECEIPT.fullmatch(n) and RECEIPT.fullmatch(n)[1] in touched})
    for n in names:
        row=assets[n].get("oci")
        if not row:raise ValueError("Cannot link legacy release asset "+n)
        scope=scope_of(n);receipts.setdefault(scope,{})[n]=row;touched.add(scope)
    for scope in touched:write_receipt(tag,scope,receipts[scope])

def remove(tag,names):
    from unified_release import REPO,gh
    actual=physical(tag);wanted=set(names)
    scopes={scope_of(n) for n in wanted}
    receipts=read_receipts(tag,{n:r for n,r in actual.items() if RECEIPT.fullmatch(n) and RECEIPT.fullmatch(n)[1] in scopes})
    for scope,rows in receipts.items():
        if not wanted.intersection(rows):continue
        for n in wanted:rows.pop(n,None)
        if rows:write_receipt(tag,scope,rows)
        else:gh("api","--method","DELETE",f"repos/{REPO}/releases/assets/{actual['oci--'+scope+'.json']['id']}")
    for n in wanted.intersection(actual):
        if not RECEIPT.fullmatch(n):gh("api","--method","DELETE",f"repos/{REPO}/releases/assets/{actual[n]['id']}")

def expand(tag,assets):
    result=dict(assets)
    for rows in read_receipts(tag,assets).values():
        for name,row in rows.items():
            if name in result:raise ValueError("Physical/OCI collision "+name)
            result[name]={"name":name,"size":row["bytes"],"digest":"sha256:"+row["sha256"],"oci":row}
    return result

def fetch_blob(row,path):
    if not record_ok(row):raise ValueError("Invalid blob descriptor")
    path.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(["oras","blob","fetch","--output",str(path),REGISTRY+"@sha256:"+row["sha256"]],check=True)
    if path.stat().st_size!=row["bytes"] or sha(path)!=row["sha256"]:raise ValueError("Blob integrity mismatch "+row["name"])

def anonymous_probe(tag="bootstrap"):
    """Initialize the package once, and fail closed if anonymous access is disabled."""
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/"registry-probe.json";p.write_text('{"schema":1,"project":"danilfg/dicts"}\n')
        row=push_batch(tag,"probe",[p])[0]
        # An empty registry config prevents ORAS from using the writer's credentials.
        config=Path(tmp)/"anonymous.json";config.write_text('{"auths":{}}')
        args=["oras","blob","fetch","--registry-config",str(config),"--output",str(Path(tmp)/"public.json"),REGISTRY+"@sha256:"+row["sha256"]]
        try:subprocess.run(args,check=True)
        except subprocess.CalledProcessError:
            raise SystemExit("GHCR package is not publicly readable. Set danilfg/dicts-data visibility to Public, then rerun the workflow.")
        if sha(Path(tmp)/"public.json")!=row["sha256"]:raise ValueError("Public registry probe integrity mismatch")
    print("Verified public OCI access:",REGISTRY,flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("action",choices=["upload","probe"]);p.add_argument("--tag",default="bootstrap");p.add_argument("files",nargs="*")
    a=p.parse_intermixed_args()
    if a.action=="probe":anonymous_probe(a.tag)
    else:publish(a.tag,a.files)
