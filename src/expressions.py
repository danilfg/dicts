"""A bounded reverse index of actual multiword dictionary headwords.

A hit is an expression, not a fabricated grammatical pattern. Only authored
or explicitly marked entries have a more specific kind. Dictionary articles
are kept as source articles, never misrepresented as clean translations.
"""
import collections
import gzip
import json
import re
from pathlib import Path

from build_pages import normalize,bucket,write_gzip
from normalized_pack import write_json

TOKENS=re.compile(r"[^\W\d_]+(?:[’'][^\W\d_]+)*",re.UNICODE)
EN_STOP=set("a an the to of in on at by for from with and or but as is are am be been being was were it its i me my you your he his she her we our they their them this that these those not no so do does did".split())
EN_IRREGULAR={"took":"take","taken":"take","made":"make","broke":"break","broken":"break","knew":"know","known":"know","went":"go","gone":"go","ran":"run","done":"do"}
MAX_PER_KEY=32
MAX_EXPRESSION_LENGTH=100
MAX_WORDS=8
BUCKETS=128
SOURCE_PRIORITY={"dicts-curated":0,"koreader":1,"freedict":2,"wikdict":3,"kaikki":4}
SEED=Path(__file__).resolve().parents[1]/"configs/expressions-en-ru.json"

def keys_for(expression,language):
    tokens=TOKENS.findall(normalize(expression).replace("’","'"))
    if not 2<=len(tokens)<=MAX_WORDS:return []
    result=[]
    for token in tokens:
        if len(token)<2 or (language=="en" and token in EN_STOP):continue
        result.append(token)
        if language=="en":
            if token in EN_IRREGULAR:result.append(EN_IRREGULAR[token])
            # Conservative aliases for transparent inflections. The extension
            # can also query its own lemma variants; aliases never create words.
            if token.endswith("ied") and len(token)>4:result.append(token[:-3]+"y")
            elif token.endswith("ed") and len(token)>4:
                result.extend((token[:-2],token[:-1]))
            elif token.endswith("ing") and len(token)>5:
                result.extend((token[:-3],token[:-3]+"e"))
            if token.endswith("s") and len(token)>3:result.append(token[:-1])
    return list(dict.fromkeys(result))

def rank(row):
    return (0 if row["kind"]!="expression" else 1,
            0 if row.get("translation") else 1,
            min((SOURCE_PRIORITY.get(s,9) for s in row.get("sources",[])),default=9),
            len(row["expression"]),row["text"],row.get("translation",""))

def add(index,key,row):
    items=index[key]
    identity=(row["text"],row["kind"],row.get("translation",""))
    if identity in items:
        return
    if len(items)>=MAX_PER_KEY:
        worst=max(items,key=lambda x:rank(items[x]))
        if rank(row)>=rank(items[worst]):return
        del items[worst]
    items[identity]=row

def dictionary_rows(expression,entry,provenance):
    """Keep references to original articles; exact phrase lookup can resolve
    the full text in the existing bilingual unit without copying raw articles."""
    articles=[]
    for source,values in sorted(entry.get("translations",{}).items()):
        if not any(isinstance(v,str) and v.strip() for v in values):continue
        info=provenance.get(source,{})
        articles.append({"source":source,**{k:info[k] for k in ("source_url","license","attribution") if info.get(k)}})
    # Kaikki compact enrichment contains actual expression definitions;
    # definitions are not target-language translations.
    for m in entry.get("meanings",[]):
        if m.get("source")=="kaikki" and m.get("text"):
            item={"source":"kaikki","definition":m["text"]}
            item.update({k:m[k] for k in ("source_url","license") if m.get(k)})
            if item not in articles:articles.append(item)
    if not articles:return None
    return {"text":expression,"expression":expression,"kind":"expression",
            "sources":sorted({a["source"] for a in articles}),"articles":articles}

def index_pair(root,descriptor,provenance,out):
    pair=descriptor["pair"];language=descriptor["from"]
    index=collections.defaultdict(dict)
    for path in sorted((root/"data"/pair).glob("*.json.gz")):
        with gzip.open(path,"rt",encoding="utf8") as stream:doc=json.load(stream)
        for expression,entry in doc["words"].items():
            if len(expression)>MAX_EXPRESSION_LENGTH or " " not in expression:continue
            keys=keys_for(expression,language)
            if not keys:continue
            row=dictionary_rows(expression,entry,provenance)
            if not row:continue
            for key in keys:add(index,key,row)
    if pair=="en-ru":
        for seed in json.loads(SEED.read_text(encoding="utf8"))["entries"]:
            row={k:v for k,v in seed.items() if k!="keys"}
            row["sources"]=[row["source"]]
            for key in set(seed["keys"]+keys_for(seed["expression"],language)):
                add(index,normalize(key),row)
    if not index:return None
    groups=[{} for _ in range(BUCKETS)]
    for key,items in index.items():
        rows=sorted(items.values(),key=rank)
        # Existing OCI kind=links envelope; existing clients ignore the
        # novel expressions field while still validating and installing it.
        groups[bucket(key,BUCKETS)][key]=[{"package":None,"record":{"expressions":rows}}]
    path="data/links/expressions/"+pair
    for i,words in enumerate(groups):
        if words:write_gzip(out/path/f"{i:02x}.json.gz",{"schema":1,"source":"expressions","pair":pair,"words":words})
    return {"pair":pair,"path":path,"buckets":BUCKETS,"entries":len(index)}

def build(root,out):
    catalog=json.loads((root/"data/catalog.json").read_text(encoding="utf8"))
    pairs=[]
    for desc in catalog["pairs"]:
        if not re.fullmatch(r"[a-z0-9]{2,20}-[a-z0-9]{2,20}",desc["pair"]):continue
        result=index_pair(root,desc,catalog.get("provenance",{}).get(desc["pair"],{}),out)
        if result:pairs.append(result)
    if not pairs:raise ValueError("No expression lookup units generated")
    write_json(out/"data/expressions/catalog.json",{"schema":1,"pairs":pairs,"notice":"Bounded reverse index of dictionary headwords and original curated examples. Unknown categories remain expression."})
    print("EXPRESSIONS READY",len(pairs),"pairs",sum(p["entries"] for p in pairs),"lookup keys",flush=True)
    return pairs
