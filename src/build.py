#!/usr/bin/env python3
"""Build independently licensed dictionary assets for danilfg/dicts.
The browser extension downloads from this repository, never from upstream.
"""
import argparse
import bz2
import datetime as dt
import gzip
import hashlib
import html
import io
import json
import re
import shutil
import struct
import tarfile
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

ROOT=Path(__file__).resolve().parent.parent
CONFIG=json.loads((ROOT/"configs/sources.json").read_text(encoding="utf8"))
LEGAL={x["id"]:x for x in json.loads((ROOT/"legal/SOURCES.json").read_text(encoding="utf8"))["families"]}
USER_AGENT="Dicts-source-sync/0.1 (github.com/danilfg/dicts)"
SOURCE_STATUSES={}
ASSETS=[]
ENRICH=defaultdict(dict)

def urlopen(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":USER_AGENT}),timeout=120)

def read_url(url,limit=160_000_000):
    with urlopen(url) as r:
        buf=io.BytesIO()
        while data:=r.read(1<<20):
            buf.write(data)
            if buf.tell()>limit:raise ValueError("Download size limit exceeded: "+url)
        return buf.getvalue()

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        while chunk:=f.read(1<<20):h.update(chunk)
    return h.hexdigest()

def record(path,source,pair,url,license_expression,version="",modified=False,attribution=""):
    if not license_expression or not attribution:
        raise ValueError("Missing legal evidence for "+path.name)
    ASSETS.append({"name":path.name,"source":source,"pair":pair,
       "source_url":url,"version":version,"license":license_expression,
       "license_url":LEGAL[source]["license_url"],
       "attribution":attribution,"modified":modified,
       "bytes":path.stat().st_size,"sha256":sha256(path),
       "download_url":"https://github.com/danilfg/dicts/releases/latest/download/"+path.name})

def zip_members(path):
    with zipfile.ZipFile(path) as z:
        bad=z.testzip()
        if bad:raise ValueError("Corrupt ZIP member: "+bad)
        return z.namelist()

def mirror_koreader(out,upstream):
    files=sorted(upstream.glob("*.zip"))
    expected=CONFIG["koreader"]["expected"]
    if len(files)!=expected:raise ValueError("Expected %d KOReader ZIPs; found %d"%(expected,len(files)))
    for f in files:
        with zipfile.ZipFile(f) as z:
            if z.testzip():raise ValueError("Corrupt ZIP: "+f.name)
            names=z.namelist()
            licenses=[x for x in names if Path(x).name.upper()=="LICENSE"]
            credits=[x for x in names if Path(x).name.upper()=="ATTRIBUTION"]
            if not licenses or not credits:raise ValueError("Missing LICENSE/ATTRIBUTION: "+f.name)
            license_text=z.read(licenses[0]).decode("utf8","replace")
            if not license_text.strip():raise ValueError("Empty original license: "+f.name)
            patterns=[("CC-BY-SA-4.0",r"CC\s*BY.SA\s*4\.0|Attribution.ShareAlike\s*4\.0"),
                      ("CC-BY-SA-3.0",r"CC\s*BY.SA\s*3\.0"),("CeCILL-C",r"CeCILL.C")]
            tag=next((label for label,regex in patterns if re.search(regex,license_text,re.I)),"SEE-EMBEDDED-LICENSE")
        dest=out/("koreader--"+f.name)
        shutil.copyfile(f,dest)   # exact original bytes; license and attribution stay inside
        record(dest,"koreader",f.stem,
               "https://github.com/danilfg/koreader-dicts/releases/tag/"+CONFIG["koreader"]["tag"],
               tag,CONFIG["koreader"]["tag"],False,
               "Daniel Gregorini and original contributors; embedded LICENSE and ATTRIBUTION")
    SOURCE_STATUSES["koreader"]={"status":"included","archives":len(files)}
    print("KOREADER",len(files),flush=True)

def tar_data(blob):
    with tarfile.open(fileobj=io.BytesIO(blob),mode="r:xz") as t:
        result={}
        for m in t:
            if m.isfile() and m.size<400_000_000:
                file=t.extractfile(m)
                if file:result[Path(m.name).name]=file.read()
    return result

def stardict(raw):
    d={k:v for k,v in raw.items() if k.endswith((".ifo",".idx",".syn",".dict.dz",".dict"))}
    if not any(k.endswith(".idx") for k in d):raise ValueError("StarDict index missing")
    if not any(k.endswith((".dict",".dict.dz")) for k in d):raise ValueError("StarDict data missing")
    return d

def extract_glossary(files,limit=170000):
    index=next(v for k,v in files.items() if k.endswith(".idx"))
    name=next(k for k in files if k.endswith((".dict",".dict.dz")))
    data=files[name]
    if name.endswith(".dz"):data=gzip.decompress(data)
    result={}
    i=0
    while i<len(index) and len(result)<limit:
        j=index.find(b"\0",i)
        if j<0 or j+9>len(index):break
        word=index[i:j].decode("utf8","replace").strip().lower()
        offset,size=struct.unpack(">II",index[j+1:j+9])
        i=j+9
        if not word or size==0 or offset+size>len(data):continue
        raw=data[offset:offset+size].decode("utf8","replace")
        value=html.unescape(re.sub(r"<[^>]+>"," ",raw))
        value=" ".join(value.replace("\0"," ").split())[:260]
        if value:result[word]=value
    return result

def merge(pair,glossary,source):
    words=ENRICH[pair]
    for word,value in glossary.items():
        entry=words.setdefault(word,{"translations":[],"meanings":[],"examples":[]})
        if len(entry["translations"])>=4:continue
        if not any(x["text"]==value for x in entry["translations"]):
            entry["translations"].append({"text":value,"source":source,
              "source_url":LEGAL[source]["source_url"]})

def package_zip(path,files,license_text,notice,source_archive=None):
    with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,payload in files.items():
            if ".." in Path(name).parts:raise ValueError("Invalid archive member")
            z.writestr(Path(name).name,payload)
        z.writestr("LICENSE-SOURCE.txt",license_text)
        z.writestr("ATTRIBUTION.txt",notice)
        if source_archive is not None:
            z.writestr("ORIGINAL-SOURCE.tar.xz",source_archive)
    zip_members(path)

def build_freedict(out):
    cfg=CONFIG["freedict"]
    catalog={x["name"]:x for x in json.loads(read_url(cfg["catalog"],20_000_000))}
    codes={"eng":"en","rus":"ru","spa":"es","deu":"de"}
    successes=0
    for name in cfg["pairs"]:
        try:
            item=catalog[name]
            formats={x["platform"]:x for x in item["releases"]}
            if not {"src","stardict"}.issubset(formats):raise ValueError("Both src and StarDict required")
            binary=read_url(formats["stardict"]["URL"])
            source=read_url(formats["src"]["URL"])
            for obj,blob in ((formats["stardict"],binary),(formats["src"],source)):
                if hashlib.sha512(blob).hexdigest()!=obj["checksum"]:raise ValueError("Upstream SHA-512 mismatch")
            raw=stardict(tar_data(binary))
            original=tar_data(source)
            tei=[v for k,v in original.items() if k.endswith((".tei",".xml"))]
            evidence=[]
            for data in tei:
                try:
                    root=ET.fromstring(data)
                    for element in root.findall(".//{*}availability")+root.findall(".//{*}licence"):
                        snippet=ET.tostring(element,encoding="unicode")
                        if snippet and snippet not in evidence:evidence.append(snippet[:10000])
                except ET.ParseError:pass
            if not evidence:raise ValueError("No original TEI licensing/copyright statement")
            terms="\n".join(evidence)
            if not re.search(r"GPL|GFDL|Creative Commons|CC[-\s]?BY|public domain|license|licence",terms,re.I):
                raise ValueError("TEI license not identifiable; requires human review")
            pair="-".join(codes.get(p,p) for p in name.split("-"))
            dest=out/("freedict--"+pair+".zip")
            notice=("FreeDict "+name+" "+item["edition"]+"\n"+formats["src"]["URL"]+
                "\nOriginal authors/copyright/license: LICENSE-SOURCE.txt and ORIGINAL-SOURCE.tar.xz"+
                "\nModified by danilfg: archive repackaging, indexed excerpt extraction")
            package_zip(dest,raw,terms,notice,source)
            merge(pair,extract_glossary(raw),"freedict")
            record(dest,"freedict",pair,formats["stardict"]["URL"],
                   "PER-DICTIONARY-TEI: see LICENSE-SOURCE.txt",item["edition"],True,notice)
            successes+=1
        except Exception as e:
            SOURCE_STATUSES["freedict:"+name]={"status":"skipped","reason":str(e)[:350]}
            print("FREEDICT SKIPPED",name,str(e)[:300],flush=True)
    SOURCE_STATUSES["freedict"]={"status":"included" if successes==len(cfg["pairs"]) else "partial",
                                  "included":successes,"requested":len(cfg["pairs"])}

def build_wikdict(out):
    cfg=CONFIG["wikdict"];count=0
    for pair in cfg["pairs"]:
        url=cfg["dir"]+"wikdict-"+pair+".zip"
        try:
            b=read_url(url,100_000_000)
            with zipfile.ZipFile(io.BytesIO(b)) as z:
                if z.testzip():raise ValueError("Corrupt upstream ZIP")
                data={Path(n).name:z.read(n) for n in z.namelist() if not n.endswith("/")}
            parsed=stardict(data)
            dest=out/("wikdict--"+pair+".zip")
            notice=("WikDict (Karl Bartel), Wiktionary contributors through DBnary\n"+
              "Source: "+url+"\nLicense: https://creativecommons.org/licenses/by-sa/4.0/\n"+
              "Modified: repackaging, local index extraction")
            package_zip(dest,parsed,notice,notice)
            merge(pair,extract_glossary(parsed),"wikdict")
            record(dest,"wikdict",pair,url,"CC-BY-SA-4.0","source version: online directory",
                   True,notice)
            count+=1
        except Exception as e:
            SOURCE_STATUSES["wikdict:"+pair]={"status":"skipped","reason":str(e)[:350]}
            print("WIKDICT SKIPPED",pair,str(e)[:300],flush=True)
    SOURCE_STATUSES["wikdict"]={"status":"included" if count==len(cfg["pairs"]) else "partial",
                                "included":count,"requested":len(cfg["pairs"])}

def build_kaikki():
    c=CONFIG["kaikki"]
    blob=read_url(c["url"],20_000_000)
    count=0
    for line in gzip.decompress(blob).splitlines():
        try:entry=json.loads(line)
        except ValueError:continue
        word=str(entry.get("word","")).strip().lower()
        if entry.get("lang_code")!="en" or not ((" " in word) or ("-" in word)) or len(word)>100:continue
        gloss=next((g for s in entry.get("senses",[]) for g in s.get("glosses",[]) if g),"")
        if not gloss:continue
        e=ENRICH["en-ru"].setdefault(word,{"translations":[],"meanings":[],"examples":[]})
        if len(e["meanings"])<2:
            e["meanings"].append({"text":gloss[:250],"source":"kaikki",
                  "source_url":"https://simple.wiktionary.org/wiki/"+quote(word.replace(" ","_")),
                  "license":"CC-BY-SA-4.0"})
        count+=1
        if count>=c["max_phrases"]:break
    if not count:raise ValueError("No valid multi-word expressions")
    SOURCE_STATUSES["kaikki"]={"status":"included","entries":count,"url":c["url"]}

def bz2_lines(url):
    with urlopen(url) as response:
        dec=bz2.BZ2Decompressor()
        pending=b""
        while block:=response.read(1<<18):
            pending+=dec.decompress(block)
            *lines,pending=pending.split(b"\n")
            for line in lines:yield line.decode("utf8","replace").rstrip("\r")
        if pending:yield pending.decode("utf8","replace")

def lookup_sentences(url,wanted):
    result={}
    for line in bz2_lines(url):
        parts=line.split("\t")
        if len(parts)<3:continue
        try:identifier=int(parts[0])
        except ValueError:continue
        if identifier in wanted and 0<len(parts[2])<260:
            result[identifier]={"text":parts[2],"author":parts[3] if len(parts)>3 else ""}
    return result

def build_tatoeba():
    c=CONFIG["tatoeba"];links={}
    for line in bz2_lines(c["links"]):
        a=line.split("\t")
        if len(a)!=2:continue
        try:links[int(a[0])]=int(a[1])
        except ValueError:continue
        if len(links)>=c["max_pairs"]:break
    if not links:raise ValueError("No sentence links")
    en=lookup_sentences(c["en"],set(links))
    ru=lookup_sentences(c["ru"],set(links.values()))
    count=0
    for enid,ruid in links.items():
        left,right=en.get(enid),ru.get(ruid)
        if not left or not right:continue
        original=left["text"]
        example={"text":original,"translation":right["text"],"source":"tatoeba",
             "source_url":"https://tatoeba.org/en/sentences/show/"+str(enid),
             "sentence_id":enid,"translation_id":ruid,"author":left["author"],
             "translation_author":right["author"],"license":"CC-BY-2.0-FR"}
        for word in set(re.findall(r"[a-z]{4,}(?:-[a-z]+)*",original.lower())):
            e=ENRICH["en-ru"].setdefault(word,{"translations":[],"meanings":[],"examples":[]})
            if len(e["examples"])<c["examples_per_word"]:e["examples"].append(example)
        count+=1
    if not count:raise ValueError("No English-Russian sentence pairs joined")
    SOURCE_STATUSES["tatoeba"]={"status":"included","sentence_pairs":count}

def save_enrichment(out):
    for pair,words in ENRICH.items():
        if not words:continue
        outpath=out/("enrichment--"+pair+".json.gz")
        payload={"schema":1,"pair":pair,"sources":LEGAL,"words":words}
        b=json.dumps(payload,ensure_ascii=False,separators=(",",":")).encode("utf8")
        with gzip.open(outpath,"wb",compresslevel=7) as f:f.write(b)
        if outpath.stat().st_size>90_000_000:raise ValueError("Enrichment too large")
        sources=sorted(set(x.get("source") for v in words.values() for key in ("translations","meanings","examples") for x in v[key]))
        record(outpath,"aggregate",pair,"https://github.com/danilfg/dicts",
               "MULTI-LICENSE-BY-RECORD: "+", ".join(sources),"1",True,
               "Respect rights of each entry via sources and metadata; see THIRD-PARTY-NOTICES.md")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--upstream",default="upstream")
    ap.add_argument("--out",default="dist")
    ap.add_argument("--mode",choices=["all","core"],default="all")
    args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    mirror_koreader(out,Path(args.upstream))
    if args.mode=="all":
        for source,fn in (("freedict",build_freedict),("wikdict",build_wikdict)):
            try:fn(out)
            except Exception as exc:
                SOURCE_STATUSES[source]={"status":"skipped","reason":str(exc)[:400]}
                print(source,"SKIPPED",str(exc),flush=True)
        for source,fn in (("kaikki",build_kaikki),("tatoeba",build_tatoeba)):
            try:fn()
            except Exception as exc:
                SOURCE_STATUSES[source]={"status":"skipped","reason":str(exc)[:400]}
                print(source,"SKIPPED",str(exc),flush=True)
    else:
        for source in ("freedict","wikdict","kaikki","tatoeba"):
            SOURCE_STATUSES[source]={"status":"not_requested","reason":"core mode"}
    save_enrichment(out)
    for a in ASSETS:
        path=out/a["name"]
        if not path.exists() or sha256(path)!=a["sha256"]:
            raise ValueError("Artifact SHA mismatch: "+a["name"])
    report={"schema":1,"repository":"danilfg/dicts",
      "generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),
      "mode":args.mode,"source_status":SOURCE_STATUSES,
      "assets":ASSETS,"legal":LEGAL,
      "notice":"Original licenses per asset; MIT only for our code."}
    (out/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    notices=["# Rights and attribution — specific released assets","",
       "This release includes THIRD-PARTY dictionary data under separate licenses.",
       "MIT on the source code does NOT apply to third-party dictionary content.",
       "See https://github.com/danilfg/dicts/blob/main/legal/NOTICE.md",""]
    for a in ASSETS:
        notices.extend(["## "+a["name"],"- Source: "+a["source_url"],
            "- Provider: "+a["source"],"- Language pair: "+a["pair"],
            "- License evidence: "+a["license"],"- License URL: "+a["license_url"],
            "- Attribution: "+a["attribution"],"- Modified: "+str(a["modified"]),
            "- SHA-256: "+a["sha256"],""])
    (out/"THIRD-PARTY-NOTICES.md").write_text("\n".join(notices),encoding="utf8")
    print("BUILD COMPLETE:",len(ASSETS),"assets",json.dumps(SOURCE_STATUSES,ensure_ascii=False),flush=True)

if __name__=="__main__":main()
