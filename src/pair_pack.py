"""Application transport: independent pair and language ZIPs in OCI layers.

Only the selected blobs are downloaded. Cross-language links are split
by target language; no third-language translation data enters a pair payload.
"""
import collections
import gzip
import json
import re
import sqlite3
import tempfile
import zipfile
from pathlib import Path

from build_pages import bucket,write_gzip
from normalized_pack import write_json,sha
from storage import REGISTRY,FORMAT

LAYOUT=FORMAT
BLOCK_MAX=32*1024*1024
LINK_BUCKETS=32
# New lexical group adapters can register here without adding a client switch.
# Fields absent from this registry are preserved as language-local records.
CROSS_FIELDS={"kaikki":"translations","conceptnet":"relations","tatoeba":"examples"}
PAIR_RE=re.compile(r"^[a-z0-9]{2,20}-[a-z0-9]{2,20}$")
LANG_RE=re.compile(r"^[a-z0-9]{2,20}$")

def split_record(group,language,entry):
    """Separate language-local information from directional links."""
    original=dict(entry); links=collections.defaultdict(list)
    field=CROSS_FIELDS.get(group)
    if not field:return original,{}
    local=[]
    if field=="examples":
        for e in entry.get(field,[]):
            base=dict(e,translations=[])
            local.append(base)
            targets=collections.defaultdict(list)
            for t in e.get("translations",[]):
                if LANG_RE.fullmatch(str(t.get("language",""))) and t["language"]!=language:
                    targets[t["language"]].append(t)
            for target,translations in targets.items():links[target].append(dict(base,translations=translations))
    else:
        for e in entry.get(field,[]):
            target=e.get("language")
            if target==language:local.append(e)
            elif LANG_RE.fullmatch(str(target or "")):links[target].append(e)
    original[field]=local
    if group=="conceptnet" and not local:original=None
    if group=="kaikki" and not local and not original.get("definitions"):original=None
    records={}
    for target,values in links.items():
        row={field:values}
        if group=="kaikki":
            row.update({k:entry[k] for k in ("source_url","license","parts_of_speech") if k in entry})
        records[target]=row
    return original,records

def mini_zips(root,files,out,stem):
    """Create bounded, deterministic ordinary standalone ZIPs for individual OCI blob downloads."""
    blocks=[]; batch=[]; total=0
    def flush():
        if not batch:return
        name=f"{stem}-{len(blocks)+1:03d}.zip"
        dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(dest,"w",compression=zipfile.ZIP_STORED,allowZip64=False) as z:
            for path in batch:
                info=zipfile.ZipInfo(path.relative_to(root).as_posix(),date_time=(1980,1,1,0,0))
                info.compress_type=zipfile.ZIP_STORED
                # Each shard is bounded; inner ZIPs use standard ZIP32.
                z.writestr(info,path.read_bytes())
        with zipfile.ZipFile(dest) as z:
            if z.testzip() is not None:raise ValueError("Invalid unit block")
        if dest.stat().st_size>BLOCK_MAX:raise ValueError("Unit block too large "+name)
        blocks.append(name)
    for path in sorted(files,key=lambda p:p.relative_to(root).as_posix()):
        size=path.stat().st_size+1024
        if size>BLOCK_MAX:raise ValueError("Increase shard count for "+str(path))
        if batch and total+size>BLOCK_MAX:
            flush();batch=[];total=0
        batch.append(path);total+=size
    flush()
    return blocks

