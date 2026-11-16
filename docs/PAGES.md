# GitHub Pages multilingual dictionary search

**Site URL (after Pages activation):** https://danilfg.github.io/dicts/

The front end is in [site/](../site/) and the build code is in
[src/build_pages.py](../src/build_pages.py). The public user interface allows
independent selection of source and target languages, a reversible direction,
source-specific full dictionary articles, available Kaikki meanings, Tatoeba
examples, original publisher links and licensing information. Russian and
English interface locales are supported. It does not fabricate translations
using an online language model.

## Actual dataset and indexing

The [GitHub Pages deployment workflow](../.github/workflows/pages.yml)
downloads the **latest main release** source archives, not data from the
original publishers. It parses each KOReader, FreeDict and WikDict StarDict
ZIP and extracts complete readable text articles (not the previous compact
260-character snippets). Dictionary entries are kept separated by their
publisher and language pair. The published main compact enrichment indexes
are used only for additional source-attributed meanings and examples.

Each pair's entries are partitioned into reproducible hashed, compressed JSON
shards. The browser fetches only the shard required for a specific term,
rather than downloading hundreds of dictionaries. The catalog is generated
from real published pairs and records per-pair source coverage. The website
shows exact word or phrase matches, not fuzzy or inflected search.

The full raw Kaikki and Tatoeba corpora, all OMW/ConceptNet data, and the
standalone OEWN packages are **separate published resources**, not silently
presented as complete page translations. The site may show compact Kaikki
meanings and Tatoeba examples when included by a released enrichment index.
A user interface for WordNet and ConceptNet needs a specialized adapter.

## First-time activation

In the GitHub repository open **Settings → Pages → Build and deployment →
Source → GitHub Actions**. Administrative access is needed for this setting.

The [Build and deploy dictionary search](../.github/workflows/pages.yml)
Action runs when site/index code changes, can be launched via workflow_dispatch
and runs for new published `data-*` main dictionary releases. It does not
rebuild the website on `lex-*` or `raw-*` publications.

A successful Pages build and deploy produces
**https://danilfg.github.io/dicts/**. If deploy-pages reports that Pages is
not configured, select GitHub Actions as the Pages source and rerun the job.

## Limits and copyright

GitHub Pages has a published-site size limit of **1 GB**. The index generator
checks the site size and **fails explicitly** if the complete source-labelled
index would exceed the supported limit. It never silently drops a language
pair or source to fit the quota. If a future collection is too big, consider
serving the indexes from a separate CDN or implementing a dedicated search API.

The original source licenses still apply. The maintainer only aggregates,
publishes and verifies technical integrity, not dictionary accuracy.
See [Third-Party Data Notice](../legal/NOTICE.md).
