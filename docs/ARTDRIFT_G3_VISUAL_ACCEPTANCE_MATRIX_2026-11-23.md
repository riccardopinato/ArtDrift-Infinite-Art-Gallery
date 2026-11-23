# Art Drift — G3: verifica visiva dei 10 mock-up approvati

**Data:** 23 novembre 2026. **Stato:** `G3_PARTIAL — NON CERTIFICATO`.

**Contratto:** `ARTDRIFT_INTERACTIVE_MOCKUP_DECISIONS_2026-11-23.md` (10/10 approvati in chat).  
**Candidato originale verificato su screenshot:** PR #40 `10158a5bf9cdce9010a32afc6eff8cd2962f326d`.  
**Revisioni correttive sul candidato:** `4837f525e49fe0dd7f6e743434ce9ff3120f8dc1` (cornice proporzionata), `3f983a9303e47eeca33b9257a65b9ef3f5e026ff` (flight artwork-only), `ff6932ae23405b42e19b7ac4a2c6287e2ca0c4a5` (X a destra); la certificazione G3 richiede screenshot/video e CI **sullo stesso HEAD finale**.

## Evidenze acquisite: 9 stati dell'app su emulatore

- [G3 run 45182960994](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45182960994): **SUCCESS**, commit QA `2231d01854d6ed8564c98ada95e6b621750c8d66` (script test) sulla base candidata `10158a5...`, artifact **14822837342**, 9 screenshot 1080×2400 + XML UI + zero eccezioni fatali registrate.
- Visualizzati: `01_home`, `02_search_atrium`, `03_favorites`, `04_curator_settings`, `05_artwork_detail`, `06_next_artwork`, `07_long_press_plaque`, `08_auto_speed_menu`, `09_immersion`.
- Il tentativo precedente [45181446813](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45181446813) aveva cliccato un quadro al posto del pulsante 25%: **test invalido per il caso 7**, corretto e rieseguito. Nel rerun il popup mostra 25/50/75/100. Nessun errore funzionale prodotto accertato da quel primo tentativo.
- **Non si dispone di tutti i dieci mock-up interattivi archiviati come PNG/golden pixel-exact nel repository**. Il controllo qui è la conformità **al contratto testuale approvato** e alle schermate reali, non una certificazione pixel-per-pixel di layout da screenshot reference.

## Tracciabilità visiva slot 1–10

| Mock-up | Evidenza osservata | Stato G3 corrente | Azione prima di approvazione |
| --- | --- | --- | --- |
| **01 Quiet Canvas** | 01 Home, 09 Immersione: toolbar e Auto scompaiono, rimane comando `Mostra comandi` | **PRELIMINARE** | Misurare comparsa/scomparsa automatica dopo esplorazione, TalkBack, visibilità recenter, camera prima/dopo |
| **02 Targhetta museale** | 07: pressione prolungata apre targhetta sull'opera reale con autore, titolo e azioni | **PRELIMINARE POSITIVO** | 20 long-press in posizioni multiple, conflitti con pan/pinch, tooltip, chiusura |
| **03 Zoom contestuale** | 05 visualizzazione statica. Nel candidato vecchio la route completa veniva scalata e la cornice non seguiva il formato: **non conforme** | **CORRETTO IN CODICE — VIDEO DA VERIFICARE** | La patch G2 anima solo la preview dal `Rect` globale della tessera; verificare 350–480 ms, cornice progressiva, X in alto a destra, reverse/tile identity, reduced-motion |
| **04 Scheda di sala** | 05/06: cartellino avorio con titolo/autore/anno e azioni; comando `Leggi la scheda` visibile | **PRELIMINARE** | Espansione, scroll, informazioni mancanti, telefonini piccoli, banner simulato |
| **05 La mia collezione** | 03: archivio avorio in stato vuoto, X per uscita | **PRELIMINARE** | Galleria con 1/50 preferiti, rimozione e riapertura opera, persistenza, camera |
| **06 Atrio della ricerca** | 02: overlay avorio, input con tastiera, filtri e collezioni reali | **PRELIMINARE** | Risultati reali su query, suggerimenti, panoramica senza tastiera, ritorno camera e query conservata |
| **07 Regia dello scorrimento** | 01/08: Auto/Pausa + popup effettivamente aperto con 4 ritmi | **PRELIMINARE POSITIVO** | Scelta e persistenza 4 velocità, pan interrompe Auto, 60/120Hz fisico, no overlay nascosto |
| **08 Gabinetto curatore** | 04: titolo editoriale e sei lingue; sezioni Pro, privacy e licenze visibili | **PRELIMINARE** | Scorrimento fino diagnostica, tocco lingua+riavvio, dimensione carattere 1.6 |
| **09 Portale museo** | Copy italiano esatto e retry verificati dai test Flutter del candidato, **non mostrati nel G3 emulatore** | **CAPTURE IN CORSO** | Screenshot reali dei widget loading e unavailable (run golden dedicato), traduzioni, retry offline effettivo |
| **10 Passeggiata tra quadri** | 05/06: precedente/successivo cambia opera e metadati; cornice in noce sul dettaglio | **PRELIMINARE** | Verificare cornice non alterata dal nuovo format, 30 passaggi, cuore, Android wallpaper, URL museo, frame video |

