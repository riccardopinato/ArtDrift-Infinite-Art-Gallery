# Art Drift — G1: congelamento baseline, evidenze e blocchi prima del redesign

**Data della ricognizione:** 23 novembre 2026  
**Progetto:** Art Drift / Gallery Drift (Drift Core condiviso)  
**Ambito autorizzato:** G1 — lettura e documentazione delle baseline; **non** implementazione Flutter o merge.  
**Stato G1:** `PARTIAL_EVIDENCE_COLLECTED / HOLD_FOR_TARGET_AND_PHYSICAL_BASELINE`.  
**Design approved:** 10/10, **design implemented:** 0/10 in questa PR.  
**Fonti normative:** `docs/ARTDRIFT_INTERACTIVE_MOCKUP_DECISIONS_2026-11-23.md`, `docs/ARTDRIFT_10_MOCKUP_INTEGRATION_QA_PLAN_2026-11-23.md`, `docs/ARTDRIFT_ADMOB_VIEWPORT_CONSTRAINT_2026-11-23.md`.

> **Distinguere sempre:** SHA/test/artefatti accertati, visual review preliminare su screenshot, risultati Android emulatore, misure prestazionali fisiche e selezione della baseline definitiva. **G1 non è PASS** finché manca la decisione tecnica sul target di integrazione e la baseline device con firma/upgrade.

## A. Due baseline candidate congelate per confronto, nessun cherry-pick

| Identità | Git SHA completo | Versione dichiarata | Provenienza / stato |
| --- | --- | --- | --- |
| **BASE-A `main`**, versione effettivamente nel branch canonico | `2dac51a6be98ed364d1e95983d1f330c84354ef7` | `0.3.5+8` | Branch main verificato; Android CI run **45086740148** successful, 2026-11-23 00:10 UTC |
| **BASE-B candidato QA v0.3.8**, top della catena | `c2d1d3e91cef0cee3005a0fdda151ff34ac903e9` | `0.3.8+11` | PR **#35 Draft**, basata su #34 e #33; Android CI run **45139436958** successful, emulatore run **45139436849** successful, 2026-11-23 08:38 UTC |
| PR #33 — catalogo originale 4.499 | `1d7c8f7a010add291948e8a4fc102436abc361c6` | candidato | Draft, base `main`; Android CI **45091170739** + Web CI **45091170750** successful |
| PR #34 — manifest 2.400 opere | `c89d426bb1c4129271df130f5ce18f35710273e4` | candidato | Draft, basata su #33; Android CI **45097133021** e curation CI **45097133006** successful |
| PR #35 — QA emulatore | `c2d1d3e91cef0cee3005a0fdda151ff34ac903e9` | candidato | Draft, basata su #34; QA script e documento, **non** un redesign |
| PR #36 — documenti mock-up e piano G1 | `docs/artdrift-visual-decisions-20261123` | non-applicabile | Draft, base `main`; cambiamenti solo `docs/`, nessuna UI implementata |
| PR #22 — diagnostica prestazioni | `929bf7526dda3e6c862ff23a7d914e980783e08f` | ramo precedente | Draft su `feat/artdrift-android-visual-first-20261122`, **non presente in main o BASE-B** per presunzione |

**Baseline definitiva d'implementazione: `UNDECIDED`.** BASE-A e BASE-B sono **fotografie immutabili e separatamente identificabili**, non due insiemi di commit liberamente componibili. Consiglio tecnico: prendere **BASE-B come candidata di riferimento visuale e funzionale**, perché include l'asset mix 2.400 e QA, ma usarla per la PR di design **solo dopo** decisione e riconciliazione delle PR #33/#34/#35 e relativi gate. BASE-A resta il confronto canonico. Nessuna promozione eseguita.

### Differenze strutturali comprovate

