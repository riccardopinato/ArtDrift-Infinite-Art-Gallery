# Art Drift — Piano di integrazione verificabile dei 10 mock-up

**Data:** 23 novembre 2026  
**Stato:** PIANO DOCUMENTALE / **NON IMPLEMENTATO**, approvazione tecnica e QA ancora da eseguire  
**Branch di lavoro:** `docs/artdrift-visual-decisions-20261123` — PR documentale **#36 Draft**  
**Contratto estetico:** `docs/ARTDRIFT_INTERACTIVE_MOCKUP_DECISIONS_2026-11-23.md` (**10/10 approvati**)  
**Contratto viewport:** `docs/ARTDRIFT_ADMOB_VIEWPORT_CONSTRAINT_2026-11-23.md` (banner futuro; **nessun SDK attivato**)  
**Factory baseline ereditata dal ciclo di design:** `App-Factory-Core@ede07c491e586215598ff68daec43e17d699aa51`. Prima dell'effettiva implementazione, ri-verificare solo se il puntatore centrale è stato aggiornato; applicare Master/Golden pertinenti con nuove verifiche, non assumere che questo documento sostituisca la Factory.

> **Mandato del 23/11/2026:** trasformare le decisioni estetiche in un piano di integrazione verificabile e in criteri di collaudo **prima di applicarle all'app**. **Non autorizza modifiche a Dart/Flutter, Drift Core, Android, APK, AdMob, cataloghi, dipendenze o merge in main.** La realizzazione avverrà in una successiva PR implementativa distinta, solo su mandato esplicito.

## 1. Baseline verificata (lettura GitHub il 23/11/2026)

| Oggetto | Stato accertato |
| --- | --- |
| Art Drift `main` | `2dac51a6be98ed364d1e95983d1f330c84354ef7`; `pubspec.yaml` **0.3.5+8** |
| Art Drift PR #33 | **Draft, non in main**: catalogo candidato di 4.499 opere e immagini locali, base `main` |
| Art Drift PR #34 | **Draft, stacked su #33**: home visiva con 2.400 opere e selezione meno concentrata sui ritratti |
| Art Drift PR #35 | **Draft, stacked su #34**: raccolta evidenze emulatore/offline/pan; FPS e accettazione visiva fisica NON certificati |
| Art Drift PR #22 | **Draft, su vecchio ramo**: diagnostica p50/p95/p99 e cache; non dare per integrata né riprodurre dati non misurati |
| Gallery Drift `main` | `dde42c11d96ee6258670b01ce9e7b3c273cc56ab` |
| Gallery Drift `pubspec.yaml` | `drift_core` è importato da Git SHA Art Drift `2dac51a6be98ed364d1e95983d1f330c84354ef7` + path `packages/drift_core` |
| Gallery Drift `docs/DRIFT_CORE_CONSUMER.md` | Riporta ancora pin `832ae259...` (non uguale al pin corrente in `pubspec.yaml`): **incongruenza documentale da riconciliare**, non correggere automaticamente Gallery in questo lavoro |
| CI disponibili su Art `main` | `.github/workflows/android.yml` (Flutter 3.50.1, analyze/test, Drift Core test, APK ARM64 interno) e `web-preview.yml` (Flutter analyze/test, Chrome tests, web build); **nessun test goldens specifico dei 10 nuovi mock-up accertato** |
| Altri vincoli di prodotto | `AGENTS.md`, `docs/PRODUCT_RELEASE_GATES_v03.md`, `docs/REFERENCE_VIDEO_BEHAVIOR.md`, `docs/DRIFT_CORE_INTEGRATION.md` |

**Decisione preflight obbligatoria:** scegliere il codice-target dell'implementazione **DOPO** risoluzione o esplicita selezione dei PR stacked #33 → #34 → #35. Non creare un design branch su #33/#34/#35 per supposizione; conservare snapshot della versione in uso. Qualunque commit cambiato nel frattempo riapre il gate di baseline e i test interessati.

### Confini Art Drift / Gallery Drift