### Difetti rilevati direttamente e correzioni (in Draft, senza merge)

1. **G3 bug nel test di selezione Auto, non nell'app:** screenshot 08 dell'esecuzione 45181446813 non apriva il menu. Coordinate corrette e screenshot 45182960994 ora valido; **RESOLVED_QA**.
2. **Cornice sproporzionata nel dettaglio:** screenshot 05/06 vecchi mostravano troppo spazio scuro e artwork molto piccolo all'interno di una cornice grande quasi quanto l'intera area del viewer. Modificato viewer: rapporto originale quando noto, fallback senza cropping e frame bloccato all'aspetto della prima opera; intagli vettoriali originali discreti. **FIXED_SOURCE, NEEDS_RENDER_REVIEW**.
3. **Transizione non conforme:** il componente scalava la route con didascalia e comandi, non la singola opera. Sostituito con preview animata sopra la pagina, rettangolo iniziale globale e fade neutro se è cambiato ID. **FIXED_SOURCE, NEEDS_MOTION_REVIEW**.
4. **X nella posizione errata:** screenshot 05/06 la mostrano in alto a sinistra; mock-up 3/10 richiede alto a destra. Commit `ff6932a...` la sposta a destra, con cuore adiacente a sinistra e test di posizione. **FIXED_SOURCE, NEEDS_RENDER_REVIEW**.

### Nuove acquisizioni richieste / eseguite

- Ramo QA `feat/artdrift-g3-ui-capture-frame-20261123` fondato su candidato `3f983a9...` (antecedente alla X a destra), [run 45187179195](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45187179195). Tenta 12 screenshot (incluso ritorno alla camera) + file MP4 9s dell'animazione reale. **Non sostituisce accettazione su HEAD definitivo**, poiché la X è stata modificata dopo il ramo.
- Ramo QA `feat/artdrift-g3-portal-goldens-20261123` basato su `ff6932a...`, [run 45188138150](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45188138150): genera PNG Flutter dei due stati del portale. Golden generati non sono reference approvati automaticamente.

## Requisiti trasversali non ancora chiusi

- 320/360/390/412/600/840dp; portrait/landscape; fontScale 1.0/1.3/1.6; screen reader e reduced motion (emulatore attuale una sola risoluzione).
- Banner futuro: unit/widget test **0/50/90 dp** su canvas `ArtAdAwareViewport` superati alla CI `10158a5...`, **non** screenshot test dei modal sheet/dettagli con banner. Nessun SDK né annuncio è attivo; non dedurre accessibilità del banner quando un sheet modale è aperto.
- FPS 60/120Hz, p95/p99/jank, 10min memory, ANR/OOM fisici: **NOT_MEASURED**. Due frame `gfxinfo` non sono campioni sufficienti.
- Certificato di firma degli APK CI diverso fra build: nessuna compatibilità upgrade in-place accertata con telefono. **G5_NO_GO**.
- PR #33/#34/#35 (catalogo), #36 (documentazione), #37/#38/#39 (fasi), #40 (candidato), Gallery Drift #15 (pin QA) ancora isolate e non fuse; verificare di nuovo prima di un'eventuale decisione successiva.

**Decisione:** `G3_HOLD` fino a prove video/screenshot della release candidata sulla stessa SHA, confronto ai 10 contratti approvati e accettazione visiva esplicita. Nessun merge, nessuna firma pubblica e nessuna prova di aggiornamento dei dati sono state eseguite.

## Aggiornamento G3 — correzioni source e nuove prove

**Candidato aggiornato:** Art Drift PR #40 `279ec531760a6f202a8867a23c7dd0d38a743383`. Il precedente SHA `ff6932ae...` ha superato tutta la CI Android ([run 45187429803](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45187429803)). Il HEAD `279ec531...` è soggetto alla propria [CI 45189795612](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45189795612); non eredita il verde precedente in modo automatico.

