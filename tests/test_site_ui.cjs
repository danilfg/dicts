const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const html=fs.readFileSync("site/index.html","utf8");
const js=fs.readFileSync("site/app.js","utf8");
const css=fs.readFileSync("site/styles.css","utf8");
test("navigation and source directory have unique matching DOM IDs",()=>{
 const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
 assert.equal(new Set(ids).size,ids.length);
 for(const id of ["translate-view","dictionary-view","source-grid","directory-version","directory-filter","about-link","sources-link","search-form","term","results","from","to","locale-btn"])assert.ok(ids.includes(id),id);
 assert.match(html,/href="#translate"/);assert.match(html,/href="#dictionaries"/);
 assert.match(js,/fetch\("\.\/data\/sources\.json"/);
 assert.match(js,/hashchange/);
});
test("compact styling and shared dictionary renderer",()=>{
 assert.match(css,/#101a2b/);assert.match(css,/#78e0b4/);
 assert.match(css,/\.dictionary-result \.lwc-compact-summary/);
 assert.match(js,/LWC_DICTIONARY_VIEW\.render/);
 assert.doesNotMatch(js,/function summaryCard|function addLexicalRecords/);
 assert.match(css,/\[hidden\]\{display:none!important\}/);
 const scripts=["entry-format","translation-utils","extra-ui","dictionary-view","result-model","app"];
 for(let i=1;i<scripts.length;i++)assert.ok(html.indexOf("./"+scripts[i-1]+".js")<html.indexOf("./"+scripts[i]+".js"));
});

const vm=require("node:vm");
const context=vm.createContext({});context.self=context;context.window=context;
for(const file of ["entry-format","translation-utils","extra-ui","dictionary-view","result-model"])
 vm.runInContext(fs.readFileSync("site/"+file+".js","utf8"),context,{filename:file+".js"});
const model=context.DictsResultModel,view=context.LWC_DICTIONARY_VIEW;
test("Pages merges dictionary sources and keeps semantic data out of translations",()=>{
 const data=model.adapt("en-ru",{
  translations:{koreader:["/ˈtest/\nпример, образец"],freedict:["пример; образчик"]},
  meanings:[{source:"kaikki",text:"A representative item."}],
  examples:[{source:"tatoeba",text:"An example.",translation:"Пример.",author:"alice",source_url:"https://tatoeba.org/en/sentences/show/1"}]
 },[
  {source:"oewn",entry:{definitions:["A representative item."],synonyms:["sample"]},meta:{license:"CC BY"}},
  {source:"omw",entry:{synonyms:["sample"]}},
  {source:"conceptnet",entry:[{word:"specimen",relation:"RelatedTo",language:"en"},{word:"проба",relation:"RelatedTo",language:"ru"},{word:"ejemplo",relation:"RelatedTo",language:"es"}]}
 ]);
 const prepared=view.prepare(data);
 assert.deepEqual(Array.from(prepared.translations,x=>x.text),["пример","образец","образчик"]);
 assert.equal(prepared.translations[0].sources.length,2);
 assert.equal(prepared.definitions.length,1);
 assert.equal(prepared.definitions[0].sources.length,2);
 assert.equal(prepared.synonyms.length,1);
 assert.equal(prepared.synonyms[0].sources.length,2);
 assert.equal(prepared.relations[0].values.length,2);
 assert.equal(prepared.examples.length,1);
 assert.ok(prepared.glosses.some(x=>x.text==="/ˈtest/"));
 assert.ok(prepared.articles.some(x=>x.text.includes("\n")));
 assert.equal(model.sourceCount(data),7);
});
test("same-script bilingual pairs and semantic-only entries are supported",()=>{
 const data=model.adapt("en-fr",{translations:{freedict:["prendre soin"]}});
 assert.equal(view.prepare(data).translations[0].text,"prendre soin");
 const semantic=view.prepare(model.adapt("en-ru",{},[{source:"oewn",entry:{definitions:["A sample"],synonyms:["specimen"]}}]));
 assert.equal(semantic.translations.length,0);assert.equal(semantic.synonyms.length,1);
});
test("duplicate sentence credits survive grouping",()=>{
 const prepared=view.prepare(model.adapt("en-ru",{examples:[
 {text:"Hello",translation:"Привет",source:"tatoeba",author:"Alice",source_url:"https://tatoeba.org/en/sentences/show/1"},
 {text:"Hello",translation:"Привет",source:"tatoeba",author:"Bob",source_url:"https://tatoeba.org/en/sentences/show/2"}
 ]}));
 assert.equal(prepared.examples.length,1);assert.equal(prepared.examples[0].links.length,2);
});
