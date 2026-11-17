"""Use authoritative validators only; otherwise fetch and verify source bytes."""
import urllib.error
import urllib.request

def strong_etag(value):
    return isinstance(value,str) and value.startswith('"') and value.endswith('"')

def request(url,user_agent,previous_etag=None,timeout=180):
    headers={"User-Agent":user_agent}
    if strong_etag(previous_etag):
        headers["If-None-Match"]=previous_etag
    try:
        return urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=timeout)
    except urllib.error.HTTPError as exc:
        if exc.code==304 and strong_etag(previous_etag):
            exc.close()
            return None
        raise

def matching_digest(old,upstream):
    digest=upstream.get("digest") or ""
    if not digest.startswith("sha256:"):return False
    return old.get("size",old.get("bytes"))==upstream.get("size") and old.get("digest","sha256:"+old.get("sha256",""))==digest
