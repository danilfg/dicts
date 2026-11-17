"""Build application-ready JSON lookup shards from the actual staged release.

Original archives are retained separately. Corpus lookups are intentional
bounded study indexes, not claims to contain every upstream sentence or edge.
"""
import argparse
import bz2
import collections
import gzip
import json
import re
import shutil
import subprocess
import tarfile
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote
from build_pages import normalize,bucket,write_gzip
from build_pages_lexical import wordnet_records,uri_concept,RELATIONS
from normalized_pack import pull,pack,write_json
from unified_release import inventory,upload
from download_pages_inputs import choose

LANGS={"eng":"en","rus":"ru","spa":"es","deu":"de","fra":"fr","ita":"it","por":"pt","jpn":"ja","cmn":"zh","zho":"zh","arb":"ar","ara":"ar","fin":"fi","ces":"cs","nld":"nl","pol":"pl","ell":"el","heb":"he","ind":"id","swe":"sv","dan":"da","nor":"no","nob":"nb","nno":"nn","ukr":"uk","tur":"tr","ron":"ro","bul":"bg","lit":"lt","lav":"lv","hrv":"hr","slv":"sl","slk":"sk","hun":"hu","hin":"hi","kor":"ko","cat":"ca","eus":"eu","glg":"gl","isl":"is","tha":"th","msa":"ms","zsm":"ms","sqi":"sq","vie":"vi","fas":"fa","ben":"bn","srp":"sr"}
def lang(code):
    code=str(code).lower().replace("_","-")
    return LANGS.get(code,code) if re.fullmatch(r"[a-z0-9-]{2,20}",code) else "und"

def shards(root,source,language,words,package=None):
    if not words:return None
    count=4 if len(words)<20_000 else 32 if len(words)<200_000 else 128
    base=Path("data")/"lexical"/source/language
    if package:base/=package
    groups=[{} for _ in range(count)]
    for word,value in words.items():
        if word:groups[bucket(word,count)][word]=value
    for i,group in enumerate(groups):
        write_gzip(root/base/f"{i:02x}.json.gz",{"schema":1,"source":source,"language":language,"words":group})
    return {"language":language,"package":package,"path":base.as_posix(),"entries":len(words),"buckets":count}

def raw_file(tag, assets, item, folder):
    folder.mkdir(parents=True,exist_ok=True)
    names=[p["asset"] for p in item["parts"]]
    pull(tag,names,folder,assets)
    target=folder/"upstream"
    with target.open("wb") as out:
        for name in names:
            path=folder/name
            with path.open("rb") as src:shutil.copyfileobj(src,out)
            path.unlink()
    if target.stat().st_size!=item["original_bytes"]:raise ValueError("Raw reassembly mismatch")
    return target

def raw_manifest(tag,assets,source,folder):
    name=source+"--SOURCE-MANIFEST.json"
    pull(tag,[name],folder,assets)
    return json.loads((folder/name).read_text())

def normalize_bilingual(tag,assets,root,folder,compact):
    names=[n for n in assets if n=="manifest.json" or (choose(n) if compact else
        (n.startswith(("koreader--","freedict--","wikdict--","enrichments-extra--")) and n.endswith(".zip")) or
        (n.startswith("enrichment--") and n.endswith(".json.gz")))]
    pull(tag,names,folder,assets)
    if compact:
        subprocess.run(["python","src/select_compact_pages.py","--downloads",str(folder),"--skipped",str(folder/"excluded")],check=True)
    subprocess.run(["python","src/build_pages.py","--download-dir",str(folder),"--manifest",str(folder/"manifest.json"),
                    "--release-tag",tag,"--site-dir",str(root),"--max-site-bytes",str(945_000_000 if compact else 0)],check=True)
    actual={x["pair"] for x in json.loads((root/"data/catalog.json").read_text())["pairs"]}
    expected={x["pair"] for x in json.loads((folder/"manifest.json").read_text())["assets"] if x["source"] in ("koreader","freedict","wikdict")}
    if expected-actual:raise ValueError("Missing normalized pairs: "+repr(sorted(expected-actual)[:20]))

