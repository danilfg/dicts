/* Vendored from danilfg/translator at 763220cb2cfa532c328fa1b5adb0897fd96dcd18.
   Keep the presentation logic aligned with that repository. */
/* Compact, source-aware dictionary presentation. All dictionary text is untrusted:
   rendered using textContent only, never inserted into innerHTML. */
(() => {
  'use strict';
  const T=self.YWA_TRANSLATION;
  const PRIMARY={freedict:'https://freedict.org/downloads/',wikdict:'https://www.wikdict.com/page/download',
    koreader:'https://github.com/danilfg/dicts',kaikki:'https://kaikki.org/',tatoeba:'https://tatoeba.org/en/downloads',oewn:'https://en-word.net/',omw:'https://omwn.org/',conceptnet:'https://conceptnet.io/'};
  const NAMES={'phrase-dictionary':'Phrase dictionary',freedict:'FreeDict',wikdict:'WikDict',koreader:'KOReader',kaikki:'Kaikki',tatoeba:'Tatoeba',oewn:'Open English WordNet',omw:'Open Multilingual Wordnet',conceptnet:'ConceptNet'};
  const UI={
    ru:{further:'Ещё',less:'Скрыть',notes:'Пояснения',from:'Источники',wordnet:'Английские определения',synonyms:'Синонимы'},
    en:{further:'More',less:'Less',notes:'Explanations',from:'Sources',wordnet:'English definitions',synonyms:'Synonyms'},
    uk:{further:'Ще',less:'Згорнути',notes:'Пояснення',from:'Джерела',wordnet:'Англійські визначення',synonyms:'Синоніми'},
    es:{further:'Más',less:'Menos',notes:'Aclaraciones',from:'Fuentes',wordnet:'Definiciones en inglés',synonyms:'Sinónimos'},
    de:{further:'Mehr',less:'Weniger',notes:'Erläuterungen',from:'Quellen',wordnet:'Englische Definitionen',synonyms:'Synonyme'},
    fr:{further:'Plus',less:'Réduire',notes:'Explications',from:'Sources',wordnet:'Définitions en anglais',synonyms:'Synonymes'},
    pt:{further:'Mais',less:'Menos',notes:'Explicações',from:'Fontes',wordnet:'Definições em inglês',synonyms:'Sinônimos'},
    zh:{further:'更多',less:'收起',notes:'释义说明',from:'来源',wordnet:'英语释义',synonyms:'同义词'}
  };
  const label=(key,language)=> (UI[String(language||'en').split('-')[0]]||UI.en)[key]||key;
  const urlOf=(provider)=>{
    const source=String(provider.source||'').toLowerCase();
    const url=String(provider.source_url||'');
    if(/^https:\/\//i.test(url)) {
      if(source==='freedict' && /^(?:https:\/\/)?(?:www\.)?freedict\.org\/?$/i.test(url)) return PRIMARY.freedict;
      if(source==='wikdict' && /^https:\/\/(?:www\.)?wikdict\.com\/?$/i.test(url)) return PRIMARY.wikdict;
      return url;
    }
    return PRIMARY[source]||'';
  };
  const keyOf=value=>String(value||'').normalize('NFC').replace(/(?<=[\p{Script=Cyrillic}])\u0301/gu,'').normalize('NFKC')
    .toLocaleLowerCase().replace(/[\s\u2013\u2014.,;:|]+/gu,' ').trim();
  const visibleText=raw=>T.decode(String(raw??''))
    .replace(/<\/?(?:p|div|li|ul|ol|br|tr|td|dd|dt)\b[^>]*>/gi,'; ')
    .replace(/<[^>]*>/g,' ').replace(/[\u0000-\u001f]/g,' ')
    .replace(/\s+/g,' ').trim();
  function separate(raw,pair){
    const text=visibleText(raw);if(!text)return {values:[],notes:[]};
    const items=[],notes=[];
    const target=pair.split('-')[1];
    for(const segment of text.split(/\s*[;|]\s*/).filter(Boolean)){
      const value=segment.trim();
      // Some older StarDict exports lost list punctuation, leaving an accented
      // sequence of separate lemmas. Only interpret a very strong signal: four
      // or more independently stress-marked Cyrillic words; ordinary phrases
      // (including multiword translations) are never split on spaces.
      if(target==='ru' && !/[A-Za-z]/.test(value)){
        const stressed=value.split(/\s+/);
        if(stressed.length>=4 && stressed.every(w=>/^[\p{Script=Cyrillic}\p{M}-]{4,}$/u.test(w)&&/\u0301/.test(w))){
          items.push(...stressed);continue;
        }
      }
      if(target==='ru' && /\p{Script=Cyrillic}/u.test(value) && /\b(?:in|to|of|with|what|degree|manner|the|by|at|from|for)\b/i.test(value)){
        const parts=[...value.matchAll(/([\p{Script=Cyrillic}\p{M}]+(?:\s+[\p{Script=Cyrillic}\p{M}]+)*)|([A-Za-z]+(?:[\s'-]+[A-Za-z]+)*)/gu)]
          .map(m=>({text:m[0].trim(),latin:!!m[2]}));
        if(parts.some(x=>x.latin && /\s/.test(x.text))){
          let previous='';
          for(let i=0;i<parts.length;i++){
            const part=parts[i];if(!part.text)continue;
            if(part.latin){
              // Source-language descriptions are not translations. Keep them as
              // explanations rather than presenting a mixed-language word list.
              let next=parts[i+1]?.latin===false?parts[i+1].text:'';
              const words=next.split(/\s+/);
              if(words.length>1 && items.some(x=>keyOf(x)===keyOf(words[0]))) next=words.slice(1).join(' ');
              if(/\s/.test(part.text))notes.push({text:part.text,detail:next});
            }else{
              let extracted=part.text;
              const words=extracted.split(/\s+/);
              // Repeated leading particles (e.g. how: 'как каким образом') are
              // removed only when the same particle was already a whole value.
              if(words.length>1 && items.some(x=>keyOf(x)===keyOf(words[0]))) extracted=words.slice(1).join(' ');
              if(extracted)items.push(extracted);
              previous=extracted;
            }
          }
          continue;
        }
      }
      items.push(value);
    }
    return {values:items,notes};
  }
  function uniqueProviders(providers){
    const result=[];
    for(const p of providers){
      const source=String(p?.source||'').toLowerCase();if(!source)continue;
      const link=urlOf(p);
      if(!result.some(r=>r.source===source&&r.source_url===link&&r.citation===p.citation&&r.license===p.license&&r.package===p.package))result.push({source,source_url:link,citation:p.citation,license:p.license,package:p.package});
    }
    return result;
  }
  function prepare(data){
    const pair=data?.pair||'en-ru';
    const entries=Array.isArray(data?.alternatives)?data.alternatives:[];
    const translations=new Map(), glosses=new Map();
    const primaryKeys=new Set(T.article(data?.primary||'',pair).values.map(keyOf).filter(Boolean));
    for(const entry of entries){
      const providers=uniqueProviders(Array.isArray(entry?.sources)&&entry.sources.length?entry.sources:[entry]);
      const normalized=entry?.article?T.article(entry.text,pair):null;
      const parsed=entry?.parsedValue?{values:[entry.text],notes:[]}:normalized?{values:normalized.values,notes:[...normalized.notes,...normalized.uncertain].map(text=>({text,detail:''}))}:separate(entry?.text||'',pair);
      for(const val of parsed.values){
        const key=keyOf(val);if(!key||primaryKeys.has(key))continue;
        if(!translations.has(key))translations.set(key,{text:val,sources:[]});
        const group=translations.get(key);group.sources=uniqueProviders([...group.sources,...providers]);
      }
      for(const gloss of parsed.notes){
        const key=keyOf(gloss.text)+'|'+keyOf(gloss.detail);
        if(!glosses.has(key))glosses.set(key,{text:gloss.text,detail:gloss.detail,sources:[]});
        const group=glosses.get(key);group.sources=uniqueProviders([...group.sources,...providers]);
      }
    }
    const definitions=[],articles=[];
    for(const entry of Array.isArray(data?.meanings)?data.meanings:[]){
      const value=entry?.kind==='article'&&entry.raw?T.decode(String(entry.text||'')).replace(/<br\s*\/?>|<\/(?:p|div|li|tr|dd|dt)>/gi,'\n').replace(/<[^>]*>/g,' ').trim():visibleText(entry?.text||'');if(!value)continue;
      if(entry.kind==='explanation'){const key=keyOf(value)+'|';const old=glosses.get(key);if(old)old.sources=uniqueProviders([...old.sources,entry]);else glosses.set(key,{text:value,detail:'',sources:uniqueProviders([entry])});continue;}
      const rows=entry.kind==='article'?articles:definitions;const match=rows.find(x=>keyOf(x.text)===keyOf(value));if(match)match.sources=uniqueProviders([...match.sources,entry]);else rows.push({text:value,sources:uniqueProviders([entry])});
    }
    const examples=[];
    for(const entry of Array.isArray(data?.examples)?data.examples:[]){
      if(!entry?.text)continue;
      const val=visibleText(entry.text), translation=visibleText(entry.translation||'');
      const providers=[{source:entry.source||'tatoeba',source_url:entry.source_url,citation:entry.author,license:entry.license}];
      if(entry.translation_url||entry.translation_author)providers.push({source:entry.source||'tatoeba',source_url:entry.translation_url,citation:entry.translation_author,license:entry.translation_license});
      const old=examples.find(x=>keyOf(x.text)===keyOf(val)&&keyOf(x.translation)===keyOf(translation));
      if(old)old.links=uniqueProviders([...old.links,...providers]);else examples.push({text:val,translation,links:uniqueProviders(providers)});
    }
    const lex=data?.wordnet&&typeof data.wordnet==='object'?data.wordnet:null;
    const wordnet=lex?{
      definitions:(Array.isArray(lex.definitions)?lex.definitions:[]).filter(x=>typeof x==='string'&&x.trim()).slice(0,8)
        .map(text=>({text:visibleText(text),sources:[{source:'oewn',source_url:'https://en-word.net/'}]})),
      synonyms:(Array.isArray(lex.synonyms)?lex.synonyms:[]).filter(x=>typeof x==='string'&&x.trim()).slice(0,25)
    }:null;
    const synonyms=[],relationGroups=new Map(),from=pair.split('-')[0];
    for(const entry of data?.synonyms||[]){const text=visibleText(entry.text);if(!text)continue;const old=synonyms.find(x=>keyOf(x.text)===keyOf(text));if(old)old.sources=uniqueProviders([...old.sources,entry]);else synonyms.push({text,sources:uniqueProviders([entry])});}
    for(const entry of data?.relations||[]){const text=visibleText(entry.text);if(!text)continue;const type=String(entry.relation||'RelatedTo').split('/').pop();const values=relationGroups.get(type)||new Map();const language=entry.language&&entry.language!==from?' ('+entry.language.toUpperCase()+')':'';const key=keyOf(text)+language;const old=values.get(key);if(old)old.sources=uniqueProviders([...old.sources,entry]);else values.set(key,{text:text+language,sources:uniqueProviders([entry])});relationGroups.set(type,values);}
    const relations=[...relationGroups].map(([type,values])=>({type,values:[...values.values()],sources:uniqueProviders([...values.values()].flatMap(x=>x.sources))}));
    const contextExpressions=[];
    for(const entry of data?.contextExpressions||[]){
      const text=visibleText(entry.text),translation=visibleText(entry.translation);
      if(!text||!translation)continue;
      const old=contextExpressions.find(x=>keyOf(x.text)===keyOf(text)&&keyOf(x.translation)===keyOf(translation));
      if(old)old.sources=uniqueProviders([...old.sources,entry]);else contextExpressions.push({text,translation,sources:uniqueProviders([entry])});
    }
    return {translations:[...translations.values()],glosses:[...glosses.values()],definitions,articles,examples,wordnet,synonyms,relations,contextExpressions};

  }
  function el(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;}
  function links(host,sources,showCitation=false){
    const providers=uniqueProviders(sources||[]);if(!providers.length)return;
    const div=el('div','lwc-mini-providers');
    // Different lexical packages can credit the same family/website.
    // Collapse their visible links, not the underlying attribution records.
    // Distinct sentence URLs (e.g. Tatoeba original and translation) still
    // receive distinct links so that each attributed sentence is reachable.
    const groups=new Map();
    for(const p of providers){
      const href=p.source==='omw'?PRIMARY.omw:p.source_url;
      const key=JSON.stringify([p.source,href]);
      if(!groups.has(key))groups.set(key,{source:p.source,href,credits:[]});
      groups.get(key).credits.push(p);
    }
    for(const {source,href,credits} of groups.values()){
      const names=[...new Set(credits.map(p=>p.citation).filter(Boolean))];
      const name=(NAMES[source]||source)+(showCitation&&names.length?' · '+names.join(', '):'');
      const title=[...new Set(credits.map(p=>[p.package,p.citation,p.license,p.source_url].filter(Boolean).join(' · ')))].filter(Boolean).join('\n\n');
      const node=el(href?'a':'span',null,name);
      if(href){node.href=href;node.target='_blank';node.rel='noopener noreferrer';}
      if(title)node.title=title;
      div.append(node);
    }
    host.append(div);
  }
  function block(container,{title,rows,defaultOpen=false,language='ru',kind,limit=3}){
    if(!rows.length)return;
    const section=el('details','lwc-compact-section');section.open=defaultOpen;
    const summary=el('summary','lwc-compact-summary');summary.append(el('span',null,title),el('span','lwc-item-count',String(rows.length)));
    const contents=el('div','lwc-compact-body');
    const list=el('div','lwc-compact-list');
    function renderRows(expanded){
      list.replaceChildren();
      const shown=expanded?rows:rows.slice(0,limit);
      if(kind==='translations'){
        // A single readable list saves vertical space even with many sources;
        // the links below credit the contributing dictionaries collectively.
        const row=el('div','lwc-compact-item');
        row.append(el('div','lwc-translation-list',shown.map(item=>item.text).join('; ')));
        links(row,shown.flatMap(item=>item.sources||[]));list.append(row);
      }else{
        for(const item of shown){const row=el('div','lwc-compact-item');
          if(kind==='glosses'){
            row.append(el('div','lwc-gloss-english',item.text));
            if(item.detail)row.append(el('div','lwc-gloss-definition',item.detail));
          }else if(kind==='relations'){
            row.append(el('div','lwc-gloss-english',relationLabel(item.type,language)),el('div','lwc-definition-text',item.values.map(x=>x.text).join('; ')));
          }else if(kind==='examples'||kind==='context-expressions'){
            row.append(el('div','lwc-example-original',item.text));
            if(item.translation)row.append(el('div','lwc-example-translated',item.translation));
          }else row.append(el('div',kind==='articles'?'lwc-definition-text lwc-raw-article':'lwc-definition-text',item.text));
          links(row,item.sources||item.links||[],kind==='examples');list.append(row);
        }
      }
    }
    renderRows(false);contents.append(list);
    if(rows.length>limit){
      let expanded=false;
      const more=el('button','lwc-compact-more',`${label('further',language)} ${rows.length-limit}`);
      more.type='button';more.onclick=(event)=>{
        event.stopPropagation();expanded=!expanded;renderRows(expanded);
        more.textContent=expanded?label('less',language):`${label('further',language)} ${rows.length-limit}`;
      };contents.append(more);
    }
    section.append(summary,contents);container.append(section);
  }
  const REL_LABELS={"en":["Associations","Synonyms","Antonyms","Type of","Part of","Used for","Has a","Properties","At location","Causes","Derived from","Similar meaning","Other connections","Dictionary articles"],"ru":["Ассоциации","Синонимы","Антонимы","Разновидность","Часть","Используется для","Содержит","Свойства","Местонахождение","Причина","Происходит от","Близкие по смыслу","Другие связи","Словарные статьи"],"uk":["Асоціації","Синоніми","Антоніми","Різновид","Частина","Використовується для","Містить","Властивості","Місце","Причина","Походить від","Близькі за змістом","Інші зв’язки","Словникові статті"],"es":["Asociaciones","Sinónimos","Antónimos","Tipo de","Parte de","Se usa para","Contiene","Propiedades","Ubicación","Causa","Derivado de","Significado similar","Otras conexiones","Artículos del diccionario"],"de":["Assoziationen","Synonyme","Antonyme","Art von","Teil von","Verwendet für","Enthält","Eigenschaften","Ort","Verursacht","Abgeleitet von","Ähnliche Bedeutung","Weitere Verbindungen","Wörterbuchartikel"],"fr":["Associations","Synonymes","Antonymes","Type de","Partie de","Utilisé pour","Contient","Propriétés","Lieu","Cause","Dérivé de","Sens proche","Autres liens","Articles de dictionnaire"],"pt":["Associações","Sinônimos","Antônimos","Tipo de","Parte de","Usado para","Contém","Propriedades","Localização","Causa","Derivado de","Sentido semelhante","Outras conexões","Artigos de dicionário"],"zh":["关联词","同义词","反义词","类别","组成部分","用途","包含","属性","位置","原因","源自","近义","其他关联","词典条目"]};
  const REL_TYPES=['RelatedTo','Synonym','Antonym','IsA','PartOf','UsedFor','HasA','HasProperty','AtLocation','Causes','DerivedFrom','SimilarTo'];
  function relationLabel(type,lang){const i=REL_TYPES.indexOf(type);return (REL_LABELS[lang]||REL_LABELS.en)[i<0?12:i];}
  function render(container,data,options={}){
    const prepared=prepare(data);
    const lang=options.language||'ru';
    const t=key=>self.LWC_EXTRA_TEXT(key,lang);
    const previous=new Map([...container.querySelectorAll('details')].map(e=>[e.querySelector('summary span')?.textContent||'',e.open]));
    container.replaceChildren();
    // On Pages, show the first two meanings immediately (the extension has its
    // own primary translation heading). Keep their source attribution visible.
    const primary=prepared.translations.slice(0,options.primaryCount||0);
    if(primary.length){
      const main=el('div','lwc-main-translation');
      main.append(el('div','lwc-main-values',primary.map(x=>x.text).join('; ')));
      links(main,primary.flatMap(x=>x.sources));container.append(main);
    }else if(options.primaryCount&&prepared.translations.length===0){
      container.append(el('p','semantic-note',lang==='ru'?'Прямой перевод не найден.':'No direct translation found.'));
    }
    const other=prepared.translations.slice(primary.length);
    block(container,{title:t('other'),rows:other,kind:'translations',defaultOpen:true,language:lang,limit:4});
    const phraseLabels={en:'Phrase in context',ru:'Фраза в контексте',uk:'Фраза в контексті',es:'Frase en contexto',de:'Ausdruck im Kontext',fr:'Expression en contexte',pt:'Expressão no contexto',zh:'上下文短语'};
    block(container,{title:phraseLabels[lang]||phraseLabels.en,rows:prepared.contextExpressions,kind:'context-expressions',defaultOpen:true,language:lang,limit:2});
    // A separate explanation section keeps English glosses out of translations.
    block(container,{title:label('notes',lang),rows:prepared.glosses,kind:'glosses',defaultOpen:other.length===0,language:lang,limit:2});
    block(container,{title:t('meaning'),rows:prepared.definitions,kind:'definitions',defaultOpen:false,language:lang,limit:2});
    block(container,{title:t('examples'),rows:prepared.examples,kind:'examples',defaultOpen:false,language:lang,limit:1});
    block(container,{title:label('synonyms',lang),rows:prepared.synonyms,kind:'translations',language:lang,limit:4});
    const semantic={ru:'Связанные понятия',en:'Related concepts',uk:'Пов’язані поняття',es:'Conceptos relacionados',de:'Verwandte Begriffe',fr:'Concepts associés',pt:'Conceitos relacionados',zh:'相关概念'};
    block(container,{title:semantic[lang]||semantic.en,rows:prepared.relations,kind:'relations',language:lang,limit:3});
    block(container,{title:(REL_LABELS[lang]||REL_LABELS.en)[13],rows:prepared.articles,kind:'articles',language:lang,limit:1});
    if(prepared.wordnet){
      block(container,{title:label('wordnet',lang),rows:prepared.wordnet.definitions,kind:'definitions',defaultOpen:false,language:lang,limit:2});
      if(prepared.wordnet.synonyms.length){
        const synonyms=el('details','lwc-compact-section'),head=el('summary','lwc-compact-summary');
        head.append(el('span',null,label('synonyms',lang)),el('span','lwc-item-count',String(prepared.wordnet.synonyms.length)));
        const body=el('div','lwc-compact-body');body.append(el('div','lwc-translation-list',prepared.wordnet.synonyms.slice(0,12).join('; ')));
        if(prepared.wordnet.synonyms.length>12){const rest=el('button','lwc-compact-more',`${label('further',lang)} ${prepared.wordnet.synonyms.length-12}`);
          rest.type='button';rest.onclick=()=>{body.querySelector('.lwc-translation-list').textContent=prepared.wordnet.synonyms.join('; ');rest.remove();};body.append(rest);}
        links(body,[{source:'oewn',source_url:'https://en-word.net/'}]);synonyms.append(head,body);container.append(synonyms);
      }
    }
    for(const detail of container.querySelectorAll('details')){
      const heading=detail.querySelector('summary span')?.textContent||'';
      if(previous.has(heading))detail.open=previous.get(heading);
    }
    const hasContent=container.children.length>0;
    if(hasContent){
      const credit=el('a','lwc-dicts-credit',label('from',lang)+' · Dicts');
      credit.href='https://github.com/danilfg/dicts';credit.target='_blank';credit.rel='noopener noreferrer';
      container.append(credit);
    }
    return {hasContent,...prepared};
  }
  self.LWC_DICTIONARY_VIEW={prepare,render,separate,keyOf};
})();