- `packages/drift_core` è il **motore condiviso canonico**: camera, pan/pinch/fling, layout deterministico, Auto e controllo velocità, tile gestures. **Non duplicare** la sua matematica dentro Art Drift.
- Le superfici museali, le fonti e gli URL ufficiali, il wallpaper e il contenuto sono **ART_ONLY**.
- Ogni aggiunta di callback/ancora della tessera/interfaccia di controllo nel Core è **SHARED_CORE**: progettare API opzionali compatibili, testare su Art e Gallery; solo dopo merge del canonico proporre un pin SHA aggiornato in Gallery tramite PR distinta e approvata.
- Album, permessi fotografici, cestino, foto private e ML on-device Gallery Drift sono **GALLERY_ONLY** e fuori ambito.

## 2. Strategia a gate: specifica → candidato isolato → prova → integrazione

**G0 — Contratto e rischi (questa PR).** Dieci decisioni approvate, requisiti e dipendenze tracciati, matrice di test e soglie candidate scritte; 0 modifiche Flutter. Evidenza: questo documento e registro 10/10. **Non implica** che un singolo mock-up sia certificato sul dispositivo.

**G1 — Congelamento baseline, prima di scrivere UI.** Registrare SHA esatti Art main/candidato, Core, Gallery pin e tutti i PR incidenti; foto/video baseline alle stesse risoluzioni, fontScale, impostazioni e catalogo della futura versione. Misurare tempi frame, PSS, tempo di caricamento, viewport e versione/firma APK installata. Prove di persistenza dati/camera/favoriti. **Acquisire in archivio revisionabile anche le 10 reference visive approvate in chat** (screenshot/registrazioni dei prototipi dove disponibili, ID, data, dimensione, hash e contratto testuale); i prototipi HTML in chat non sono asset Flutter né golden pixel-exact già presenti nel repo. Se baseline o reference non sono riproducibili, l'eventuale difformità va esplicitata e validata prima di implementare; non dichiarare parità visiva da una descrizione.

**G2 — Sviluppo isolato e test automatici**, quando autorizzato: PR implementativa separata da #36, feature flag/disattivazione sicura dove utile, commit piccoli e reversibili, Dart/Flutter analyze, widget/unit/integration tests e golden/screenshots in CI sul **HEAD esatto**. No merge fino a risultati G3/G4.

**G3 — Collaudo visivo e funzionale reale** sul candidato: revisione manuale screenshot/video e percorsi multi-touch/keyboard/TalkBack con evidenze firmate; test AdMob con **slot simulato** (no SDK), 0/50/90dp ed altezza variabile di prova, senza assimilare questi valori alle dimensioni pubblicitarie reali.

**G4 — Collaudo prestazionale comparativo** sullo stesso telefono e build release/profile: tempi frame reali, pan e zoom, opening transition, Auto 25/50/75/100, warm/cache, memoria, carico su sessione lunga e condizioni offline/rete lenta. Confrontare baseline e candidato; regressione oltre soglia → **STOP e riparazione**. Emulator PASS ≠ physical PASS.

**G5 — Accettazione di promozione**, sempre separata: approvazione del collaudo su dispositivo Android, verifica persistenza aggiornamento APK e compatibilità della firma prima del merge. Scoperta o mancata evidenza su uno dei gate → PR resta Draft. **Play Store / pubblicazione commerciale** richiede inoltre diritti immagini, firma stabile, hosted privacy policy, Data Safety e monetizzazione-consenso, non coperti dall'approvazione estetica.

### Stati di evidenza (non sostituibili)
`DESIGN_APPROVED` → `SOURCE_IMPLEMENTED` → `CI_GREEN_EXACT_HEAD` → `VISUAL_APPROVED` → `PHYSICAL_ACCEPTED` → `PROMOTION_AUTHORIZED`. `PLAY_READY` è un gate commerciale ulteriore. Non usare mai “PASS” senza prova, data, dispositivo e SHA.

## 3. Matrice di tracciabilità dei mock-up

