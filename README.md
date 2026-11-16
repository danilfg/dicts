# Dicts — Open Multilingual Dictionary Aggregator

**One independent GitHub collection of offline bilingual dictionaries, definitions, WordNets, example sentences and semantic knowledge.**

Dicts is maintained by [danilfg](https://github.com/danilfg). It aggregates third-party data with source and licensing information, checks published files and offers them through [GitHub Releases](https://github.com/danilfg/dicts/releases). The verified main collection includes **806 bilingual dictionary archives**: 74 KOReader, 305 FreeDict and 427 WikDict. These are **package counts, not unique language-pair counts**. Additionally, ConceptNet's upstream semantic graph covers 304 languages with very different levels of vocabulary coverage; that does **not** mean there are 304 complete translation dictionaries.

[**Download dictionaries**](https://github.com/danilfg/dicts/releases/latest) · [**All releases**](https://github.com/danilfg/dicts/releases) · [**Update sources**](https://github.com/danilfg/dicts/actions/workflows/update.yml) · [**Audit releases**](https://github.com/danilfg/dicts/actions/workflows/audit.yml)

## What is included?

All eight source families are collected under this repository. **The main release, full text-corpus releases and lexical-network releases are separate downloads.**

| Source | Contents | Download | License / attribution |
|---|---|---|---|
| [KOReader dictionaries](koreader/README.md) | 74 bilingual StarDict ZIP dictionaries | [Main release](https://github.com/danilfg/dicts/releases/latest), `koreader--*.zip` | **Per ZIP**: embedded LICENSE and ATTRIBUTION; terms vary |
| [FreeDict](freedict/README.md) | 305 bilingual dictionary packages, automatically discovered | [Main release](https://github.com/danilfg/dicts/releases/latest), `freedict--*.zip` | **Per dictionary** TEI licensing; GPL/GFDL and other terms may apply |
| [WikDict](wikdict/README.md) | 427 bilingual StarDict ZIPs, automatically discovered | [Main release](https://github.com/danilfg/dicts/releases/latest), `wikdict--*.zip` | CC BY-SA 4.0; credit WikDict, DBnary, Wiktionary |
| [Kaikki / Wiktionary](kaikki/README.md) | Machine-readable Wiktionary text; a separate **limited** compact expression index | [Raw corpus](https://github.com/danilfg/dicts/releases?q=raw-kaikki), [main indexes](https://github.com/danilfg/dicts/releases/latest) | Applicable Wiktionary CC BY-SA text and any individual exceptions |
| [Tatoeba](tatoeba/README.md) | Multilingual sentences and translation links **without audio**; selected study examples | [Raw corpus](https://github.com/danilfg/dicts/releases?q=raw-tatoeba), [main indexes](https://github.com/danilfg/dicts/releases/latest) | Text CC BY 2.0 France or explicitly designated CC0 |
| [Open English WordNet](open-english-wordnet/README.md) | English definitions, synsets, synonyms and semantic relations; normalized English index | [Lexical release](https://github.com/danilfg/dicts/releases?q=lex-oewn) | CC BY 4.0 **plus required Princeton WordNet attribution** |
| [Open Multilingual Wordnet](open-multilingual-wordnet/README.md) | Multilingual synsets and lexical relationships in WN-LMF | [Lexical release](https://github.com/danilfg/dicts/releases?q=lex-omw) | **Different license for each WordNet**, with individual citations |
| [ConceptNet](conceptnet/README.md) | Common-sense graph of concepts and semantic relations, spanning 304 upstream languages | [Lexical release](https://github.com/danilfg/dicts/releases?q=lex-conceptnet) | **Data:** CC BY-SA 4.0; preserve DATA-CREDITS and provenance |

The main archive numbers above are from a completed, independently audited release. Future releases may differ; check the published **manifest**, not only this README. A family may contain source materials in a format that cannot be read as a simple bilingual StarDict dictionary.

## Downloads and formats

For normal language-pair downloads use [Releases → Latest](https://github.com/danilfg/dicts/releases/latest), for example [EN–RU KOReader](https://github.com/danilfg/dicts/releases/latest/download/koreader--en-ru.zip), [EN–RU FreeDict](https://github.com/danilfg/dicts/releases/latest/download/freedict--en-ru.zip), or [EN–RU WikDict](https://github.com/danilfg/dicts/releases/latest/download/wikdict--en-ru.zip).

| Format | What it means |
|---|---|
| `koreader--PAIR.zip`, `freedict--PAIR.zip`, `wikdict--PAIR.zip` | Bilingual StarDict dictionary packages; an application must support the included files |
| `enrichment--PAIR.json.gz` | Compact meanings and study examples (custom JSON format, **not** StarDict) |
| `enrichments-extra--NNN.zip` | Groups of additional language indexes that must be extracted before use |
| `lexicon--oewn-en.json.gz` | Normalized English WordNet index |
| `lex-omw-*` / `lex-conceptnet-*` release assets | Original multilingual lexical-network files, requiring suitable readers |
| `raw-kaikki-*` / `raw-tatoeba-*` release assets | Original textual corpora; large sources may be split into numbered `.partNNN` files |

For the **entire main dictionary collection**, use [BUNDLE-PARTS.json](https://github.com/danilfg/dicts/releases/latest/download/BUNDLE-PARTS.json) and download every listed `dicts-part-NNN.zip`, or `dicts-all.zip` when the collection fits in a single archive. These bundles do **not** contain the separately published full raw corpora and WordNet/ConceptNet releases.

The main release includes [manifest.json](https://github.com/danilfg/dicts/releases/latest/download/manifest.json), [SHA256SUMS.txt](https://github.com/danilfg/dicts/releases/latest/download/SHA256SUMS.txt) and [THIRD-PARTY-NOTICES.md](https://github.com/danilfg/dicts/releases/latest/download/THIRD-PARTY-NOTICES.md). Lexical releases each include `LEXICAL-MANIFEST.json` and `THIRD-PARTY-LEXICAL-NOTICES.md`; raw releases include `SOURCE-MANIFEST.json` and `ATTRIBUTION-AND-LICENSE.txt`. They identify actual published files and the relevant origin/rights information.

## Online dictionary search

**[Open the multilingual translator](https://danilfg.github.io/dicts/)** — a GitHub Pages interface for comparing original KOReader, FreeDict and WikDict dictionary entries side by side. Choose the source and target languages, search a word or phrase, read complete available definitions, review examples and follow original copyright/source links.

The search index is generated by [GitHub Actions](.github/workflows/pages-all-pairs.yml) from the original published dictionaries and compact multilingual enrichment indexes, with small on-demand gzip shards. See [Pages setup and data coverage](docs/PAGES.md). The deployed website now exposes **753 verified source–target language directions**, generated from 720 compact-enrichment directions plus original KOReader data for directions without equivalent compact indexes. For the initial six English/Russian/Spanish/German directions, it preserves complete original KOReader, FreeDict and WikDict articles. Other directions may have compact rather than full original articles; the unabridged source archives are still available in Releases. The published searchable site is **932.5 MB**, within the GitHub Pages limit.

**Semantic lookup is now integrated:** [Open English WordNet](https://github.com/danilfg/dicts/releases?q=lex-oewn), [Open Multilingual Wordnet](https://github.com/danilfg/dicts/releases?q=lex-omw) and [ConceptNet](https://github.com/danilfg/dicts/releases?q=lex-conceptnet) appear in their own attributed cards whenever a matching indexed term exists. WordNet definitions and ConceptNet relations are **not additional literal translations**. The first published semantic lookup covers English and selected Spanish vocabulary; complete original lexical datasets remain in separate GitHub Releases.

## Using the data in applications

Useful for offline translators, e-readers, language-learning tools, NLP applications and individual dictionary libraries. All downloads are distributed through **danilfg/dicts**. During a build, GitHub Actions may contact the original source providers.

The current **Learn Words with Cards** extension uses KOReader and compatible compact enrichment indexes. It does **not** automatically download every independent dictionary, grouped index, raw corpus, WordNet or ConceptNet graph. The lexical-network data need additional extension-side adapters before they can appear in popup definitions or study cards.

## Updating and verifying sources

Use [**Update all dictionary sources**](https://github.com/danilfg/dicts/actions/workflows/update.yml), choose **main**, then **Run workflow → all**. It also runs monthly. The workflow checks the original KOReader publication (with a maintainer-hosted fallback), discovers FreeDict/WikDict packages, builds main dictionary indexes and separately publishes full text-corpus and lexical-network releases.

The **core** mode limits processing to the basic KOReader collection. OEWN and OMW track publisher release identifiers; the ConceptNet source currently uses the published 5.7.0 assertions snapshot. The main and lexical release routines avoid some duplicate publications; **raw-corpus runs may still publish new snapshots on repeated updates**. Failed optional sources must be checked in workflow logs and source-status information; a green GitHub Actions result does not by itself mean every upstream file exists in that release.

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
src/audit_release.py    Checksums and published-release audit
tests/              Automated tests
koreader/ freedict/ wikdict/ kaikki/ tatoeba/
open-english-wordnet/ open-multilingual-wordnet/ conceptnet/
legal/NOTICE.md legal/SOURCES.json
docs/LEGAL-REVIEW-CHECKLIST.md
LICENSE
```

[**GitHub Releases**](https://github.com/danilfg/dicts/releases) · [**Issues**](https://github.com/danilfg/dicts/issues) · [**Third-party notices**](legal/NOTICE.md)
