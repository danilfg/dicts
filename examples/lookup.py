#!/usr/bin/env python3
"""Reference client for normalized Dicts releases (Python 3.10+, standard library)."""
import argparse
import gzip
import hashlib
import json
import re
import shutil
import urllib.request
import zipfile
from pathlib import Path

BASE = "https://github.com/danilfg/dicts/releases/"
GROUPS = ("bilingual", "oewn", "omw", "conceptnet", "kaikki", "tatoeba")
TAG = re.compile(r"v\d{4}\.\d{2}\.\d{2}\.\d+\.\d+")
ASSET = re.compile(r"[A-Za-z0-9._-]+")


def digest_file(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for buf in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(buf)
    return h.hexdigest()


def verified(data, meta):
    if len(data) != meta["bytes"] or hashlib.sha256(data).hexdigest() != meta["sha256"]:
        raise ValueError("Checksum or length mismatch")
    return data


def normalize(word):
    return " ".join(word.casefold().strip().split())


def member_for(query, folder, buckets):
    n = hashlib.sha256(query.encode("utf-8")).digest()[0] % buckets
    return f"{folder}/{n:02x}.json.gz"


class Client:
    def __init__(self, cache, version=None):
        if version and not TAG.fullmatch(version):
            raise ValueError("Expected a calendar-versioned release tag")
        self.cache_root = Path(cache)
        if version and (self.cache_root / version / "LEXICAL-INDEX.json").is_file():
            master_bytes = (self.cache_root / version / "LEXICAL-INDEX.json").read_bytes()
        else:
            url = BASE + (f"download/{version}/" if version else "latest/download/") + "LEXICAL-INDEX.json"
            with urllib.request.urlopen(url, timeout=120) as stream:
                master_bytes = stream.read(4_000_001)
            if len(master_bytes) > 4_000_000:
                raise ValueError("Unexpectedly large master index")
        self.master = json.loads(master_bytes)
        tag = self.master["version"]
        if self.master["schema"] != 1 or self.master["format"] != "gzip-json-shards" or not TAG.fullmatch(tag):
            raise ValueError("Unsupported normalized release")
        if version and tag != version:
            raise ValueError("Unexpected release")
        self.base = BASE + f"download/{tag}/"
        if self.master["download_base"] != self.base:
            raise ValueError("Unexpected download origin")
        self.cache = self.cache_root / tag
        self.cache.mkdir(parents=True, exist_ok=True)
        (self.cache / "LEXICAL-INDEX.json").write_bytes(master_bytes)

    def fetch(self, name, meta):
        if not ASSET.fullmatch(name) or name in (".", ".."):
            raise ValueError("Unsafe asset name")
        target = self.cache / name
        if target.is_file() and target.stat().st_size == meta["bytes"] and digest_file(target) == meta["sha256"]:
            return target
        temporary = target.with_suffix(target.suffix + ".partial")
        try:
            with urllib.request.urlopen(self.base + name, timeout=180) as response, temporary.open("wb") as out:
                shutil.copyfileobj(response, out, 1024 * 1024)
            if temporary.stat().st_size != meta["bytes"] or digest_file(temporary) != meta["sha256"]:
                raise ValueError("Asset checksum mismatch: " + name)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        return target

    def group(self, name):
        meta = self.master["groups"][name]
        index = json.loads(self.fetch(meta["index"], meta).read_bytes())
        if index["schema"] != 1 or index["group"] != name:
            raise ValueError("Unexpected group index")
        return index

    def read_member(self, index, member):
        meta = index["members"][member]
        package = next(p for p in index["packages"] if p["name"] == meta["pack"])
        path = self.fetch(package["name"], package)
        with zipfile.ZipFile(path) as archive:
            data = verified(archive.read(member), meta)
        if member.endswith(".gz"):
            data = gzip.decompress(data)
        result = json.loads(data)
        if result["schema"] != 1:
            raise ValueError("Unsupported member schema")
        return result

    def lookup(self, query, group, pair=None, language=None):
        key = normalize(query)
        index = self.group(group)
        if group == "bilingual":
            catalog = self.read_member(index, "data/catalog.json")
            selected = next((x for x in catalog["pairs"] if x["pair"] == pair), None)
            if selected is None:
                return []
            path = member_for(key, "data/" + pair, selected["buckets"])
            shard = self.read_member(index, path)
            if shard["pair"] != pair:
                raise ValueError("Wrong pair")
            entry = shard["words"].get(key)
            if entry is None:
                return []
            return [{"pair": pair, "entry": entry, "provenance": catalog["provenance"].get(pair, {})}]
        catalog = self.read_member(index, f"data/lexical/{group}/catalog.json")
        results = []
        for desc in catalog["languages"]:
            if desc["language"] != language:
                continue
            path = member_for(key, desc["path"], desc["buckets"])
            shard = self.read_member(index, path)
            if shard["language"] != language or shard["source"] != group:
                raise ValueError("Wrong lexical shard")
            entry = shard["words"].get(key)
            if entry is not None:
                results.append({"source": group, "descriptor": desc, "entry": entry})
        return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("word")
    parser.add_argument("--group", choices=GROUPS, default="bilingual")
    parser.add_argument("--pair", default="en-ru")
    parser.add_argument("--language")
    parser.add_argument("--version")
    parser.add_argument("--cache", default=".dicts-cache")
    args = parser.parse_args()
    if args.group != "bilingual" and not args.language:
        parser.error("--language is required for lexical groups")
    client = Client(args.cache, args.version)
    result = client.lookup(args.word, args.group, args.pair, args.language)
    print(json.dumps({"version": client.master["version"], "query": normalize(args.word),
                      "results": result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
