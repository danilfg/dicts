"""Compare source data, ignoring generated manifests and packaging timestamps."""
import hashlib
import subprocess
import tempfile
import zipfile
from pathlib import Path

ZIP_PREFIXES = ("koreader--", "freedict--", "wikdict--")
SOURCE_PREFIXES = ("kaikki--", "tatoeba--", "oewn--", "omw--", "conceptnet--")
METADATA_SUFFIXES = ("--SOURCE-MANIFEST.json", "--LEXICAL-MANIFEST.json",
                     "--THIRD-PARTY-LEXICAL-NOTICES.md")

def source_assets(assets):
    return {name: item for name, item in assets.items()
            if ((name.startswith(ZIP_PREFIXES) and name.endswith(".zip"))
                or (name.startswith(SOURCE_PREFIXES) and not name.endswith(METADATA_SUFFIXES)))}

def diff_plan(previous, candidate):
    old, new = source_assets(previous), source_assets(candidate)
    changes = set(old) ^ set(new)
    repacked = []
    for name in sorted(set(old) & set(new)):
        if old[name]["digest"] == new[name]["digest"]:
            continue
        if name.startswith(ZIP_PREFIXES):
            repacked.append(name)
        else:
            changes.add(name)
    return sorted(changes), repacked

def zip_fingerprint(path):
    files = {}
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            if info.filename in files:
                raise ValueError("Duplicate member in " + str(path))
            h = hashlib.sha256()
            with archive.open(info) as stream:
                while chunk := stream.read(1024 * 1024):
                    h.update(chunk)
            files[info.filename] = h.hexdigest()
    return files

def confirm_zip_changes(previous_tag, candidate_tag, names, repo):
    for start in range(0, len(names), 25):
        batch = names[start:start + 25]
        with tempfile.TemporaryDirectory() as tmp:
            old, new = Path(tmp)/"old", Path(tmp)/"new"
            for tag, folder in ((previous_tag, old), (candidate_tag, new)):
                folder.mkdir()
                args = ["gh", "release", "download", tag, "-R", repo, "--dir", str(folder)]
                for name in batch:
                    args.extend(["--pattern", name])
                subprocess.run(args, check=True)
            changed = [name for name in batch
                       if zip_fingerprint(old/name) != zip_fingerprint(new/name)]
            if changed:
                return changed
        print(f"Compared repacked dictionaries: {min(start+25,len(names))}/{len(names)}", flush=True)
    return []
