#!/usr/bin/env python3
"""Republish the static Dicts UI using already published Pages search shards.

Avoids rebuilding 1.8GB of ZIP dictionaries and avoids GitHub REST API rate
limits on every CSS, translation, or client-side rendering change.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import pathlib
import time
import urllib.error
import urllib.request

DEFAULT_BASE = "https://danilfg.github.io/dicts/data/"
MAX_SHARD_SIZE = 50_000_000

def get_bytes(url: str, cap: int) -> bytes:
    headers = {"User-Agent": "danilfg-dicts-pages-ui/1.0", "Accept-Encoding": "identity"}
    for attempt in range(4):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=90) as response:
                data = response.read(cap + 1)
                if len(data) > cap:
                    raise ValueError(f"Published asset exceeds size limit: {url}")
                if not data:
                    raise ValueError(f"Empty published asset: {url}")
                return data
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == 3:
                raise
            time.sleep(1 + attempt * 2)
    raise AssertionError("Unreachable")

def copy_existing_index(target: pathlib.Path, base: str = DEFAULT_BASE) -> dict:
    base = base.rstrip("/") + "/"
    catalog = json.loads(get_bytes(base + "catalog.json", 10_000_000))
    if catalog.get("schema") != 1 or not isinstance(catalog.get("pairs"), list):
        raise ValueError("Live Pages catalog missing schema/pairs")
    pairs = catalog["pairs"]
    if not pairs or len(pairs) > 1500:
        raise ValueError("Unexpected number of indexed language pairs")
    data_dir = target / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )

    tasks = []
    for pair in pairs:
        name = pair.get("pair")
        bucket_count = pair.get("buckets")
        if (not isinstance(name, str) or not name.replace("-", "").isalnum()
                or not isinstance(bucket_count, int) or bucket_count not in (1, 4, 16, 32)):
            raise ValueError(f"Invalid catalog pair/bucket entry: {pair}")
        for index in range(bucket_count):
            path = f"{name}/{index:02x}.json.gz"
            tasks.append((name, path))

    def fetch(item: tuple[str, str]) -> tuple[str, int]:
        name, relative = item
        payload = get_bytes(base + relative, MAX_SHARD_SIZE)
        if payload[:2] != b"\x1f\x8b":
            raise ValueError("Published search index is not gzip: " + relative)
        output = data_dir / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(payload)
        return name, len(payload)

    totals: dict[str, int] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for pair, size in pool.map(fetch, tasks):
            totals[pair] = totals.get(pair, 0) + size

    for item in pairs:
        expected = item.get("compressed_bytes")
        actual = totals.get(item["pair"])
        if actual != expected:
            raise ValueError(
                f"Search index incomplete for {item['pair']}: {actual} bytes, expected {expected}"
            )
    print(
        f"Copied existing published search index: {len(pairs)} language pairs, "
        f"{len(tasks)} shards, {sum(totals.values()):,} bytes; no GitHub API requests",
        flush=True,
    )
    return catalog

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-dir", default="site")
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    args = parser.parse_args()
    copy_existing_index(pathlib.Path(args.site_dir), args.base_url)

if __name__ == "__main__":
    main()