| Slot | Intervento / punto di aggancio previsto | Ownership | Criterio oggettivo e test da aggiungere | Dipendenze |
| --- | --- | --- | --- | --- |
| **1 Quiet Canvas** | `DriftCanvas` attualmente attenua comandi dopo 3 s: proporre estensione opzionale ART UI per nascondere/richiamare controlli senza cambiare la camera | **SHARED_CORE** se tocca widget Core; art skin **ART_ONLY** | Widget/integration: nascosti i comandi, ripristino touch/TalkBack, camera `x,y,zoom` identica, Auto coerente, no controlli irraggiungibili | Precede 2/3/7 |
| **2 Targhetta museale** | Gesture long-press su tile in `drift_canvas.dart`, UI del cartellino Art-only | **SHARED_CORE** per riconoscimento gesture/rect callback opzionale + **ART_ONLY** overlay | 20 pressioni prolungate: una sola targhetta per tile corretta; drag e pinch non attivano la targhetta; metadati assenti omessi; X/Esplora/Preferiti accessibili | 1, API Core, 3 |
| **3 Zoom contestuale noce** | Tile rect/origin + overlay dettaglio; `lib/screens/artwork_detail.dart` | **SHARED_CORE** solo per esposizione non distruttiva rect/identity se necessaria; il dettaglio **ART_ONLY** | Tocchi su 4 angoli: apertura parte dalla tile reale, proporzioni contain, cornice solo nel dettaglio, X inversa verso tessera corretta; camera e ID tile invariati | 2, API anchor, 4 |
| **4 Scheda di sala** | Componente Art-only `MuseumPlaque` per scheda compatta/espansa | **ART_ONLY** | Campi disponibili/assenti, multilinea e titoli lunghi; contenuti scrollabili, quadro non tagliato; test 0/50/90dp banner e fontScale | 3 |
| **5 La mia collezione** | `lib/screens/favorites_sheet.dart`, `lib/services/favorites.dart` | **ART_ONLY** | Galleria a 0/1/50+ preferiti, aggiungi/rimuovi, ID con stesso numero in musei diversi, riavvio persistente, migrazione preferiti legacy, ritorno a camera invariata | UI 3/4 riutilizzata dove previsto |
| **6 Atrio della ricerca** | `lib/screens/search_sheet.dart` + `lib/search/gallery_search.dart` (motore invariato) | **ART_ONLY** | Pennello in alto centro **w=viewport/3** a 320/360/390/600dp, suggerimenti locali senza richieste remote, ricerca esterna solo su gesto esplicito; riapertura stato/camera, query assente → stato vuoto | 3/4/5 |
| **7 Regia scorrimento** | Il Core ha già Auto/Pausa e cicli 25/50/75/100; il mock richiede **popover** invece del ciclo diretto | **SHARED_CORE** se UI/callback esposte nel Core, skin **ART_ONLY** | In 60 e 120Hz, Auto avanza realmente, Pausa si ferma, scelta persiste, manual gesture ferma Auto, 4 ritmi; Gallery test invariati | 1, API Core opzionale |
| **8 Gabinetto curatore** | `lib/screens/settings_sheet.dart` e `lib/ui/localization.dart` | **ART_ONLY** | Sei lingue IT/EN/FR/ES/DE/PT; label/scroll no overflow e persistenza al riavvio; Pro gratis/no acquisto, privacy/licenze reali, X; XSS/link privacy non introdotti | Indipendente |
| **9 Portale del museo** | `lib/main.dart`, solo loading/error/ready | **ART_ONLY** | Test testo italiano esatto **«Il museo sta aprendo»** / **«la visita sta per cominciare»**; traduzioni UI rivedute per EN/FR/ES/DE/PT senza sostituire l'originale IT; uscita quando dati pronti senza timer; offline primo avvio mostra errore reale, retry reale, dati cache esistenti conservati | Indipendente |
| **10 Passeggiata quadri** | Precedente/successivo, cuore, wallpaper Android e scheda museo già in `lib/screens/artwork_detail.dart` | **ART_ONLY** | 30 switch consecutivi: immagine/titolo/metadati/favoriti sempre stesso ID; cornice fissa e contain; link originale corretto; wallpaper solo Android con conferma, X torna a stessa camera | 3/4/5 |

**Rischio specifico 3 ↔ 10:** il ritorno zoom verso la tile d'origine **non deve animare l'opera sbagliata** dopo che l'utente ha usato precedente/successivo. Strategia da testare: o si chiude verso la tessera d'origine solo se l'ID visualizzato coincide, oppure il ritorno usa una transizione neutra che preserva la camera; non falsificare l'identità. La scelta applicativa va esplicitata nella PR prima del merge.

**Rischio specifico 7:** l'Auto è già nel Core e la percentuale ora **cicla per tap**. L'overlay di selezione non è una proprietà già implementata. Preferire API UI opzionali/adattatori anziché cambiare il comportamento standard di Gallery Drift; se serve una modifica Core canonica, preparare test e PR pin Gallery separata, mai duplicare.

