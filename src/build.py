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
import sqlite3
import os
import subprocess
import tempfile
import time
from html.parser import HTMLParser
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
from upstream_cache import request,strong_etag

ROOT=Path(__file__).resolve().parent.parent
CONFIG=json.loads((ROOT/"configs/sources.json").read_text(encoding="utf8"))
LEGAL={x["id"]:x for x in json.loads((ROOT/"legal/SOURCES.json").read_text(encoding="utf8"))["families"]}
USER_AGENT="Dicts-source-sync/0.1 (github.com/danilfg/dicts)"
SOURCE_STATUSES={}
ASSETS=[]
ENRICH=defaultdict(dict)
INDEX_DB=None
PREVIOUS_TAG=os.getenv('PREVIOUS_RELEASE_TAG','')
PREVIOUS={}
PREVIOUS_ASSETS={}
FALLBACKS={}

def load_previous(out):
    if not PREVIOUS_TAG:return
    from unified_release import inventory
    PREVIOUS_ASSETS.clear()
    PREVIOUS_ASSETS.update(inventory(PREVIOUS_TAG))
    print('Previous release inventory cached:',len(PREVIOUS_ASSETS),'files',flush=True)
    with tempfile.TemporaryDirectory() as tmp:
        from normalized_pack import pull
        pull(PREVIOUS_TAG,['manifest.json'],Path(tmp),PREVIOUS_ASSETS)
        PREVIOUS.update({a['name']:a for a in json.loads((Path(tmp)/'manifest.json').read_text())['assets']})

def carry_file(out,name,reason):
    item=PREVIOUS.get(name)
    if any(a['name']==name for a in ASSETS):return True
    FALLBACKS[name]={'source':name.split('--')[0], 'reason':str(reason)[:350], 'previous_release':PREVIOUS_TAG, 'retained':bool(item)}
    if not item:return False
    from normalized_pack import pull
    pull(PREVIOUS_TAG,[name],out,PREVIOUS_ASSETS)
    path=out/name
    if path.stat().st_size!=item['bytes'] or sha256(path)!=item['sha256']:raise ValueError('Previous asset integrity mismatch: '+name)
    ASSETS.append(dict(item))
    print('Reused verified prior file',name,flush=True)
    if item['source'] in ('freedict','wikdict'):
        with zipfile.ZipFile(path) as z:
            raw=stardict({Path(n).name:z.read(n) for n in z.namelist() if n.endswith(('.ifo','.idx','.dict','.dict.dz','.dict.gz','.idx.gz','.syn'))})
        merge(item['pair'],extract_glossary(raw),item['source'])
    return True

def carry_family(out,source,reason):
    names=sorted(n for n,a in PREVIOUS.items() if a['source']==source)
    if not names:raise ValueError('No previous usable '+source+' source')
    for name in names:carry_file(out,name,reason)
    count=sum(a['source']==source for a in ASSETS)
    SOURCE_STATUSES[source]={'status':'included','included':count,'discovered':count,'archives':count,'fallback':True,'reason':str(reason)[:350]}

def carry_enrichment(source,reason):
    if not PREVIOUS_TAG:raise ValueError('No previous enrichment for '+source)
    field='meanings' if source=='kaikki' else 'examples'
    for words in ENRICH.values():
        for row in words.values():row[field]=[x for x in row[field] if x.get('source')!=source]
    with tempfile.TemporaryDirectory() as tmp:
        name='enrichment--en-ru.json.gz'
        from normalized_pack import pull
        pull(PREVIOUS_TAG,[name],Path(tmp),PREVIOUS_ASSETS)
        path=Path(tmp)/name
        if sha256(path)!=PREVIOUS[name]['sha256']:raise ValueError('Previous enrichment integrity mismatch')
        with gzip.open(path,'rt',encoding='utf8') as f:words=json.load(f)['words']
        count=0
        for word,row in words.items():
            records=[x for x in row.get(field,[]) if x.get('source')==source]
            if records:
                ENRICH['en-ru'].setdefault(word,{'translations':[],'meanings':[],'examples':[]})[field].extend(records)
                count+=len(records)
        if not count:raise ValueError('No previous usable enrichment for '+source)
    SOURCE_STATUSES[source]={'status':'included','fallback':True,'reason':str(reason)[:350]}
    FALLBACKS[source+'--compact-enrichment']={'source':source,'reason':str(reason)[:350],'previous_release':PREVIOUS_TAG,'retained':True}

