/* Vendored from danilfg/translator at 763220cb2cfa532c328fa1b5adb0897fd96dcd18.
   Keep the presentation logic aligned with that repository. */
/* Safe, concise dictionary display. Never use innerHTML with dictionary text. */
(() => {
  'use strict';
  const named={nbsp:' ',amp:'&',lt:'<',gt:'>',quot:'"',apos:"'",mdash:'—',ndash:'–',hellip:'…',bull:'•',middot:'·',lsquo:'‘',rsquo:'’',ldquo:'“',rdquo:'”',laquo:'«',raquo:'»',times:'×',trade:'™',copy:'©',reg:'®',shy:'',thinsp:' ',ensp:' ',emsp:' '};
  function decode(value){
    let result=String(value??'');
    for(let pass=0;pass<2;pass++){
      result=result.replace(/&(?:#(x[0-9a-f]+|\d+)|([a-z][a-z0-9]{1,12}));?/gi,(match,number,word)=>{
        if(number){const code=number[0].toLowerCase()==='x'?parseInt(number.slice(1),16):Number(number);return Number.isInteger(code)&&code>0&&code<=0x10ffff&&!(code>=0xd800&&code<=0xdfff)?String.fromCodePoint(code):'�';}
        return Object.prototype.hasOwnProperty.call(named,word.toLowerCase())?named[word.toLowerCase()]:match;
      });
    }
    return result;
  }
  // Schema 1 contains readable articles, not guaranteed individual translations.
  // Keep uncertain material as a note; never split ordinary multiword phrases on spaces.
  const cyr=new Set(['ru','uk','be','bg','mk','sr','kk','ky','tg','mn','ba','ce']);
  const latin=new Set(['en','es','de','fr','pt','it','nl','sv','no','da','fi','pl','cs','sk','sl','hr','ro','hu','tr','vi','id','af','eo','ca','eu','gl','et','lv','lt']);
  const scripts={ar:/\p{Script=Arabic}/u,fa:/\p{Script=Arabic}/u,ur:/\p{Script=Arabic}/u,he:/\p{Script=Hebrew}/u,el:/\p{Script=Greek}/u,zh:/\p{Script=Han}/u,ja:/[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}]/u,ko:/\p{Script=Hangul}/u,hi:/\p{Script=Devanagari}/u};
  const script=lang=>cyr.has(lang)?/\p{Script=Cyrillic}/u:latin.has(lang)?/\p{Script=Latin}/u:scripts[lang];
  const k=v=>String(v).normalize('NFC').replace(/\u0301/g,'').toLocaleLowerCase().replace(/\s+/g,' ').trim();
  function article(raw,pair='en-ru'){
    const [from,to]=String(pair).split('-'),src=script(from),dst=script(to);
    const cross=src&&dst&&src.source!==dst.source;
    const values=[],notes=[],uncertain=[];
    function add(arr,v){v=String(v||'').trim().replace(/^[,;:.\s]+|[,;:\s]+$/g,'').trim();if(v&&!arr.some(x=>k(x)===k(v)))arr.push(v);}
    const readable=decode(raw).replace(/<br\s*\/?>|<\/(?:p|div|li|tr|dd|dt)>/gi,'; ').replace(/<[^>]*>/g,' ').replace(/[\r\n]+/g,'; ').replace(/[\u0000-\u001f]+/g,' ').replace(/\s+/g,' ').trim();
    if(!readable)return {values,notes,uncertain};
    let s=readable.replace(/\[[^\]]{1,180}\]/gu,' ').replace(/(?:^|\s)\/[^/]{1,100}\/(?=\s|$)/gu,' ').replace(/>>.*$/,'').trim();
    const strip=v=>v.replace(/^(?:(?:\d+[.)]\s*|(?:adj(?:ective)?|adv(?:erb)?|noun|verb|n|v|prep|pron|interj(?:ection)?|conj(?:unction)?|phrase|exclamation|idiom)\b\.?\s*(?:\([^)]{1,90}\)\s*)?))+/i,'').trim();
    for(let part of s.split(/\s*[;|]\s*|\s+\/\s+/u).filter(Boolean)){
      part=strip(part).trim();if(!part)continue;
      const dash=part.match(/^(.+?)\s+[—–]\s+(.+)$/u);
      if(dash&&((cross&&dst.test(dash[1])&&!dst.test(dash[2])&&src.test(dash[2]))||(!cross&&dash[2].split(/\s+/).length>=6))){add(notes,dash[2]);part=dash[1];}
      if(cross){
        if(!dst.test(part)){
          if(/^[A-Z0-9][A-Z0-9.+-]{1,11}$/u.test(part))add(values,part);
          else add(notes,part);
          continue;
        }
        // Script transitions are clear in e.g. English/Russian. Preserve all
        // target-language phrases; source-language runs become explanations.
        if(src.test(part)){
          let runs=[],current='',kind=null;
          for(const ch of part){const t=dst.test(ch)?'target':src.test(ch)?'source':null;if(t&&kind&&t!==kind){runs.push({kind,text:current});current='';}if(t)kind=t;current+=ch;}
          if(current)runs.push({kind,text:current});
          for(const run of runs){let value=strip(run.text.trim());if(run.kind==='target'){for(const v of value.split(/\s*,\s*/)){const piece=v.replace(/^[\s/—–]+|[\s/—–.]+$/g,'').trim();if(piece.length>140||piece.split(/\s+/).length>15)add(uncertain,piece);else add(values,piece);}}
            else{value=value.replace(/^[\s/—–.,]+|[\s/—–]+$/g,'');if(value&&/[\p{L}]{2}/u.test(value))add(notes,value);}}
          continue;
        }
      }
      // Commas are useful separators in short enumerations for differing
      // scripts; long or sentence-like source articles stay outside translation.
      if(part.length>140||part.split(/\s+/).length>15||(!cross&&/[.!?]\s+\p{Lu}/u.test(part))){add(uncertain,part);continue;}
      for(const v of (cross?part.split(/\s*,\s*/):[part]))add(values,v.replace(/^[\s/—–]+|[\s/—–]+$/g,''));
    }
    // If a flattened repeat consists entirely of already-known complete
    // phrases, drop only that repeat, not a novel multiword translation.
    const compact=values.filter(v=>{
      const tokens=k(v).split(' ');if(tokens.length<2)return true;
      const candidates=values.filter(x=>k(x)!==k(v)).map(x=>k(x).split(' ')).sort((a,b)=>b.length-a.length);
      let i=0,n=0;while(i<tokens.length){const match=candidates.find(c=>c.every((w,j)=>tokens[i+j]===w));if(!match)return true;i+=match.length;n++;}return n<2;
    });
    if(!compact.length&&!notes.length&&!uncertain.length)add(uncertain,readable);
    return {values:compact,notes,uncertain};
  }
  function clean(raw,pair='en-ru'){
    const parts=article(raw,pair).values;
    const s=parts.slice(0,2).join('; ');
    return s.length>150?s.slice(0,147).trim()+'…':s;
  }
  // Consolidate identical meanings while retaining all source attributions.
  // Note: input may be old cards with a single source or new grouped records.
  function uniqueAlternatives(items,pair='en-ru'){
    const groups=new Map();
    for(const entry of Array.isArray(items)?items:[]){
      const text=clean(entry?.text||'',pair);
      if(!text)continue;
      const key=text.normalize('NFKC').toLocaleLowerCase()
        .replace(/[.,;:|\u2013\u2014]+/gu,' ').replace(/\s+/gu,' ').trim();
      if(!key)continue;
      if(!groups.has(key))groups.set(key,{text,sources:[]});
      const group=groups.get(key);
      const providers=Array.isArray(entry.sources)&&entry.sources.length?entry.sources:[entry];
      for(const provider of providers){
        const source=String(provider?.source||entry?.source||'').toLowerCase();
        const url=String(provider?.source_url||entry?.source_url||'');
        if(!source)continue;
        if(!group.sources.some(v=>v.source===source))group.sources.push({source,source_url:/^https:\/\//.test(url)?url:''});
      }
    }
    return [...groups.values()];
  }
  self.YWA_TRANSLATION={clean,decode,article,uniqueAlternatives};
})();