## 4. Sequenza dei lavori e parallelismo controllato

**Fase A · preflight e harness (obbligatoria, unica).** Risolvere la baseline fra `main` e PR #33/#34/#35; recuperare prove Android esistenti, correggere solo nel futuro percorso consentito l'incongruenza pin-doc di Gallery, acquisire baseline screenshot e benchmark; scrivere test di caratterizzazione camera/tile/viewport e protocolli di confronto senza cambiare il layout.

**Fase B · superfici Art-only (parallelizzabili in PR figlie isolate).**
- **9** loading/error/ready; **8** settings e sei lingue.
- **5** preferiti; **6** ricerca. Nessuna fusione anticipata di questi rami: ciascuno con screenshot e test focalizzati.
- Predisporre componente `AdAwareArtViewport` o equivalente **solo in Art Drift**, con altezza banner effettiva, `SafeArea` e viewport ricalcolato; banner solo **simulato**.

**Fase C · interazioni Core e overlay (sequenziale sui punti condivisi).**
- **1 e 7**: definire contratto controlli/Quiet/Auto, test Art + Gallery e API opzionali; evitare di alterare motore fisico Auto e world mapping.
- **2**: long-press e tile-anchor (l'eventuale API condivisa), con widget Art-only e test conflitti gesture.
- **3 → 4 → 10**: zoom origin-based, cornice, scheda di sala, poi navigazione fra quadri. Verificare la compatibilità dei 3 aspetti prima di procedere.

**Fase D · integrazione candidata, mai direttamente su main.** Comporre soltanto rami già con gate locali verdi, nessun merge di PR stacked non approvate; rieseguire l'intera regressione su una **PR finale di implementazione**. Se il Core cambia, Gallery esegue CI + verifica device separatamente e resta al pin precedente fino ad approvazione.

**Fase E · handoff/accettazione.** Confronto visivo 10/10 su Android, report prestazioni vs baseline, verifica salvaguardia dati e firma APK, evidenza linkata ai commit; **solo dopo** richiedere approvazione distinta di merge. Distribuzione pubblica fuori scope.

## 5. Matrice visual QA e usabilità

| Dimensione | Casi obbligatori | Gate |
| --- | --- | --- |
| Display | 320, 360, 390, 412, 600 e ~840 dp; almeno telefono compatto, normale e tablet; portrait e landscape | Nessun RenderFlex overflow, testo/azioni tagliati, slot Ad che copre contenuti |
| Accessibilità | font scale 1.0, 1.3, 1.6; TalkBack; touch target adeguati; high-contrast / reduced-motion | Comandi X, cuore, popup, ricerca/lingue raggiungibili e con etichette; niente motion obbligatorio |
| Tema | Dark art canvas + pannelli avorio/oro dei mock-up; no nuova barra inferiore | Composizione coerente con le dieci decisioni e le immagini reference; niente copia di asset non licenziati |
| Banner | banner simulator: assente, visibile 50dp, 90dp, ridimensionamento al volo e ritorno ad assente | Inset rispettati; content bottom == ad top quando presente, == viewport bottom quando assente; pan/zoom salvati |
| Gesture | tap breve, 500ms long-press, pan in quattro direzioni, pinch a due dita, fling, close X | Nessuna apertura involontaria o salto camera; correlazione tile/opera invariata |
| Artwork | verticali/orizzontali, titoli molto lunghi, dati mancanti, miniature offline/non disponibili | `BoxFit.contain` in detail, media originale non tagliato; titolo/autore/diritti non inventati |
| Stati | caricamento lento, primo avvio offline, retry fallito/successivo, lista preferiti vuota, query vuota, 0 risultati | Messaggi veri e azioni attive; nessun finto successo o timer di ritardo |
| Snapshot / video | screenshot base + candidato con ID scenario; video 60Hz della sequenza 2→3→4→10 e giro Auto | Revisione umana delle differenze intenzionali, difformità annotate e riparate |
| Compatibilità Android/Web | Android release/profile + Chrome web preview; verificare differenze per wallpaper e navigazione esterna | No chiamata wallpaper su web; Nessun crash o overlay senza chiusura |

**Test di non regressione critica:** (i) posizione world/focal point dopo pinch; (ii) output deterministico tile key→artwork ID in almeno 50 coordinate; (iii) `artdrift.camera` prima/dopo ogni overlay e al riavvio; (iv) preferiti migrati/riavviati; (v) layer touch: ad simulator esterno ai gesture handlers; (vi) UI scroll non assorbe pan del canvas quando chiusa.

## 6. Performance QA — protocolli e soglie proposte

**Nessuna misura qui è dichiarata già PASS.** Prima fissare baseline `B` e candidato `C` sullo **stesso dispositivo**, stesso refresh rate, stessa rete/cache, stesso numero/playlist opere e impostazioni identiche; non confondere PSS, imageCache, GPU memory e FPS.

| Misura / prova | Raccolta evidenze | Soglia candidata per promozione |
| --- | --- | --- |
| Frame Flutter in profile/release | `FrameTiming`/tracing build + raster, p50/p95/p99; 3 sessioni da ≥60s per percorso | A 60Hz: p95 frame ≤16,67 ms e p99 ≤33,33 ms; altrimenti blocco, con screenshot/traccia del caso |
| Jank grave | Conteggio frames con tempo >50ms (escludere avvio asset documentato separatamente) | ≤1% dei frame nel percorso stabile; 0 lunghe sospensioni imputabili ai nuovi overlay |
| Performance relativa | Confronto p95/p99 B vs C nei medesimi 4 percorsi: pan veloce, pinch, Auto, 30 aperture/switch | Regressione p95 **≤10%** rispetto a B; quando B supera già la soglia assoluta, richiedere miglioramento/analisi esplicita e decisione documentata |
| Memoria Flutter image cache | `PaintingBinding.instance.imageCache` + timeline, baseline e dopo 10min di navigazione | Rispettare configurazione esistente (max 110 immagini / 48 MiB nella baseline Art `main`), senza crescita non limitata |
| Memoria processo Android | PSS/heap via `adb shell dumpsys meminfo`, 3 letture dopo warm-up | Mediana C ≤+15% di B e nessuna crescita lineare non recuperata dopo 10 min; annotare cache/warm state |
| Tempi UI | Cold start, primo frame con catalogo pronto, apertura/chiusura dettagli, lookup ricerca locale | Nessuna attesa artificiale; p95 apertura viewer ≤+10% vs B, non bloccare input con operazioni sincrone |
| Stabilità | 10 min Auto + 50 pan + 20 pinch + 30 cambi opera; offline on/off e ritorno background | **0** eccezioni fatali, OOM, ANR, frame infinito; posizione e ID invariati |
| Core virtualization | Widget/key count, layout deterministico e `DriftPrefetchPlan` | Cap nominale di 180 tile mantenuto, lookup deterministico, prefetch limitato (8 per batch / history 256), non allargare il mondo per un overlay |

Se refresh rate 90/120Hz, riportare anche il budget 11,1/8,3 ms separatamente; il test a 60Hz resta riferimento comparabile, non una promessa generica di 120 FPS. Se `gfxinfo` restituisce 0 frame, segnare `NOT_MEASURED`: è vietato dedurre FPS da tale output. Se baseline API/device o metriche non sono raccoglibili, gate `BLOCKED_EVIDENCE`, mai PASS per presunzione.

**Evidenze per ciascun benchmark:** hardware/model, Android API, display Hz, Flutter build mode e commit SHA, versione catalogo, rete/cold-warm, script/versione strumento, campioni grezzi, mediane e percentili, log ANR, screenshot/tracce, firma revisore.

## 7. QA automatico previsto — senza modificare test adesso

**Riutilizzare** `packages/drift_core/test/drift_core_test.dart` (Auto 60/120Hz, geometria, prefetch), `test/curated_search_ui_test.dart` (1/3 ricerca e autocomplete), `test/favorites_hub_test.dart` (preferiti e migrazione), `test/localization_entitlement_test.dart` (sei lingue, Pro fail-closed), `test/world_layout_test.dart` e `test/art_remote_image_test.dart`.

**Da aggiungere nella futura PR** (nomi proposti):
- `test/design/quiet_and_auto_controls_test.dart`: 1/7, persisted speed, visibility/semantics.
- `test/design/tile_longpress_anchor_test.dart`: 2/3, gesture arena, rect origin e identity.
- `test/design/artwork_zoom_plaque_test.dart`: 3/4, contain, data absent/long, reverse X.
- `test/design/favorites_search_curator_test.dart`: 5/6/8, cuore, search 1/3, sei lingue, offline, Pro.
- `test/design/museum_portal_test.dart`: 9, exact string, cold/offline/retry error.
- `test/design/detail_tour_test.dart`: 10, next/prev, attribution, wallpaper Android mock, external museum.
- `test/design/ad_viewport_contract_test.dart`: 0/50/90dynamic, no ghost padding, dynamic resize + camera.
- `integration_test/design_full_journey_test.dart`: 1→2→3→4→10; 5→6→8→9 and background/foreground; independent Android/browser scenarios.
- Golden screenshot tests at stable device presets; fail only on **non-reviewed** visual diffs, not on arbitrary score thresholds. Static AppBlock demo artwork **non sostituisce** immagini del catalogo reale.

**CI futura su exact-head:** Flutter `analyze`, `test`, Drift Core tests, Chrome selected tests, Android ARM64 internal APK; screenshots & traces uploaded come artefatti immutabili; no “PASS” se screenshot raccolti ma non esaminati. Codice e test implementativi **non** sono aggiunti da questo documento.

## 8. Modello di report accettazione

Per ogni `UX-01` … `UX-10` produrre un record con:

```yaml
id: UX-03
design_decision: "Zoom contestuale con cornice museale"
design_status: DESIGN_APPROVED
source_status: NOT_IMPLEMENTED
ci_status: NOT_RUN
visual_status: NOT_REVIEWED
physical_status: NOT_TESTED
app_target_sha: null
core_sha: null
gallery_pin_sha: null
device: null
android_api: null
refresh_hz: null
screen_dp: null
font_scale: null
ad_height_test_dp: null
screenshots_before: []
screenshots_after: []
video_evidence: []
test_run_urls: []
metrics_artifacts: []
regressions: []
reviewer: null
decision: HOLD
```

I valori cambiano esclusivamente sulla base di evidenze. Il report deve contenere **anche gli esiti FAIL, PENDING e NOT_MEASURED**; niente screenshot o log personali pubblicati senza verifica di sensibilità. Per Gallery Drift usare solo dati sintetici nelle prove pubbliche.

## 9. Criterio finale GO / NO-GO e attività escluse

**GO per proposta di merge** soltanto se:
1. baseline attuale/release candidata e Core pin riconciliati; decisioni in contratti e 10/10 test tracciati;
2. tutti i test automatici su HEAD esatto passati, screenshot/golden approvati dall'utente o revisore design, anche con fontScale/landscape;
3. Android fisico ha superato fluidità, touch, no regressione camera, no OOM/ANR, preferiti persistenti, ricerca locale e 6 lingue;
4. banner simulato verifica il viewport con altezza 0/50/90 e resize, senza introdurre ad SDK;
5. prova di aggiornamento **senza perdita dati** e firma/package/versionCode compatibili, se si intende installare sopra l'app esistente;
6. per eventuali modifiche **SHARED_CORE**, Gallery Drift ha test/compatibilità e PR di aggiornamento SHA **separata**, senza auto-merge;
7. utente autorizza **separatamente** la promozione dopo esame del report finale.

**NO-GO** con evidenze mancanti, differenze visive non approvate, non conformità camera/gesti, problemi performance, assenza di conferma firma/upgrade, PR basale non selezionata o interazioni sfondo/link non coerenti. La PR implementativa rimane Draft; si corregge e si ripete la matrice.

**Fuori scope di questo mandato:** modifiche al codice Dart, nuovi asset, import di immagini, pubblicità AdMob attiva e UMP, pagamento Pro, Play Store, release firmata, merge `main`, propagazione in Gallery Drift. La futura monetizzazione richiede un percorso di policy/consenso/entitlement separato e conserva la regola viewport già approvata.

---
**Sintesi decisionale:** piano scritto; prerequisiti di collaudo specificati; **10/10 DESIGN_APPROVED**, **0/10 SOURCE_IMPLEMENTED**, **0/10 PHYSICAL_ACCEPTED** in questa fase. Il documento non afferma di aver eseguito test, screenshot o benchmark che non sono stati effettuati.
