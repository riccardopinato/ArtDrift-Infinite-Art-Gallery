# Art Drift — 283 candidature sul canvas interno, non pubblicabile

Le 283 immagini prioritarie sono prodotte da [PR #95](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/pull/95), workflow 45962610069, tramite 3 wave QA 100+100+83. La nuova build di test consente di **vederle insieme sul canvas**, non di certificarne o distribuirne automaticamente i diritti.

La versione normale della app ha `assets/museums/catalog_curated_commons_review.json = []` e `ARTDRIFT_INTERNAL_ART_REVIEW=false`, quindi non contiene il gruppo sperimentale. In una speciale build QA Android con `ARTDRIFT_INTERNAL_ART_REVIEW=true` e `ARTDRIFT_ENABLE_CURATED_COMMONS=true`, il workflow scarica direttamente i 283 record source-traced e genera il catalogo di revisione. Risultato atteso: **4.784 opere visualizzabili** (4.500 esistenti, 1 Sisley Met CC0, 283 preview). Tutti gli elementi di ricerca sono marcati `artdrift_research_only=true`, `commercially_approved=false`, `source_provenance_verified=false`, `worldwide_distribution_reviewed=false`; non sono inseriti nel catalogo commerciale.

Ciascuna schermata di dettaglio dichiara «REVISIONE INTERNA — NON PUBBLICARE» e mostra link a pagina file Commons, licenza dichiarata e crediti del riproduttore. L'esportazione come wallpaper è disabilitata.

Non viene eseguito alcun merge in main, deploy pubblico o produzione di APK commercialmente firmato. **Il vantaggio è verificare simultaneamente 283 opere su Android** senza verifiche seriali una alla volta. Le autorizzazioni per il rilascio commerciale rimangono un gate separato.
