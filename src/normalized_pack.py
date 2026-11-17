"""Pack verified, source-labelled JSON shards into release-sized assets."""
import hashlib
import json
import shutil
import subprocess
import struct
import zipfile
from pathlib import Path

MAX_PACK = 1_400_000_000
GROUPS = ("bilingual","pages","oewn","omw","conceptnet","kaikki","tatoeba","pages-lexical")

def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f,"sha256").hexdigest()

def pull(tag, names, directory, assets=None):
    from unified_release import REPO, inventory, digest
    directory.mkdir(parents=True, exist_ok=True)
    assets = assets if assets is not None else inventory(tag)
    names = sorted(set(names))
    for start in range(0,len(names),40):
        batch = names[start:start+40]
        cmd = ["gh","release","download",tag,"-R",REPO,"--dir",str(directory),"--clobber"]
        for name in batch:
            if name not in assets:raise ValueError("Missing input "+name)
            cmd.extend(["--pattern",name])
        subprocess.run(cmd, check=True)
        for name in batch:
            path=directory/name
            if path.stat().st_size!=assets[name]["size"] or sha(path)!=digest(assets[name]):
                raise ValueError("Input integrity error: "+name)
    return directory

def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n",encoding="utf8")

def pack(root,group,output,max_bytes=MAX_PACK):
    files=sorted(p for p in root.rglob("*") if p.is_file() and p.name!=".nojekyll")
    if not files:raise ValueError("Empty normalized group: "+group)
    output.mkdir(parents=True,exist_ok=True)
    groups=[];current=[];size=0
    for path in files:
        amount=path.stat().st_size+1024
        if amount>=max_bytes:raise ValueError("Shard too large: "+str(path))
        if current and size+amount>=max_bytes:
            groups.append(current);current=[];size=0
        current.append(path);size+=amount
    if current:groups.append(current)
    packages=[];members={}
    for i,batch in enumerate(groups,1):
        name=f"normalized--{group}-{i:03d}.zip"
        dest=output/name
        with zipfile.ZipFile(dest,"w",compression=zipfile.ZIP_STORED,allowZip64=True) as z:
            for path in batch:
                member=path.relative_to(root).as_posix()
                info=zipfile.ZipInfo(member,date_time=(1980,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_STORED;info.external_attr=0o644<<16
                with z.open(info,"w",force_zip64=True) as dst,path.open("rb") as src:
                    shutil.copyfileobj(src,dst,1024*1024)
                members[member]={"pack":name,"bytes":path.stat().st_size,"sha256":sha(path)}
        if dest.stat().st_size>=max_bytes:raise ValueError("Pack too large "+name)
        with zipfile.ZipFile(dest) as z, dest.open("rb") as raw:
            if z.testzip() is not None:raise ValueError("Corrupt ZIP "+name)
            for entry in z.infolist():
                raw.seek(entry.header_offset)
                header=raw.read(30)
                if header[:4]!=b"PK\x03\x04" or entry.compress_type!=zipfile.ZIP_STORED:raise ValueError("Invalid stored ZIP member")
                name_len,extra_len=struct.unpack_from("<HH",header,26)
                members[entry.filename]["offset"]=entry.header_offset+30+name_len+extra_len
        packages.append({"name":name,"bytes":dest.stat().st_size,"sha256":sha(dest)})
    doc={"schema":1,"group":group,"packages":packages,"members":members}
    write_json(output/f"normalized--{group}-index.json",doc)
    return doc

def unpack(packs,doc,target):
    seen=set()
    for item in doc["packages"]:
        path=packs/item["name"]
        if sha(path)!=item["sha256"] or path.stat().st_size!=item["bytes"]:
            raise ValueError("Normalized pack integrity mismatch")
        with zipfile.ZipFile(path) as z:
            for entry in z.infolist():
                name=entry.filename
                dst=target/name
                if name in seen or not dst.resolve().is_relative_to(target.resolve()):
                    raise ValueError("Unsafe/duplicate normalized member "+name)
                meta=doc["members"][name]
                if meta["pack"]!=path.name or entry.file_size!=meta["bytes"]:
                    raise ValueError("Invalid member manifest "+name)
                dst.parent.mkdir(parents=True,exist_ok=True)
                with z.open(entry) as src,dst.open("wb") as out:shutil.copyfileobj(src,out)
                if sha(dst)!=meta["sha256"]:raise ValueError("Member checksum mismatch "+name)
                seen.add(name)
    if seen!=set(doc["members"]):raise ValueError("Missing normalized members")
