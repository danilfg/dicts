// Chrome MV3 service-worker reference; use host_permissions for github.com,
// ghcr.io, release-assets.githubusercontent.com and *.githubusercontent.com.
// Store verified blocks in IndexedDB keyed by SHA-256 (not by release tag).
const ROOT = 'https://github.com/danilfg/dicts/releases/';
const REGISTRY = 'ghcr.io/danilfg/dicts-data';
const te = new TextDecoder();
const get = async (url, init) => {
  const r = await fetch(url, init);
  if (!r.ok) throw Error('HTTP ' + r.status);
  return r;
};
async function verified(buffer, meta) {
  if (buffer.byteLength !== meta.bytes) throw Error('Wrong size');
  const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256',buffer))]
    .map(n => n.toString(16).padStart(2,'0')).join('');
  if (hash !== meta.sha256) throw Error('Wrong SHA-256');
  return buffer;
}
export async function catalog(version) {
  if (version && !/^v\d{4}\.\d{2}\.\d{2}\.\d+\.\d+$/.test(version)) throw Error('Invalid tag');
  const m = await (await get(ROOT + (version ? 'download/'+version+'/' : 'latest/download/') + 'LEXICAL-INDEX.json')).json();
  const base = ROOT+'download/'+m.version+'/';
  if (m.schema !== 1 || m.format !== 'oci-pair-v1' || m.registry !== REGISTRY ||
      !/^v\d{4}\.\d{2}\.\d{2}\.\d+\.\d+$/.test(m.version) ||
      (version && m.version !== version) || m.download_base !== base) throw Error('Unsupported catalog');
  const raw = await (await get(base+'PAIR-INDEX.json')).arrayBuffer();
  const c = JSON.parse(te.decode(await verified(raw,m.pair_index)));
  if (c.schema !== 1 || c.format !== m.format || c.registry !== REGISTRY || c.version !== m.version) throw Error('Wrong catalog');
  return c;
}
export function select(c,pair) {
  const p=c.pairs[pair];
  if (!p) throw Error('Unknown direction');
  const out=[];
  for (const [group,g] of Object.entries(c.groups)) {
    if (g.pairs[pair]) out.push({group,scope:'pairs',id:pair,blocks:g.pairs[pair]});
    for (const lang of new Set([p.from,p.to]))
      if (g.languages[lang]) out.push({group,scope:'languages',id:lang,blocks:g.languages[lang]});
  }
  return out;
}
async function token() {
  const url='https://ghcr.io/token?service=ghcr.io&scope='+encodeURIComponent('repository:danilfg/dicts-data:pull');
  return (await (await get(url)).json()).token;
}
export async function install(c,pair,cache) {
  // cache implements async get(hex) and put(hex, ArrayBuffer), backed by IndexedDB.
  const selected=select(c,pair);
  let auth;
  for (const unit of selected) for (const b of unit.blocks) {
    if (!/^[a-f0-9]{64}$/.test(b.sha256) || b.bytes<1 || b.bytes>32*1024*1024) throw Error('Bad block');
    const existing=await cache.get(b.sha256);
    if (existing) {
      try { await verified(existing,b); continue; } catch { /* refetch corrupted block */ }
    }
    auth ||= await token();
    const url='https://ghcr.io/v2/danilfg/dicts-data/blobs/sha256:'+b.sha256;
    let response=await fetch(url,{headers:{Authorization:'Bearer '+auth}});
    if (response.status===401) {
      auth=await token();
      response=await fetch(url,{headers:{Authorization:'Bearer '+auth}});
    }
    if (!response.ok) throw Error('Blob HTTP '+response.status);
    await cache.put(b.sha256,await verified(await response.arrayBuffer(),b));
  }
  return {version:c.version,pair,units:selected};
}
// Read blocks using a ZIP library that supports ZIP_STORED, then GZIP
// decompress selected JSON members. Respect UNIT.json and the schema docs.
// Use a Unicode casefold implementation, not JS toLowerCase() for all scripts.
