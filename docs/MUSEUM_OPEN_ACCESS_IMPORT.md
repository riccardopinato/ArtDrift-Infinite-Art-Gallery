# ArtDrift — PR musei Open Access (21/11/2026)

## Contratto di integrazione
Questa PR resta **DRAFT, senza merge** finché le PR parallele #7/#8 Drift Core e Gallery Drift non vengono riconciliate. L'ambito è **solo** immagini, catalogo, adattatori musei, provenienza/diritti e scheda dell'opera. Non modificare motore infinito, canvas, navigazione, ricerca semantica, impostazioni o billing.

Baseline ArtDrift main d329161c88f26eadf30e3f2ad3452c6e36aac604; App-Factory-Core 9391419c6b7c9c23c2f978262fe8fe6670c68160 (Master v27, Golden Index v31). Golden Versioned Editorial Catalog (draft), Offline Content Packs (draft).

## Fonti Open Access e stato import

| Fonte | Accesso verificato | Licenza / regola di ammissione | Stato |
|---|---|---|---|
| Art Institute of Chicago | AIC API e IIIF | is_public_domain=true | 72 già presenti, intoccati |
| The Metropolitan Museum of Art | Collection API v1.1 Search e v1 Object | isPublicDomain=true per record, dipinto e URL immagini ufficiale | Import attivo |
| Cleveland Museum of Art | Open Access API | share_license_status=CC0, type Painting, immagini su host ufficiale | Import attivo |
| Rijksmuseum | Linked Art Search + resolver + catena VisualItem/DigitalObject + IIIF micr.io | **solo** con edm:rights RDF/XML esplicito Public Domain Mark/CC0 per oggetto + IIIF | **80 opere reali importate** |
| National Gallery of Art (Washington) | dataset Open Data ufficiali NGA objects/published_images CSV | solo published_images.openaccess=1, painting e URL IIIF ufficiale | **60 opere reali importate** via streaming CSV |
| J. Paul Getty Museum | Linked Art / IIIF | solo singole immagini con CC0 su subject_to; non importare narrazioni coperte da copyright | Prova ufficiale IIIF3 per immagine CC0; massimo 1 opera verificabile, senza bulk enumerate |
| Paris Musées | API con account/token richiesto | diritto CC0 individuale | HOLD, nessuna chiave inclusa nell'app |
| Smithsonian Open Access | **archivio S3 ufficiale SAAM EDAN NDJSON pubblico senza chiave** | metadata_usage=CC0 E media.usage.access=CC0, pittura, host ids.si.edu | **60 opere reali importate** |
| Museo Egizio Torino | Catalogo dichiara immagini CC0 | nessuna API bulk pubblica qui verificata | HOLD, niente scraping |
| Pinacoteca di Brera | Catalogo online | uso commerciale non automaticamente autorizzato | HOLD |
| Wikimedia / Europeana | Aggregatori | diritti per file, attribuzione, prova fonte | HOLD |
| Google Arts & Culture | Visualizzazione | non è licenza di riuso | ESCLUSO |

## Dati per opera

ID stabile del provider, museo, titolo, autore se presente, anno/data se presenti, tecnica e materiali, dimensioni se disponibili, provenienza, credito, URL ufficiale, URL immagine, licenza e URL evidenza diritti. La descrizione breve in italiano è una frase **originale basata sui campi fattuali**, non il testo curatoriale soggetto a diritto d'autore.

## Peso, immagini, privacy

- Ogni nuova opera riceve una miniatura WebP di circa 220 px compressa a qualità 60. **Budget massimo 2,6 MB** di nuove miniature, massimo 22 KB per immagine; nessuna immagine full HD incorporata.
- Gli originali restano sui server ufficiali e vengono richiesti solo all'apertura o durante lo zoom. L'app conserva lo stesso limite alla cache RAM già previsto per il canvas.
- I 72 dipinti AIC e i relativi file sono mantenuti nello stesso ordine in catalogo. La galleria virtuale può ripetere le opere lontano; una futura sostituzione del mapping modulo catalogo è lavoro del Drift Core, **non da questa PR**. Espandere il catalogo modifica inevitabilmente l'associazione opera-cella: verificare dopo integrazione.
- L'import automatico e i controlli per licenze avvengono solo in CI su richiesta, senza API IA a pagamento e senza chiavi nel client; niente fetching massivo su dispositivi degli utenti.
- Per l'uscita commerciale servono riesame dei diritti per i file accettati, audit sulle condizioni dei provider, Privacy Policy ospitata e Play Data Safety.

## Gate di test

All'interno di Flutter test: numero di opere, ID univoci, licenza, provenienza, dominio e schema, presenza effettiva di ogni WebP e byte budget. GitHub Actions: flutter analyze, test, build APK ARM64 su head esatto della PR. Queste verifiche non equivalgono a collaudo visivo/fisico o approvazione legale dello store.

## Primo dataset importato e verificato

- **Run importazione base #44899564247 PASS:** 184 WebP, Met 34 + Cleveland 150, 696.194 byte immagini.
- **Run incrementale #44900334157 PASS:** **384 nuove opere**, ripartite **Cleveland 150 / Met 34 / Rijksmuseum 80 / NGA 60 / Smithsonian 60**. Nuovi WebP: **1.478.950 byte** totali; JSON di metadati: ~378 KB. Il totale dell'app comprende inoltre 72 opere AIC originali, quindi **456 opere**.
- Importer incrementale idempotente: preserva i primi 184 file, non riscarica miniature già verificate, memorizza provenienza, diritti e metadati; termina se il corpus non supera il gate minimo.
- La connessione Smithsonian tramite S3 ufficiale è confermata keyless con filtro CC0 su **singola immagine**, distinta dalla API Smithsonian che richiede una chiave.
- Getty: manifest IIIF3 per *Irises* riporta diritti CC0 sia al livello manifest sia al livello Canvas; il campione singolo può essere aggiunto soltanto dopo download e test asset. Il numero totale definitivo dipende dall'ultimo import e dai test Flutter esatti.
- Per NGA, dati Open Data CSV ~83/92 MB vengono **letti esclusivamente nel runner CI come stream**, non aggiunti al repository e non distribuiti con l'APK. Solo metadati/miniature finali.
- Resta aperto il collaudo Play/licenze commerciali e la scelta comune di mapping stabile con PR #8.
