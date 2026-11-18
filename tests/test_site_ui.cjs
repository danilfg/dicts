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
test("compact styling and full article expansion",()=>{
 assert.match(css,/#101a2b/);assert.match(css,/#78e0b4/);
 assert.match(js,/index<5\?article:rest/);
 assert.match(js,/article-more/);
 assert.match(css,/\[hidden\]\{display:none!important\}/);
});
