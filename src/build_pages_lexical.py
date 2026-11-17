#!/usr/bin/env python3
"""Compile real, attributed Open English WordNet, OMW and ConceptNet into
small, directly fetchable GitHub Pages lookup shards.

Only the *lookup index* is curated/size-bounded; complete original source
archives remain in the lexical GitHub Releases.
"""
from __future__ import annotations
import argparse
import collections
import gzip
import json
import hashlib
import io
import os
import pathlib
import tarfile
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Iterator

from build_pages import normalize, bucket, write_gzip

RELATIONS = {"RelatedTo","Synonym","Antonym","IsA","HasA","PartOf","UsedFor",
             "HasProperty","CapableOf","AtLocation","DerivedFrom","SimilarTo",
             "FormOf","DefinedAs","MannerOf","HasSubevent"}
SOURCE_RELEASES = {
 "oewn": "lex-oewn-2025-edition-v1",
 "omw": "lex-omw-v2.0-v1",
 "conceptnet": "lex-conceptnet-5.7.0-v1",
}
# Only project-owned, public release files are downloaded by GitHub Actions.
def asset_url(source,filename):
    return f"https://github.com/danilfg/dicts/releases/latest/download/{filename}" if os.getenv("DICT_UNIFIED_RELEASE") else f"https://github.com/danilfg/dicts/releases/download/{SOURCE_RELEASES[source]}/{filename}"

def local(tag):return tag.rsplit("}",1)[-1]
def wordnet_records(path:pathlib.Path):
    with gzip.open(path,"rt",encoding="utf8") as file:source=json.load(file)
    if source.get("source")!="oewn" or source.get("language")!="en":
        raise ValueError("Expected genuine English WordNet release index")
    records={}
    for word,record in source["words"].items():
        label=normalize(word)
        if not label:continue
        defs=list(dict.fromkeys(x.strip() for x in record.get("definitions",[]) if isinstance(x,str) and x.strip()))[:8]
        synonyms=list(dict.fromkeys(x.strip() for x in record.get("synonyms",[]) if isinstance(x,str) and x.strip()))[:25]
        if defs or synonyms:records[label]={"definitions":defs,"synonyms":synonyms}
    if len(records)<10_000:raise ValueError("Unexpectedly small OEWN source: "+str(len(records)))
    return records

def omw_records(path:pathlib.Path,language:str):
    """Read WN-LMF synsets and senses, not guessed bilingual correspondences."""
    definitions:dict[str,list[str]]={}
    senses:dict[str,set[str]]=collections.defaultdict(set)
    synonyms:dict[str,set[str]]=collections.defaultdict(set)
    xml_count=0
    with tarfile.open(path,"r:xz") as package:
        for item in package:
            if not item.isfile() or not item.name.lower().endswith(".xml"):continue
            xml_count+=1
            file=package.extractfile(item)
            if file is None:continue
            for _event,e in ET.iterparse(file,events=("end",)):
                name=local(e.tag)
                if name=="Synset":
                    sid=e.get("id","")
                    defs=[" ".join("".join(v.itertext()).split()) for v in e
                          if local(v.tag)=="Definition"]
                    if sid:definitions[sid]=[v for v in defs if v][:4]
                    e.clear()
                elif name=="LexicalEntry":
                    lemma=next((v.get("writtenForm","") for v in e if local(v.tag)=="Lemma"),"")
                    label=normalize(lemma)
                    if label:
                        for sense in e.iter():
                            if local(sense.tag)=="Sense":
                                syn=sense.get("synset","")
                                if syn:
                                    senses[label].add(syn)
                                    synonyms[syn].add(lemma)
                    e.clear()
    if xml_count==0:raise ValueError("OMW archive contains no WN-LMF XML: "+str(path))
    result={}
    for word,ids in senses.items():
        defs=list(dict.fromkeys(d for sid in ids for d in definitions.get(sid,[]) if d))[:6]
        syn=sorted(set(w for sid in ids for w in synonyms.get(sid,set()) if normalize(w)!=word))[:20]
        if defs or syn:result[word]={"definitions":defs,"synonyms":syn}
    return result

def uri_concept(text):
    parts=str(text).split("/")
    if len(parts)<4 or parts[1]!="c" or not parts[2]:return None
    language=parts[2].lower()
    word=normalize(urllib.parse.unquote(parts[3]).replace("_"," "))
    if not word or len(word)>90:return None
    return language,word

