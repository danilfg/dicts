"use strict";
(function(){
const $=id=>document.getElementById(id);
const SOURCE_NAMES={koreader:"KOReader",freedict:"FreeDict",wikdict:"WikDict",kaikki:"Kaikki / Wiktionary",tatoeba:"Tatoeba"};
const TRANSLATIONS={
 en:{eyebrow:"OPEN, SOURCE-ATTRIBUTED WORD DATA",title1:"Every word has",title2:"more than one meaning.",description:"Compare translations across independent dictionaries. Explore examples, definitions and the people behind the data — all in one place.",from:"FROM",to:"TO",search:"Search",placeholder:"Type a word or phrase...",try:"Try:",loading:"Loading language pairs…",coverage:"language pairs available",results:"DICTIONARY RESULTS",meanings:"meanings",entries:"entries",sourceCount:"sources",pronounce:"Pronounce word",copy:"Copy search link",notFound:"No exact match in this dictionary pair",notFoundDetail:"Try a different form of the word, or switch the language direction.",source:"Original source",license:"License",download:"Download dictionary",credit:"Attribution",definitions:"Definitions & expressions",examples:"Examples in context",noSource:"No lexical data for this word",error:"Couldn't load this dictionary index. Please try again or check the Pages build.",building:"This dictionary's searchable index is not available yet. Check GitHub Actions.",offline:"The searchable index is unavailable. Check your internet connection.",emptyTitle:"Discover a word from different perspectives.",emptyDescription:"Choose two languages, then search for a word or an expression.",directoryEyebrow:"THE DATA BEHIND THE WORDS",directoryTitle:"Independent sources, one search.",browse:"Explore all datasets ↗",tile1:"Bilingual dictionaries with original source notices.",tile2:"Open bilingual dictionaries and language pairs.",tile3:"More translations from Wiktionary-derived data.",tile4:"More data",tile5:"Wiktionary examples, Tatoeba, WordNet and ConceptNet resources.",footer:"Translations are supplied by third parties as is. See original licenses and authorship.",attributions:"Licenses & attribution ↗",about:"About",sources:"Data sources",swapUnavailable:"No dictionary is published for the opposite direction.",noPairs:"No language pairs are available for this source language.",sourceType:"Source dictionary",total:"Full entry",sentences:"Example sentences",word:"Word",parts:"Independent dictionaries"},
 ru:{eyebrow:"ОТКРЫТЫЕ СЛОВАРИ С УКАЗАНИЕМ ИСТОЧНИКОВ",title1:"У каждого слова",title2:"больше одного значения.",description:"Сравнивайте переводы из независимых словарей, изучайте определения, примеры употребления и первоисточники — в одном месте.",from:"С ЯЗЫКА",to:"НА ЯЗЫК",search:"Перевести",placeholder:"Введите слово или выражение…",try:"Попробуйте:",loading:"Загружаем языковые пары…",coverage:"языковых пар для поиска",results:"РЕЗУЛЬТАТЫ ПО СЛОВАРЯМ",meanings:"значений",entries:"записей",sourceCount:"источников",pronounce:"Озвучить слово",copy:"Скопировать ссылку",notFound:"Точное совпадение не найдено",notFoundDetail:"Попробуйте другую форму слова или измените направление перевода.",source:"Первоисточник",license:"Лицензия",download:"Скачать словарь",credit:"Атрибуция",definitions:"Определения и выражения",examples:"Примеры употребления",noSource:"Для этого слова пока нет данных",error:"Не удалось загрузить словарный индекс. Проверьте работу Pages или повторите запрос.",building:"Индекс этой пары ещё не опубликован. Проверьте GitHub Actions.",offline:"Словарный индекс недоступен. Проверьте соединение с интернетом.",emptyTitle:"Узнавайте слово с разных сторон.",emptyDescription:"Выберите языки и найдите слово или выражение.",directoryEyebrow:"ОТКУДА ПОЛУЧЕНЫ ДАННЫЕ",directoryTitle:"Независимые словари, единый поиск.",browse:"Все источники ↗",tile1:"Двуязычные словари с оригинальными лицензиями.",tile2:"Открытые словари для множества языковых пар.",tile3:"Дополнительные переводы на основе Wiktionary.",tile4:"Другие данные",tile5:"Выражения Kaikki, примеры Tatoeba, WordNet и ConceptNet.",footer:"Переводы получены от сторонних авторов и предоставлены как есть. Соблюдайте лицензии.",attributions:"Лицензии и авторство ↗",about:"О проекте",sources:"Источники",swapUnavailable:"Для обратного направления словарь пока не опубликован.",noPairs:"Для выбранного языка пока нет других направлений.",sourceType:"Исходный словарь",total:"Полная статья",sentences:"Примеры употребления",word:"Слово",parts:"Независимые словари"}
};
const UI={"en":{"translator":"Translator","dictionaries":"Dictionaries","heroDescription":"Translations, definitions and examples from open dictionaries.","from":"FROM","to":"TO","search":"Search","placeholder":"Type a word or phrase…","try":"Try:","loading":"Loading language pairs…","coverage":"language pairs available","results":"DICTIONARY RESULTS","emptyTitle":"Discover a word from different perspectives.","emptyDescription":"Choose two languages, then search for a word or an expression.","directoryEyebrow":"Sources, versions and licenses","browse":"Release ↗","directoryFilter":"Find a dictionary","directoryPlaceholder":"Name or language pair","directoryNote":"Versions come from the published release. Full source data are available in the release.","footer":"Translations are supplied by third parties as is. See original licenses and authorship.","attributions":"Licenses & attribution ↗","swap":"Swap languages","pronounce":"Pronounce word","copy":"Copy search link","notFound":"No exact match","notFoundDetail":"Try a different form or language direction.","error":"Could not load the dictionary index.","building":"Index not yet available.","noPairs":"No language pairs available.","swapUnavailable":"Opposite direction unavailable.","source":"Original source","license":"License","eyebrow":"OPEN, SOURCE-ATTRIBUTED WORD DATA"},"ru":{"translator":"Переводчик","dictionaries":"Список словарей","heroDescription":"Переводы, определения и примеры из открытых словарей.","from":"С ЯЗЫКА","to":"НА ЯЗЫК","search":"Перевести","placeholder":"Введите слово или выражение…","try":"Попробуйте:","loading":"Загружаем языковые пары…","coverage":"языковых пар для поиска","results":"РЕЗУЛЬТАТЫ ПО СЛОВАРЯМ","emptyTitle":"Узнавайте слово с разных сторон.","emptyDescription":"Выберите языки и найдите слово или выражение.","directoryEyebrow":"Источники, версии и лицензии","browse":"Релиз ↗","directoryFilter":"Найти словарь","directoryPlaceholder":"Название или языковая пара","directoryNote":"Версии берутся из опубликованного релиза. Полные данные доступны в релизе.","footer":"Переводы предоставлены сторонними авторами как есть.","attributions":"Лицензии и авторство ↗","swap":"Поменять языки местами","pronounce":"Озвучить слово","copy":"Скопировать ссылку","notFound":"Точное совпадение не найдено","notFoundDetail":"Попробуйте другую форму или направление.","error":"Не удалось загрузить индекс.","building":"Индекс ещё недоступен.","noPairs":"Нет языковых пар.","swapUnavailable":"Обратное направление недоступно.","source":"Первоисточник","license":"Лицензия","eyebrow":"ОТКРЫТЫЕ СЛОВАРИ С УКАЗАНИЕМ ИСТОЧНИКОВ"},"uk":{"translator":"Перекладач","dictionaries":"Словники","heroDescription":"Переклади, визначення й приклади з відкритих словників.","from":"З МОВИ","to":"НА МОВУ","search":"Перекласти","placeholder":"Введіть слово або вираз…","try":"Спробуйте:","loading":"Завантаження мовних пар…","coverage":"доступних мовних пар","results":"РЕЗУЛЬТАТИ","emptyTitle":"Дізнайтеся більше про слово.","emptyDescription":"Оберіть мови та знайдіть слово або вираз.","directoryEyebrow":"Джерела, версії та ліцензії","browse":"Реліз ↗","directoryFilter":"Знайти словник","directoryPlaceholder":"Назва або мовна пара","directoryNote":"Версії та повні дані доступні в релізі.","footer":"Переклади сторонніх авторів надаються як є.","attributions":"Ліцензії та авторство ↗","swap":"Поміняти мови","pronounce":"Вимовити слово","copy":"Копіювати посилання","notFound":"Точного збігу немає","notFoundDetail":"Спробуйте іншу форму або напрямок.","error":"Не вдалося завантажити індекс.","building":"Індекс недоступний.","noPairs":"Немає мовних пар.","swapUnavailable":"Зворотний напрямок недоступний.","source":"Джерело","license":"Ліцензія","eyebrow":"ВІДКРИТІ СЛОВНИКОВІ ДАНІ"},"de":{"translator":"Übersetzer","dictionaries":"Wörterbücher","heroDescription":"Übersetzungen, Definitionen und Beispiele aus offenen Wörterbüchern.","from":"VON","to":"NACH","search":"Suchen","placeholder":"Wort oder Ausdruck eingeben…","try":"Versuche:","loading":"Sprachpaare werden geladen…","coverage":"verfügbare Sprachpaare","results":"WÖRTERBUCHERGEBNISSE","emptyTitle":"Entdecke ein Wort aus verschiedenen Perspektiven.","emptyDescription":"Wähle zwei Sprachen und suche ein Wort.","directoryEyebrow":"Quellen, Versionen und Lizenzen","browse":"Release ↗","directoryFilter":"Wörterbuch suchen","directoryPlaceholder":"Name oder Sprachpaar","directoryNote":"Versionen und vollständige Daten sind im Release verfügbar.","footer":"Übersetzungen von Dritten werden ohne Gewähr bereitgestellt.","attributions":"Lizenzen und Quellen ↗","swap":"Sprachen tauschen","pronounce":"Wort aussprechen","copy":"Suchlink kopieren","notFound":"Keine genaue Übereinstimmung","notFoundDetail":"Versuche eine andere Form oder Richtung.","error":"Index konnte nicht geladen werden.","building":"Index noch nicht verfügbar.","noPairs":"Keine Sprachpaare verfügbar.","swapUnavailable":"Gegenrichtung nicht verfügbar.","source":"Originalquelle","license":"Lizenz","eyebrow":"OFFENE WÖRTERBUCHDATEN"},"es":{"translator":"Traductor","dictionaries":"Diccionarios","heroDescription":"Traducciones, definiciones y ejemplos de diccionarios abiertos.","from":"DE","to":"A","search":"Buscar","placeholder":"Escribe una palabra o expresión…","try":"Prueba:","loading":"Cargando pares de idiomas…","coverage":"pares disponibles","results":"RESULTADOS","emptyTitle":"Descubre una palabra desde distintas perspectivas.","emptyDescription":"Elige dos idiomas y busca una palabra.","directoryEyebrow":"Fuentes, versiones y licencias","browse":"Versión ↗","directoryFilter":"Buscar diccionario","directoryPlaceholder":"Nombre o par de idiomas","directoryNote":"Las versiones y los datos completos están disponibles en la publicación.","footer":"Las traducciones de terceros se ofrecen tal cual.","attributions":"Licencias y atribución ↗","swap":"Intercambiar idiomas","pronounce":"Pronunciar palabra","copy":"Copiar enlace","notFound":"Sin coincidencia exacta","notFoundDetail":"Prueba otra forma o dirección.","error":"No se pudo cargar el índice.","building":"Índice aún no disponible.","noPairs":"No hay pares disponibles.","swapUnavailable":"Dirección inversa no disponible.","source":"Fuente original","license":"Licencia","eyebrow":"DATOS LÉXICOS ABIERTOS"},"fr":{"translator":"Traducteur","dictionaries":"Dictionnaires","heroDescription":"Traductions, définitions et exemples de dictionnaires ouverts.","from":"DE","to":"VERS","search":"Rechercher","placeholder":"Saisir un mot ou une expression…","try":"Essayez :","loading":"Chargement des paires…","coverage":"paires disponibles","results":"RÉSULTATS","emptyTitle":"Découvrez un mot sous différents angles.","emptyDescription":"Choisissez deux langues et recherchez un mot.","directoryEyebrow":"Sources, versions et licences","browse":"Version ↗","directoryFilter":"Trouver un dictionnaire","directoryPlaceholder":"Nom ou paire de langues","directoryNote":"Les versions et données complètes sont disponibles dans la publication.","footer":"Les traductions de tiers sont fournies en l’état.","attributions":"Licences et attribution ↗","swap":"Inverser les langues","pronounce":"Prononcer le mot","copy":"Copier le lien","notFound":"Aucune correspondance exacte","notFoundDetail":"Essayez une autre forme ou direction.","error":"Impossible de charger l’index.","building":"Index indisponible.","noPairs":"Aucune paire disponible.","swapUnavailable":"Direction inverse indisponible.","source":"Source originale","license":"Licence","eyebrow":"DONNÉES LEXICALES OUVERTES"},"pt-BR":{"translator":"Tradutor","dictionaries":"Dicionários","heroDescription":"Traduções, definições e exemplos de dicionários abertos.","from":"DE","to":"PARA","search":"Buscar","placeholder":"Digite uma palavra ou expressão…","try":"Experimente:","loading":"Carregando pares de idiomas…","coverage":"pares disponíveis","results":"RESULTADOS","emptyTitle":"Descubra uma palavra de várias perspectivas.","emptyDescription":"Escolha dois idiomas e procure uma palavra.","directoryEyebrow":"Fontes, versões e licenças","browse":"Versão ↗","directoryFilter":"Encontrar dicionário","directoryPlaceholder":"Nome ou par de idiomas","directoryNote":"Versões e dados completos estão disponíveis na publicação.","footer":"Traduções de terceiros são fornecidas como estão.","attributions":"Licenças e atribuição ↗","swap":"Trocar idiomas","pronounce":"Pronunciar palavra","copy":"Copiar link","notFound":"Nenhuma correspondência exata","notFoundDetail":"Tente outra forma ou direção.","error":"Não foi possível carregar o índice.","building":"Índice indisponível.","noPairs":"Não há pares disponíveis.","swapUnavailable":"Direção inversa indisponível.","source":"Fonte original","license":"Licença","eyebrow":"DADOS LEXICAIS ABERTOS"},"zh-CN":{"translator":"翻译器","dictionaries":"词典","heroDescription":"开放词典中的翻译、释义和例句。","from":"源语言","to":"目标语言","search":"搜索","placeholder":"输入单词或短语…","try":"试试：","loading":"正在加载语言对…","coverage":"个可用语言对","results":"词典结果","emptyTitle":"从不同角度了解单词。","emptyDescription":"选择两种语言并搜索单词或短语。","directoryEyebrow":"来源、版本和许可证","browse":"发布版本 ↗","directoryFilter":"查找词典","directoryPlaceholder":"名称或语言对","directoryNote":"版本和完整数据可在发布版本中获取。","footer":"第三方翻译按原样提供。","attributions":"许可证和署名 ↗","swap":"交换语言","pronounce":"朗读单词","copy":"复制链接","notFound":"没有完全匹配的结果","notFoundDetail":"尝试其他词形或翻译方向。","error":"无法加载词典索引。","building":"索引尚不可用。","noPairs":"没有可用语言对。","swapUnavailable":"反向翻译不可用。","source":"原始来源","license":"许可证","eyebrow":"开放词典数据"}};
const params=new URLSearchParams(location.search);
const state={locale:Object.hasOwn(UI,params.get("ui"))?params.get("ui"):"en",
 catalog:null,byPair:new Map(),cache:new Map(),current:null,searchNumber:0};
const el=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e};
const t=k=>UI[state.locale]?.[k]||TRANSLATIONS[state.locale]?.[k]||TRANSLATIONS.en[k]||k;
function urlSafe(value){try{const u=new URL(value);return u.protocol==="https:"||u.protocol==="http:"?u.href:null}catch{return null}}
function anchor(label,url){const a=el("a","",label);const safe=urlSafe(url);if(safe){a.href=safe;a.target="_blank";a.rel="noopener noreferrer"}return a}
function setStatus(message,type){const e=$("status");e.textContent=message||"";e.className="status"+(type?" "+type:"")}
function normalize(s){return String(s||"").trim().toLocaleLowerCase().replace(/ß/g,"ss").replace(/ς/g,"σ").replace(/\s+/g," ")}
function languageName(code){try{const codeFixed=code==="iw"?"he":code;const d=new Intl.DisplayNames([state.locale],{type:"language"});return d.of(codeFixed)||code.toUpperCase()}catch{return code.toUpperCase()}}
function languageLabel(code){return languageName(code)+" ("+code.toUpperCase()+")"}
function pairValue(){return $("from").value+"-"+$("to").value}
function loadLocale(){
 document.documentElement.lang=state.locale;
 $("locale-btn").value=state.locale;
 $("promo-link").href="./lingoinview/"+(state.locale==="en"?"":state.locale+"/");
 $("eyebrow").textContent=t("eyebrow");
 $("hero-title").textContent=t("translator");
 $("hero-description").textContent=t("heroDescription");
 $("from-label").textContent=t("from");$("to-label").textContent=t("to");
 $("search-label").textContent=t("search");$("term").placeholder=t("placeholder");
 $("try-label").textContent=t("try");
 $("empty-title")?.replaceChildren(document.createTextNode(t("emptyTitle")));
 $("empty-description")?.replaceChildren(document.createTextNode(t("emptyDescription")));
 $("directory-eyebrow").textContent=t("directoryEyebrow");
 $("directory-title").textContent=t("dictionaries");
 $("browse-data").textContent=t("browse");
 $("footer-disclaimer").textContent=t("footer");
 $("footer-licenses").textContent=t("attributions");
 $("about-link").textContent=t("translator");
 $("sources-link").textContent=t("dictionaries");
 $("directory-filter-label").textContent=t("directoryFilter");
 $("directory-filter").placeholder=t("directoryPlaceholder");
 $("directory-note").textContent=t("directoryNote");
 if(directoryData)renderDirectory();
 $("swap").setAttribute("aria-label",t("swap"));
 $("term").setAttribute("aria-label",t("placeholder"));
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

function countLabel(count,type){
 return window.DictsEntryFormat
   ?window.DictsEntryFormat.formatCount(count,type,state.locale)
   :count+" "+t(type);
}
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
async function getLexicalRecords(word,sourceLanguage){
 const catalog=await getLexicalCatalog();
 const sources=Object.keys(catalog?.sources||{}).filter(id=>
   catalog.sources[id]?.languages?.some(item=>item.language===sourceLanguage));
 const looked=await Promise.allSettled(sources.map(src=>lookupLexical(src,sourceLanguage,word)));
 return looked.flatMap((result,i)=>result.status==="fulfilled"&&result.value?.entry?[{source:sources[i],...result.value}]:[]);
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
 const badges=el("div","result-summary"),body=el("div","dictionary-result");
 target.append(badges,body);
 const update=lexical=>{
   const data=window.DictsResultModel.adapt(pair,entry||{},lexical,state.catalog.provenance?.[pair]||{});
   const prepared=window.LWC_DICTIONARY_VIEW.render(body,data,{language:state.locale,primaryCount:2});
   badges.replaceChildren(el("span","count-pill",countLabel(window.DictsResultModel.sourceCount(data),"sourceCount")),
     el("span","count-pill",countLabel(prepared.translations.length,"translations")));
   if(prepared.examples.length)badges.append(el("span","count-pill",countLabel(prepared.examples.length,"examples")));
 };
 return update;
}
async function search(){
 if(!state.catalog)return;
 const raw=$("term").value.trim();
 if(!raw){++state.searchNumber;$("search-btn").disabled=false;setStatus("");emptyResult(t("emptyTitle"),t("emptyDescription"));return}
 const word=normalize(raw);const pair=pairValue();
 const metadata=state.byPair.get(pair);
 if(!metadata){setStatus(t("noPairs"),"error");return}
 const request=++state.searchNumber;
 setStatus(t("loading"),"loading");
 $("search-btn").disabled=true;
 updateAddress(raw);
 try{
   // Independent lexical indexes load in parallel, without blocking the first translations.
   const lexicalPromise=getLexicalRecords(word,metadata.from).catch(error=>{console.warn("Semantic lookup unavailable:",error);return []});
   const shard=await shaBucket(word,metadata.buckets);
   const payload=await getShard(pair,shard);
   if(request!==state.searchNumber)return;
   const entry=payload.words[word];
   let update;
   if(entry){update=render(raw,pair,entry,metadata);update([])}
   else emptyResult(t("notFound"),t("notFoundDetail"));
   setStatus("");
   lexicalPromise.then(lexical=>{
     if(request!==state.searchNumber||!lexical.length)return;
     if(!update)update=render(raw,pair,entry,metadata);
     update(lexical);
   }).catch(error=>console.warn("Semantic rendering unavailable:",error));
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
$("locale-btn").addEventListener("change",()=>{
 const a=$("from").value,b=$("to").value;
 state.locale=Object.hasOwn(UI,$("locale-btn").value)?$("locale-btn").value:"en";
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