# Dicts GitHub Pages — multilingual dictionary search

**Public website:** https://danilfg.github.io/dicts/

The [responsive site](../site/) supports English/Russian interface language,
independent source/target language selection, reversing the direction,
pronunciation via browser TTS, source-separated word entries, and direct links
to original data licenses and repository releases. It never generates
translations with a language model.

## Sources and what is actually indexed

| Source | What the website displays | How indexed |
|---|---|---|
| KOReader | Complete readable source articles for the initial six language directions; also original articles for language directions without a compact enrichment | Selected original published StarDict ZIP files |
| FreeDict + WikDict | Original complete articles for the initial six directions; additional available language pairs through **compact enrichment indexes** | Main dictionary release, without redistributing every full article into Pages |
| Kaikki | Available compact Wiktionary meanings/expressions | Main release enrichment |
| Tatoeba | Available example sentences with translations and source credits | Main release enrichment; no audio |
| Open English WordNet | Definitions, related words, synonyms | Source-attributed English lookup shards derived from the original published WordNet |
| Open Multilingual Wordnet | Definitions and synonyms in the currently indexed English/Spanish OMW resources | Original WN-LMF archives, cited and individually licensed |
| ConceptNet | Semantic relations and related concepts in indexed English/Spanish datasets | Selected real edges extracted from the full official ConceptNet assertions release |

**Semantic relations are not literal bilingual translations.** Full raw
Kaikki/Tatoeba corpora and complete original WordNet/ConceptNet archives
are independently named assets in unified versions in [GitHub Releases](https://github.com/danilfg/dicts/releases).
The bounded WordNet/ConceptNet Pages lookup data must not be described as
the entire original graph.

## Indexing, limits and all language pairs

All search data are compiled into per-pair and per-source **gzip-compressed
hash shards**. The browser loads only the shard needed for the searched word.
The published `data/catalog.json` is authoritative: language options appear
only for pairs whose searchable data are actually published.

The [all-language-pairs workflow](../.github/workflows/pages-all-pairs.yml)
has successfully deployed **753 searchable language directions** using approximately **932.5 MB** of page assets. It downloads the main dictionaries from **this repository's Releases**, verifies
source checksums, and attempts to index every published language direction.
To meet GitHub Pages' **1 GB** limit, the builder prefers compact
FreeDict/WikDict indexes where available, while keeping complete KOReader
archives for directions **without** compact equivalents and keeping original
full entries for six core English/Russian/Spanish/German directions.

This choice conserves space without dropping entire language directions.
**It does not mean that every original source's entire dictionary is indexed
on Pages.** Full original source ZIP files remain downloadable and source
attribution is preserved for the entries actually displayed. The workflow
fails if a published language direction is missing or the site exceeds the
limit; a successful run is required before claiming expanded live coverage.

The older [legacy full-ZIP Pages workflow](../.github/workflows/pages.yml)
is manual-only: its original attempt produced over 1 GB of compressed output
and could not be published.

## Automatic updates

- [All dictionary pairs](../.github/workflows/pages-all-pairs.yml): for
  successful unified update runs, new dated versions and manual runs
- [WordNet and ConceptNet](../.github/workflows/pages-lexical.yml): for
  new dated versions and manual runs; historical lexical downloads remain available
- [UI-only updates](../.github/workflows/pages-quickstart.yml): deploys
  the changed website with copied already published shards, without
  re-downloading or rebuilding the complete dictionary collection

The first successful [GitHub Pages configuration](https://github.com/danilfg/dicts/settings/pages)
requires **Build and deployment → Source → GitHub Actions**. Pages Actions
must have Pages write and ID-token permissions. Deployment can be retried
if GitHub temporarily rate-limits its Pages API.

## Reliability, licensing and attribution

The actual source packages, source status, hashes and licensing notices
are recorded in each dataset's release manifest. The project MIT license
does not apply to the original source content.

The website renders external content as **text, not active HTML**.
Even source-separated entries may contain incomplete or erroneous content:
there is no guarantee of linguistic accuracy. For per-source terms
and redistribution obligations see [legal/NOTICE.md](../legal/NOTICE.md).

## Unified release pipeline

The monthly update workflow now stages sources (retaining verified prior data when upstream fails), creates normalized release packs, validates them, publishes, and invokes the Pages reusable workflow. Pages downloads only the prepared `pages` and `pages-lexical` groups, verifies hashes and extracts them. The full application indexes are separately available in Releases and are not subject to the Pages 1 GB site cap. Manual Pages deployment is for recovery after a successful normalized release.
