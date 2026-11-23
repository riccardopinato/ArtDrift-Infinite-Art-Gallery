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
| Guggenheim New York + Peggy Guggenheim Venezia | **ADAPTER CANDIDATO**: Wikidata P195 e Wikimedia Commons, ID musei Q201469 / Q1049033 (verificato su Wikidata) | File Commons CC0/PDM con prova per file; età dell'autore e licenza sottoposte comunque a revisione editoriale |
| Paris Musées (MAM) | **Wikidata P195 candidato Q857276**; GraphQL ufficiale **HOLD** perché richiede token | Solo immagini CC0 per oggetto; non aggirare autenticazione |
| Barnes Foundation | **Wikidata P195 candidato Q808462**; API/download ufficiale **HOLD** | Pubblico dominio per singola opera, non per intera collezione |
| Finnish National Gallery | **Wikidata P195 candidato**: Q754507 Ateneum + Q2983474 National Gallery; API/dump ufficiale **HOLD** | Diritti CC0 per singola immagine |
| Belvedere Vienna | **Wikidata P195 candidato Q303139**; bulk API ufficiale **HOLD** | Solo oggetti contrassegnati CC0 |
| Yale University Art Gallery | **Wikidata P195 candidato Q1568434**; IIIF ufficiale **HOLD** | IIIF non equivale a licenza: verifica open access dell'oggetto |
| Nationalmuseum Stockholm | HOLD: oggetti PD, CC BY-SA e protetti | Art Drift attualmente richiede PD/CC0 |
| Nasjonalmuseet Oslo | **Wikidata P195 candidato Q1132918**; DigitaltMuseum ufficiale **HOLD** | Diritti su oggetto e fotografia distinti, CC BY-NC non ammessa |
| Te Papa Wellington | HOLD: REST API | Licenze metadati e fotografie distinte |
| Birmingham Museum of Art (USA) | HOLD | Politica specifica dell'ente |
| Birmingham Museums Trust (Regno Unito) | HOLD | Ente distinto; non presumere CC0 universale |

**HOLD** significa che questa PR non implementa né rivendica scraping dalla relativa API ufficiale. La ricerca Wikidata, dove presente, è un percorso **separato** e subordinato alla disponibilità di Wikidata Query Service. Non usare scraper HTML non autorizzati.

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
    python tools/artdrift_museum_ingest.py --source moma --max-records 5000
    python tools/artdrift_museum_ingest.py --source verified --max-records 5000
    python tools/artdrift_museum_ingest.py --source bulk --max-records 5000
    # Solo quando WDQS non impone rate limit:
    python tools/artdrift_museum_ingest.py --source wikidata --museum Q1049033 --max-records 100

Output non versionato:

    .artdrift_ingest/modern_art.jsonl
    .artdrift_ingest/modern_art.sql

Verifica gli output prima di un caricamento, anche se i test sono verdi.

## Collegare un database D1 ESISTENTE

Non creare nuovi servizi Cloudflare, account o spese tramite questa PR. Quando database, permessi e quota sono confermati:

    npx wrangler@4 d1 execute NOME_DB --remote --file=cloudflare/d1/migrations/0001_museum_ingest.sql
    npx wrangler@4 d1 execute NOME_DB --remote --file=.artdrift_ingest/modern_art.sql

L'Action `D1 modern-art staging` offre un workflow manuale per sorgente (incluso `bulk`), numero record e `upload_remote` (default **false**). Se si usa l'upload, servono secrets `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` e variabile `ARTDRIFT_D1_DATABASE` già configurati. Non condividere i valori nella chat o nel repository.

Cloudflare D1 non accetta `BEGIN TRANSACTION`/ `COMMIT` espliciti negli import Wrangler. L'SQL generato non contiene transazioni manuali.

## Gate QA e diritti

I test coprono: filtro Tate, esclusione immagini non licenziate, artista morto troppo recentemente, host contraffatti, corretta evasione SQL, fingerprint, duplicati, filtro della view. CI test e run di acquisizione live restano distinti; nessun numero di opere nuove o caricamento D1 è dichiarato finché non è verificato.

La licenza della *fotografia* non basta a garantire la riutilizzabilità dell'*opera rappresentata* in tutte le giurisdizioni. Prima della pubblicazione servono controlli su copyright dell'artista, provenienza, eventuali diritti dei fotografi, attribuzione e permessi di distribuzione.

## Fonti primarie

- https://github.com/tategallery/collection
- https://www.wikidata.org/wiki/Q201469
- https://www.wikidata.org/wiki/Q1049033
- https://commons.wikimedia.org/
- https://apicollections.parismusees.paris.fr/en/opendata
- https://www.barnesfoundation.org/collection/open-access-and-copyright
- https://sammlung.belvedere.at/opencontent/images
- https://kokoelma.kansallisgalleria.fi/en/api-sovelluskehittajille
- https://developers.cloudflare.com/d1/best-practices/import-export-data/
- https://developers.cloudflare.com/d1/platform/limits/

Provenienza codice: **NEW_IMPLEMENTATION** (nessun codice proprietario di musei copiato).
## Lotti verificati e aggregazione offline (24/11/2026)

Acquisizione reale GitHub Actions (non dato teorico):
- Tate: **233** metadati pittorici, senza immagini.
- MoMA: **253** metadati pittorici, senza immagini (CSV Git LFS ~73 MB).
- Catalogo Open Access *già presente nell'app*: **65** URL di immagini CC0 accettati da policy tecnica, ancora in `HOLD` editoriale.
- Combinazione prevista: **551** record distinti per `source_key`; il merge effettivo va confermato sul workflow corrente. Le 65 opere non sono necessariamente nuove per l'app.
- Wikidata Query Service ha restituito **HTTP 429 durante incidente (1 req/min)**: il workflow non avvia automaticamente ricerche Wikidata parallele.

Il job `merge_staged` scarica gli artefatti dei tre job di **uno stesso run**, ricontrolla fingerprint, provenienza e diritti con `tools/artdrift_merge_staging.py`, elimina duplicati identici e rifiuta conflitti. Applica il file SQL in SQLite in memoria **due volte** per controllare idempotenza e verifica che la view pubblicabile rimanga vuota.

Esecuzione offline su artefatti scaricati:

    python tools/artdrift_merge_staging.py \
      .artdrift_inputs/tate/modern_art.jsonl \
      .artdrift_inputs/moma/modern_art.jsonl \
      .artdrift_inputs/verified/modern_art.jsonl

**Importante**: `IMAGE_RIGHTS_VERIFIED` nel file di staging indica che la policy automatica di acquisizione ha trovato un'indicazione esplicita di licenza e provenienza. Non equivale a una nuova revisione legale indipendente delle 65 immagini. Serve sempre `publication_status=APPROVED` dopo revisione prima dell'uso in produzione.

### Configurazione Cloudflare non dimostrata

Il repo non contiene un binding/configurazione D1 di produzione verificabile, e i secret GitHub non sono ispezionabili da questa pipeline. Nessuna esecuzione di staging locale garantisce l'esistenza del database remoto o il corretto binding di Wrangler. `upload_remote` resta **false** per default; prima di attivarlo vanno verificati ID del database, autorizzazioni API, migrazione e limiti D1. Non configurare approvazione `APPROVED` tramite import generico.
