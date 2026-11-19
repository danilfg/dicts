# Normalized dictionary format — developer reference (schema 1)

The [monthly update workflow](../.github/workflows/update.yml) builds application-ready lookup data and publishes it with the original source archives. Applications do not need a StarDict, WN-LMF or ConceptNet parser.

**Availability:** the new format is usable after the first successful release containing `format: oci-pair-v1` in [LEXICAL-INDEX.json](https://github.com/danilfg/dicts/releases/latest/download/LEXICAL-INDEX.json). Older releases may contain legacy indexes; reject unsupported formats. The examples on this page are synthetic schema illustrations, not verified upstream translations, corpus records, identifiers or author names.

## Normalization pipeline

1. Discover upstream datasets. Use authoritative hashes and strong HTTP ETags where available; otherwise download data to compare.
2. Reuse verified previous files when an upstream is unreachable; report failures in release notes and `REFRESH-REPORT.json`.
3. Compare source contents, including ZIP members, ignoring packaging timestamps. After the first format upgrade, unchanged sources alone do not trigger a release.
4. Parse original files, preserve source attribution and separate bilingual articles, definitions, examples and semantic relations.
5. Write UTF-8 JSON shards compressed with gzip. Split cross-language relationships by target, build ZIP blocks of at most 32 MiB for directions or individual languages, then publish independent OCI blobs with SHA-256 and sizes.
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

## Release and registry protocol

Release metadata is immutable after publication. Data files are stored in **`ghcr.io/danilfg/dicts-data`**. A package is OCI data (not a Docker image to run). A logical file is an OCI layer; OCI manifests retain the layer references. Release receipts (`oci--*.json`) list the files, manifest digests and content hashes. Original source files and convenience bundles use the same transport. Do not delete package versions referenced by any release.

### Registry collection aliases

`ghcr.io/danilfg/dicts-data:latest` and the exact dated release tag (for example `v2026.11.17.25.1`) point to the same verified OCI catalog manifest for the current public release. The catalog includes the master and pair indexes, full inventory, checksums, report and licensing metadata. It does not contain all dictionary bytes; follow the pair index to download individual blocks. Internal batch tags are not application entry points. Use `oras pull ghcr.io/danilfg/dicts-data:latest -o dicts-catalog` to obtain the metadata without a Docker daemon. The monthly workflow promotes the aliases after successful release publication. Its optional `catalog_only` mode repairs the current aliases without rebuilding any data.

### Step 1 — discover and pin

Fetch `https://github.com/danilfg/dicts/releases/latest/download/LEXICAL-INDEX.json`. Require schema 1, format `oci-pair-v1`, expected registry and pinned download base. Example (synthetic digest and byte count):

```json
{
  "schema": 1,
  "version": "v2026.12.01.24.1",
  "format": "oci-pair-v1",
  "registry": "ghcr.io/danilfg/dicts-data",
  "download_base": "https://github.com/danilfg/dicts/releases/download/v2026.12.01.24.1/",
  "pair_index": {"name":"PAIR-INDEX.json","bytes":123456,"sha256":"<64 hex characters>"},
  "groups": {}
}
```

Fetch the pair index from the pinned release, verify exact bytes/SHA-256, and require the same version, registry and format.

### Step 2 — select all applicable groups

```json
{
  "schema":1,
  "format":"oci-pair-v1",
  "registry":"ghcr.io/danilfg/dicts-data",
  "version":"v2026.12.01.24.1",
  "download_base":"https://github.com/danilfg/dicts/releases/download/v2026.12.01.24.1/",
  "pairs":{"en-ru":{"from":"en","to":"ru","sources":["koreader","freedict","wikdict"]}},
  "groups":{
    "bilingual":{
      "pairs":{"en-ru":[{"bytes":123456,"sha256":"<64 hex characters>","manifest":"sha256:<64 hex characters>"}]},
      "languages":{}
    },
    "oewn":{
      "pairs":{},
      "languages":{"en":[{"bytes":123456,"sha256":"<64 hex characters>","manifest":"sha256:<64 hex characters>"}]}
    }
  }
}
```

The example intentionally omits other groups. Select `groups[*].pairs[PAIR]` and `groups[*].languages[FROM]` / `[TO]` when present. Iterate **all** groups, deduplicate blocks by SHA-256, and do not download unrelated directions. `pairs[*].sources` identifies translation sources; semantic/example groups are discovered independently. Match the requested direction exactly (EN–RU and RU–EN are independent). Codes in this version are lowercase alphanumeric language identifiers of 2–20 characters, not arbitrary compound BCP47 tags.

### Step 3 — anonymous HTTP downloads

```text
GET https://ghcr.io/token?service=ghcr.io&scope=repository%3Adanilfg%2Fdicts-data%3Apull
GET https://ghcr.io/v2/danilfg/dicts-data/blobs/sha256:<64 hex characters>
Authorization: Bearer <anonymous pull token>
```

Allow HTTPS redirects, but do not forward Authorization to a different host. Verify size and SHA-256 before caching. A public package requires no account or personal credentials. Refresh the anonymous pull token on expiry. Do not download the entire OCI manifest's other layers. For CLI consumers use `oras blob fetch ghcr.io/danilfg/dicts-data@sha256:DIGEST --output FILE`.

### Step 4 — unit layout and lookup

Each independently downloadable ZIP is one block (at most 32 MiB). Combine the member directory of every block of a given group/scope/id. Exactly one block has `UNIT.json`; verify its identity. ZIPs use ZIP_STORED; the data members are GZIP-compressed UTF-8 JSON. Unit examples:

```json
{"schema":1,"group":"bilingual","scope":"pairs","id":"en-ru","kind":"bilingual",
 "descriptor":{"pair":"en-ru","from":"en","to":"ru","buckets":16,"entries":123,"sources":[]},"provenance":{}}
```

```json
{"schema":1,"group":"omw","scope":"languages","id":"es","kind":"lexical",
 "descriptors":[{"language":"es","package":"omw-es-2.0","path":"data/lexical/omw/es/omw-es-2.0","entries":100,"buckets":4,"rights":{"license":"<actual component license>","citation":"<actual citation>"}}]}
```

```json
{"schema":1,"group":"kaikki","scope":"pairs","id":"en-ru","kind":"links",
 "path":"data/links/kaikki/en-ru","buckets":32}
```

Bilingual data files: `data/PAIR/NN.json.gz`. Lexical data files: `descriptor.path/NN.json.gz` for each descriptor (every edition/lexicon). Linked data files: `UNIT.path/NN.json.gz`; their `words[KEY]` contains a list of `{"package": "...", "record": {...}}` objects. The record preserves the corresponding cross-language field (`translations`, `relations`, or `examples`) filtered to the selected target language. Language-local units contain same-language material only. Preserve records and provenance, even for newly registered groups. Clients can install unknown groups following the same protocol; unfamiliar record kinds require a rendering adapter.

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
Each shard normally contains many words. Kaikki, Tatoeba and ConceptNet examples below illustrate pre-split record fields; cross-language values are placed in the exact-direction link units. For instance, a Kaikki EN–RU links record contains only Russian targets, not Spanish.

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
global reverse ILI index. Use per-package rights in the unit descriptor.

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
Cross-language edges are transported in the directional link units rather than the language-local unit. `dataset` may
be null. Do not present semantic edges as literal translations.

## Reference clients

- [Python 3.10+](../examples/lookup.py): list, install and search all available groups; pair-specific SHA-256 caching with the standard library.
- [Java 17 + Maven](../examples/java/pom.xml): installation from the same catalog, no Docker daemon.
- [Chrome MV3](../examples/browser/oci-client.mjs): anonymous fetch, pair selection and verified download to an IndexedDB-compatible cache interface. The extension supplies storage and ZIP/JSON readers.

```bash
python examples/lookup.py --list
python examples/lookup.py --pair en-ru --install
python examples/lookup.py car --pair en-ru
mvn -f examples/java/pom.xml compile exec:java -Dexec.mainClass=DictsPair -Dexec.args="en-ru"
```

Cache by content digest, not file name or release. Use a pinned version for repeatable installation; Python can search a pinned fully cached pair offline. Unknown optional fields must not be discarded when redistributing data. If a future provider introduces a new record kind, update only its rendering adapter. The catalog, rather than hardcoded groups, is the download contract.

## Rights and compatibility

See [source licensing and notices](../legal/NOTICE.md) and the release's `SOURCES.json`, `NOTICE.md`, `THIRD-PARTY-NOTICES.md`, component manifests and original archives. The code's MIT license is separate from dictionary content. Sources remain independently attributed and original obligations apply. The report `REFRESH-REPORT.json` identifies retained older data. This protocol is not compatible with older whole-group release ZIP indexes; use the correct versioned reader.

## Optional expressions reverse index

The `expressions` group is derived from full bilingual normalized shards, including
available compact Kaikki expression definitions. It is not a ninth upstream
dictionary. It uses the existing `oci-pair-v1` schema, pair scope and
`kind: "links"` envelope; no translation pair is added by this group.
Old clients dynamically select it and ignore the unknown `expressions` field.
They may download additional bytes but do not need a protocol upgrade.

Use the existing SHA-256 first-byte bucket algorithm (128 buckets) on the
normalized selected word and its lemma variants. The member path is
`data/links/expressions/<pair>/<bucket>.json.gz`. Missing shards/keys mean no
matches. Each key returns an array of wrappers, with
`record.expressions` containing up to 32 matches.
`text` is the display title; `expression` is the lookup form.
`kind` is one of `expression`, `construction`, `phrasal_verb`, `idiom`,
`collocation`, `fixed_expression`. Unclassified headwords stay `expression`;
the algorithm does not infer grammatical templates from arbitrary phrases.
`articles` holds the original source/rights and optional Kaikki definition.
Resolve the original phrase in the existing bilingual unit and apply the
regular translation parser before presenting any article as a translation.
For authored starter entries only, `translation`, `example`,
`example_translation`, `source`, `language` and `license` are explicit.
`configs/expressions-en-ru.json` contains the MIT-licensed original examples.
The source data retain their own licenses and attribution.

The reverse index is bounded and heuristic, not exhaustive; the initial
hand-authored patterns are EN→RU only. Other pairs index existing multiword
headwords. Full Kaikki structural fields and corpus phrase mining are future
coverage improvements. Existing Pages compact packs are unchanged.
