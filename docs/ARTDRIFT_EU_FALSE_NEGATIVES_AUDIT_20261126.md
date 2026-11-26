# Art Drift — audit dei falsi negativi sui musei europei (26 novembre 2026)

## Rettifica della conclusione precedente
L'affermazione implicita "tre musei internazionali contengono un solo dipinto adatto" era **scorretta**. Il valore 1 nel report del primo campione era il risultato di una pipeline sperimentale incompleta, non il numero di opere coerenti disponibili nei cataloghi. L'audit ha trovato e riprodotto errori gravi di coverage/metadata e separato i veri blocchi da una qualità artistica insufficiente.

## Root cause documentate e rimedi
1. **Rijksmuseum**: `landschap` aveva 246 risultati (verificato da API); il codice leggeva **100**, senza seguire `next.id`. Inoltre su circa 270 ID nei tre gruppi di ricerca ne processava massimo 102 (34×3), in ordine SHA pseudo-casuale **prima di selezionare epoca e soggetto**. L'API Linked Art ufficiale supporta `creationDate=18??`/`19??` e `next.id`. Ho implementato paginazione, filtri per periodo, bilanciamento delle query e quattro canary ufficiali.
2. **Nationalmuseum Sweden**: dalla ricerca testuale ottenevamo 211/135/193 ID unici per shard, ma il programma estraeva solo i primi 34 in ordine SHA e **solo dopo** applicava controlli title/date/PD. Tutti i 87 risultati campionati saltavano la valutazione colori. Con qualificazione **prima** del cap sulle immagini il nuovo run ha richiesto 30+25+23=78 immagini e **5 file tecnicamente PASS**. Re-run: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45828680441.
3. **Städel Museum**: primi 200 record OAI letti contenevano **zero nodi LIDO**, prima intestazione `status=deleted`. I tombstone OAI non sono opere e non devono entrare nel denominatore di selezione. I primi tentativi di filtro `from` erano inoltre nella granularità errata. Ho aggiunto filtro per record attivi, datestamp completo, paginazione e fail-closed. L'endpoint non ha ancora prodotto record LIDO attivi nella sessione: stato corretto = **SOURCE_UNAVAILABLE_OR_PARTIAL**, **NON** "0 dipinti buoni". Le pagine ufficiali documentano realmente quadri impressionisti di Sisley, Pissarro e Cézanne.
4. **Cromia**: la soglia soggettiva di luminosità **55%** può escludere dipinti vivaci con meno del **20%** di superfici molto scure. Esempio verificato dal report raster Rijks: `SK-A-2288`, *Landscape on the Oise*, Daubigny, dark **19,06%** (entro il limite utente), sat **53,89%**, vivid **56,14%**, mean lum **49,35%** (respinto solo per media luminanza). La scheda ufficiale Rijks dichiara PD e pittura 1872. Esito da riaprire in **VISUAL REVIEW**, non distribuire automaticamente.

