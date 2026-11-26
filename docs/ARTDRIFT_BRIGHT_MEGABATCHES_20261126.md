# Art Drift — Mega-batch arte luminosa, 26 novembre 2026

## Obiettivo e soglia estetica
Priorità a dipinti moderni, paesaggi/giardini/marine/fiori, colori vivaci e luminosi, ritratti ridotti a zero nell'editorial shortlist. Le immagini **tanto scure** vengono eliminate o messe in HOLD. Soglia di ricerca sui pixel veri: luminanza media >= 0,55, pixel con luminanza <0,31 non oltre il 10% dell'immagine, saturazione media >= 0,18 e pixel vivaci >= 0,18. Esito colorimetrico non sostituisce QA visivo.

## Fonti e batch effettivamente eseguiti
| Fonte | Attività | Stato registrato |
|---|---|---|
| NGA / National Gallery of Art | PR #69, wave 1+2 | **27** opere eleggibili per QA estetico, 2 opere troppo scure messe in HOLD; non importate nel canvas |
| Met OA / Metropolitan Museum | Full MetObjects.csv ufficiale: **503.479 schede** analizzate | **278** nuovi candidati metadati, NON tutti approvati |
| Met OA / immagini ufficiali | 8 batch image QA sui 278, hash/pixel/museo | **21** immagini colorimetricamente PASS, 257 eliminate/HOLD |
| CMA / Cleveland Art | 6 batch API + image QA | **8** immagini colorimetricamente PASS, altre 5 MET dei primi 18 batch coincidevano con il successivo audit MET completo |
| SMK / National Gallery of Denmark | 8 batch API, esclusi 70 ID collegati a PR #68 | **7** immagini colorimetricamente PASS |
| AIC / Art Institute of Chicago | 6 batch metadata search OA e immagine | metadati trovati, ma **nessuna immagine tecnicamente verificata** per blocchi HTTP 403 da host d'immagine: non conteggiare come importabile |
| Wikimedia Commons | 8 batch per artisti PD, CDN ufficiale e licenza file | pipeline sperimentale; NON conteggiare fino a manifest definitivo e controllo attribuzione |

**Senza ricontare i cinque MET già inclusi nei primi 13 risultati, le nuove opere che hanno superato almeno i gate di immagine sono 36 = 21 MET + 8 CMA + 7 SMK.** Non equivalgono a 36 opere editorialmente e giuridicamente pronte all'import.

Il report QA estetico `research/mass_bright/20261126/bright_consolidated_editorial_review.json` identifica **18 opere nuove** esaminate tramite contact sheet (11 PRIORITY_BRIGHT, 7 LIGHT_BUT_SOFT) e sposta i titoli a scene religiose, stampe a inchiostro di tavolozza spenta, e alcune composizioni fuori dal gusto richiesto in HOLD/esclusione editoriale. **Totale 27 NGA + 18 nuove = 45** candidate editoriali prima degli ulteriori controlli giuridici e delle wave Wikimedia.

## Evidence / link verificabili
- Official NGA selected and 2 dark HOLD: `research/nga/20261126/nga_bright_combined_shortlist.json`.
- 18 independent AIC/CMA/MET jobs: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45813706451 (some individual zero-result jobs failure; aggregate succeeded).
- Full official MET OA CSV: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45815636520 (PASS).
- MET actual item/image verification: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45815859462 (PASS).
- SMK multilingual image verification: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45814424944 (some zero-result jobs failure; aggregate succeeded).
- Persisted OA scene metadata queue (278 only, image HOLD): `research/mass_bright/20261126/met_full_csv_scenic_queue.json`.
- MET real image QA 21: `research/mass_bright/20261126/met_full_csv_verified_bright.json`.
- CMA+MET initial image QA: `research/mass_bright/20261126/bright_mass_combined.json`.
- SMK 7 real image QA: `research/mass_bright/20261126/smk_megabatch_verified.json`.

## Safeguards
1. No changes to `assets/museums`, `assets/gallery`, runtime canvas, Flutter, Drift Core, GalleryDrift, user favorites, or APK.
2. Source image OA/PD is not automatic worldwide commercial legal clearance. Still requires per artwork third-party rights and territorially appropriate clearance.
3. Image batch jobs may have **zero** qualifying artworks: job failure from zero-selection is not proof that CI code is broken; always consult per-batch evidence, source API HTTP status and aggregator stats. Future improvement: accept documented empty shards gracefully.
4. Commons experimental image files must show exact official thumbnail URL, explicit per-file PD/CC0 metadata, artist provenance and final duplicates with museum image SHA. Wikimedia may rate-limit with HTTP 429; obey limits, do not retry aggressively.
5. Stop and flag if source downloads return HTTP 403/429 or lack official image. Do not replace with guessed URLs or unauthorized assets.
6. PR #70 is stacked on PR #69, and unrelated PR #68 contains 53 modern art sources and 24 SMK discoveries. Keep independent while auditing rights and provenance.
7. Priority: use user-approved aesthetics, not filling quantity quotas with dark paintings.

**Status at checkpoint:** Source research and technical validations performed, editorial shortlist saved; no legal final import or deployment.

## Wave Wikimedia Commons: otto batch CONCLUSI (26 novembre)
- Workflow https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45815982003: **8/8 shard PASS + aggregazione PASS**. Scaricate immagini reali dal CDN ufficiale `thumb.wikimedia.org`, senza bypassare rate limit; la versione prima del fix non era valida per questo conteggio.
- **2.703** possibili file ricerca nel metadata sweep, **880** raster scaricati/verificati, **113** file Open Access PD/CC0 con luminosità e pixel vivaci sopra i limiti; **1.823** file non ancora verificati pixel per ragioni di limite batch. I 113 hanno ID file Commons distinti, **non sono garantiti opere uniche** (copie fotografiche diverse della stessa tela possibili).
- Secondo filtro più severo di vivacità: saturazione media >= 0,24, quota pixel vivaci >= 0,30, con 17 esclusioni editoriali esplicite di duplicati sospetti, disegni beige, ritratti o opere già rappresentate; **58 file Commons in shortlist cromatica forte**, **55 in HOLD** per soggetto, palette o possibile duplicato. Altre verifiche su stessa opera fra musei, provenienza, paese di diffusione e dispositivi restano obbligatorie.
- Nuovo manifest `research/mass_bright/20261126/commons_pd_color_stronger_editorial_queue.json`, raw verified `research/mass_bright/20261126/commons_pd_bright_verified.json`.
- Contando le registrazioni per fonte (senza pretendere di aver risolto tutte le duplicazioni inter-museo): **27 NGA + 18 museo extra + 58 Commons = 103 candidature stilistiche di partenza**. Zero opere di queste wave importate nella app.

Per una crescita ulteriore del catalogo non bisogna scambiare i 2.703 metadati Commons con immagini effettivamente approvate; serviranno batch separati per i rimanenti 1.823 media e collaudi individuali.
