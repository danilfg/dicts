"use strict";
(function(){
const $=id=>document.getElementById(id);
const SOURCE_NAMES={koreader:"KOReader",freedict:"FreeDict",wikdict:"WikDict",kaikki:"Kaikki / Wiktionary",tatoeba:"Tatoeba"};
const TRANSLATIONS={
 en:{eyebrow:"OPEN, SOURCE-ATTRIBUTED WORD DATA",title1:"Every word has",title2:"more than one meaning.",description:"Compare translations across independent dictionaries. Explore examples, definitions and the people behind the data — all in one place.",from:"FROM",to:"TO",search:"Search",placeholder:"Type a word or phrase...",try:"Try:",loading:"Loading language pairs…",coverage:"language pairs available",results:"DICTIONARY RESULTS",meanings:"meanings",entries:"entries",sourceCount:"sources",pronounce:"Pronounce word",copy:"Copy search link",notFound:"No exact match in this dictionary pair",notFoundDetail:"Try a different form of the word, or switch the language direction.",source:"Original source",license:"License",download:"Download dictionary",credit:"Attribution",definitions:"Definitions & expressions",examples:"Examples in context",noSource:"No lexical data for this word",error:"Couldn't load this dictionary index. Please try again or check the Pages build.",building:"This dictionary's searchable index is not available yet. Check GitHub Actions.",offline:"The searchable index is unavailable. Check your internet connection.",emptyTitle:"Discover a word from different perspectives.",emptyDescription:"Choose two languages, then search for a word or an expression.",directoryEyebrow:"THE DATA BEHIND THE WORDS",directoryTitle:"Independent sources, one search.",browse:"Explore all datasets ↗",tile1:"Bilingual dictionaries with original source notices.",tile2:"Open bilingual dictionaries and language pairs.",tile3:"More translations from Wiktionary-derived data.",tile4:"More data",tile5:"Wiktionary examples, Tatoeba, WordNet and ConceptNet resources.",footer:"Translations are supplied by third parties as is. See original licenses and authorship.",attributions:"Licenses & attribution ↗",about:"About",sources:"Data sources",swapUnavailable:"No dictionary is published for the opposite direction.",noPairs:"No language pairs are available for this source language.",sourceType:"Source dictionary",total:"Full entry",sentences:"Example sentences",word:"Word",parts:"Independent dictionaries"},
 ru:{eyebrow:"ОТКРЫТЫЕ СЛОВАРИ С УКАЗАНИЕМ ИСТОЧНИКОВ",title1:"У каждого слова",title2:"больше одного значения.",description:"Сравнивайте переводы из независимых словарей, изучайте определения, примеры употребления и первоисточники — в одном месте.",from:"С ЯЗЫКА",to:"НА ЯЗЫК",search:"Перевести",placeholder:"Введите слово или выражение…",try:"Попробуйте:",loading:"Загружаем языковые пары…",coverage:"языковых пар для поиска",results:"РЕЗУЛЬТАТЫ ПО СЛОВАРЯМ",meanings:"значений",entries:"записей",sourceCount:"источников",pronounce:"Озвучить слово",copy:"Скопировать ссылку",notFound:"Точное совпадение не найдено",notFoundDetail:"Попробуйте другую форму слова или измените направление перевода.",source:"Первоисточник",license:"Лицензия",download:"Скачать словарь",credit:"Атрибуция",definitions:"Определения и выражения",examples:"Примеры употребления",noSource:"Для этого слова пока нет данных",error:"Не удалось загрузить словарный индекс. Проверьте работу Pages или повторите запрос.",building:"Индекс этой пары ещё не опубликован. Проверьте GitHub Actions.",offline:"Словарный индекс недоступен. Проверьте соединение с интернетом.",emptyTitle:"Узнавайте слово с разных сторон.",emptyDescription:"Выберите языки и найдите слово или выражение.",directoryEyebrow:"ОТКУДА ПОЛУЧЕНЫ ДАННЫЕ",directoryTitle:"Независимые словари, единый поиск.",browse:"Все источники ↗",tile1:"Двуязычные словари с оригинальными лицензиями.",tile2:"Открытые словари для множества языковых пар.",tile3:"Дополнительные переводы на основе Wiktionary.",tile4:"Другие данные",tile5:"Выражения Kaikki, примеры Tatoeba, WordNet и ConceptNet.",footer:"Переводы получены от сторонних авторов и предоставлены как есть. Соблюдайте лицензии.",attributions:"Лицензии и авторство ↗",about:"О проекте",sources:"Источники",swapUnavailable:"Для обратного направления словарь пока не опубликован.",noPairs:"Для выбранного языка пока нет других направлений.",sourceType:"Исходный словарь",total:"Полная статья",sentences:"Примеры употребления",word:"Слово",parts:"Независимые словари"}
};
const params=new URLSearchParams(location.search);
const state={locale:params.get("ui")==="ru"?"ru":params.get("ui")==="en"?"en":(navigator.language||"en").toLowerCase().startsWith("ru")?"ru":"en",
 catalog:null,byPair:new Map(),cache:new Map(),current:null,searchNumber:0};
const el=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e};
const t=k=>TRANSLATIONS[state.locale][k]||k;
function urlSafe(value){try{const u=new URL(value);return u.protocol==="https:"||u.protocol==="http:"?u.href:null}catch{return null}}
function anchor(label,url){const a=el("a","",label);const safe=urlSafe(url);if(safe){a.href=safe;a.target="_blank";a.rel="noopener noreferrer"}return a}
function setStatus(message,type){const e=$("status");e.textContent=message||"";e.className="status"+(type?" "+type:"")}
function normalize(s){return String(s||"").trim().toLocaleLowerCase().replace(/ß/g,"ss").replace(/ς/g,"σ").replace(/\s+/g," ")}
function languageName(code){try{const codeFixed=code==="iw"?"he":code;const d=new Intl.DisplayNames([state.locale],{type:"language"});return d.of(codeFixed)||code.toUpperCase()}catch{return code.toUpperCase()}}
function languageLabel(code){return languageName(code)+" ("+code.toUpperCase()+")"}
function pairValue(){return $("from").value+"-"+$("to").value}
function loadLocale(){
 document.documentElement.lang=state.locale;
 $("locale-btn").textContent=state.locale==="ru"?"EN":"RU";
 $("eyebrow").textContent=t("eyebrow");
 $("hero-title").textContent=state.locale==="ru"?"Переводчик":"Translator";
 $("hero-description").textContent=state.locale==="ru"?"Переводы, определения и примеры из открытых словарей.":"Translations, definitions and examples from open dictionaries.";
 $("from-label").textContent=t("from");$("to-label").textContent=t("to");
 $("search-label").textContent=t("search");$("term").placeholder=t("placeholder");
 $("try-label").textContent=t("try");
 $("empty-title")?.replaceChildren(document.createTextNode(t("emptyTitle")));
 $("empty-description")?.replaceChildren(document.createTextNode(t("emptyDescription")));
 $("directory-eyebrow").textContent=state.locale==="ru"?"Источники, версии и лицензии":"Sources, versions and licenses";
 $("directory-title").textContent=state.locale==="ru"?"Список словарей":"Dictionaries";
 $("browse-data").textContent=state.locale==="ru"?"Релиз ↗":"Release ↗";
 $("footer-disclaimer").textContent=t("footer");
 $("footer-licenses").textContent=t("attributions");
 $("about-link").textContent=state.locale==="ru"?"Переводчик":"Translator";
 $("sources-link").textContent=state.locale==="ru"?"Список словарей":"Dictionaries";
 $("directory-filter-label").textContent=state.locale==="ru"?"Найти словарь":"Find a dictionary";
 $("directory-filter").placeholder=state.locale==="ru"?"Название или языковая пара":"Name or language pair";
 $("directory-note").textContent=state.locale==="ru"?"Версии берутся из опубликованного релиза; дата снимка не является версией исходного проекта. Сайт использует компактные индексы, полные исходные данные доступны в релизе.":"Versions come from the published release; a snapshot date is not an upstream version. The website uses compact indexes; full source data are available in the release.";
 if(directoryData)renderDirectory();
 $("swap").setAttribute("aria-label",state.locale==="ru"?"Поменять языки местами":"Swap languages");
 $("term").setAttribute("aria-label",state.locale==="ru"?"Слово для поиска":"Word or phrase to translate");
 if(state.catalog)$("coverage-text").textContent=state.catalog.pairs.length+" "+t("coverage");
}
function fillLanguages(from,to){
 if(!state.catalog)return;
 const froms=[...new Set(state.catalog.pairs.map(p=>p.from))].sort((a,b)=>languageName(a).localeCompare(languageName(b),state.locale));
 $("from").replaceChildren();
 for(const lang of froms){const option=el("option","",languageLabel(lang));option.value=lang;$("from").append(option)}
 const actualFrom=froms.includes(from)?from:froms.includes("en")?"en":froms[0];
 $("from").value=actualFrom;
 fillTargets(actualFrom,to);
}
function fillTargets(from,to){
 const targets=[...new Set(state.catalog.pairs.filter(p=>p.from===from).map(p=>p.to))].sort((a,b)=>languageName(a).localeCompare(languageName(b),state.locale));
 $("to").replaceChildren();
 for(const lang of targets){const option=el("option","",languageLabel(lang));option.value=lang;$("to").append(option)}
 $("to").value=targets.includes(to)?to:targets.includes("ru")?"ru":targets[0]||"";
 if(!targets.length)setStatus(t("noPairs"),"error")
}
function emptyResult(title,detail){
 const section=$("results");section.replaceChildren();
 const card=el("div","no-results");
 card.append(el("h2","",title),el("p","",detail));section.append(card);
}
function updateAddress(query){
 const u=new URL(location.href);
 if(query)u.searchParams.set("q",query);else u.searchParams.delete("q");
 u.searchParams.set("from",$("from").value);
 u.searchParams.set("to",$("to").value);
 u.searchParams.set("ui",state.locale);
 history.replaceState(null,"",u.pathname+u.search+u.hash)
}
async function shaBucket(word,count){
 const digest=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(word));
 return new Uint8Array(digest)[0]%count;
}
async function getShard(pair,bucketNum){
 const key=pair+"--"+bucketNum;
 if(state.cache.has(key))return state.cache.get(key);
 const url="./data/"+encodeURIComponent(pair)+"/"+bucketNum.toString(16).padStart(2,"0")+".json.gz";
 const response=await fetch(url,{cache:"force-cache"});
 if(!response.ok)throw new Error("HTTP "+response.status+": "+url);
 if(!("DecompressionStream" in window))throw new Error("This browser does not support gzip decompression");
 const stream=response.body.pipeThrough(new DecompressionStream("gzip"));
 const decoded=await new Response(stream).json();
 if(decoded.pair!==pair||!decoded.words)throw new Error("Invalid dictionary shard");
 if(state.cache.size>=7)state.cache.delete(state.cache.keys().next().value);
 state.cache.set(key,decoded);
 return decoded;
}
function sourceInfo(pair,id){return (state.catalog.provenance[pair]||{})[id]||{}}
function countLabel(count,type){
 return window.DictsEntryFormat
   ?window.DictsEntryFormat.formatCount(count,type,state.locale)
   :count+" "+t(type);
}
function summaryCard(title,count,id){
 const card=el("details","dictionary-card");card.open=false;
 const summary=el("summary");
 const icon=el("span","source-avatar",id==="koreader"?"K":id==="freedict"?"F":id==="wikdict"?"W":id==="kaikki"?"K":id==="oewn"?"O":id==="omw"?"M":id==="conceptnet"?"C":"T");icon.dataset.source=id;
 const heading=el("span","source-title");heading.append(el("b","",title),el("small","",countLabel(count,"entries")));
 summary.append(icon,heading,el("span","chevron","⌄"));card.append(summary);
 const body=el("div","source-body");card.append(body);
 return {card,body};
}
function sourceFooter(body,info){
 const foot=el("div","source-footer");
 if(info.license)foot.append(el("span","",t("license")+": "+info.license));
 if(info.source_url)foot.append(anchor(t("source")+" ↗",info.source_url));
 if(info.download_url)foot.append(anchor(t("download")+" ↗",info.download_url));
 body.append(foot);
 if(info.attribution){
   const details=el("details","entry-credit");const sum=el("summary","",t("credit"));details.append(sum,el("p","",info.attribution));body.append(details)
 }
}
function addFormattedArticle(container,original,from,to){
 const format=window.DictsEntryFormat;
 if(!format){container.append(el("div","article-raw",String(original||"")));return}
 const lines=format.parseEntry(original,from,to);
 const article=el("div","dictionary-article");
 const more=el("details","article-more");
 const rest=el("div","article-rest");
 more.append(el("summary","",state.locale==="ru"?"Показать всю статью":"Show full article"),rest);
 for(const [index,line] of lines.entries()){
    const destination=index<5?article:rest;
    if(line.kind==="phonetic"){
      const p=el("div","article-phonetic");
      p.append(el("span","ipa-label",state.locale==="ru"?"Транскрипция":"Pronunciation"));
      const chips=el("div","ipa-variants");
      const variants=format.phoneticVariants(line.text);
      for(const variant of variants)chips.append(el("span","ipa-variant",variant));
      p.append(chips);destination.append(p);continue
    }
    if(line.kind==="part"){
      destination.append(el("div","article-part",line.text));continue
    }
    const row=el("div","article-line");
    if(line.number)row.append(el("span","article-number",line.number));
    if(line.part)row.append(el("span","article-part",line.part));
    const detail=el("div","article-detail");
    if(line.kind==="sense"){
      detail.append(el("div","article-translation",line.translation));
      detail.append(el("div","article-explanation",line.explanation));
    }else{
      detail.append(el("div",line.kind==="translation"?"article-translation":line.kind==="explanation"?"article-explanation":"article-raw",line.text))
    }
    row.append(detail);destination.append(row);
 }
 if(rest.childNodes.length)article.append(more);
 container.append(article);
}
function renderTranslations(word,pair,entry){
 let firstTranslationCard=true;
 const fragment=document.createDocumentFragment();
 let sourceCount=0,total=0;
 for(const id of Object.keys(entry.translations||{})){
   const entries=(entry.translations||{})[id]||[];
   if(!entries.length)continue;
   sourceCount++;
   const {card,body}=summaryCard(SOURCE_NAMES[id]||id,entries.length,id);
   if(firstTranslationCard){card.open=true;firstTranslationCard=false;}
   const extra=el("details","article-more");const extraBody=el("div","article-rest");extra.append(el("summary","",state.locale==="ru"?"Другие статьи":"More articles"),extraBody);
   for(const [index,meaning] of entries.entries()){
      if(typeof meaning!=="string"||!meaning.trim())continue;
      const div=el("div","definition");
      addFormattedArticle(div,meaning,pair.split("-")[0],pair.split("-")[1]);
      (index<2?body:extraBody).append(div);total++;
   }
   if(extraBody.childNodes.length)body.append(extra);
   sourceFooter(body,sourceInfo(pair,id));fragment.append(card)
 }
 const meanings=(entry.meanings||[]).filter(x=>x&&x.text);
 if(meanings.length){
   const types=new Map();
   for(const m of meanings){const source=m.source||"kaikki";if(!types.has(source))types.set(source,[]);types.get(source).push(m)}
   for(const [source,items] of types){
     const {card,body}=summaryCard(source==="kaikki"?"Kaikki / Wiktionary":source,items.length,source);
     for(const m of items){
        const div=el("div","definition");addFormattedArticle(div,m.text,pair.split("-")[0],pair.split("-")[1]);
        if(m.source_url){div.append(el("div","entry-credit")).append(anchor(t("source")+" ↗",m.source_url))}
        body.append(div);
     }
     fragment.append(card);sourceCount++;
   }
 }
 const examples=(entry.examples||[]).filter(x=>x&&x.text);
 if(examples.length){
    const {card,body}=summaryCard("Tatoeba · "+t("sentences"),examples.length,"tatoeba");
    for(const example of examples){
      const d=el("div","definition");d.append(el("div","example-text",example.text));
      if(example.translation)d.append(el("div","example-translation",example.translation));
      const credit=el("div","example-author");
      const parts=[];
      const author=window.DictsEntryFormat?.cleanCredit(example.author)||"";
      if(author)parts.push(document.createTextNode(author));
      if(example.source_url)parts.push(anchor(t("source")+" ↗",example.source_url));
      if(example.license)parts.push(document.createTextNode(example.license));
      for(const [index,item] of parts.entries()){
        if(index>0)credit.append(document.createTextNode(" · "));
        credit.append(item);
      }
      if(parts.length)d.append(credit);
      body.append(d);
    }
    fragment.append(card);sourceCount++;
 }
 return {fragment,sourceCount,total:total+meanings.length,examples:examples.length}
}
/* Optional semantic sources: independent of bilingual translations and safely
   rendered only after matching published, source-labelled lookup data. */
