/* Structured, lossless presentation of already indexed dictionary articles.
   The parser never translates, rewrites or removes source meanings. */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  if(root)root.DictsEntryFormat=api;
})(typeof window!=="undefined"?window:null,function(){
"use strict";

const CYRILLIC=/[\u0400-\u052f]/;
const LATIN=/[A-Za-z]/;
const POS=/^(adjective|adverb|noun|verb|pronoun|preposition|conjunction|interjection|article|numeral|participle|adj\.?|adv\.?|prep\.?|pron\.?|conj\.?|interj\.?|n\.?|v\.?)(?=\s|$)/i;
const PHONETIC=/^\/[^/]{2,}\/(?:\s*[,;]?\s*\/[^/]+\/)*\s*$/;

function script(char){
  if(CYRILLIC.test(char))return "cyrillic";
  if(LATIN.test(char))return "latin";
  return "";
}
function languageScript(code){
  if(["ru","rus","uk","ukr","bg","bul","be","bel","sr","srp","mk","mkd"].includes(code))return "cyrillic";
  if(["en","eng","de","deu","es","spa","fr","fra","it","ita","pt","por","nl","nld"].includes(code))return "latin";
  return "";
}
function splitSourceAndTarget(line,from,to){
  const a=languageScript(from),b=languageScript(to);
  if(!a||!b||a===b)return null;
  let first=null,splitAt=-1,changeCount=0;
  for(let i=0;i<line.length;i++){
    const type=script(line[i]);
    if(!type)continue;
    if(!first)first=type;
    else if(type!==first){
      changeCount++;
      if(splitAt===-1)splitAt=i;
      first=type;
    }
  }
  if(changeCount!==1||splitAt<1)return null;
  const left=line.slice(0,splitAt).trim().replace(/\s*[—–-]\s*$/u,"").trim();
  const right=line.slice(splitAt).trim();
  const leftScript=script([...left].find(x=>script(x))||"");
  const rightScript=script([...right].find(x=>script(x))||"");
  if(!left||!right||leftScript===rightScript)return null;
  // Avoid splitting "HTTP-запрос": the ASCII portion is a technical acronym.
  const latinValue=leftScript==="latin"?left:right;
  if(/^[A-Z]{2,7}[-–—]?$/.test(latinValue))return null;
  const target=leftScript===b?left:right;
  const explanation=leftScript===a?left:right;
  if(!target||!explanation)return null;
  return {translation:target,explanation};
}
function parseLine(line,from,to){
  let text=String(line||"").trim();
  if(!text)return null;
  if(PHONETIC.test(text))return {kind:"phonetic",text};
  // Separate recurring part-of-speech headings from lexicographic senses.
  let part="";
  const match=text.match(POS);
  if(match){
    part=match[0].trim();
    text=text.slice(match[0].length).trim();
    if(!text)return {kind:"part",text:part};
  }
  let number="";
  const numbered=text.match(/^(\d{1,3})[.)]\s+/);
  if(numbered){number=numbered[1];text=text.slice(numbered[0].length).trim()}
  if(PHONETIC.test(text))return {kind:"phonetic",text,part,number};
  const split=splitSourceAndTarget(text,from,to);
  if(split)return {kind:"sense",number,part,...split};
  const a=languageScript(from),b=languageScript(to);
  const chars=[...text].filter(ch=>script(ch));
  const scriptFound=chars.length&&script(chars[0]);
  const kind=scriptFound===b&&a!==b?"translation":scriptFound===a&&a!==b?"explanation":"text";
  return {kind,number,part,text};
}
function parseEntry(input,from,to){
  const text=String(input||"").replace(/\r/g,"");
  const lines=text.split(/\n/).map(s=>s.trim()).filter(Boolean);
  return lines.map(line=>parseLine(line,from,to)).filter(Boolean);
}
const RUSSIAN_FORMS={
  entries:["запись","записи","записей"],
  meanings:["значение","значения","значений"],
  sourceCount:["источник","источника","источников"],
  examples:["пример","примера","примеров"]
};
const ENGLISH_FORMS={entries:["entry","entries"],meanings:["meaning","meanings"],sourceCount:["source","sources"],examples:["example","examples"]};
function formatCount(count,type,locale="en"){
  const n=Math.max(0,Math.trunc(Number(count)||0));
  if(locale==="ru"&&RUSSIAN_FORMS[type]){
    const forms=RUSSIAN_FORMS[type];
    const tail=n%10,tail2=n%100;
    const index=tail2>=11&&tail2<=14?2:tail===1?0:tail>=2&&tail<=4?1:2;
    return n+" "+forms[index];
  }
  const forms=ENGLISH_FORMS[type];
  return n+" "+(forms?(n===1?forms[0]:forms[1]):type);
}
function cleanCredit(value){
  if(value==null)return "";
  const text=String(value).trim();
  return /^(?:\\N|N\/A|NULL|NONE|UNKNOWN|-|—)?$/i.test(text)?"":text;
}
function phoneticVariants(input){
  const text=String(input||"").trim();
  if(!text)return [];
  const tokens=[...text.matchAll(/\/[^/\r\n]{2,140}\//gu)].map(m=>m[0]);
  if(!tokens.length)return [text];
  const residue=text.replace(/\/[^/\r\n]{2,140}\//gu,"").replace(/[\s,;|،、·]+/gu,"");
  if(residue)return [text];
  return [...new Set(tokens)];
}
return {parseEntry,parseLine,splitSourceAndTarget,languageScript,formatCount,cleanCredit,phoneticVariants};
});
