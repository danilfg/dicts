# FreeDict — all available pairs

The GitHub Actions builder discovers **every language pair** listed in the official [FreeDict machine-readable catalog](https://freedict.org/freedict-database.json); there is no fixed six-pair allowlist. Each pair is independently downloaded, checksum-verified against upstream SHA-512, and checked for a TEI license statement. All publishable StarDict packages are offered in Releases as `freedict--<pair>.zip`. Unavailable/unlicensed/incompatible packages are **reported as skipped** rather than silently claimed complete.

FreeDict dictionaries have **separate licenses** (some GPL/GFDL). Exact source TEI and attribution evidence accompany each transformed ZIP; the output remains under the original licenses. Read the original documents before commercial redistribution. Data accuracy and translation quality are the responsibility of the upstream authors; this independent aggregator does not verify linguistic correctness.
