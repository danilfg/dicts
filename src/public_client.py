"""Anonymous, verified GHCR downloads for applications (stdlib only)."""
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache

REGISTRY="ghcr.io/danilfg/dicts-data"
MAX_BLOCK=32*1024*1024

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected=super().redirect_request(req,fp,code,msg,headers,newurl)
        if redirected and urllib.parse.urlsplit(newurl).netloc!=urllib.parse.urlsplit(req.full_url).netloc:
            redirected.remove_header("Authorization")
        if urllib.parse.urlsplit(newurl).scheme!="https":
            raise ValueError("Refusing insecure redirect")
        return redirected

OPENER=urllib.request.build_opener(SafeRedirect())

@lru_cache(maxsize=1)
def anonymous_token():
    query=urllib.parse.urlencode({"service":"ghcr.io","scope":"repository:danilfg/dicts-data:pull"})
    url="https://ghcr.io/token?"+query
    with OPENER.open(url,timeout=30) as r:
        return json.load(r)["token"]

def public_blob(registry,block):
    if registry!=REGISTRY or not re.fullmatch(r"[0-9a-f]{64}",block["sha256"]) or not 0<block["bytes"]<=MAX_BLOCK:
        raise ValueError("Invalid OCI descriptor")
    url="https://ghcr.io/v2/danilfg/dicts-data/blobs/sha256:"+block["sha256"]
    for attempt in range(2):
        req=urllib.request.Request(url,headers={"Authorization":"Bearer "+anonymous_token()})
        try:
            with OPENER.open(req,timeout=180) as r:data=r.read(block["bytes"]+1)
            break
        except urllib.error.HTTPError as exc:
            if exc.code!=401 or attempt:raise
            anonymous_token.cache_clear()
    if len(data)!=block["bytes"] or hashlib.sha256(data).hexdigest()!=block["sha256"]:
        raise ValueError("OCI blob integrity mismatch")
    return data