const LEXICAL_NAMES={oewn:"Open English WordNet",omw:"Open Multilingual Wordnet",conceptnet:"ConceptNet"};
let lexicalCatalogPromise=null;
async function getLexicalCatalog(){
 if(!lexicalCatalogPromise){
   lexicalCatalogPromise=fetch("./data/lexical/catalog.json",{cache:"no-cache"})
     .then(r=>r.ok?r.json():null)
     .catch(()=>null);
 }
 return lexicalCatalogPromise;
}
async function lookupLexical(source,language,word){
 const catalog=await getLexicalCatalog();
 const metadata=catalog?.sources?.[source];
 const resource=metadata?.languages?.find(x=>x.language===language);
 if(!resource)return null;
 const number=await shaBucket(word,resource.buckets);
 const name=number.toString(16).padStart(2,"0");
 const response=await fetch("./data/lexical/"+source+"/"+encodeURIComponent(language)+"/"+name+".json.gz");
 if(!response.ok)return null;
 if(!("DecompressionStream" in window))return null;
 const content=await new Response(response.body.pipeThrough(new DecompressionStream("gzip"))).json();
 if(content.source!==source||content.language!==language||!content.words)return null;
 return {entry:content.words[word],meta:metadata};
}
function addLexicalRecords(container,source,result,from,to){
 const data=source==="conceptnet"&&Array.isArray(result.entry)?result.entry.filter(x=>!x.language||x.language===from||x.language===to):result.entry;
 const fragment=document.createDocumentFragment();
 const addSubtitle=(label)=>{
   const labelElement=el("div","lexical-subtitle",label);fragment.append(labelElement);
 };
 if(source==="conceptnet"){
   if(!Array.isArray(data)||!data.length)return false;
   for(const [relation,relations] of Object.entries(Object.groupBy?Object.groupBy(data,x=>x.relation):
     data.reduce((obj,x)=>{(obj[x.relation]??=[]).push(x);return obj;},{}))){
      const section=el("div","lexical-relation");
      section.append(el("span","lexical-rel-name",relation.replace(/([a-z])([A-Z])/g,"$1 $2")));
      const tags=el("div","lexical-tags");
      for(const item of relations.slice(0,12)){
        const lang=item.language||"";
        tags.append(el("span","lexical-tag",item.word+(lang?" · "+lang.toUpperCase():"")));
      }
      section.append(tags);fragment.append(section);
   }
 }else{
   const definitions=Array.isArray(data.definitions)?data.definitions.filter(Boolean):[];
   const synonyms=Array.isArray(data.synonyms)?data.synonyms.filter(Boolean):[];
   if(definitions.length){
     addSubtitle(state.locale==="ru"?"Определения":"Definitions");
     const list=el("div","lexical-definitions");
     for(const def of definitions.slice(0,8))list.append(el("div","lexical-definition",def));
     fragment.append(list);
   }
   if(synonyms.length){
     addSubtitle(state.locale==="ru"?"Синонимы и связанные слова":"Synonyms and related words");
     const tags=el("div","lexical-tags");
     for(const term of synonyms.slice(0,25))tags.append(el("span","lexical-tag",term));
     fragment.append(tags);
   }
 }
 if(!fragment.childNodes.length)return false;
 container.append(fragment);
 return true;
}
async function renderLexical(word,sourceLanguage,requestId,targetLanguage){
 const catalog=await getLexicalCatalog();
 if(!catalog||requestId!==state.searchNumber)return;
 const sources=Object.keys(catalog.sources||{}).filter(id=>
   catalog.sources?.[id]?.languages?.some(item=>item.language===sourceLanguage));
 if(!sources.length)return;
 const looked=await Promise.allSettled(sources.map(src=>lookupLexical(src,sourceLanguage,word)));
 if(requestId!==state.searchNumber)return;
 let cards=0;
 const section=el("section","lexical-block");
 const header=el("div","lexical-heading",state.locale==="ru"?"ОПРЕДЕЛЕНИЯ И СМЫСЛОВЫЕ СВЯЗИ":"DEFINITIONS & SEMANTIC RELATIONS");
 section.append(header);
 for(const [i,result] of looked.entries()){
   if(result.status!=="fulfilled"||!result.value?.entry)continue;
   const source=sources[i],info=result.value.meta;
   const {card,body}=summaryCard(LEXICAL_NAMES[source],1,source);
   card.classList.add("semantic-card");
   const intro=el("div","semantic-note",
     source==="conceptnet"
     ?(state.locale==="ru"?"Связанные понятия — не прямые переводы":"Related concepts — not literal translations")
     :(state.locale==="ru"?"Определения и лексические связи — не прямые переводы":"Definitions and lexical connections — not translations"));
   body.append(intro);
   if(!addLexicalRecords(body,source,result.value,sourceLanguage,targetLanguage))continue;
   sourceFooter(body,{license:info.license,source_url:info.source_url,download_url:info.release_url,
                      attribution:info.title+"; original contributors and rightsholders"});
   section.append(card);
   cards++;
 }
 if(cards){
   // Add semantic information *after* translations and examples.
   const root=$("results");
   if(root.querySelector(".no-results"))root.replaceChildren(el("h2","semantic-only-heading",word),el("p","semantic-note",state.locale==="ru"?"Прямой перевод не найден. Доступны смысловые данные.":"No direct translation found. Semantic data are available."));
   root.append(section);
 }
}
function render(word,pair,entry,metadata){
 const target=$("results");target.replaceChildren();
 const heading=el("div","results-head");
 const left=el("div");left.append(el("span","result-eyebrow",t("results")),el("h2","",word));
 left.append(el("div","result-meta",languageLabel(metadata.from)+" → "+languageLabel(metadata.to)));
 const buttons=el("div","actions");
 const speak=el("button","circle-action","◖))");speak.type="button";speak.title=t("pronounce");speak.setAttribute("aria-label",t("pronounce"));
 speak.addEventListener("click",()=>{if(!("speechSynthesis" in window))return;window.speechSynthesis.cancel();const utterance=new SpeechSynthesisUtterance(word);utterance.lang=metadata.from;speechSynthesis.speak(utterance)});
 const copy=el("button","circle-action","⧉");copy.type="button";copy.title=t("copy");copy.setAttribute("aria-label",t("copy"));
 copy.addEventListener("click",()=>navigator.clipboard?.writeText(location.href).then(()=>setStatus(t("copy")+" ✓")));
 buttons.append(speak,copy);heading.append(left,buttons);target.append(heading);
 const content=renderTranslations(word,pair,entry);
 const badges=el("div","result-summary");
 badges.append(el("span","count-pill",countLabel(content.sourceCount,"sourceCount")),el("span","count-pill",countLabel(content.total,"entries")));
 if(content.examples)badges.append(el("span","count-pill",countLabel(content.examples,"examples")));
 target.append(badges,content.fragment);
}
async function search(){
 if(!state.catalog)return;
 const raw=$("term").value.trim();
 if(!raw){emptyResult(t("emptyTitle"),t("emptyDescription"));return}
 const word=normalize(raw);const pair=pairValue();
 const metadata=state.byPair.get(pair);
 if(!metadata){setStatus(t("noPairs"),"error");return}
 const request=++state.searchNumber;
 setStatus(t("loading"),"loading");
 $("search-btn").disabled=true;
 updateAddress(raw);
 try{
   const shard=await shaBucket(word,metadata.buckets);
   const payload=await getShard(pair,shard);
   if(request!==state.searchNumber)return;
   const entry=payload.words[word];
   if(entry){render(raw,pair,entry,metadata);setStatus("")}
   else{emptyResult(t("notFound"),t("notFoundDetail"));setStatus("")}
   // Look up independent lexical/semantic networks, never relabelled as translation.
   renderLexical(word,metadata.from,request,metadata.to).catch(error=>console.warn("Semantic lookup unavailable:",error));
 }catch(err){
   if(request!==state.searchNumber)return;
   console.error("Lookup error",err);
   emptyResult(t("error"),String(err.message||err));
   setStatus(t("error"),"error")
 }finally{if(request===state.searchNumber)$("search-btn").disabled=false}
}
async function load(){
 loadLocale();
 try{
   const resp=await fetch("./data/catalog.json",{cache:"no-cache"});
   if(!resp.ok)throw Error("HTTP "+resp.status);
   state.catalog=await resp.json();
   if(!Array.isArray(state.catalog.pairs)||!state.catalog.pairs.length)throw Error("No indexed dictionaries");
   state.byPair=new Map(state.catalog.pairs.map(x=>[x.pair,x]));
   fillLanguages(params.get("from")||"en",params.get("to")||"ru");
   $("coverage-text").textContent=state.catalog.pairs.length+" "+t("coverage");
   if(params.get("q")){$("term").value=params.get("q");await search()}
 }catch(err){
   console.error("Catalog unavailable:",err);
   setStatus(t("building")+" "+String(err.message||err),"error");
 }
}
$("search-form").addEventListener("submit",e=>{e.preventDefault();search()});
$("from").addEventListener("change",()=>{fillTargets($("from").value,"");if($("term").value.trim())search()});
$("to").addEventListener("change",()=>{if($("term").value.trim())search()});
$("swap").addEventListener("click",()=>{
 const a=$("from").value,b=$("to").value;
 if(!state.byPair.has(b+"-"+a)){setStatus(t("swapUnavailable"),"error");return}
 fillLanguages(b,a);if($("term").value.trim())search();else setStatus("")
});
$("locale-btn").addEventListener("click",()=>{
 const a=$("from").value,b=$("to").value;
 state.locale=state.locale==="ru"?"en":"ru";
 loadLocale();if(state.catalog){fillLanguages(a,b);if($("term").value.trim())search();else updateAddress("")}
});
document.querySelectorAll("[data-example]").forEach(btn=>btn.addEventListener("click",()=>{
 $("term").value=btn.dataset.example;search()
}));
document.addEventListener("keydown",event=>{
 if(!$("translate-view").hidden&&event.key==="/"&&!["INPUT","TEXTAREA","SELECT"].includes(document.activeElement.tagName)){
  event.preventDefault();$("term").focus()
 }
});