Git tree: gli **stessi sei file** in `packages/drift_core/` hanno **blob SHA identici** fra BASE-A e BASE-B. La struttura condivisa non cambia in questo confronto. Sono diversi in BASE-B `lib/main.dart`, `lib/canvas/infinite_gallery.dart`, `lib/screens/artwork_detail.dart`, `lib/screens/favorites_sheet.dart`, `lib/screens/search_sheet.dart`, `lib/screens/settings_sheet.dart`; invece `lib/ui/gallery_toolbar.dart` e `lib/ui/localization.dart` sono byte-identici. La manifest `assets/museums/canvas_visual_color_v1.json` è **presente solo in BASE-B**. Gli asset/modelli non vanno ricostruiti da screenshot.

### Contratto condiviso Gallery Drift (lettura, nessuna scrittura)

- Gallery Drift `main@dde42c11d96ee6258670b01ce9e7b3c273cc56ab`.
- Il pin **effettivo** in `GalleryDrift/pubspec.yaml` è `drift_core` da Art Drift commit `2dac51a6be98ed364d1e95983d1f330c84354ef7` e `packages/drift_core`. La documentazione `GalleryDrift/docs/DRIFT_CORE_CONSUMER.md` riporta un **SHA precedente** `832ae259aa2988fc3b0e1db261034a596a9a793f`: discrepanza di provenance **da riconciliare in una PR Gallery separata**; non modifica il pin effettivo.
- Gallery PR **#12** e **#14** risultano Draft: nessuna modifica foto/albums/permessi/gallery in questo G1.
- Cambi futuri a gesture/tile-anchor/Auto in Core richiederanno verifica su entrambi i consumatori e pin PR distinto. Nessuna implementazione parallela del Core in Art.

## B. Prove CI e artefatti realmente recuperati

| Fonte | Risultato verificato | Campo di applicazione |
| --- | --- | --- |
| [main Android CI run 45086740148](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45086740148) | `completed/success`, analyze/test/ARM64 internal APK | BUILD/CI di BASE-A, non collaudo visivo su dispositivo |
| [BASE-B Android CI run 45139436958](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45139436958) | `completed/success`, Flutter 3.50.1, Core test, Flutter tests, build release ARM64, identity e signer report | BUILD/CI su exact SHA `c2d1d3e...`, non G3/G4 |
| [BASE-B emulator run 45139436849](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45139436849) | `completed/success`, test emulatore Pixel 6 API35 x86_64 software GPU, **48 swipes** | Smoke Android/emulatore G1; non device fisico / FPS |
| BASE-B emulator artifact | ID GitHub **14801876239**, nome `ArtDrift-Emulator-Pan-Memory-Report`, 3.955.026 bytes, screenshot + report JSON | Materializzato/estratto e ispezionato nella sessione; **artefatto con scadenza (30 giorni circa)**, non archivio permanente |
| BASE-A ARM64 artifact | ID **14780255007**, ZIP 11.105.940 byte; APK interno **20.734.906 byte** | Artifact recuperato da run 45086740148 e SHA-256 verificato |
| BASE-B ARM64 artifact | ID **14802440244**, ZIP 29.444.547 byte; APK interno **39.786.803 byte** | Artifact recuperato da run 45139436958 e SHA-256 verificato; signing **INTERNAL_TEST_ONLY** |

### Impronte immutabili degli artefatti scaricati

| File | SHA-256 |
| --- | --- |
| `BASE-A/app-release.apk` (20.734.906 B) | `e05138fb8ad5b80d7cccb1bd6a5e97e386977255147dace6d508b9c668f38308` |
| `BASE-B/app-release.apk` (39.786.803 B) | `7ba967e305d8e52630be591d98e2fa8105022457c89d24871e5ce481998124a7` |
| BASE-A artifact ZIP | `abbf4f2feba3340a01a7e5dd239a48878a605dd36756afe974df67531d10662a` |
| BASE-B artifact ZIP | `90c3e62c2154c37d6a2376f7c751006e21be75dce7a0b610e92eeebc1135dd72` |
| QA emulatore artifact ZIP | `083ef664943f0745b3f2eb5f4886b3254a8dc816a55c8e5217cdebf378a266b2` |

