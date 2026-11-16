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
 $("hero-title").replaceChildren(document.createTextNode(t("title1")),document.createElement("br"),el("em","",t("title2")));
 $("hero-description").textContent=t("description");
 $("from-label").textContent=t("from");$("to-label").textContent=t("to");
 $("search-label").textContent=t("search");$("term").placeholder=t("placeholder");
 $("try-label").textContent=t("try");
 $("empty-title")?.replaceChildren(document.createTextNode(t("emptyTitle")));
 $("empty-description")?.replaceChildren(document.createTextNode(t("emptyDescription")));
 $("directory-eyebrow").textContent=t("directoryEyebrow");
 $("directory-title").textContent=t("directoryTitle");$("browse-data").textContent=t("browse");
 $("tile-koreader").textContent=t("tile1");$("tile-freedict").textContent=t("tile2");
 $("tile-wikdict").textContent=t("tile3");$("tile-other-title").textContent=t("tile4");
 $("tile-other").textContent=t("tile5");$("footer-disclaimer").textContent=t("footer");
 $("footer-licenses").textContent=t("attributions");$("about-link").textContent=t("about");
 $("sources-link").textContent=t("sources");
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
function summaryCard(title,count,id){
 const card=el("details","dictionary-card");card.open=true;
 const summary=el("summary");
 const icon=el("span","source-avatar",id==="koreader"?"K":id==="freedict"?"F":id==="wikdict"?"W":id==="kaikki"?"K":"T");icon.dataset.source=id;
 const heading=el("span","source-title");heading.append(el("b","",title),el("small","",count+" "+t("entries")));
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
 for(const line of lines){
    if(line.kind==="phonetic"){
      const p=el("div","article-phonetic",line.text);article.append(p);continue
    }
    if(line.kind==="part"){
      article.append(el("div","article-part",line.text));continue
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
    row.append(detail);article.append(row);
 }
 container.append(article);
}
function renderTranslations(word,pair,entry){
 const fragment=document.createDocumentFragment();
 let sourceCount=0,total=0;
 for(const id of ["koreader","freedict","wikdict"]){
   const entries=(entry.translations||{})[id]||[];
   if(!entries.length)continue;
   sourceCount++;
   const {card,body}=summaryCard(SOURCE_NAMES[id],entries.length,id);
   for(const meaning of entries){
      if(typeof meaning!=="string"||!meaning.trim())continue;
      const div=el("div","definition");
      addFormattedArticle(div,meaning,pair.split("-")[0],pair.split("-")[1]);
      body.append(div);total++;
   }
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
      if(example.author)credit.append(document.createTextNode(example.author+" · "));
      if(example.source_url)credit.append(anchor(t("source")+" ↗",example.source_url));
      if(example.license)credit.append(document.createTextNode(" · "+example.license));
      d.append(credit);body.append(d);
    }
    fragment.append(card);sourceCount++;
 }
 return {fragment,sourceCount,total:total+meanings.length+examples.length,examples:examples.length}
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
 badges.append(el("span","count-pill",content.sourceCount+" "+t("sourceCount")),el("span","count-pill",content.total+" "+t("meanings")));
 if(content.examples)badges.append(el("span","count-pill",content.examples+" "+t("examples")));
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
 if(event.key==="/"&&!["INPUT","TEXTAREA","SELECT"].includes(document.activeElement.tagName)){
  event.preventDefault();$("term").focus()
 }
});
load()
})();