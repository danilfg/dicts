/* Adapter from compact GitHub Pages shards to Translator's shared view model.
   Semantic resources are never used as direct translations. */
(() => {
 'use strict';
 const T=self.YWA_TRANSLATION,V=self.LWC_DICTIONARY_VIEW,F=self.DictsEntryFormat;
 const credit=(source,info={})=>({source,source_url:info.source_url||'',license:info.license||'',citation:info.citation||info.attribution||'',package:info.package||''});
 const list=value=>Array.isArray(value)?value:[];
 const clean=value=>F?.cleanCredit(value)||'';
 function adapt(pair,entry={},lexical=[],provenance={}){
   const [from,to]=pair.split('-');
   const data={pair,alternatives:[],meanings:[],examples:[],synonyms:[],relations:[],contextExpressions:[]};
   for(const [source,articles] of Object.entries(entry.translations||{})){
     const sourceCredit=credit(source,provenance[source]);
     for(const text of list(articles)){
       if(typeof text!=='string'||!text.trim())continue;
       const parsed=T.article(text,pair);
       for(const value of parsed.values)data.alternatives.push({...sourceCredit,text:value,parsedValue:true});
       for(const note of parsed.notes)data.meanings.push({...sourceCredit,text:note,kind:'explanation'});
       for(const line of F.parseEntry(T.decode(text),from,to)){
         if(line.kind==='phonetic')for(const variant of F.phoneticVariants(line.text))data.meanings.push({...sourceCredit,text:variant,kind:'explanation'});
       }
       // Preserve complex original articles, including uncertain fragments,
       // pronunciation, grammatical labels and punctuation, in a closed block.
       if(parsed.values.length!==1||parsed.notes.length||parsed.uncertain.length||V.keyOf(text)!==V.keyOf(parsed.values[0]))
         data.meanings.push({...sourceCredit,text,kind:'article',raw:true});
     }
   }
   for(const item of list(entry.meanings)){
     if(!item?.text)continue;
     const source=item.source||'kaikki';
     data.meanings.push({...credit(source,provenance[source]),...item,source});
   }
   for(const item of list(entry.examples)){
     if(!item?.text)continue;
     const source=item.source||'tatoeba';
     data.examples.push({...credit(source,provenance[source]),...item,source,author:clean(item.author),translation_author:clean(item.translation_author)});
   }
   for(const item of list(entry.contextExpressions))if(item?.text&&item.translation)data.contextExpressions.push(item);
   for(const item of list(entry.synonyms))if(item?.text)data.synonyms.push(item);
   for(const item of list(entry.relations))if(item?.text&&(!item.language||item.language===from||item.language===to))data.relations.push(item);
   for(const {source,entry:record,meta} of lexical){
     if(!record)continue;
     const c=credit(source,meta);
     if(source==='conceptnet'){
       for(const item of list(record))if(item?.word&&(!item.language||item.language===from||item.language===to))
         data.relations.push({...c,text:item.word,relation:item.relation,language:item.language||from});
     }else if(source==='oewn'||source==='omw'){
       for(const text of list(record.definitions))if(typeof text==='string'&&text.trim())data.meanings.push({...c,text});
       for(const text of list(record.synonyms))if(typeof text==='string'&&text.trim())data.synonyms.push({...c,text});
     }
   }
   return data;
 }
 function sourceCount(data){
   return new Set(Object.values(data).filter(Array.isArray).flat().map(x=>x.source).filter(Boolean)).size;
 }
 self.DictsResultModel={adapt,sourceCount};
})();