1. **UX-03/10 — source corretto:** la cornice in noce segue l'aspetto dell'opera iniziale, resta stabile durante precedente/successivo, e l'animazione usa esclusivamente la preview del quadro (non ridimensiona l'intera pagina). L'ancora è convertita da coordinate canvas locali a rettangolo globale prima della navigazione; ritorno neutro quando cambia l'identità. La X è adesso in alto a destra; il cuore è a sinistra della X. Test di geometria e disaccoppiamento pagina/preview aggiunti.
2. **UX-09 — screenshot leggibili:** [run 45188974485](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45188974485) **SUCCESS**, artifact **14824618214**, due golden Flutter 390×844 di loading ed errore. Sono stati caricati font Sans/Serif reali nel test (non più Ahem). Copy italiano approvato presente, pulsante Riprova visibile. I caratteri di alcuni ornamenti del codice vecchio apparivano come quadratini; sulla PR #40 il commit `62bf0aec19d95e4217fb464a57698b9471b4f6ad` li sostituisce con icone Material vettoriali. **Nuova cattura successiva al commit non ancora disponibile.** I PNG di golden sono mock rendering della UI, non prove di network/retry lato Android.
3. **UX-01 — Quiet Canvas:** nel candidato vecchio l'Immersione manuale funzionava ma l'Auto museale e la toolbar esterna non attenuavano l'opacità dopo l'inattività. Aggiunti `AnimatedOpacity` (3 s, 350 ms) nel solo percorso `museumControls: true`, Listener Art-only per ripristino al tocco e test di idle/restore nel Core, commit `279ec531760a6f202a8867a23c7dd0d38a743383`. **Sorgente corretto, screenshot dinamici e CI finale da confermare.**
4. **Video G3 primo tentativo:** [run 45187179195](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45187179195) **FAILED PER AMBIENTE EMULATORE**: ADB `device offline` / `error: closed` e processo emulator-5554 irraggiungibile, prima dell'acquisizione completa (`05_artwork_detail.png` vuoto). Artifact parziale 14823564740. **Non dedurre un crash dell'app né validità/non validità dell'animazione da questo run**.
5. **Video G3 secondo tentativo isolato:** [run 45189143707](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45189143707), ramo QA separato dal commit `ff6932ae...` con un solo avvio e screenrecord 9 secondi (apertura, chiusura, cambio opera, chiusura). **IN ESECUZIONE** all'annotazione; non segnarlo come evidenza finché il MP4 non è prodotto e ispezionato. È comunque precedente alle ultime due rifiniture Portale/Quiet.
6. **Gallery Drift consumer regression:** il default di Core è invariato, ma il ramo QA di Gallery PR #15 ha pin temporaneo aggiornato al Core `279ec531...` (commit Gallery `820cfb7bea0cc6e9bd623e0ef90a8317758efbe6`). [Run 45189960820](https://github.com/riccardopinato/GalleryDrift/actions/runs/45189960820) e [45189949702](https://github.com/riccardopinato/GalleryDrift/actions/runs/45189949702) **in corso**. Gallery `main` non toccato.

**G3 complessivo: HOLD**. Il confronto del mock-up approvato è testuale e non pixel-exact; manca still/video su HEAD definitivo per flight/quiet e visualizzazione con banner, fontScale e più formati. G4/G5 non certificati; `main` intatto.

## G3 update — current build / consumer gates / motion evidence (23 November 2026)

### Independently completed checks

- **Art Drift #40 current candidate** `279ec531760a6f202a8867a23c7dd0d38a743383`: [CI #45189795612](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45189795612) **SUCCESS** (Flutter/Core analysis, tests, internal ARM64 APK), artifact **14825721422**. This is a code CI pass, **not a final visual/performance/signature release certification**.
- **Gallery Drift consumer QA #15**, temporary Core dependency pin at the same Art SHA `279ec531...`: [runs #45189960820](https://github.com/riccardopinato/GalleryDrift/actions/runs/45189960820) and [#45189949702](https://github.com/riccardopinato/GalleryDrift/actions/runs/45189949702) both **SUCCESS** (including Gallery's own Android build). Gallery `main` remains untouched.
- **G3 speed picker** rerun #45182960994 **SUCCESS**: all 4 museum Auto options visible in actual Android screenshot. 
- **G3 portal goldens** #45188974485 **SUCCESS**, using real serif/sans fonts; note that the vector ornament replacement on #40 postdates the golden images.

### Video capture caveat / alternative

- [Original frame-video run #45187179195](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45187179195): **FAILED** — virtual Android device became unreachable; `error: closed`; only five screenshot files valid in partial artifact 14823564740.
- [Single-launch video retry #45189143707](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45189143707): **FAILED**, logs show `adb: device offline` and `error: closed` before usable MP4; artifact 14824579862 holds only `01_before_open.png`, `display_size.txt`, `pid_before.txt` and an empty `screenrecord.log`. **Not evidence of an Art Drift runtime crash**. Do not count an MP4 as captured.
- Alternative **deterministic Flutter animation-frame QA** branch `feat/artdrift-g3-flight-frames-20261123`, commit `d48843705554874ea75ffa82da26a4768ff0b737`, based on exact app HEAD `279ec531...`: [run #45194694125](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45194694125). Six output PNGs requested at flight phases 0/25/50/75/100% and different-artwork neutral-fade fallback, using genuine bundled `assets/gallery/thumbs/874.webp` rather than stock or a fabricated picture. **PENDING** until CI and human screenshot examination; these are component-level renderings, not a physical-device capture or an exact approved reference.
- All G3 gates remain **HOLD** until supported visual evidence and user acceptance. No merge to Art Drift or Gallery Drift `main`; no APK update over an installation with unknown signer.
