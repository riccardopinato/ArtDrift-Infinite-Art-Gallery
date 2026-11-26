# Art Drift: 486 source-linked reproduction rights audit (26 November 2026)

Scope: the exact 486 candidates from PR #84 (`b82a4574db3d504141b6d2e95e403aa743c771e3`), including 485 Commons file IDs and Städel 1350.

Every file gets individual source-license evidence, credit/artist/source fields, file SHA change checks, attribution terms, provider context, and a distinct HOLD reason. The source-rights workflow queries live Wikimedia Commons imageinfo in 4 shards with maximum 2 parallel workers, no API-proxy workarounds, and fail-closed missing-file or rate-limited handling.

**Publication gate remains closed:** 0 commercial approvals; no runtime app/catalog changes, no Cloudflare writes, no automatic merge, no rights approval based on age or Commons tags.

**Legal scope:** EU 70 years after painter's death generally applies to the actual painting when artist identity is correct; Art. 14 Directive (EU) 2019/790 and Italian LDA Art. 32-quater govern non-original faithful copies. Italian cultural heritage code arts. 107/108 may impose additional access/reuse conditions. Other territorial laws, creative photos, individual CC BY and BY-SA credit/SA obligations, and direct museum rights must be reviewed.

**Städel case:** Sisley *Bank of the Seine in Autumn*, inventory 1350, work-specific official museum page says Picture Copyright: Public Domain, while upstream record claimed CC BY-SA 4.0. Preserve this conflict and review file provenance before use:
https://sammlung.staedelmuseum.de/en/work/bank-of-the-seine-in-autumn

Primary sources:
- https://eur-lex.europa.eu/eli/dir/2019/790/oj
- https://www.normattiva.it/atto/caricaDettaglioAtto?atto.codiceRedazionale=21G00192&atto.dataPubblicazioneGazzetta=2021-11-27
- https://www.normattiva.it/atto/caricaDettaglioAtto?atto.articolo.numero=108&atto.codiceRedazionale=004G0066&atto.dataPubblicazioneGazzetta=2004-02-24
- https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia
- https://creativecommons.org/licenses/by-sa/4.0/