## QA sui cinque Swedish recuperati
Riferimento `research/museums/20261126/false_negative_recovered_swedish_visual_qa.json`:
- **2** preferiti da approfondire (Landskap; Cows in a Meadow);
- **2** facoltativi da valutare (Winter Landscape with Magpies; Summer Evening — figura umana presente);
- **1** escluso come soggetto centrato sulle persone (The Artist's Wife on the Beach);
- **0** pubblicati nel catalogo app o certificati per diritti worldwide.

## Controprove dai cataloghi ufficiali, non dal motore di ricerca interno
File `research/museums/20261126/official_artwork_counterexamples.json` — 9 opere/riferimenti a pagine istituzionali:
- Städel: Alfred Sisley *Bank of the Seine in Autumn*, Camille Pissarro *View of the Côte Saint-Denis, Pontoise*, Paul Cézanne *Landscape. Road with Trees in Rocky Mountains*, *Houses by the Bank of the River Zaan*.
- Rijksmuseum: Dijsselhof *Tulip Fields* (PD), Daubigny *Landscape on the Oise* (PD); inoltre Van Dongen *Still Life with Flowers* esiste ma è marcato **copyright eredi/Pictoright**, dunque non importabile senza diritti.
- Nationalmuseum: Larsson *Landscape Study from Barbizon*, Nils Kreuger *Evening in August*.

**Attenzione:** pagina ufficiale che conferma l'opera ≠ verifica pixel del file ≠ diritto commerciale worldwide. Il registro canary non è un lotto pronto per l'APK.

## Correzioni pipeline GitHub già apportate
- `tools/artdrift_eu_new_museums_batch.py`: search Rijks con periodo e paginazione; Swedish pre-filtro metadati; Städel OAI status e failure esplicito.
- `tools/artdrift_eu_new_museums_aggregate.py`: distingue `SOURCE_UNAVAILABLE_OR_PARTIAL` da `TECHNICAL_SAMPLE_ONLY`; `catalog_exhaustively_searched=false` e `source_zero_artworks_proven=false`.
- `tools/artdrift_eu_false_negative_audit.py`: replay su API ufficiali; report `research/museums/20261126/false_negative_diagnostics.json`.
- Nessun catalogo runtime, APK, componenti UI o file immagini live modificati.

## Direzione corretta
1. Harvest delle collezioni **a pagine e per epoche**, con tracking `seen/eligible/filtered/image_checked/unknown`, non batch 34 pseudo-casuali.
2. Ricerca multilivello su titolo, soggetto, scuola, artista, categoria e tag istituzionali; non obbligare "landscape" nel titolo.
3. Campionamento cromatico di tutte le immagini OA eleggibili senza considerare un 403/401 o record deleted come "opera scura".
4. Shortlist per **ranking** più che taglio netto alle medie: casi ad alta saturazione e dark ≤20% con luminanza sotto55% passano a REVISIONE VISIVA, non a pubblicazione.
5. Fonti ufficiali e diritti per opera, deduplicazione cross-museo per artista/titolo/dati + hash, solo dopo import a catalogo canonico.
6. Nessun risultato va presentato come esaustivo senza provare la copertura del denominatore.

**Esito:** diagnosi con falsi negativi confermati; correzione Swedish validata su GitHub; Städel bloccato nei feed attivi e con artwork documentato dal sito; sampling Rijks parzialmente corretto ma il gate cromatico necessita di valutazione curatoriale dei near-miss. Non dichiarare cataloghi vuoti o app aggiornata.

## P1 fix aggiuntivo: near-miss ad alta vivacità
Nella pipeline per il Rijksmuseum è stato introdotto `visual_review_exception()`: fra i casi scartati dal gate automatico, vengono recuperati **esclusivamente come HOLD di visione** gli oggetti con superfici molto scure ≤20%, media luminanza ≥46%, saturazione ≥30% e pixel vivaci ≥35%. L'obiettivo è non eliminare *Landscape on the Oise* (SK-A-2288: dark 19,06%, lum 49,35%, sat 53,89%, vivid 56,14%). I candidati sono etichettati `HOLD_HIGH_CHROMA_VISUAL_REVIEW__MEAN_LUMINANCE_ONLY` e la CI prepara un `visual_review_high_chroma.jpg` separato dal contact sheet delle immagini formalmente PASS. **Questa misura non cambia la soglia già approvata dall'utente, non importa opere e non autorizza immagini con copyright.** Aggiunto regression test nel suite `test_artdrift_eu_new_museums_batch.py`.


## P0 Städel follow-up: major works, GetRecord, CDN
The research collector now queries the museum's official scope:major OAI set,
ignores deleted tombstones, follows bounded resumptionToken pages and falls back
to ListIdentifiers + GetRecord for active LIDO records. The CDN of the official
museum is allowlisted with strict HTTPS and redirect checks. Metadata matches
titles or controlled LIDO subject terms; the painting year is taken only from
the Work conception/creation event, never from acquisition. OAI image links
are declared CC BY-SA 4.0 at feed level; per-image reuse and credit remain
HOLD. No app runtime assets, release, or canonical artwork imports are changed.
See https://sammlung.staedelmuseum.de/en/oai/guide .
