# Art Drift — acquisizione arte moderna e staging Cloudflare D1

Stato: **PR candidata / ART_ONLY**. Non modifica Drift Core, Gallery Drift, l'APK, il canvas, i preferiti o i cataloghi esistenti.

## Baseline verificata

- Art Drift main: `2dac51a6be98ed364d1e95983d1f330c84354ef7`.
- Gallery Drift main: `dde42c11d96ee6258670b01ce9e7b3c273cc56ab`, che punta a Drift Core `2dac51a`.
- App Factory Core: `ede07c491e586215598ff68daec43e17d699aa51`, Master v27 / Golden Index v31.
- Contratti consultati: Versioned Editorial Catalog, Import/Export e Provenance Ledger (tutti **DRAFT**, non copie certificate).

## Fonti e stato operativo

| Fonte | Stato attuale | Regola |
|---|---|---|
| Tate Modern / Tate Britain | **ADAPTER PRONTO**: CSV pubblico GitHub, filtro artisti famosi + tecniche pittoriche | Solo metadati CC0; **nessuna immagine Tate**. Snapshot storica aggiornata l'ultima volta nell'ottobre 2014 |
| Guggenheim New York + Peggy Guggenheim Venezia | **ADAPTER CANDIDATO**: Wikidata P195 e Wikimedia Commons, ID musei Q201469 / Q1054284 | File Commons CC0/PDM con prova per file; età dell'autore e licenza sottoposte comunque a revisione editoriale |
| Paris Musées (MAM) | HOLD: GraphQL richiede account/token | Solo immagini CC0 per oggetto; non aggirare autenticazione |
| Barnes Foundation | HOLD: download per opera | Pubblico dominio per singola opera, non per intera collezione |
| Finnish National Gallery | HOLD: API/dump disponibili, schema media da validare | Diritti CC0 per singola immagine |
| Belvedere Vienna | HOLD: download Open Content CC0, nessun bulk API verificato | Solo oggetti contrassegnati CC0 |
| Yale University Art Gallery | HOLD: IIIF | IIIF non equivale a licenza: verifica open access dell'oggetto |
| Nationalmuseum Stockholm | HOLD: oggetti PD, CC BY-SA e protetti | Art Drift attualmente richiede PD/CC0 |
| Nasjonalmuseet Oslo | HOLD: DigitaltMuseum | Diritti su oggetto e fotografia distinti, CC BY-NC non ammessa |
| Te Papa Wellington | HOLD: REST API | Licenze metadati e fotografie distinte |
| Birmingham Museum of Art (USA) | HOLD | Politica specifica dell'ente |
| Birmingham Museums Trust (Regno Unito) | HOLD | Ente distinto; non presumere CC0 universale |

**HOLD** significa che questa PR non implementa né rivendica scraping per quella fonte. Non usare scraper HTML non autorizzati.

## Come funziona

Pipeline: `fonte ufficiale → adattatore → record canonico → verifica diritti → SQL D1 staging → revisione editoriale separata`.

- Un ID stabile `provider:native_id` impedisce duplicati e preserva identità tra importazioni.
- Il contenuto è identificato da fingerprint SHA-256; riimportazioni uguali sono idempotenti.
- Variazione del fingerprint revoca l'eventuale approvazione precedente (`HOLD`).
- Ogni import parte da `publication_status=HOLD` senza cancellare opere assenti da un nuovo batch.
- La view `artdrift_publishable_modern_art` espone solo record approvati con immagine, licenza ed evidenza verificabili.
- Foto e file HD **non entrano in D1**; D1 riceve metadati e URL, non byte immagini.
- Non è ancora stato creato un client D1 per l'app né un R2 proxy: la PR non cambia quanto mostrato sul canvas.

## Riproduzione locale / generazione SQL

Python 3.11+; solo standard library.

    python -m unittest discover -s tools -p 'test_artdrift_museum_ingest.py' -v
    python tools/artdrift_museum_ingest.py --source tate --max-records 500
    python tools/artdrift_museum_ingest.py --source wikidata --max-records 100

Output non versionato:

    .artdrift_ingest/modern_art.jsonl
    .artdrift_ingest/modern_art.sql

Verifica gli output prima di un caricamento, anche se i test sono verdi.

## Collegare un database D1 ESISTENTE

Non creare nuovi servizi Cloudflare, account o spese tramite questa PR. Quando database, permessi e quota sono confermati:

    npx wrangler@4 d1 execute NOME_DB --remote --file=cloudflare/d1/migrations/0001_museum_ingest.sql
    npx wrangler@4 d1 execute NOME_DB --remote --file=.artdrift_ingest/modern_art.sql

L'Action `D1 modern-art staging` offre un workflow manuale per sorgente, numero record e `upload_remote` (default **false**). Se si usa l'upload, servono secrets `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` e variabile `ARTDRIFT_D1_DATABASE` già configurati. Non condividere i valori nella chat o nel repository.

Cloudflare D1 non accetta `BEGIN TRANSACTION`/ `COMMIT` espliciti negli import Wrangler. L'SQL generato non contiene transazioni manuali.

## Gate QA e diritti

I test coprono: filtro Tate, esclusione immagini non licenziate, artista morto troppo recentemente, host contraffatti, corretta evasione SQL, fingerprint, duplicati, filtro della view. CI test e run di acquisizione live restano distinti; nessun numero di opere nuove o caricamento D1 è dichiarato finché non è verificato.

La licenza della *fotografia* non basta a garantire la riutilizzabilità dell'*opera rappresentata* in tutte le giurisdizioni. Prima della pubblicazione servono controlli su copyright dell'artista, provenienza, eventuali diritti dei fotografi, attribuzione e permessi di distribuzione.

## Fonti primarie

- https://github.com/tategallery/collection
- https://www.wikidata.org/wiki/Q201469
- https://www.wikidata.org/wiki/Q1054284
- https://commons.wikimedia.org/
- https://apicollections.parismusees.paris.fr/en/opendata
- https://www.barnesfoundation.org/collection/open-access-and-copyright
- https://sammlung.belvedere.at/opencontent/images
- https://kokoelma.kansallisgalleria.fi/en/api-sovelluskehittajille
- https://developers.cloudflare.com/d1/best-practices/import-export-data/
- https://developers.cloudflare.com/d1/platform/limits/

Provenienza codice: **NEW_IMPLEMENTATION** (nessun codice proprietario di musei copiato).