def normalize_omw(path):
    terms=collections.defaultdict(set);senses=collections.defaultdict(set);synsets={};language=None
    with tarfile.open(path,"r:xz") as t:
        for item in t:
            if not item.isfile() or not item.name.endswith(".xml"):continue
            stream=t.extractfile(item)
            for event,e in ET.iterparse(stream,events=("start","end")):
                name=e.tag.rsplit("}",1)[-1]
                if event=="start" and name=="Lexicon":
                    language=lang(e.get("language","und"))
                if event!="end":continue
                if name=="LexicalEntry":
                    lemma=next((x.get("writtenForm","") for x in e if x.tag.rsplit("}",1)[-1]=="Lemma"),"")
                    word=normalize(lemma)
                    if word:
                        for x in e.iter():
                            if x.tag.rsplit("}",1)[-1]=="Sense" and x.get("synset"):
                                sid=x.get("synset");terms[sid].add(lemma);senses[word].add(sid)
                    e.clear()
                elif name=="Synset":
                    sid=e.get("id")
                    if sid:
                        synsets[sid]={"id":sid,"ili":e.get("ili"),"pos":e.get("partOfSpeech"),
                                      "definitions":[" ".join("".join(x.itertext()).split()) for x in e if x.tag.rsplit("}",1)[-1]=="Definition"]}
                    e.clear()
    if not language or not senses:raise ValueError("No OMW word records in "+path.name)
    words={}
    for word,ids in senses.items():
        rows=[synsets[sid] for sid in sorted(ids) if sid in synsets]
        defs=list(dict.fromkeys(d for row in rows for d in row["definitions"] if d))
        synonyms=sorted({term for sid in ids for term in terms[sid] if normalize(term)!=word})
        words[word]={"definitions":defs,"synonyms":synonyms,"synsets":rows}
    return language,words

def normalize_conceptnet(path,root,folder):
    # Split the graph to disk by language before processing each language.
    # Bounded LRU handles ensure all encountered language codes can be indexed.
    spools=folder/"spools";spools.mkdir()
    handles=collections.OrderedDict()
    def emit(language,row):
        if language not in handles:
            if len(handles)>=24:handles.popitem(last=False)[1].close()
            handles[language]=(spools/(language+".jsonl")).open("a",encoding="utf8")
        handles.move_to_end(language)
        handles[language].write(json.dumps(row,ensure_ascii=False,separators=(",",":"))+"\n")
    try:
        with gzip.open(path,"rt",encoding="utf8") as f:
            for line in f:
                cols=line.rstrip("\n").split("\t")
                if len(cols)<5:continue
                relation=cols[1].split("/")[-1]
                if relation not in RELATIONS:continue
                a,b=uri_concept(cols[2]),uri_concept(cols[3])
                if not a or not b or a==b:continue
                try:meta=json.loads(cols[4])
                except ValueError:continue
                if not meta.get("license"):continue
                edge={"relation":relation,"license":meta["license"],"dataset":meta.get("dataset"),"uri":cols[0],"weight":float(meta.get("weight") or 1)}
                for left,right in [(a,b)]+([(b,a)] if relation in ("RelatedTo","Synonym","Antonym","SimilarTo") else []):
                    emit(lang(left[0]),[left[1],dict(edge,word=right[1],language=lang(right[0]))])
    finally:
        for f in handles.values():f.close()
    result=[]
    for file in sorted(spools.glob("*.jsonl")):
        words={}
        with file.open(encoding="utf8") as f:
            for line in f:
                word,edge=json.loads(line)
                if word not in words and len(words)>=100_000:continue
                items=words.setdefault(word,{"relations":[]})["relations"]
                key=(edge["relation"],edge["language"],edge["word"])
                if any((x["relation"],x["language"],x["word"])==key for x in items):continue
                if len(items)<12:items.append(edge)
                else:
                    low=min(range(len(items)),key=lambda i:items[i]["weight"])
                    if edge["weight"]>items[low]["weight"]:items[low]=edge
        row=shards(root,"conceptnet",file.stem,words)
        if row:result.append(row)
        file.unlink()
    return result

