# Art Drift — Consolidamento PR #42, #43 e #44

Data di lavoro: 24 novembre 2026. **Candidato in Draft: non distribuire né unire a `main` senza gate.**

## Composizione

- PR [#42](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/pull/42): 4.499 opere preesistenti + 27 Commons + 558 quattro nuovi musei Smithsonian = **5.084** opere in cinque file catalogo. Le nuove 585 sono **già comprese** in 5.084, non un lotto ulteriore.
- PR [#43](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/pull/43): basata esattamente sulla testa della #42; contiene Worker D1 read-only, ricerca museale FTS e client Flutter opzionale. Lo stesso catalogo 5.084 risulta già importato in D1 `museum_works` e verificato con test E2E Worker, senza dipendere da questa nuova PR.
- PR [#44](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/pull/44): 535 righe in una tabella D1 separata `artdrift_museum_ingest`, scritte e verificate nell'esecuzione [45297815828](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45297815828). Di queste, 233 Tate + 253 MoMA contengono **solo metadati** e 49 Cleveland sono **già nel catalogo 5.084**; 535 `HOLD`, nessuna pubblicata.
- Questo ramo è basato su PR #43 (include #42) e integra soltanto i 10 file applicativi/docs di #44 e un workflow di QA **senza scritture remote**, preservando schema separato, verifiche copyright e crediti.

## Regola di identità: non sommare ciecamente i conteggi

La tabella `museum_works` usa una `source_key` per **ID interno della app** (esempio Cleveland `cleveland:20095272`); la tabella `artdrift_museum_ingest` usa **ID nativo del museo** (`cleveland:95272`). Le chiavi testuali sono diverse pur rappresentando la stessa opera.

**Deduplica canonica:** (`museum_source`, `museum_native_id`) della tabella base corrisponde a (`provider`, `native_id`) dello staging. Non collassare titoli/artisti uguali tra musei diversi: «Untitled» non identifica da solo un'opera.

Attesa condizionata al controllo CI effettivo: **5.084 + 535 − 49 = 5.570 identità distinte**, delle quali **486** sono solo nuove schede metadata-only, **49** sovrapposte da Cleveland. Questo totale NON significa 5.570 opere visibili, licenziate o pronte per il canvas.

Il codice `tools/artdrift_consolidate_catalogs.py` ricostruisce i cinque cataloghi originali attraverso lo stesso normalizzatore canonico di #43, poi riconcilia i 535 record con fingerprint e URL consentiti. Rifiuta dati malformati, duplicati nella stessa origine e conflitti nei titoli sulla stessa identità primaria. Genera un `consolidation_report.json` analizzabile (inclusi i 49 abbinamenti). Verifica identità senza modificare l'APK o eseguire query D1 di scrittura.

## Deduplica esposta nella API

`GET /api/v1/modern-approved` della PR #43 legge soltanto `artdrift_publishable_modern_art`, ovvero opere con `APPROVED` + `IMAGE_RIGHTS_VERIFIED`. L'ulteriore filtro SQL esclude qualsiasi riga già presente in `museum_works` **per identità nativa o per `source_key`**. Questo previene la riproposizione delle 49 Cleveland dopo un'eventuale approvazione.

Sullo staging D1 attuale, tutte le 535 righe sono in `HOLD`: il nuovo endpoint (solo dopo deploy Worker) non restituisce alcuna nuova immagine.

## Sicurezza e diritti

- **Nessuna approvazione automatica**; autore e copyright dell'opera, immagine e credito restano oggetto di revisione. Le 27 Commons Creative Commons non sono equiparate a pubblico dominio. Le 558 Smithsonian richiedono ulteriore QA per singola opera.
- Tate e MoMA (486 nuovi identificativi) sono **solo metadati**: non mostrarli come tile con immagine inventata.
- Cleveland: 20 corrispondenze piene, 28 fallback WebP/JPG preview-as-full correggibili e 1 differenza URL ulteriore; 9 voci Rousseau fuori brief da rivalutare, 7 con titoli di porte/decorazioni. Le 28 rettifiche restano proposte SQL testate, non eseguite da questa PR.
- `CLOUDFLARE_ACCOUNT_ID` / `CLOUDFLARE_API_TOKEN` non sono copiati in file. Workflow D1 consolidato **non contiene alcun comando `d1 execute`** né ingressi per scritture remote; può solo effettuare `wrangler d1 info` in lettura e preparare artefatti.
- Il Worker non è distribuito da questo ramo. Client Flutter `ARTDRIFT_ENABLE_APPROVED_MODERN` resta disabilitato per default. Canvas, Supabase, preferiti e R2 non vengono toccati.

## Gate di chiusura

1. Test Worker Node, Flutter analyze + test + Web + Android ARM64, test Python importer e controllo SQL SQLite.
2. Workflow D1 completa staging consolidato, controllo 49 sovrapposizioni e consegna del report. Nessuna pubblicazione.
3. Riconciliare l'ordine delle PR stacked #41, #42, #43 e questo delta prima del merge. **Non unire la #44 direttamente a main in parallelo**, perché lo stesso codice è ora inserito nel ramo consolidato.
4. Prima di approvare opere o abilitare il canvas: revisione giuridica/editoriale dei singoli record, QA immagini su dispositivo reale e test perf D1/Worker.