def init_index(out):
    global INDEX_DB
    INDEX_DB=sqlite3.connect(str(out/'_enrich.sqlite3'))
    INDEX_DB.execute("PRAGMA journal_mode=MEMORY")
    INDEX_DB.execute("PRAGMA synchronous=OFF")
    INDEX_DB.execute("CREATE TABLE IF NOT EXISTS translations (pair TEXT NOT NULL, word TEXT NOT NULL, source TEXT NOT NULL, meaning TEXT NOT NULL, PRIMARY KEY(pair,word,source)) WITHOUT ROWID")

def urlopen(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":USER_AGENT}),timeout=120)

def read_url(url,limit=160_000_000):
    for attempt in range(3):
        try:
            with urlopen(url) as r:
                buf=io.BytesIO()
                while data:=r.read(1<<20):
                    buf.write(data)
                    if buf.tell()>limit:raise ValueError("Download size limit exceeded: "+url)
                return buf.getvalue()
        except (OSError, TimeoutError):
            if attempt==2:raise
            time.sleep(2**attempt)

def conditional_read(url,previous,limit):
    etag=previous.get("upstream_etag") if previous.get("source_url")==url else None
    for attempt in range(3):
        try:
            response=request(url,USER_AGENT,etag,120)
            if response is None:return None,etag
            with response as r:
                current=r.headers.get("ETag")
                buf=io.BytesIO()
                while data:=r.read(1<<20):
                    buf.write(data)
                    if buf.tell()>limit:raise ValueError("Download size limit exceeded: "+url)
                return buf.getvalue(), current if strong_etag(current) else None
        except OSError:
            if attempt==2:raise
            time.sleep(2**attempt)

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
       "download_url":"https://github.com/danilfg/dicts/releases/latest/download/RELEASE-MANIFEST.json"})

def zip_members(path):
    with zipfile.ZipFile(path) as z:
        bad=z.testzip()
        if bad:raise ValueError("Corrupt ZIP member: "+bad)
        return z.namelist()

def mirror_koreader(out,upstream):
    info_path=upstream/"SOURCE_INFO.json"
    info=json.loads(info_path.read_text()) if info_path.exists() else {}
    files=sorted(upstream.glob("*.zip"))
    expected=int(info.get("expected",CONFIG["koreader"]["expected"]))
    if expected<CONFIG["koreader"]["expected"] or len(files)!=expected:
        raise ValueError("Expected %d or more verified KOReader ZIPs; found %d"%(expected,len(files)))
    FALLBACKS.update(info.get('fallbacks',{}))
    source_repo=info.get("repository",CONFIG["koreader"]["repo"])
    source_tag=info.get("tag",CONFIG["koreader"]["tag"])
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
        if dest.name in FALLBACKS and FALLBACKS[dest.name]["retained"]:
            item=PREVIOUS[dest.name]
            if sha256(dest)!=item["sha256"]:raise ValueError("Retained KOReader mismatch")
            ASSETS.append(dict(item))
            continue
        record(dest,"koreader",f.stem,
               "https://github.com/"+source_repo+"/releases/tag/"+source_tag,
               tag,source_tag,False,
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
    for name,payload in raw.items():
        if name.endswith((".idx.gz",".idx.dz")):
            d[name.rsplit(".",1)[0]]=gzip.decompress(payload)
        if name.endswith(".dict.gz"):
            d[name[:-3]]=gzip.decompress(payload)
    if not any(k.endswith(".idx") for k in d):
        raise ValueError("StarDict index missing; archive names: "+repr(sorted(raw)[:25]))
    if not any(k.endswith((".dict",".dict.dz")) for k in d):
        raise ValueError("StarDict data missing; archive names: "+repr(sorted(raw)[:25]))
    return d

def extract_glossary(files):
    index=next(v for k,v in files.items() if k.endswith(".idx"))
    name=next(k for k in files if k.endswith((".dict",".dict.dz")))
    data=files[name]
    if name.endswith(".dz"):data=gzip.decompress(data)
    result={}
    i=0
    while i<len(index):
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
    """Store *all* published bilingual meanings without a language-pair whitelist.
    SQLite prevents hundreds of available language pairs exhausting RAM.
    """
    if not glossary:return
    if INDEX_DB is None:raise ValueError("Enrichment index is not initialized")
    INDEX_DB.executemany("INSERT OR REPLACE INTO translations(pair,word,source,meaning) VALUES(?,?,?,?)",
        ((pair,word,source,value) for word,value in glossary.items() if word and value))
    INDEX_DB.commit()

def package_zip(path,files,license_text,notice,source_archive=None):
    with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        def write(name, payload):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,payload,compresslevel=6)
        for name,payload in sorted(files.items()):
            if ".." in Path(name).parts:raise ValueError("Invalid archive member")
            write(Path(name).name,payload)
        write("LICENSE-SOURCE.txt",license_text)
        write("ATTRIBUTION.txt",notice)
        if source_archive is not None:
            write("ORIGINAL-SOURCE.tar.xz",source_archive)
    zip_members(path)

