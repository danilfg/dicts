"use strict";
const assert=require("node:assert/strict");
const {test}=require("node:test");
const parser=require("../site/entry-format.js");

test("KOReader: Russian translations and English definitions are separated",()=>{
 const actual=parser.parseLine("adj. 1. вдумчивый — Demonstrating thought or careful consideration.","en","ru");
 assert.equal(actual.kind,"sense");
 assert.equal(actual.part,"adj.");
 assert.equal(actual.number,"1");
 assert.equal(actual.translation,"вдумчивый");
 assert.equal(actual.explanation,"Demonstrating thought or careful consideration.");
});
test("FreeDict: an English gloss followed by a Russian translation",()=>{
 const a=parser.parseLine("Demonstrating kindness or consideration for others. внимательный","en","ru");
 assert.equal(a.kind,"sense");
 assert.equal(a.translation,"внимательный");
 assert.equal(a.explanation,"Demonstrating kindness or consideration for others.");
});
test("WikDict: Cyrillic list before English gloss",()=>{
 const a=parser.parseLine("заботливый, чуткий, внимательный — demonstrating kindness to others","en","ru");
 assert.equal(a.translation,"заботливый, чуткий, внимательный");
 assert.equal(a.explanation,"demonstrating kindness to others");
});
test("Reverse direction labels Cyrillic as explanation",()=>{
 const a=parser.parseLine("ответственный responsible","ru","en");
 assert.equal(a.kind,"sense");
 assert.equal(a.translation,"responsible");
 assert.equal(a.explanation,"ответственный");
});
test("IPA transcription and separate part of speech",()=>{
 const a=parser.parseEntry("/ˈθɔːtfəl/\nadjective\nвдумчивый","en","ru");
 assert.equal(a[0].kind,"phonetic");
 assert.equal(a[1].kind,"part");
 assert.equal(a[2].kind,"translation");
});
test("Single-language dictionaries are preserved without artificial translation",()=>{
 const a=parser.parseLine("Demonstrating thought or careful consideration.","en","de");
 assert.equal(a.kind,"text");
 assert.equal(a.text,"Demonstrating thought or careful consideration.");
});
test("Technical acronyms are not treated as English explanations",()=>{
 const a=parser.parseLine("HTTP-запрос","en","ru");
 assert.notEqual(a.kind,"sense");
 assert.equal(a.text,"HTTP-запрос");
});
test("Full entries keep original text and line count",()=>{
 const a=parser.parseEntry("adjective\n\nDemonstrating thought. вдумчивый\nчуткий","en","ru");
 assert.equal(a.length,3);
 assert.equal(a[1].kind,"sense");
 assert.equal(a[2].text,"чуткий");
});
test("No HTML is interpreted during parsing",()=>{
 const result=parser.parseLine("<script>alert(1)</script> вдумчивый","en","ru");
 assert.equal(result.kind,"sense");
 assert.match(result.explanation,/script/);
});