def pack_application(root,group,output):
    """Create only pair-addressable application blocks; Pages stays separate."""
    with tempfile.TemporaryDirectory(dir=root.parent) as tmp:
        work=Path(tmp); units=work/"units"; units.mkdir()
        catalog=work/"unit-data"; catalog.mkdir()
        directories={"pairs":{},"languages":{}}
        pair_meta={}
        def emit(scope,key,files,base,meta):
            if not files:return
            if not (PAIR_RE if scope=="pairs" else LANG_RE).fullmatch(key):
                # Existing app pair syntax uses ISO-like two/three-letter language codes.
                # BCP47 variants with hyphens cannot be represented unambiguously in this API.
                return
            unit_file=base/"UNIT.json"
            write_json(unit_file,dict(meta,schema=1,group=group,scope=scope,id=key))
            # ZIP paths are relative to base; original member paths are preserved.
            directories[scope][key]=mini_zips(base,files+[unit_file],units,f"{scope}/{key}")
            unit_file.unlink()
        if group=="bilingual":
            doc=json.loads((root/"data/catalog.json").read_text())
            for row in doc["pairs"]:
                key=row["pair"]; files=list((root/"data"/key).glob("*.json.gz"))
                if not files:raise ValueError("Missing bilingual unit "+key)
                emit("pairs",key,files,root,{"kind":"bilingual","descriptor":row,"provenance":doc["provenance"].get(key,{})})
                if PAIR_RE.fullmatch(key):pair_meta[key]={"from":row["from"],"to":row["to"],"sources":sorted(set(doc["provenance"].get(key,{}))|{x["id"] for x in row["sources"]})}
        else:
            doc=json.loads((root/"data/lexical"/group/"catalog.json").read_text())
            by_lang=collections.defaultdict(list)
            db=sqlite3.connect(work/"links.sqlite")
            db.execute("PRAGMA journal_mode=OFF")
            db.execute("PRAGMA synchronous=OFF")
            db.execute("CREATE TABLE links(pair TEXT,bucket INTEGER,word TEXT,package TEXT,record TEXT)")
            try:
                for desc in doc["languages"]:
                    language=desc["language"]
                    if not LANG_RE.fullmatch(language):continue
                    by_lang[language].append(desc)
                    for path in sorted((root/desc["path"]).glob("*.json.gz")):
                        if group not in CROSS_FIELDS:continue
                        with gzip.open(path,"rt",encoding="utf8") as stream:shard=json.load(stream)
                        local={}; rows=[]
                        for word,entry in shard["words"].items():
                            base,links=split_record(group,language,entry)
                            if base is not None:local[word]=base
                            for target,record in links.items():
                                rows.append((language+"-"+target,bucket(word,LINK_BUCKETS),word,desc["package"] or "",json.dumps(record,ensure_ascii=False,separators=(",",":"))))
                        if rows:db.executemany("INSERT INTO links VALUES(?,?,?,?,?)",rows)
                        shard["words"]=local
                        write_gzip(path,shard)
                    db.commit()
                for language,descs in sorted(by_lang.items()):
                    files=[p for d in descs for p in (root/d["path"]).glob("*.json.gz")]
                    emit("languages",language,files,root,{"kind":"lexical","descriptors":descs})
                db.execute("CREATE INDEX link_order ON links(pair,bucket,word,package)")
                db.commit()
                pairs=[r[0] for r in db.execute("SELECT DISTINCT pair FROM links ORDER BY pair")]
                for key in pairs:
                    files=[]; base=catalog/key
                    words={}; current=None
                    def flush():
                        if current is None:return
                        path=base/"data"/"links"/group/key/f"{current:02x}.json.gz"
                        write_gzip(path,{"schema":1,"source":group,"pair":key,"words":words});files.append(path)
                    for n,word,package,record in db.execute("SELECT bucket,word,package,record FROM links WHERE pair=? ORDER BY bucket,word,package",(key,)):
                        if n!=current:
                            flush();current=n;words={}
                        words.setdefault(word,[]).append({"package":package or None,"record":json.loads(record)})
                    flush()
                    emit("pairs",key,files,base,{"kind":"links","path":f"data/links/{group}/{key}","buckets":LINK_BUCKETS})
                    if group=="kaikki":
                        src,dst=key.split("-")
                        pair_meta[key]={"from":src,"to":dst,"sources":[group]}
                    for file in files:file.unlink()
            finally:db.close()
        if not any(directories.values()):raise ValueError("Empty application group "+group)
        output.mkdir(parents=True,exist_ok=True)
        members={}
        for source_path in sorted(units.rglob("*.zip")):
            key=source_path.relative_to(units).as_posix()
            name="unit--"+group+"--"+key.replace("/","--")
            target=output/name
            source_path.replace(target)
            members[key]={"name":name,"bytes":target.stat().st_size,"sha256":sha(target)}
        result={"schema":1,"group":group,"layout":LAYOUT,"units":directories,"pair_meta":pair_meta,"members":members}
        write_json(output/f"normalized--{group}-index.json",result)
        return result

def build_pair_index(tag,indexes,base,assets):
    """Merge independently produced group directories into a small public API."""
    pairs={}; groups={}
    for group,doc in indexes.items():
        if doc.get("layout")!=LAYOUT:raise ValueError("Missing OCI layout "+group)
        mapped={"pairs":{},"languages":{}}
        seen=set()
        for scope in mapped:
            for key,names in doc["units"][scope].items():
                if not names or not (PAIR_RE if scope=="pairs" else LANG_RE).fullmatch(key):raise ValueError("Invalid unit "+key)
                blocks=[]
                for name in names:
                    if name in seen:raise ValueError("Duplicate OCI block "+name)
                    seen.add(name);m=doc["members"][name];row=assets[m["name"]]
                    size=m["bytes"]
                    if not 0<size<=BLOCK_MAX or row["size"]!=size or row["digest"]!="sha256:"+m["sha256"] or row.get("oci",{}).get("registry")!=REGISTRY:
                        raise ValueError("Invalid OCI block "+name)
                    blocks.append({"bytes":size,"sha256":m["sha256"],"manifest":row["oci"]["manifest"]})
                mapped[scope][key]=blocks
        if seen!=set(doc["members"]):raise ValueError("Unaddressed OCI block "+group)
        groups[group]=mapped
        for key,row in doc.get("pair_meta",{}).items():
            if key not in mapped["pairs"]:raise ValueError("Unaddressed pair "+key)
            existing=pairs.setdefault(key,{"from":row["from"],"to":row["to"],"sources":[]})
            if existing["from"]!=row["from"] or existing["to"]!=row["to"]:raise ValueError("Pair mismatch")
            existing["sources"]=sorted(set(existing["sources"]+row["sources"]))
    if not pairs:raise ValueError("Empty pair catalog")
    # A pair is offered only when at least one actual translation source exists.
    languages={v[k] for v in pairs.values() for k in ("from","to")}
    for g in groups.values():
        g["pairs"]={k:v for k,v in g["pairs"].items() if k in pairs}
        g["languages"]={k:v for k,v in g["languages"].items() if k in languages}
    return {"schema":1,"format":LAYOUT,"registry":REGISTRY,"version":tag,"download_base":base,"pairs":pairs,"groups":groups}