def build_freedict(out):
    cfg=CONFIG["freedict"]
    catalog={x["name"]:x for x in json.loads(read_url(cfg["catalog"],20_000_000)) if isinstance(x,dict) and x.get("name")}
    codes={"eng":"en","rus":"ru","spa":"es","deu":"de"}
    requested=sorted(catalog) if cfg.get("pairs")=="all" else cfg.get("pairs",[])
    successes=0
    for name in requested:
        pair="-".join(codes.get(p,p) for p in name.split("-"))
        dest=out/("freedict--"+pair+".zip")
        try:
            item=catalog[name]
            formats={x["platform"]:x for x in item["releases"]}
            if not {"src","stardict"}.issubset(formats):raise ValueError("Both src and StarDict required")
            previous=PREVIOUS.get(dest.name,{})
            upstream_hashes={p:formats[p]["checksum"] for p in ("src","stardict")}
            if previous.get("upstream_hashes")==upstream_hashes:
                carry_file(out,dest.name,"verified upstream checksums unchanged")
                FALLBACKS.pop(dest.name,None)
                successes+=1
                continue
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
            ASSETS[-1]["upstream_hashes"]=upstream_hashes
            successes+=1
        except Exception as e:
            if carry_file(out,dest.name,e):successes+=1
            SOURCE_STATUSES["freedict:"+name]={"status":"skipped","reason":str(e)[:350]}
            print("FREEDICT SKIPPED",name,str(e)[:300],flush=True)
    if not successes:raise ValueError("No FreeDict packages")
    SOURCE_STATUSES["freedict"]={"status":"included","included":successes,"discovered":successes,"upstream_discovered":len(requested),"requested":"all available"}

class WikiZipLinks(HTMLParser):
    def __init__(self):
        super().__init__();self.names=set()
    def handle_starttag(self,tag,attrs):
        if tag!="a":return
        href=dict(attrs).get("href","")
        match=re.fullmatch(r"wikdict-([a-z0-9]+-[a-z0-9]+)\.zip",href,re.I)
        if match:self.names.add(match.group(1).lower())