def normalize_kaikki(tag,assets,root,folder):
    report=raw_manifest(tag,assets,"kaikki",folder);result=[]
    for item in report["sources"]:
        edition=item["parts"][0]["asset"].split("--",1)[1].split(".part")[0]
        with tempfile.TemporaryDirectory(dir=folder) as tmp:
            p=raw_file(tag,assets,item,Path(tmp))
            by_lang=collections.defaultdict(dict);total=0
            with gzip.open(p,"rt",encoding="utf8") as f:
                for line in f:
                    try:e=json.loads(line)
                    except ValueError:continue
                    word=normalize(str(e.get("word","")));language=lang(e.get("lang_code","und"))
                    if not word or len(word)>100 or language=="und":continue
                    words=by_lang[language]
                    if word not in words and (len(words)>=10_000 or (total>=200_000 and words)):continue
                    defs=[g for s in e.get("senses",[]) for g in s.get("glosses",[]) if isinstance(g,str) and g][:8]
                    translations=[{"text":t["word"],"language":lang(t.get("code","und"))} for t in e.get("translations",[]) if isinstance(t.get("word"),str)][:20]
                    if not defs and not translations:continue
                    if word not in words:
                        words[word]={"definitions":[],"translations":[],"parts_of_speech":[],"source_url":"https://"+("simple" if edition=="simple" else edition)+".wiktionary.org/wiki/"+quote(str(e["word"]).replace(" ","_")),"license":"CC BY-SA 4.0; exceptions may apply"}
                        total+=1
                    row=words[word]
                    row["definitions"]=list(dict.fromkeys(row["definitions"]+defs))[:8]
                    for tr in translations:
                        if tr not in row["translations"] and len(row["translations"])<20:row["translations"].append(tr)
                    if e.get("pos") and e["pos"] not in row["parts_of_speech"]:row["parts_of_speech"].append(e["pos"])
            for language,words in sorted(by_lang.items()):
                row=shards(root,"kaikki",language,words,edition)
                if row:result.append(row)
    return result

def bz_lines(path):
    # Tatoeba .tar.bz2 exports may be either actual tar containers or TSV streams.
    with bz2.open(path,"rb") as raw:
        if raw.peek(512)[257:262]==b"ustar":
            with tarfile.open(fileobj=raw,mode="r|") as tar:
                for member in tar:
                    if member.isfile():
                        for line in tar.extractfile(member):yield line.decode("utf8","replace").rstrip("\r\n")
        else:
            for line in raw:yield line.decode("utf8","replace").rstrip("\r\n")

def normalize_tatoeba(tag,assets,root,folder):
    report=raw_manifest(tag,assets,"tatoeba",folder)
    detail=next(x for x in report["sources"] if "sentences_detailed" in x["original_url"])
    links=next(x for x in report["sources"] if x["original_url"].endswith("/links.tar.bz2"))
    sentences={};counts=collections.Counter()
    with tempfile.TemporaryDirectory(dir=folder) as tmp:
        p=raw_file(tag,assets,detail,Path(tmp))
        for line in bz_lines(p):
            cols=line.split("\t")
            if len(cols)<4 or not cols[0].isdigit():continue
            language=lang(cols[1]);text=cols[2]
            if language=="und" or not text or len(text)>300 or not cols[3] or counts[language]>=5000:continue
            sentences[int(cols[0])]={"text":text,"language":language,"author":cols[3],"translations":[],"source_url":"https://tatoeba.org/en/sentences/show/"+cols[0],"license":"CC BY 2.0 FR"}
            counts[language]+=1
    with tempfile.TemporaryDirectory(dir=folder) as tmp:
        p=raw_file(tag,assets,links,Path(tmp))
        for line in bz_lines(p):
            cols=line.split("\t")
            if len(cols)!=2 or not all(x.isdigit() for x in cols):continue
            a,b=map(int,cols)
            if a not in sentences or b not in sentences:continue
            left,right=sentences[a],sentences[b]
            if left["language"]!=right["language"] and len(left["translations"])<4 and not any(x["language"]==right["language"] for x in left["translations"]):
                left["translations"].append({k:right[k] for k in ("text","language","author","source_url","license")})
    by_lang=collections.defaultdict(dict)
    for sentence in sentences.values():
        words=by_lang[sentence["language"]]
        for word in sorted(set(re.findall(r"[^\W\d_]+(?:[-’'][^\W\d_]+)*",normalize(sentence["text"]),re.UNICODE))):
            if len(word)<2 or len(word)>70:continue
            rows=words.setdefault(word,{"examples":[]})["examples"]
            if len(rows)<3:rows.append(sentence)
    result=[]
    for language,words in sorted(by_lang.items()):
        row=shards(root,"tatoeba",language,words)
        if row:result.append(row)
    return result

