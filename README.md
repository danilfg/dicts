# Dicts — Unified Offline Dictionary Distribution

> **DISCLAIMER / ОТКАЗ ОТ ГАРАНТИЙ КАЧЕСТВА:** This repository is an independent **aggregator, packager and distributor**, not the author or editorial reviewer of third-party dictionary entries. The maintainer does **not warrant or certify** the correctness, completeness, freshness, translation quality, examples, or suitability for any particular purpose. Dictionary content, meanings, omissions and errors originate with their respective authors and publishers. Users should verify consequential translations against primary sources. The maintainer remains responsible for complying with applicable law, license notices, and any obligations that cannot lawfully be excluded. This statement does not waive statutory rights, does not override upstream licenses, and is subject to mandatory consumer protection law where applicable.

**Dicts** is an independent, publicly accessible collection of offline bilingual dictionaries, translations, idioms, multi-word expressions and example sentences, maintained by [danilfg](https://github.com/danilfg). The goal is to let developers and learners download verified packages from **one GitHub Releases page**, rather than integrating five different hosting services.

**[Download latest release](https://github.com/danilfg/dicts/releases/latest)** | **[See all bundle parts](https://github.com/danilfg/dicts/releases/latest/download/BUNDLE-PARTS.json)** | **[Run an update](https://github.com/danilfg/dicts/actions/workflows/update.yml)**

> **IMPORTANT — OWNERSHIP AND LICENSES:** Third-party dictionary content **does not become MIT-licensed** when added to this repository. Each source and each original dictionary package retains its original copyright, source attribution and licensing conditions. MIT covers only independently authored automation code and project documentation. This repository is not endorsed by or affiliated with the source projects.

## What is included?

| Folder | Data source | Release assets | Coverage model |
|---|---|---|---|
| [koreader](koreader/README.md) | [DanielGregorini/koreader-dicts](https://github.com/DanielGregorini/koreader-dicts) | KOReader-prefixed StarDict ZIP files | 74 dictionaries |
| [freedict](freedict/README.md) | [FreeDict](https://freedict.org/downloads/) | FreeDict-prefixed StarDict ZIP files | **Auto-discovered all catalogued language pairs**, verified individually |
| [wikdict](wikdict/README.md) | [WikDict](https://www.wikdict.com/page/download) | WikDict-prefixed StarDict ZIP files | **Every discovered available StarDict language pair** |
| [kaikki](kaikki/README.md) | [Kaikki/Wiktextract](https://kaikki.org/dictionary/rawdata.html) | Browser enrichment + independent raw text archive release | **All currently discoverable textual Wiktionary editions** in raw release; browser index is separate |
| [tatoeba](tatoeba/README.md) | [Tatoeba](https://tatoeba.org/en/downloads) | Browser enrichment + independent raw text archive release | **Full multilingual sentence/translation exports**; no audio |

Previous releases were **limited previews**. The build now automatically discovers all available FreeDict and WikDict language pairs and attempts them without a fixed six-pair allowlist; source packages that fail validation are shown as skipped in the manifest. The same **Run workflow (all)** button also mirrors **the complete available textual Kaikki Wiktionary editions and Tatoeba's multi-language text exports** to dedicated `raw-kaikki-*` and `raw-tatoeba-*` GitHub Releases. These are full upstream text archives, **not** all converted into browser lookups yet. Audio/media are excluded because their rights and technical distribution are separate. A full archive bigger than 2 GiB is transparently split into numbered parts and reassembled by concatenation. A verified release must have `SOURCE-MANIFEST.json` and original-source attribution. 

This is **not a mirror of every language pair in every project**. Only release files listed in the machine-readable [manifest](https://github.com/danilfg/dicts/releases/latest/download/manifest.json) are guaranteed to be part of a particular snapshot. The previous release was an **initial limited snapshot**, not the whole available corpus. It contained 74 KOReader packages, just 6 FreeDict directions, just 6 WikDict directions, 2,725 Kaikki expressions and 29,983 Tatoeba pairs. The repository is being expanded to automatic source discovery and full-text archives; **do not interpret the current manifest as a complete mirror of every upstream dictionary**. The published manifest, not the general README, records the actual scope.

## Download the collection

| Download | Description |
|---|---|
| [**BUNDLE-PARTS.json**](https://github.com/danilfg/dicts/releases/latest/download/BUNDLE-PARTS.json) | Lists **all parts** of the collection, with SHA-256 and contents. The complete collection is sharded when it exceeds the maximum single-file size |
| [koreader--en-ru.zip](https://github.com/danilfg/dicts/releases/latest/download/koreader--en-ru.zip) | English to Russian KOReader/StarDict dictionary |
| [koreader--ru-en.zip](https://github.com/danilfg/dicts/releases/latest/download/koreader--ru-en.zip) | Russian to English KOReader/StarDict dictionary |
| [freedict--en-ru.zip](https://github.com/danilfg/dicts/releases/latest/download/freedict--en-ru.zip) | English to Russian FreeDict data |
| [wikdict--en-ru.zip](https://github.com/danilfg/dicts/releases/latest/download/wikdict--en-ru.zip) | English to Russian WikDict data |
| [enrichment--en-ru.json.gz](https://github.com/danilfg/dicts/releases/latest/download/enrichment--en-ru.json.gz) | Extra meanings, multi-word expressions and example sentences |
| [manifest.json](https://github.com/danilfg/dicts/releases/latest/download/manifest.json) | Asset list, sources, versions, sizes, checksums, attribution and license metadata |
| [SHA256SUMS.txt](https://github.com/danilfg/dicts/releases/latest/download/SHA256SUMS.txt) | Integrity checksums of release files |
| [THIRD-PARTY-NOTICES.md](https://github.com/danilfg/dicts/releases/latest/download/THIRD-PARTY-NOTICES.md) | Release-specific author and license notices |

All ready-to-use files are delivered from **github.com/danilfg/dicts**, not directly from upstream hosts. Upstream URLs are accessed **by GitHub Actions during the build process**. Bundled ZIP parts are a convenience compilation, not a claim that all data share a single license. When the collection is small enough there is one `dicts-all.zip`; otherwise download every `dicts-part-NNN.zip` listed in `BUNDLE-PARTS.json`. Large raw Kaikki and Tatoeba archives are in their own raw-source releases.

Dictionary packages use StarDict data that can be read by suitable clients. Supplementary enrichment indexes use JSON.GZ and require an application adapter; they are not standalone StarDict dictionaries. Download size and expanded disk usage differ.

## Update every source with one button

The workflow is defined in [Update all dictionary sources](.github/workflows/update.yml).

1. Open [Actions / Update all dictionary sources](https://github.com/danilfg/dicts/actions/workflows/update.yml).
2. Choose **Run workflow**, branch **main**, and mode **all**. The optional **core** mode limits the build to the required KOReader packages.
3. GitHub Actions fetches the latest original data, validates checksums where available, retains original licensing evidence, builds language indexes, and publishes a snapshot to Releases.
4. Verify the successful run and inspect its published manifest for included/omitted sources and individual licensing metadata.

**The single `all` workflow also creates separate raw-text source releases**: [Kaikki full archives](https://github.com/danilfg/dicts/releases?q=raw-kaikki) and [Tatoeba full text](https://github.com/danilfg/dicts/releases?q=raw-tatoeba). These releases are deliberately NOT marked Latest; the main dictionary release remains the default for the browser extension. If a text archive exceeds GitHub's 2-GiB file limit, it is published as sequential `.part001`, `.part002`, etc. The complete original file is reconstructed by joining every part in order. Each raw release ships its own SOURCE-MANIFEST.json and ATTRIBUTION-AND-LICENSE.txt. 

A monthly schedule is also configured. For KOReader, the workflow checks the original author's latest release and falls back to an independently maintained [danilfg mirror](https://github.com/danilfg/koreader-dicts/releases) if required. Other families are obtained from their original publishers **only by the build runner**. The process is designed to avoid duplicate new releases when package contents have not changed.

Important: an optional upstream source may fail to download or pass verification. Such failures are logged; they do **not** mean every advertised data source was included. For a definitive list, read the manifest and per-source status of that release.

### Ограничение ответственности за содержание словарей

**Dicts — агрегатор и технический распространитель, а не автор или редакция словарей.** Владелец репозитория не составляет словарные статьи, не осуществляет их сплошную лингвистическую экспертизу и **не гарантирует точность, полноту, актуальность, качество перевода, отсутствие ошибок или пригодность сведений для конкретной цели**. Значения, переводы, примеры и иные сведения публикуются по материалам независимых источников «как есть» (*as is*) в пределах, допускаемых применимым законодательством. Пользователю рекомендуется самостоятельно проверять существенные переводы по первоисточникам.

**Это уведомление не отменяет обязательных требований закона и прав потребителей.** Оно также не исключает обязанностей владельца репозитория по законности перераспространения, соблюдению авторских прав и лицензий, корректности технической упаковки и предоставлению обязательной информации об источниках. Претензии по содержанию исходных словарных статей целесообразно адресовать их правообладателям; сообщения о повреждённых архивах, нарушенной атрибуции или ошибках сборки — через Issues этого репозитория.

## Licensing, attribution and commercial reuse

**A compilation is not a relicensing.** Each family has individual rights, and some individual dictionary packages have different terms from others in the same family.

| Source | Commercial use | Obligations and limits |
|---|---|---|
| KOReader packages | Depends on the **specific ZIP**; packages have distinct licenses, including CC BY-SA and CeCILL-C | Inspect and retain embedded LICENSE and ATTRIBUTION, link to the original source, keep any required derivative/share-alike notices |
| FreeDict | Some GPL/GFDL-based packages allow commercial redistribution when their conditions are satisfied | **Read each dictionary's TEI rights header**; maintain attribution, full applicable license statements and any corresponding-source obligations; check mixed-license compatibility |
| WikDict | CC BY-SA allows commercial use with conditions | Credit Karl Bartel/WikDict, DBnary and Wiktionary contributors as applicable; link to source and license; identify modifications and satisfy ShareAlike for adaptations |
| Kaikki/Wiktionary | Eligible text is generally CC BY-SA 4.0, which permits commercial use subject to obligations | Credit Wiktionary contributors, source entries, license, and modifications. Separately licensed media are not distributed here |
| Tatoeba | Text entries can carry CC BY 2.0 France or explicitly designated CC0 terms | Preserve sentence IDs, source links, author credits and applicable license conditions. No Tatoeba audio is distributed |
| Dicts original build scripts | MIT | Keep the MIT notice on the original project code; **MIT does not cover the redistributed dictionaries** |

**Do not assume you may:**
- Label all included data MIT, public domain, or proprietary;
- Remove source copyright/attribution records;
- Prevent downstream recipients from exercising CC BY-SA rights on original or adapted content;
- Treat availability on GitHub as permission to redistribute material under any desired terms;
- Claim the original projects endorse your application;
- Combine GPL/GFDL/CC BY-SA datasets into a new derivative database without assessing license compatibility.

Creative Commons Attribution-ShareAlike licenses can permit **paid commercial applications** and redistribution, but attribution, change notices and adapted-data ShareAlike obligations remain enforceable. Other packages may impose different or additional requirements. Selling independent software features does not confer exclusive rights to third-party dictionary text.

**Consult the original license and, for a proposed commercial combined database, qualified counsel.** These repository notices are a compliance aid and do not replace legal advice.

Detailed documents:
- [Legal NOTICE](legal/NOTICE.md) — copyright, upstream authors, license separation and modifications.
- [Source licensing registry](legal/SOURCES.json) — machine-readable data-family provenance, licensing and required notices.
- [Release legal review checklist](docs/LEGAL-REVIEW-CHECKLIST.md) — checks before republishing or selling an integrated product.
- [Release-specific THIRD-PARTY-NOTICES](https://github.com/danilfg/dicts/releases/latest/download/THIRD-PARTY-NOTICES.md) — details for each actually published asset.
- The original LICENSE/ATTRIBUTION/TEI rights declarations included in individual archives.

## Repository layout

    dicts/
      .github/workflows/update.yml   Update-and-publish GitHub Action
      configs/sources.json           Configured upstream sources and language pairs
      src/build.py                   Downloading, checking and assembling indexes
      src/package_release.py         Combined ZIP and checksum generation
      tests/                         Build tests
      koreader/ freedict/ wikdict/    Dictionary source documentation
      kaikki/ tatoeba/               Expression and example data documentation
      legal/NOTICE.md                Copyright and third-party rights
      legal/SOURCES.json             Source and licensing registry
      docs/LEGAL-REVIEW-CHECKLIST.md
      LICENSE                        MIT license for original project code only

## Information for developers

Each release includes a manifest with the actual asset names, language pairs, source URLs, version information, SHA-256 digests, modification status and per-asset license evidence. The enrichment format also retains original source metadata per translation, meaning and example, allowing applications to display credits beside the data.

Developers should choose only the language pairs they need, verify downloaded files against their checksums, read the corresponding licenses, and preserve attribution when distributing or showing text. Using a StarDict reader does not automatically support the separate enrichment JSON.GZ format.

**Issue reporting:** [Open an issue](https://github.com/danilfg/dicts/issues) with the affected package, exact dictionary entry, upstream source or Tatoeba sentence ID. Third-party lexical content is redistributed **as-is** with no editorial guarantee of accuracy, completeness or fitness for any use, subject to non-excludable statutory rights. Claims about upstream entries should be directed to the data originator; packaging, licensing, integrity and repository issues may be reported here.