**Dimensione APK:** BASE-B è **+19.051.897 byte (+91,883%)** rispetto a BASE-A nei due APK interni. Questa è una differenza **preesistente al redesign**, da tenere come budget/riscontro nella G4; non attribuire la crescita a cambi estetici mai implementati e non confondere ZIP compressi con APK interni.

**Firma e identità:** il report `apk-integrity.txt` di BASE-B dichiara source SHA `c2d1d3e...`, package `com.riccardopinato.artdrift`, `SIGNING_CLASS=INTERNAL_TEST_ONLY`. `apk-signer-report.txt` dichiara signer **Android Debug**, v2 certificate SHA-256 `61e90e80d993e490fc87caa7bb2ebd0243ec814d1fe300a97fea363091722b0d`. **Questo NON prova la compatibilità della firma dell'APK installato sul telefono.** Nessun installer o upgrade è stato eseguito. La firma BASE-A non è stata certificata con un signer-report omologo in questo G1.

## C. Evidenza emulatore G1 effettiva — JSON e immagini esaminate

Provenienza: run [45139436849](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45139436849), artifact ID **14801876239**, file originali `screenshot_before.png`, `screenshot.png`, `report.json`. Le due PNG sono **1080 × 2400 px**, RGBA.

| Attributo test | Valore osservato |
| --- | --- |
| Dispositivo | **Emulatore** Pixel 6 / Android API35 / x86_64 / software GPU |
| Radio/airplane | Flight mode flag 1; Wi-Fi e data disattivati; **non** network packet audit |
| Processo | Avviato prima e sopravvissuto dopo |
| Gesti conclusi | **48/48** (12 cicli di quattro direzioni, riproducibili in script) |
| screenshot_before | **2.081.113 B**, SHA-256 `d9e753f660eb60824ab11c9d64a2d9f4a210e4658039528bb1627dc7d071b072` |
| screenshot_after | **1.867.611 B**, SHA-256 `8684dad9bb54c60279e78ec0491e1367ad434b66de3ca20fe4f86713fa0c063d` |
| PSS processo prima | **111.796 KiB** |
| PSS processo dopo | **110.210 KiB** |
| Fatal AndroidRuntime registrati | **0** (log vuoto) |
| Smoke del parser | **PASS**, lista failures vuota |
| `gfxinfo` frames rendered | **0** |
| FPS / frame-time p50/p95/p99 | **NOT_MEASURED**: numeri stampati da gfxinfo in assenza di frame validi sono **invalidi**, **non** prestazioni dell'app |
| Baseline fisica, batteria, termica | **NOT_TESTED** |

**Verifica visiva preliminare effettuata sui due PNG:** il mosaico contiene realmente opere e non solo placeholder; dopo i 48 gesti la finestra inquadra un'altra porzione di opere mentre rimangono leggibili **ricerca a pennello centrale, cuore, ingranaggio e recenter**. Non emergono schermate completamente bianche o errori di rendering macroscopici. Questa ispezione **non** conferma cromia/calibrazione, riconoscibilità di ogni singola opera, perfetta geometria world→tile, vera fluidità o parità col mock-up approvato. Il branding compatto e la leggibilità dei controlli Auto attenuati, e gli inset con status/navigation bar, vanno verificati sul display reale; **non** si segnano già come bug certi da sole immagini.

**Persistenza immagini:** nel flusso G1 corrente i PNG e ZIP sono stati recuperati localmente per analisi, ma **non committati nel repository** (strumenti GitHub testuali e no modifica di assets). L'artifact GitHub conserva gli originali fino alla scadenza della retention. **Prima della futura integrazione** archiviarli stabilmente con SHA e snapshot di riferimento degli **stessi 10 mock-up approvati**, poiché gli AppBlock interattivi nella chat non costituiscono Golden pixel-exact versionate nel codice.

## D. Evidenze G1 mancanti / gate aperti