def build_wikdict(out):
    cfg=CONFIG["wikdict"];count=0
    if cfg.get("pairs")=="all":
        parser=WikiZipLinks()
        parser.feed(read_url(cfg["dir"],2_000_000).decode("utf8","replace"))
        requested=sorted(parser.names)
        if not requested:raise ValueError("WikDict directory did not list any ZIP packages")
    else:requested=cfg.get("pairs",[])
    for pair in requested:
        url=cfg["dir"]+"wikdict-"+pair+".zip"
        try:
            name="wikdict--"+pair+".zip"
            b,etag=conditional_read(url,PREVIOUS.get(name,{}),100_000_000)
            if b is None:
                carry_file(out,name,"HTTP 304: upstream archive unchanged")
                FALLBACKS.pop(name,None)
                count+=1
                continue
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
            if etag:ASSETS[-1]["upstream_etag"]=etag
            count+=1
        except Exception as e:
            if carry_file(out,"wikdict--"+pair+".zip",e):count+=1
            SOURCE_STATUSES["wikdict:"+pair]={"status":"skipped","reason":str(e)[:350]}
            print("WIKDICT SKIPPED",pair,str(e)[:300],flush=True)
    if not count:raise ValueError("No WikDict packages")
    SOURCE_STATUSES["wikdict"]={"status":"included","included":count,"discovered":count,"upstream_discovered":len(requested),"requested":"all available"}

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
    """Produce one browser index for *every* bilingual pair found in providers."""
    pairs=set(ENRICH)
    pairs.update(r[0] for r in INDEX_DB.execute("SELECT DISTINCT pair FROM translations"))
    first_level={a["pair"] for a in ASSETS if a["source"]=="koreader"}
    # Browser-loadable indexes for every KOReader pair; other indexes are
    # distributed together in numbered archives to remain below 1000 assets.
    secondary=[]
    for pair in sorted(pairs):
        words=ENRICH.pop(pair,{})
        sources=set()
        for word,source,meaning in INDEX_DB.execute(
                "SELECT word,source,meaning FROM translations WHERE pair=? ORDER BY word,source",(pair,)):
            entry=words.setdefault(word,{"translations":[],"meanings":[],"examples":[]})
            if len(entry["translations"])<8 and not any(x["text"]==meaning and x["source"]==source for x in entry["translations"]):
                entry["translations"].append({"text":meaning,"source":source,"source_url":LEGAL[source]["source_url"]})
                sources.add(source)
        if not words:continue
        for values in words.values():
            for typ in ("translations","meanings","examples"):
                sources.update(x.get("source") for x in values[typ] if x.get("source"))
        outpath=out/("enrichment--"+pair+".json.gz")
        # JSON data are written as a stream to avoid serializing large datasets twice.
        with outpath.open("wb") as output:
            with gzip.GzipFile(filename="",fileobj=output,mode="wb",mtime=0,compresslevel=7) as zipped:
                zipped.write(('{"schema":1,"pair":'+json.dumps(pair)+',"sources":'+
                    json.dumps(LEGAL,ensure_ascii=False,separators=(",",":"))+',"words":{').encode("utf8"))
                first=True
                for word,data in words.items():
                    if not first:zipped.write(b",")
                    first=False
                    zipped.write((json.dumps(word,ensure_ascii=False)+":"+
                        json.dumps(data,ensure_ascii=False,separators=(",",":"))).encode("utf8"))
                zipped.write(b"}}")
        if outpath.stat().st_size>90_000_000:
            raise ValueError("Enrichment too large for browser: "+pair+
                "; use the separate source ZIPs or publish sharded indexes")
        if pair in first_level:
            record(outpath,"aggregate",pair,"https://github.com/danilfg/dicts",
                   "MIXED-PER-ENTRY: "+", ".join(sorted(sources)),"1",True,
                   "Each entry retains upstream source and attribution; see THIRD-PARTY-NOTICES.md")
        else:
            secondary.append(outpath)
    if secondary:
        for k in range(0,len(secondary),40):
            group=secondary[k:k+40]
            dest=out/("enrichments-extra--%03d.zip"%(k//40+1))
            with zipfile.ZipFile(dest,"w",compression=zipfile.ZIP_STORED) as z:
                for item in group:z.write(item,item.name)
                z.writestr("ATTRIBUTION.txt",
                    "Mixed independently licensed records. Each JSON.GZ embeds its "+
                    "source registry and each entry's provenance; "+
                    "see THIRD-PARTY-NOTICES.md and legal/NOTICE.md.")
            zip_members(dest)
            record(dest,"aggregate","multi",
                "https://github.com/danilfg/dicts",
                "MIXED-PER-ENTRY; see embedded record.source and legal/SOURCES.json",
                "1",True,"Original authors/source metadata embedded in each indexed record")
            for item in group:item.unlink()
        SOURCE_STATUSES["extra_enrichment_packs"]={"status":"included",
            "packs":(len(secondary)+39)//40,"language_pairs":len(secondary)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--upstream",default="upstream")
    ap.add_argument("--out",default="dist")
    ap.add_argument("--mode",choices=["all","core"],default="all")
    args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    init_index(out)
    load_previous(out)
    try:mirror_koreader(out,Path(args.upstream))
    except Exception as exc:carry_family(out,"koreader",exc)
    if args.mode=="all":
        for source,fn in (("freedict",build_freedict),("wikdict",build_wikdict)):
            print('Starting',source,flush=True)
            try:fn(out)
            except Exception as exc:
                carry_family(out,source,exc)
                print(source,"RETAINED",str(exc),flush=True)
        for source,fn in (("kaikki",build_kaikki),("tatoeba",build_tatoeba)):
            print('Starting compact enrichment',source,flush=True)
            try:fn()
            except Exception as exc:
                carry_enrichment(source,exc)
                print(source,"RETAINED",str(exc),flush=True)
    else:
        for source in ("freedict","wikdict","kaikki","tatoeba"):
            SOURCE_STATUSES[source]={"status":"not_requested","reason":"core mode"}
    print('Saving bilingual indexes',flush=True)
    save_enrichment(out)
    INDEX_DB.close()
    (out/"_enrich.sqlite3").unlink(missing_ok=True)
    # Remove failed temporary outputs before uploading the candidate inventory.
    published_names={a["name"] for a in ASSETS}
    for path in out.glob("*.zip"):
        if path.name not in published_names:path.unlink()
    for a in ASSETS:
        path=out/a["name"]
        if not path.exists() or sha256(path)!=a["sha256"]:
            raise ValueError("Artifact SHA mismatch: "+a["name"])
    report={"schema":1,"repository":"danilfg/dicts",
      "generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),
      "bundle_format":2,"bundle_name":"BUNDLE-PARTS.json",
      "mode":args.mode,"source_status":SOURCE_STATUSES,"fallbacks":FALLBACKS,
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
