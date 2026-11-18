# Dicts — Open Multilingual Dictionary Aggregator

[**LingoInView — language learning extension**](https://danilfg.github.io/dicts/lingoinview/) · [Privacy Policy](https://danilfg.github.io/dicts/lingoinview/privacy.html)

**One independent GitHub collection of offline bilingual dictionaries, definitions, WordNets, example sentences and semantic knowledge.**

Dicts is maintained by [danilfg](https://github.com/danilfg). It aggregates third-party data with source and licensing information, checks published files and offers versioned catalogs through [GitHub Releases](https://github.com/danilfg/dicts/releases). The verified main collection includes **806 bilingual dictionary archives**: 74 KOReader, 305 FreeDict and 427 WikDict. These are **package counts, not unique language-pair counts**. Additionally, ConceptNet's upstream semantic graph covers 304 languages with very different levels of vocabulary coverage; that does **not** mean there are 304 complete translation dictionaries.

**[🌐 Try the live online dictionary →](https://danilfg.github.io/dicts/)** — search words and compare translations, definitions and examples directly in your browser.

[**Download dictionaries**](https://github.com/danilfg/dicts/releases/latest) · [**All releases**](https://github.com/danilfg/dicts/releases) · [**Update sources**](https://github.com/danilfg/dicts/actions/workflows/update.yml) · [**Audit releases**](https://github.com/danilfg/dicts/actions/workflows/audit.yml)

## What is included?

All eight source families are collected under this repository. **New dated versions consolidate all eight source families into one release.** The existing unified releases remain available. New OCI-backed releases use their dated catalog to resolve all source files, rather than thousands of release attachments.

| Source | Contents | Download | License / attribution |
|---|---|---|---|
| [KOReader dictionaries](koreader/README.md) | 74 bilingual StarDict ZIP dictionaries | [Latest release](https://github.com/danilfg/dicts/releases/latest), `koreader--*.zip` | **Per ZIP**: embedded LICENSE and ATTRIBUTION; terms vary |
| [FreeDict](freedict/README.md) | 305 bilingual dictionary packages, automatically discovered | [Latest release](https://github.com/danilfg/dicts/releases/latest), `freedict--*.zip` | **Per dictionary** TEI licensing; GPL/GFDL and other terms may apply |
| [WikDict](wikdict/README.md) | 427 bilingual StarDict ZIPs, automatically discovered | [Latest release](https://github.com/danilfg/dicts/releases/latest), `wikdict--*.zip` | CC BY-SA 4.0; credit WikDict, DBnary, Wiktionary |
| [Kaikki / Wiktionary](kaikki/README.md) | Machine-readable Wiktionary text; a separate **limited** compact expression index | [Latest release](https://github.com/danilfg/dicts/releases/latest) | Applicable Wiktionary CC BY-SA text and any individual exceptions |
| [Tatoeba](tatoeba/README.md) | Multilingual sentences and translation links **without audio**; selected study examples | [Latest release](https://github.com/danilfg/dicts/releases/latest) | Text CC BY 2.0 France or explicitly designated CC0 |
| [Open English WordNet](open-english-wordnet/README.md) | English definitions, synsets, synonyms and semantic relations; normalized English index | [Latest release](https://github.com/danilfg/dicts/releases/latest) | CC BY 4.0 **plus required Princeton WordNet attribution** |
| [Open Multilingual Wordnet](open-multilingual-wordnet/README.md) | Multilingual synsets and lexical relationships in WN-LMF | [Latest release](https://github.com/danilfg/dicts/releases/latest) | **Different license for each WordNet**, with individual citations |
| [ConceptNet](conceptnet/README.md) | Common-sense graph of concepts and semantic relations, spanning 304 upstream languages | [Latest release](https://github.com/danilfg/dicts/releases/latest) | **Data:** CC BY-SA 4.0; preserve DATA-CREDITS and provenance |

The main archive numbers above are from a completed, independently audited release. Future releases may differ; check the published **manifest**, not only this README. A family may contain source materials in a format that cannot be read as a simple bilingual StarDict dictionary.

## Downloads — one pair, all available sources

**[Current release](https://github.com/danilfg/dicts/releases/latest)** · **[GHCR package](https://github.com/danilfg/dicts/pkgs/container/dicts-data)** · **[Developer specification](docs/NORMALIZATION.md)**

OCI-format releases use **`ghcr.io/danilfg/dicts-data`**, a public OCI **data artifact**, not a runnable Docker image. Releases remain the immutable, dated entry point and include catalogs, source manifests, licenses, checksums and change reports. Older published releases retain their original downloadable assets.

The registry's `latest` and dated version tags point to a small **complete-collection catalog artifact**, not an individual source batch. Internal tags ending in a source name and a hash are storage manifests; do not use them to discover the latest collection. With ORAS, download only catalog metadata:

```bash
oras pull ghcr.io/danilfg/dicts-data:latest -o dicts-catalog
# Or pin a published version:
oras pull ghcr.io/danilfg/dicts-data:v2026.11.17.25.1 -o dicts-catalog
```

The canonical browser/API entry point remains the release metadata below. Docker is not required.

1. Read [LEXICAL-INDEX.json](https://github.com/danilfg/dicts/releases/latest/download/LEXICAL-INDEX.json). Require `format: oci-pair-v1`.
2. Pin the returned version and read its verified `PAIR-INDEX.json`. Choose the source and target language from the catalog.
3. For every catalog group download the blocks for the exact **direction**, plus language-local blocks for its two languages. Each block is an independent, at most 32 MiB OCI blob, identified by SHA-256. No other language packages are required.
4. Cache by digest, verify length and hash, read ZIP/GZIP JSON. Retain original provenance and licenses.

No Docker daemon, account, PAT or API key is needed for consumers after the package is public; request an anonymous GHCR pull token. For the first OCI release the maintainer may need to set package visibility to Public. The previous release remains current until the new release passes verification.

```bash
python examples/lookup.py --list
python examples/lookup.py --pair en-ru --install
python examples/lookup.py car --pair en-ru
mvn -f examples/java/pom.xml compile exec:java -Dexec.mainClass=DictsPair -Dexec.args="en-ru"
```

See the [browser/Chrome example](examples/browser/oci-client.mjs) and [Java example](examples/java/src/main/java/DictsPair.java). Pin a real dated tag with `--version TAG` in Python or pass it as Java's second argument. Use the [complete inventory](https://github.com/danilfg/dicts/releases/latest/download/RELEASE-MANIFEST.json) to download a specific raw file or the full collection, rather than downloading all language units by default. Each logical file has a name, bytes, SHA-256 and, for OCI files, an `oci` descriptor. With ORAS:

```bash
oras blob fetch ghcr.io/danilfg/dicts-data@sha256:<file-digest> --output <file-name>
```

Replace placeholders with the manifest values and verify SHA-256. `gh release download` downloads release metadata, not all OCI data. `BUNDLE-PARTS.json` still maps convenience ZIP parts; raw numbered chunks are joined in order without modifying their bytes.

## Online dictionary search

**[Open the multilingual translator](https://danilfg.github.io/dicts/)** — a GitHub Pages interface for comparing original KOReader, FreeDict and WikDict dictionary entries side by side. Choose the source and target languages, search a word or phrase, read complete available definitions, review examples and follow original copyright/source links.

The search index is generated by the main [GitHub Actions workflow](.github/workflows/update.yml) and deployed from prebuilt compact normalized packs, with small on-demand gzip shards. See [Pages setup and data coverage](docs/PAGES.md). The deployed website now exposes **753 verified source–target language directions**, generated from 720 compact-enrichment directions plus original KOReader data for directions without equivalent compact indexes. For the initial six English/Russian/Spanish/German directions, it preserves complete original KOReader, FreeDict and WikDict articles. Other directions may have compact rather than full original articles; the unabridged source archives are available through the release inventory. The published searchable site is **932.5 MB**, within the GitHub Pages limit.

**Semantic lookup is now integrated:** [Open English WordNet](https://github.com/danilfg/dicts/releases/latest), [Open Multilingual Wordnet](https://github.com/danilfg/dicts/releases/latest) and [ConceptNet](https://github.com/danilfg/dicts/releases/latest) appear in their own attributed cards whenever a matching indexed term exists. WordNet definitions and ConceptNet relations are **not additional literal translations**. The first published semantic lookup covers English and selected Spanish vocabulary; complete original lexical datasets are downloadable as OCI files listed in the unified release inventory.

## Normalized application data

Format: **`oci-pair-v1`**, schema 1. See [normalization and JSON examples](docs/NORMALIZATION.md). Every source adapter produces a source-tagged unit. Applications dynamically iterate the groups in the pair index, not a hardcoded provider list.

| Group | Available normalized data |
|---|---|
| bilingual | Original readable KOReader, FreeDict and WikDict articles; selected legacy study records, by direction |
| oewn | English definitions and synonyms |
| omw | Individual WordNets with synset/ILI IDs and per-package licenses, by language |
| conceptnet | Selected attributed same-language semantic relations and directional cross-language relations |
| kaikki | Compact definitions, selected directional translations and parts of speech, by edition/language |
| tatoeba | Compact attributed examples and directional linked translations |
| pages / pages-lexical | Separate compact website-only indexes; not downloaded by pair clients |

The raw source files are retained. Compact limits do not mean complete upstream coverage. ILI and graph relations are not guaranteed literal translations.

## Using the data in applications

Useful for offline translators, e-readers, language-learning tools, NLP applications and individual dictionary libraries. All downloads are distributed through **danilfg/dicts**. During a build, GitHub Actions may contact the original source providers.

The current **Learn Words with Cards** extension must adopt the OCI pair protocol before it can use the new artifacts. The reference browser module implements catalog verification and pair-specific blob downloads. The lexical-network data need additional extension-side adapters before they can appear in popup definitions or study cards.

## Updating and verifying sources

Use [**Update all dictionary sources**](https://github.com/danilfg/dicts/actions/workflows/update.yml) → **Run workflow** → **main**. For troubleshooting catalog aliases only, enable the optional `catalog_only` input; it does not rebuild source data or modify the release. This single workflow runs on the first day of every month at 04:17 UTC, and orchestrates checks, downloads, normalization, validation, release publication, OCI catalog alias promotion and the Pages deployment. Where an upstream supplies reliable SHA-256/SHA-512 or a strong HTTP ETag, unchanged files are reused from the last verified release instead of being downloaded again from upstream. Otherwise the data must be fetched to determine whether they changed. Unavailable dictionaries retain their last verified files when possible, regardless of source family; new unavailable files without prior versions are reported. Successful changes from other sources can be published in the same complete snapshot. Release notes and `REFRESH-REPORT.json` identify added, modified, removed, unchanged and retained source files and the reason for fallback. If no source data changed and normalized packs already exist, the draft is deleted. The first OCI pair release is a one-time format upgrade. Publication is blocked for integrity errors or missing mandatory normalized groups, not for upstream outages with verified fallback copies. Versions use `vYYYY.MM.DD.RUN.ATTEMPT` (UTC). Release catalog URLs remain stable; data files are fetched by digest instead of per-file release URLs. The scheduled run is not a real-time upstream notification. Immutable release inventories are cached per worker; public legacy assets are fetched directly and OCI blobs by digest. The preflight checks GitHub REST API budget and waits for the current quota window to reset if insufficient, instead of retrying hundreds of exhausted API requests.

Run [**Audit published dictionary collections**](https://github.com/danilfg/dicts/actions/workflows/audit.yml) to check published SHA-256, bundle completeness, source notices and representative file formats. This **technical audit does not validate the accuracy of every dictionary entry**.

## Licenses, attribution and commercial use

**The repository's [MIT LICENSE](LICENSE) covers original automation code and independently written project documentation, not the redistributed dictionaries or graph data.** A bundle does not replace the original component license. Each package must be evaluated under its own terms.

| Family | Commercial-use and redistribution conditions |
|---|---|
| KOReader | Inspect each ZIP's original LICENSE/ATTRIBUTION (different packages may have CC BY-SA, CeCILL-C or other terms); retain all required notices |
| FreeDict | Inspect the specific TEI rights header and comply with the applicable GPL/GFDL or other license, attribution and source-distribution requirements |
| WikDict | Credit the original creators and Wiktionary/DBnary contributors; preserve CC BY-SA 4.0, license links, changes and applicable ShareAlike obligations |
| Kaikki/Wiktionary | Credit original Wiktionary text, contributors and extraction source; comply with CC BY-SA for qualifying text, and assess exceptions separately |
| Tatoeba | Retain original sentence IDs, source links, authors where available and CC BY 2.0 France or explicit CC0 status; **audio is excluded** |
| Open English WordNet | Apply CC BY 4.0 **and** credit Princeton WordNet and the Open English WordNet team; preserve original notices and identify normalized changes |
| Open Multilingual Wordnet | **Per-lexicon license and citation**; some index labels are incomplete shorthand, so inspect the original license before commercial adaptation |
| ConceptNet | **CC BY-SA 4.0 for data**, original `DATA-CREDITS.md` and source provenance; its software `LICENSE.txt` is not the data license |

Open licenses may permit commercial use **subject to attribution, sharing and other applicable obligations**. Do not claim all files are MIT, remove credits or assume separately licensed sources may be combined into a single newly relicensed derivative database.

See [legal/NOTICE.md](legal/NOTICE.md), the [source license registry](legal/SOURCES.json), the [legal review checklist](docs/LEGAL-REVIEW-CHECKLIST.md), and the original source licenses. This documentation aids compliance but is not legal advice.

## Quality and responsibility

**Dicts is an independent aggregator and technical distributor—not the author or editor of its source dictionaries.** The maintainer does not individually proofread source entries and does **not guarantee accuracy, completeness, currency, translation quality or fitness for any purpose**. Information is provided **as is**, to the extent permitted by law; consequential translations should be checked with authoritative sources.

This disclaimer does **not** override mandatory statutory rights or the maintainer's obligations concerning lawful redistribution, copyright, licensing, attribution, or technical file integrity. For original linguistic mistakes contact the source author; for package/attribution problems [open an issue](https://github.com/danilfg/dicts/issues).

## Repository structure

```text
.github/workflows/  Automated updates and release auditing
configs/            Upstream sources and options
src/build.py        Main dictionary and study index generation
src/mirror_raw.py   Kaikki and Tatoeba full-text snapshots
src/sync_lexical.py Open English WordNet, OMW and ConceptNet
src/package_release.py  Main collection archive splitting
src/unified_release.py  Unified calendar-versioned release validation
src/audit_release.py    Checksums and published-release audit
src/normalize_sources.py   Normalized JSON conversion
src/normalized_pack.py     Shard ZIP packaging and verification
src/pair_pack.py           Language and direction units
src/storage.py             Content-addressed OCI publishing and release receipts
examples/lookup.py        Python reference client
examples/java/             Java 17 reference client
examples/browser/          Chrome MV3 download reference
docs/NORMALIZATION.md     Developer format specification
tests/              Automated tests
koreader/ freedict/ wikdict/ kaikki/ tatoeba/
open-english-wordnet/ open-multilingual-wordnet/ conceptnet/
legal/NOTICE.md legal/SOURCES.json
docs/LEGAL-REVIEW-CHECKLIST.md
LICENSE
```

[**GitHub Releases**](https://github.com/danilfg/dicts/releases) · [**Issues**](https://github.com/danilfg/dicts/issues) · [**Third-party notices**](legal/NOTICE.md)