| Gate | Stato oggi | Cosa serve per chiuderlo |
| --- | --- | --- |
| **G1.1 — Sorgenti e Core pin** | **PASS_SOURCE_SNAPSHOT** | SHA Art main, candidato, Gallery, PR e Core confrontati; ripetere se cambiano |
| **G1.2 — CI exact-head** | **PASS_CI_EXISTING** | GitHub Actions main e PR35 success, nessun test specifico dei 10 mock-up |
| **G1.3 — Screenshot baseline candidato** | **PARTIAL_VISUAL_REFERENCE** | Due PNG di emulatore ispezionati; archiviazione durevole e scenario esteso ancora aperti |
| **G1.4 — Screenshot BASE-A/main** | **NOT_CAPTURED** | Compilazione/inquadratura comparabile stessa impostazione, orientamento, risoluzione, catalogo differente da annotare |
| **G1.5 — Metriche fisiche su stesso device** | **BLOCKED_PHYSICAL** | Dispositivo Android, release/profile, 60/90/120 Hz se supportato, PSS, frame timings p50/p95/p99, startup, 60s pan+Auto+zoom, termica/memoria |
| **G1.6 — Persistenza / update installato** | **BLOCKED_DEVICE_SIGNER** | APK realmente installato: `applicationId`, `versionCode`, fingerprint cert, copia/pre-backup preferiti e camera; test upgrade in-place senza disinstallare né cambiare firma |
| **G1.7 — Target implementativo unico** | **UNDECIDED** | Decisione PR base `main` o candidato #35 dopo gestione stack #33/#34; non merge implicito |
| **G1.8 — Mock-up visual references** | **NOT_ARCHIVED** | Dieci screenshot/video delle varianti approvate + coppia scenario/criterio; niente nuova UI reale |
| **G1.9 — Privacy/immagini commerciali** | **NOT_CLEARED_FOR_RELEASE** | Review diritti e policy separati da G1; nessuna pubblicazione o AdMob |

### Procedura di completamento G1 sul dispositivo (futura, non eseguita)

1. Leggere `adb shell pm path com.riccardopinato.artdrift`, versione e firma dell'**app installata** senza sostituirla. **Non rimuovere o reinstallare** per test di semplice lettura.
2. Salvare privacy-safe il conteggio/ID di preferiti e camera persistita; no backup privati in GitHub. Testare successivo upgrade solo con **stessa firma** e versione più recente.
3. Fotografare/acquisire schermate della versione realmente installata: 320/360/390/412dp, portrait/landscape, display con gesture bar. Separare BASE-A e BASE-B; evitare confronti pixel-identici fra cataloghi diversi.
4. Su release/profile a condizioni ripetibili: 3 × 60s pan, 3 × 60s Auto, 20 pinch, 30 detail open/close, startup offline e con rete, lettura frame Flutter (build+raster), PSS e screen recording.
5. Registrare tempi assoluti e regressioni solo dopo campioni grezzi; non derivare FPS da artifact emulator con 0 frame.
6. Misurare layout con **banner simulato** assente/50/90dp e cambio dinamico (non SDK): questa è evidenza del futuro contratto, non prova AdMob reale.
7. Congelare SHA del target e approvare confronto prima di scrivere Dart; altrimenti mantenere `HOLD_FOR_BASELINE`.

## E. Decisione G1

**PASS limitato alle evidenze documentali:** SHA, Core parity, CI artifact metadata, input APK fingerprints e screenshot emulatore di BASE-B.  
**HOLD complessivo:** nessuna baseline fisica comparabile, mancano capture BASE-A e 10 reference asset durevoli, APK installato/firma ignoti, sorgente-target da decidere.  
**GO implementazione:** **NO**, fino a chiusura dei prerequisiti pertinenti.  
**Nessuna modifica eseguita:** `.dart`, `pubspec.yaml`, `packages/drift_core`, Gallery Drift, APK utenti, Ads SDK, permessi, file immagine nel repo, `main`.

Tutte le prestazioni citate sono **baseline emulator o build artifact**, non certificazione Android fisico, Play Ready o del redesign.