let directoryData=null,directoryPending=null;
const DESC={
 koreader:["Двуязычные словари StarDict с оригинальными лицензиями и авторством.","Bilingual StarDict dictionaries with original licenses and attribution."],
 freedict:["Открытые двуязычные словари; исходные TEI и словарные статьи.","Open bilingual dictionaries with original TEI sources and articles."],
 wikdict:["Переводы из данных Wiktionary и DBnary.","Translations derived from Wiktionary and DBnary."],
 kaikki:["Определения, части речи, значения и переводы из Wiktionary.","Wiktionary definitions, parts of speech, senses and translations."],
 tatoeba:["Предложения, примеры употребления и связанные переводы без аудио.","Sentence examples and linked translations, without audio."],
 oewn:["Английские определения, синонимы и лексические связи.","English definitions, synonyms and lexical relations."],
 omw:["Многоязычные WordNet, синсеты и лексические связи.","Multilingual WordNets, synsets and lexical relations."],
 conceptnet:["Семантические связи и связанные понятия, не прямые переводы.","Semantic relations and related concepts, not literal translations."]
};
function bilingual(ru,en){return state.locale==="ru"?ru:en}
function setRoute(){
 const dict=location.hash==="#dictionaries";
 $("translate-view").hidden=dict;$("dictionary-view").hidden=!dict;
 for(const [id,on] of [["about-link",!dict],["sources-link",dict]]){
   if(on)$(id).setAttribute("aria-current","page");else $(id).removeAttribute("aria-current");
 }
 if(dict)loadDirectory();
}
function renderDirectory(){
 if(!directoryData)return;
 const data=directoryData;
 $("directory-version").textContent=bilingual("Коллекция: ","Collection: ")+data.release_tag+(data.published_at?" · "+data.published_at.slice(0,10):"");
 $("browse-data").href="https://github.com/danilfg/dicts/releases/tag/"+encodeURIComponent(data.release_tag);
 const filter=$("directory-filter").value.trim().toLowerCase();
 const root=$("source-grid");root.replaceChildren();
 for(const row of data.sources){
   const desc=DESC[row.id]?.[state.locale==="ru"?0:1]||row.description||"";
   const packages=row.packages||[];
   if(filter&&![row.name,row.id,desc,...packages.map(p=>p.pair||p.name||"")].some(x=>String(x).toLowerCase().includes(filter)))continue;
   const card=el("article","source-tile");
   const head=el("div","directory-source-head");
   const avatar=el("span","source-avatar",(row.name||row.id).slice(0,1));avatar.dataset.source=row.id;
   const title=el("div","directory-source-title");title.append(el("h2","",row.name),el("p","",desc));
   head.append(avatar,title);card.append(head);
   const meta=el("div","directory-source-meta");
   const status=row.status==="retained"||row.status==="updated_with_stale_data";
   if(status)meta.append(el("span","retained-label",bilingual("Сохранены прежние данные","Previous data retained")));
   const versions=row.versions||[];
   const ver=versions.length===1?versions[0]:versions.length>1?bilingual("Разные версии (","Multiple versions (")+versions.length+")":bilingual("Не указана источником","Not specified by upstream");
   const version=el("div","version-text",bilingual("Версия: ","Version: ")+ver);
   meta.append(version);
   if(row.snapshot_date)meta.append(el("div","",bilingual("Дата манифеста: ","Manifest date: ")+row.snapshot_date.slice(0,10)));
   if(row.previous_release&&status)meta.append(el("div","",bilingual("Предыдущий релиз: ","Previous release: ")+row.previous_release));
   if(row.package_count!=null)meta.append(el("span","",bilingual("Файлов/пакетов: ","Files/packages: ")+row.package_count));
   card.append(meta);
   if(packages.length){
      const details=el("details","directory-packages");
      details.append(el("summary","",bilingual("Версии отдельных пакетов","Individual package versions")+" ("+packages.length+")"));
      const body=el("div","package-list");
      details.addEventListener("toggle",()=>{
        if(!details.open||body.childNodes.length)return;
        for(const p of packages){
          const item=el("div","package-row");
          item.append(el("span","",p.pair||p.name||"—"),el("span","",p.version||bilingual("Не указана","Not specified")));
          body.append(item);
        }
      });
      details.append(body);card.append(details);
   }
   const foot=el("div","source-footer");
   if(row.source_url)foot.append(anchor(t("source")+" ↗",row.source_url));
   if(row.license_url)foot.append(anchor(t("license")+" ↗",row.license_url));
   if(row.license)foot.append(el("span","",row.license));
   card.append(foot);root.append(card);
 }
 if(!root.childNodes.length)root.append(el("p","semantic-note",bilingual("Словари не найдены.","No matching dictionaries.")));
}
async function loadDirectory(){
 if(directoryData){renderDirectory();return}
 if(directoryPending)return directoryPending;
 $("directory-version").textContent=bilingual("Загрузка каталога…","Loading catalog…");
 directoryPending=(async()=>{
   try{
     const r=await fetch("./data/sources.json",{cache:"no-cache"});
     if(!r.ok)throw Error("HTTP "+r.status);
     const data=await r.json();
     if(data.schema!==1||!Array.isArray(data.sources)||!data.sources.length)throw Error("Invalid source catalog");
     directoryData=data;renderDirectory();
   }catch(e){$("directory-version").textContent=bilingual("Каталог недоступен. Повторите позже.","Catalog unavailable. Try again later.");console.warn(e)}
   finally{directoryPending=null}
 })();
 return directoryPending;
}
window.addEventListener("hashchange",setRoute);
$("directory-filter").addEventListener("input",renderDirectory);

setRoute();
load()
})();