def run(tag,group,work,previous=""):
    assets=inventory(tag);root=work/"normalized";folder=work/"inputs";folder.mkdir(parents=True,exist_ok=True)
    result=[]
    if previous:
        prior=inventory(previous)
        if "LEXICAL-INDEX.json" in prior:
            pull(tag,["REFRESH-REPORT.json"],folder,assets)
            report=json.loads((folder/"REFRESH-REPORT.json").read_text())
            relevant={"bilingual":("koreader","freedict","wikdict","kaikki","tatoeba"),"pages":("koreader","freedict","wikdict","kaikki","tatoeba"),"pages-lexical":("oewn","omw","conceptnet")}.get(group,(group,))
            unchanged=all(report["sources"][s]["status"] in ("unchanged","retained") for s in relevant)
            if unchanged and group not in ("bilingual","pages","pages-lexical"):
                index=f"normalized--{group}-index.json"
                if index in prior:
                    pull(previous,[index],folder,prior)
                    doc=json.loads((folder/index).read_text())
                    names=[item["name"] for item in doc["packages"]]
                    pull(previous,names,folder,prior)
                    upload(tag,[folder/index]+[folder/name for name in names])
                    print("Reused verified normalized "+group,flush=True)
                    return
    if group in ("bilingual","pages"):
        normalize_bilingual(tag,assets,root,folder,group=="pages")
    elif group=="oewn":
        name="lexicon--oewn-en.json.gz";pull(tag,[name],folder,assets)
        result=[shards(root,group,"en",wordnet_records(folder/name))]
    elif group=="omw":
        names=sorted(n for n in assets if re.fullmatch(r"omw--omw-[a-z0-9]+-[0-9.]+\.tar\.xz",n))
        if len(names)<20:raise ValueError("OMW individual packages missing")
        pull(tag,names+["omw--PER-PACKAGE-LICENSES.json"],folder,assets)
        licenses=json.loads((folder/"omw--PER-PACKAGE-LICENSES.json").read_text())
        for name in names:
            language,words=normalize_omw(folder/name)
            package=name.removeprefix("omw--").removesuffix(".tar.xz")
            row=shards(root,group,language,words,package)
            row["rights"]=licenses.get(name.removeprefix("omw--"),{})
            if not row["rights"].get("license"):raise ValueError("Missing component license "+name)
            result.append(row)
    elif group=="conceptnet":
        name="conceptnet--assertions-5.7.0.csv.gz";pull(tag,[name],folder,assets)
        result=normalize_conceptnet(folder/name,root,folder)
    elif group=="kaikki":result=normalize_kaikki(tag,assets,root,folder)
    elif group=="tatoeba":result=normalize_tatoeba(tag,assets,root,folder)
    elif group=="pages-lexical":
        names=["lexicon--oewn-en.json.gz","conceptnet--assertions-5.7.0.csv.gz"]
        omw=[n for n in assets if re.fullmatch(r"omw--omw-(en|es)-[0-9.]+\.tar\.xz",n)]
        if len(omw)!=2:raise ValueError("Missing Pages OMW packages")
        pull(tag,names+omw,folder,assets)
        cmd=["python","src/build_pages_lexical.py","--oewn",str(folder/names[0]),"--conceptnet",str(folder/names[1]),"--site-dir",str(root)]
        for n in omw:cmd+=["--omw",n.split("-")[3]+"="+str(folder/n)]
        subprocess.run(cmd,check=True)
    if group not in ("bilingual","pages","pages-lexical"):
        if not result or any(not row for row in result):raise ValueError("No normalized data for "+group)
        write_json(root/"data"/"lexical"/group/"catalog.json",{"schema":1,"source":group,"languages":result,"release":tag,"notice":"Compact lookup; original source archives and licenses remain authoritative."})
    out=work/"packs";pack(root,group,out)
    upload(tag,sorted(out.iterdir()))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--tag",required=True);p.add_argument("--group",required=True);p.add_argument("--work",default="normalization-work");p.add_argument("--previous",default="")
    a=p.parse_args();run(a.tag,a.group,Path(a.work),a.previous)
