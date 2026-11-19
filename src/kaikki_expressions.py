"""Source-backed optional Kaikki expression hints and morphological aliases.

Raw structured records, not inferred translations. Same-language only.
"""
from collections import defaultdict
from urllib.parse import quote
from build_pages import normalize
from expressions import keys_for,MAX_EXPRESSION_LENGTH,MAX_PER_KEY

MAX_LOOKUP_KEYS=20_000
MAX_FORMS=32

def kind_for(entry):
    tags={str(t).lower() for s in entry.get("senses",[]) for t in s.get("tags",[])}
    pos=str(entry.get("pos","")).lower()
    if "idiomatic" in tags or pos=="idiom":return "idiom"
    if "phrasal-verb" in tags or pos in ("phrasal-verb","phrasal verb"):return "phrasal_verb"
    return "expression"

def collect(index,forms,entry,language,edition):
    word=normalize(str(entry.get("word","")))
    if not word or len(word)>MAX_EXPRESSION_LENGTH:return
    url="https://"+edition+".wiktionary.org/wiki/"+quote(str(entry["word"]).replace(" ","_"))
    origin={"source":"kaikki","source_url":url,"license":"CC BY-SA 4.0; exceptions may apply"}
    def add(expression,kind,keys,lookup):
        expression=normalize(expression)
        if len(expression)>MAX_EXPRESSION_LENGTH or not keys_for(expression,language):return
        row={"text":expression,"expression":expression,"kind":kind,"lookup":lookup,**origin}
        for key in keys:
            if len(index)>=MAX_LOOKUP_KEYS and key not in index:continue
            items=index.setdefault(key,[])
            if len(items)<MAX_PER_KEY and not any(x["expression"]==expression and x["kind"]==kind for x in items):
                items.append(row)
    if keys_for(word,language):add(word,kind_for(entry),keys_for(word,language),word)
    for item in entry.get("derived",[]) or []:
        term=item.get("word") if isinstance(item,dict) else None
        if not isinstance(term,str):continue
        # The explicit derived link is not a verified translation or POS.
        add(term,"expression",list(dict.fromkeys([word]+keys_for(term,language))),normalize(term))
    for sense in entry.get("senses",[]) or []:
        for item in sense.get("form_of",[]) or []:
            lemma=item.get("word") if isinstance(item,dict) else None
            if not isinstance(lemma,str) or not lemma.strip() or len(lemma)>MAX_EXPRESSION_LENGTH:continue
            if len(forms)>=MAX_LOOKUP_KEYS and word not in forms:continue
            values=forms.setdefault(word,[])
            row={"lemma":normalize(lemma),**origin}
            if len(values)<MAX_FORMS and row not in values:values.append(row)

def merge(words,index,forms):
    for key,items in index.items():
        if items:words.setdefault(key,{"definitions":[],"translations":[],"parts_of_speech":[]})["expression_refs"]=items
    for key,items in forms.items():
        if items:words.setdefault(key,{"definitions":[],"translations":[],"parts_of_speech":[]})["lemma_refs"]=items
