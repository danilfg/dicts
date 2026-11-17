# Normalized dictionary format — developer reference (schema 1)

The [monthly update workflow](../.github/workflows/update.yml) builds application-ready lookup data and publishes it with the original source archives. Applications do not need a StarDict, WN-LMF or ConceptNet parser.

**Availability:** the new format is usable after the first successful release containing [LEXICAL-INDEX.json](https://github.com/danilfg/dicts/releases/latest/download/LEXICAL-INDEX.json). Older releases do not have this index. The examples on this page are synthetic schema illustrations, not verified upstream translations, corpus records, identifiers or author names.

## Normalization pipeline

1. Discover upstream datasets. Use authoritative hashes and strong HTTP ETags where available; otherwise download data to compare.
2. Reuse verified previous files when an upstream is unreachable; report failures in release notes and `REFRESH-REPORT.json`.
3. Compare source contents, including ZIP members, ignoring packaging timestamps. After the first format upgrade, unchanged sources alone do not trigger a release.
4. Parse original files, preserve source attribution and separate bilingual articles, definitions, examples and semantic relations.
5. Write UTF-8 JSON shards compressed with gzip. Group shards into ZIP assets, each below 1.4 GB, and record SHA-256 and sizes.
6. Verify source and normalized inventories; publish a dated immutable version. Deploy the prepared compact Pages indexes.

Implementation: [bilingual conversion](../src/build_pages.py), [lexical/corpus conversion](../src/normalize_sources.py), [packaging](../src/normalized_pack.py), [release comparison](../src/release_plan.py), [validation](../src/unified_release.py).

## Source coverage

| Source | Input | Normalized group and output |
|---|---|---|
| KOReader | StarDict ZIP | `bilingual`: source-separated original readable articles |
| FreeDict | StarDict / TEI source | `bilingual`: articles; original TEI rights retained |
| WikDict | StarDict ZIP | `bilingual`: articles |
| Kaikki / Wiktionary | JSONL.GZ | `kaikki`: definitions, translations, parts of speech |
| Tatoeba | BZ2 / TAR.BZ2 | `tatoeba`: attributed sentences and linked translations |
| Open English WordNet | WN-LMF XML -> English JSON | `oewn`: definitions, synonyms |
| Open Multilingual Wordnet | WN-LMF TAR.XZ | `omw`: definitions, synonyms, synset IDs, ILI and POS |
| ConceptNet | Assertions CSV.GZ | `conceptnet`: typed semantic edges, language, weight and provenance |

The `pages` and `pages-lexical` groups are separate compact website indexes. They are not the full application indexes.

Bilingual articles retain readable text (including semicolons and line breaks) but are not guaranteed to be structured into individual senses, grammar, pronunciation or idioms. Do not split article strings indiscriminately. Original markup and fields not parsed remain in the original source archives. WordNet/ConceptNet records must not be rendered as literal translations.

## Release layout

```text
LEXICAL-INDEX.json
REFRESH-REPORT.json
RELEASE-MANIFEST.json
SHA256SUMS.txt
normalized--bilingual-index.json
normalized--bilingual-001.zip
normalized--bilingual-002.zip      # if needed
normalized--oewn-index.json
normalized--oewn-001.zip
normalized--omw-index.json
normalized--omw-001.zip
normalized--conceptnet-index.json
normalized--conceptnet-001.zip
normalized--kaikki-index.json
normalized--kaikki-001.zip
normalized--tatoeba-index.json
normalized--tatoeba-001.zip
normalized--pages-index.json
normalized--pages-lexical-index.json
... other packages and original source assets
```

Names and part counts are illustrative: always discover actual pack names from the indexes.

The master index has `schema` (integer 1), `version` (release tag), `format` (`gzip-json-shards`), `download_base` (the **pinned release** URL ending in a slash) and `groups` (object keyed by group). Each group descriptor contains `index`, `bytes` and `sha256`.

Each group index has this shape (values such as sizes and hashes are illustrative placeholders):

```json
{
  "schema": 1,
  "group": "bilingual",
  "packages": [
    {
      "name": "normalized--bilingual-001.zip",
      "bytes": 123456,
      "sha256": "<64 lowercase hex characters>"
    }
  ],
  "members": {
    "data/catalog.json": {
      "pack": "normalized--bilingual-001.zip",
      "bytes": 1234,
      "sha256": "<64 lowercase hex characters>"
    },
    "data/en-ru/00.json.gz": {
      "pack": "normalized--bilingual-001.zip",
      "bytes": 5678,
      "sha256": "<64 lowercase hex characters>"
    }
  }
}
```

SHA-256 values are calculated over the exact file bytes, including compressed
bytes for GZIP members. Download a group index from the pinned release URL,
verify its hash and size from the master index, then verify ZIPs and members.
A member may be in any listed ZIP. Do not assume that one ZIP contains an entire language.

### Catalogs and shard selection

- `bilingual` / `pages`: `data/catalog.json` lists `pairs` with fields
  `pair`, `from`, `to`, `entries`, `sources`, `buckets`, `compressed_bytes`.
  `provenance[pair][source]` carries download/source URLs, license and attribution.
  Shards: `data/PAIR/NN.json.gz`.
- `oewn`, `omw`, `conceptnet`, `kaikki`, `tatoeba`:
  `data/lexical/GROUP/catalog.json` lists `languages`. Each descriptor includes
  `language`, `package` (string or null), `path`, `entries`, `buckets`.
  OMW also has `rights` with the per-package license and citation. A language
  may have several descriptors (OMW lexicons or Kaikki editions). Use every
  desired descriptor, not just the first. Shards: `PATH/NN.json.gz`.
- `pages-lexical`: `data/lexical/catalog.json` with `sources` keyed by
  `oewn`, `omw`, `conceptnet`; each source has `languages` descriptors
  and metadata. This legacy website view has a different ConceptNet entry
  shape (an array of relations rather than an object). Application clients
  should prefer the full source groups.

Language codes come from the catalogs. Some two- and three-letter codes
coexist; do not assume all codes are ISO 639-1 or collapse distinct languages
without consulting the data. `en-ru` and `ru-en` are independent directions.

The exact shard algorithm is [in the builder](../src/build_pages.py):
normalize the query using Python Unicode `casefold()`, strip and collapse
whitespace with a single ASCII space; compute SHA-256 of UTF-8; use the first
digest byte modulo the advertised bucket count. Format that number as two
lowercase hexadecimal digits. Bucket counts are data-driven (bilingual:
1/4/16/32; full lexical groups: 4/32/128). Do not hardcode the count.
JavaScript's `toLowerCase()` is not identical to Unicode casefold for all
languages; use a compatible Unicode case-fold implementation.

```python
import hashlib
key = " ".join(query.casefold().strip().split())
bucket = hashlib.sha256(key.encode("utf-8")).digest()[0] % buckets
filename = f"{bucket:02x}.json.gz"
```

Read the GZIP member as UTF-8 JSON and access `words[key]`. A missing key is
a normal not-found result, not an error. There is no stemming or fuzzy search
in this format.

## Record examples

All examples show the **decompressed** JSON. The values are synthetic.
Each shard normally contains many words.

### KOReader, FreeDict and WikDict — bilingual

```json
{
  "schema": 1,
  "pair": "en-ru",
  "words": {
    "car": {
      "translations": {
        "koreader": ["автомобиль; машина"],
        "freedict": ["автомобиль"],
        "wikdict": ["машина"]
      },
      "meanings": [],
      "examples": []
    }
  }
}
```

`translations` is an object keyed by source, with arrays of article strings,
not necessarily independently parsed translations. A source may be missing
for a word. Keep each source separate and resolve licensing through the catalog
and original source package. `meanings` and `examples` contain legacy compact
study records from Kaikki/Tatoeba when available, not WordNet or ConceptNet.

### Kaikki / Wiktionary

```json
{
  "schema": 1,
  "source": "kaikki",
  "language": "en",
  "words": {
    "car": {
      "definitions": ["A road vehicle."],
      "translations": [
        {"text": "автомобиль", "language": "ru"},
        {"text": "coche", "language": "es"}
      ],
      "parts_of_speech": ["noun"],
      "source_url": "https://en.wiktionary.org/wiki/car",
      "license": "CC BY-SA 4.0; exceptions may apply"
    }
  }
}
```

The compact index has up to 10,000 terms per language per edition,
approximately 200,000 per edition, 8 definitions and 20 translations per
term. Use the package/edition descriptor when selecting a shard. Full
Wiktionary exports are retained separately. Idioms can appear as headwords;
there is no separate guaranteed idiom or phrasal-verb field in schema 1.

### Tatoeba

```json
{
  "schema": 1,
  "source": "tatoeba",
  "language": "en",
  "words": {
    "car": {
      "examples": [
        {
          "text": "I have a car.",
          "language": "en",
          "author": "<source author>",
          "translations": [
            {
              "text": "У меня есть машина.",
              "language": "ru",
              "author": "<translation author>",
              "source_url": "https://tatoeba.org/en/sentences/show/<id>",
              "license": "CC BY 2.0 FR"
            }
          ],
          "source_url": "https://tatoeba.org/en/sentences/show/<id>",
          "license": "CC BY 2.0 FR"
        }
      ]
    }
  }
}
```

The compact index selects up to 5,000 attributed sentences per language,
3 examples per term and 4 linked translations per sentence. A sentence may
have no selected translation. The source URL carries the sentence ID.
Preserve both original and translation authors; inspect original source terms
for individual CC0 records and other rights.

### Open English WordNet (OEWN)

```json
{
  "schema": 1,
  "source": "oewn",
  "language": "en",
  "words": {
    "car": {
      "definitions": ["A motor vehicle."],
      "synonyms": ["automobile", "auto"]
    }
  }
}
```

The full OEWN lookup group provides definitions and synonyms. The original
English intermediate `lexicon--oewn-en.json.gz` additionally contains selected
relations. Preserve OEWN and Princeton WordNet attribution.

### Open Multilingual Wordnet (OMW)

```json
{
  "schema": 1,
  "source": "omw",
  "language": "es",
  "words": {
    "coche": {
      "definitions": ["Vehículo de motor."],
      "synonyms": ["automóvil"],
      "synsets": [
        {
          "id": "<original synset id>",
          "ili": "<original interlingual index id>",
          "pos": "n",
          "definitions": ["Vehículo de motor."]
        }
      ]
    }
  }
}
```

Original synset IDs and ILI are kept where available. `ili` and `pos` can
be null. Same ILI across languages indicates a shared lexical concept,
not guaranteed literal translation. Schema 1 does not yet provide a
global reverse ILI index. Use per-package rights in the OMW catalog.

### ConceptNet

```json
{
  "schema": 1,
  "source": "conceptnet",
  "language": "en",
  "words": {
    "car": {
      "relations": [
        {
          "relation": "RelatedTo",
          "word": "road",
          "language": "en",
          "license": "cc:by-sa/4.0",
          "dataset": "<original dataset URI>",
          "uri": "<original assertion URI>",
          "weight": 2.0
        }
      ]
    }
  }
}
```

Relations include selected types such as Synonym, Antonym, RelatedTo, IsA,
PartOf and UsedFor. Only selected edges with source license metadata are
included: up to 100,000 terms per language and 12 relations per term.
The target language may differ from the source language. `dataset` may
be null. Do not present semantic edges as literal translations.

## Using the data in your application

The reference client [examples/lookup.py](../examples/lookup.py) uses only the
Python standard library. It downloads the master index once, pins the
release URL, verifies the group index/required ZIPs/selected members and
prints matching records. Downloads are cached under a version-specific
directory. The first download can be large because even one word may require
a grouped ZIP. Subsequent lookups work from the local cached ZIPs.

```bash
python examples/lookup.py car --pair en-ru
python examples/lookup.py car --group oewn --language en
python examples/lookup.py coche --group omw --language es
python examples/lookup.py car --group conceptnet --language en
python examples/lookup.py car --group kaikki --language en
python examples/lookup.py car --group tatoeba --language en
```

Pin a release explicitly using `--version TAG` rather than mixing resources
from `latest` on every HTTP request. The client performs network access on
its first invocation (unless all required assets are already cached and a
version is pinned). See [the client source](../examples/lookup.py) for
the download, cache and member-verification implementation.

A browser extension may instead import the required ZIPs once, decompress
only needed shards and cache them in IndexedDB. Do not require users to
download full raw corpora to search a word.

### Compatibility and licensing

- Check `schema` before reading data. Ignore unknown optional fields; use the
  authoritative catalog and manifests, not hardcoded lists.
- Keep entire source records and individual licenses. Do not silently combine
  separately licensed databases into a new license.
- Read [source licensing and notices](../legal/NOTICE.md) and original source
  archives. The project MIT license applies to code, not all redistributed data.
- Read `REFRESH-REPORT.json` for availability and changes since the previous
  release. A retained source may be older than the release tag.
