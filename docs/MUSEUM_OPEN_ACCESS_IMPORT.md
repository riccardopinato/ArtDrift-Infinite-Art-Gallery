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

- **Due livelli per evitare APK enormi:** le prime 457 opere dispongono di miniature WebP offline (72 iniziali + 385 da sei musei); le successive 4.043 opere hanno **solo metadati** in un JSON da 3,69 MB e anteprime ufficiali via rete caricate a richiesta. Nessuna immagine HD incorporata.
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
- **Getty: 1 opera reale aggiunta**, *Irises* (Vincent van Gogh, **1889**, tecnica/medium registrati) con manifest e Canvas IIIF3 CC0 verificati. Il campo anno e l'artista sono derivati dai dati Linked Art ufficiali, non da stringhe costruite.
- Per NGA, dati Open Data CSV ~83/92 MB vengono **letti esclusivamente nel runner CI come stream**, non aggiunti al repository e non distribuiti con l'APK. Solo metadati/miniature finali.
- Resta aperto il collaudo Play/licenze commerciali e la scelta comune di mapping stabile con PR #8.

## Stato consolidato della PR #9 (senza merge)

- **385 opere internazionali reali**, 6 musei: Cleveland 150, Rijksmuseum 80, National Gallery of Art 60, Smithsonian American Art Museum 60, Metropolitan 34, Getty 1.
- 72 opere AIC preesistenti e intatte: **457 quadri totali disponibili nel canvas dell'app dopo un merge coordinato**.
- I 385 WebP aggiunti pesano **1.488.348 byte** (meno di 1,5 MB); catalogo internazionale JSON ~380 KB; nessuna foto ad alta risoluzione è stata incorporata.
- L'ultimo import di riparazione metadati Getty è terminato con successo nella [GitHub Actions #44900885772](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/44900885772). La CI Flutter e APK dell'head esatto deve essere valutata separatamente.
- Nessuna modifica della PR è stata ancora integrata in `main`; il merge sarà coordinato con Drift Core PR #8 e Gallery Drift.

## Espansione globale definitiva — 21/11/2026 (PR #9, senza merge)

- **4.500 opere complessive**: 72 WebP AIC iniziali + 385 WebP di altri musei + **4.043 record internazionali remoti**. Nessun file WebP aggiuntivo in questa ondata.
- **10 istituzioni uniche nel complesso**; il nuovo livello internazionale distribuisce: Cleveland 1.584, National Gallery of Art Washington 739, SMK Danimarca 500, Smithsonian American Art Museum 350, Smithsonian National Museum of Asian Art 350, Smithsonian National Portrait Gallery 225, Rijksmuseum 160, Metropolitan Museum of Art 135.
- **3.691.868 byte** di catalogo globale (non immagini), JSON con URL immagine ufficiale, titolo, autore e anno se presenti, mezzo/tecnica, dimensioni se presenti, museo, fonte e licenza, ID e revisioni. Totale delle miniature WebP offline nuove dalle wave precedenti: **1.488.348 byte**.
- **Importazione base globale:** [Actions #44901874348 SUCCESS](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/44901874348) ha acquisito 3.915 record preliminari (inclusi 629 AIC remoti).
- **QA immagini reale:** [Actions #44902484571](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/44902484571), 7 anteprime per gruppo: otto gruppi 56/56 HTTP 200, ma AIC remoto 0/7 (HTTP 403). La pipeline di smoke test iniziale *non* certificava la raggiungibilità nonostante il successo del job.
- **Quarantena AIC remoto:** eliminati 629 record non visualizzabili e sostituiti con **757 dipinti Cleveland CC0** (fonte e singoli diritti verificati), senza toccare i 72 dipinti AIC già disponibili offline. [Actions #44902738744 SUCCESS](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/44902738744); controllo idempotente/conteggi [#44902810169 SUCCESS](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/44902810169).
- **QA finale disponibilità anteprime:** [Actions #44902826929 SUCCESS](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/44902826929): 56/56 anteprime funzionanti in otto gruppi remoti, **zero errori nel campione**. La singola immagine tra le 4.043 potrebbe comunque non rispondere o avere condizioni di rete diverse su Android: collaudo completo/device non certificato.
- **Dati mancanti non inventati**: alcuni record non hanno autore, dimensioni o tecnica; schede sintetiche originali costruite solo da metadati effettivamente acquisiti. La descrizione museale coperta da copyright non viene copiata.
- **Coordinamento ancora aperto**: questo ramo non ha cambiato canvas motore/camera e non ha fatto merge in main. La stabilità posizione->opera dopo espansione dipende dalla versione del Drift Core nell'altra chat; la PR #9 conserva il proprio gate di accorpamento.