def conceptnet_records(path,eligible:dict[str,set[str]]):
    """Stream original 5.7 assertions; keep up to 12 source-linked relations
    per indexed word. Do not represent this selective lookup as all assertions.
    """
    records:dict[str,dict[str,list]]=collections.defaultdict(dict)
    counted=0
    with gzip.open(path,"rt",encoding="utf8",errors="replace") as f:
        for line in f:
            cols=line.rstrip("\n").split("\t")
            if len(cols)<5:continue
            relation=cols[1].split("/")[-1]
            if relation not in RELATIONS:continue
            first=uri_concept(cols[2]);second=uri_concept(cols[3])
            if not first or not second or first==second:continue
            candidates=[(first,second)]
            if relation in ("RelatedTo","Synonym","Antonym","SimilarTo"):
                candidates.append((second,first))
            for (lang,word),(target_lang,target_word) in candidates:
                if lang not in eligible or word not in eligible[lang]:continue
                if len(word)>70 or len(target_word)>90:continue
                by_word=records[lang]
                options=by_word.setdefault(word,[])
                if len(options)>=12:continue
                row={"relation":relation,"word":target_word,"language":target_lang}
                if row not in options:
                    options.append(row);counted+=1
    if counted<2000:raise ValueError("ConceptNet extraction unexpectedly tiny: "+str(counted))
    return records

def publish_index(target:pathlib.Path,source:str,lang:str,words:dict,buckets:int=32):
    if not words:return None
    directory=target/"data"/"lexical"/source/lang
    grouped=[{} for _ in range(buckets)]
    for word,record in words.items():
        if not word or not record:continue
        grouped[bucket(word,buckets)][word]=record
    size=0
    for i,group in enumerate(grouped):
        dest=directory/f"{i:02x}.json.gz"
        write_gzip(dest,{"schema":1,"source":source,"language":lang,"words":group})
        size+=dest.stat().st_size
    print(f"LEXICAL {source}/{lang}: {len(words)} terms / {size} bytes",flush=True)
    return {"language":lang,"entries":len(words),"buckets":buckets,"compressed_bytes":size}

def build(oewn:pathlib.Path,conceptnet:pathlib.Path,omw:list[tuple[str,pathlib.Path]],site:pathlib.Path):
    oewn_data=wordnet_records(oewn)
    omw_data={}
    for lang,path in omw:
        result=omw_records(path,lang)
        if result:omw_data[lang]=result
    allowed={"en":set(oewn_data)}
    for lang,data in omw_data.items():allowed.setdefault(lang,set()).update(data)
    graph=conceptnet_records(conceptnet,allowed)
    sources={
       "oewn":{"title":"Open English WordNet","license":"CC BY 4.0; Princeton WordNet attribution",
          "source_url":"https://en-word.net/downloads",
          "release_url":"https://github.com/danilfg/dicts/releases/tag/"+SOURCE_RELEASES["oewn"],
          "languages":[]},
       "omw":{"title":"Open Multilingual Wordnet","license":"Per-lexicon; see original rights and citations",
          "source_url":"https://omwn.org/",
          "release_url":"https://github.com/danilfg/dicts/releases/tag/"+SOURCE_RELEASES["omw"],
          "languages":[]},
       "conceptnet":{"title":"ConceptNet","license":"CC BY-SA 4.0, with data-source attribution",
          "source_url":"https://github.com/commonsense/conceptnet5/blob/master/DATA-CREDITS.md",
          "release_url":"https://github.com/danilfg/dicts/releases/tag/"+SOURCE_RELEASES["conceptnet"],
          "languages":[]}
    }
    for src,records in [("oewn",{"en":oewn_data}),("omw",omw_data),("conceptnet",graph)]:
        for lang,items in records.items():
            result=publish_index(site,src,lang,items)
            if result:sources[src]["languages"].append(result)
    catalog={"schema":1,"sources":sources,
             "notice":"Derived lookup subsets, NOT full raw corpora. Definitions and graph edges are not translations. See source attribution and individual licenses."}
    dest=site/"data"/"lexical"/"catalog.json"
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(catalog,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf8")
    return catalog

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--oewn",type=pathlib.Path,required=True)
    p.add_argument("--conceptnet",type=pathlib.Path,required=True)
    p.add_argument("--omw",action="append",default=[],help="LANG=path/to/archive.tar.xz")
    p.add_argument("--site-dir",type=pathlib.Path,default=pathlib.Path("site"))
    args=p.parse_args()
    langs=[]
    for item in args.omw:
        lang,name=item.split("=",1)
        langs.append((lang,pathlib.Path(name)))
    build(args.oewn,args.conceptnet,langs,args.site_dir)

if __name__=="__main__":main()
