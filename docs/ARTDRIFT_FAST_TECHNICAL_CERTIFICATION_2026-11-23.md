# Art Drift — certificazione tecnica rapida (23/11/2026)

**CERTIFICATO:** `ARTDRIFT_G2_CANDIDATE_QA_PASS`  
**NON CERTIFICATO:** `G3_FINAL_PIXEL_OR_MOTION_PASS`, `G4_DEVICE_PERFORMANCE_PASS`, `G5_IN_PLACE_UPGRADE_OR_PUBLIC_RELEASE`.  
**Decisione operativa:** **GO per collaudo/iterazione del candidato, NO-GO per merge/publish o aggiornamento dell'app installata.** Questa decisione evita di ripetere prove già verdi e non sostituisce requisiti non osservati.

## Identità bloccata

- Repository `riccardopinato/ArtDrift-Infinite-Art-Gallery`.
- PR [#40](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/pull/40), branch `feat/artdrift-g2-integrated-candidate-20261123`, **SHA `279ec531760a6f202a8867a23c7dd0d38a743383`**; PR aperta e Draft.
- Base PR #35 `c2d1d3e91cef0cee3005a0fdda151ff34ac903e9` (stack dipendente da #34 e #33).
- Branch principale **`main@2dac51a6be98ed364d1e95983d1f330c84354ef7`**, **non modificato**.
- 22 file nel diff della PR #40, inclusi 9 test/widget oltre alle modifiche UI, adattatore canvas e `packages/drift_core/lib/src/drift_canvas.dart`. Non chiamare questo release build.

## Evidenza di verifica — risultati effettivi

| Verifica | Esito certificato | Provenienza |
| --- | --- | --- |
| `flutter analyze` + `flutter test` + Core tests (HEAD) | **PASS** | [Art Drift Android CI #45189795612](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45189795612), `completed/success`, exact SHA `279ec531...` |
| APK ARM64 interno (HEAD) | **BUILD PASS**, non pubblicabile come aggiornamento affidabile | Stesso workflow #45189795612, firma interna di test |
| Consumer Gallery Drift, con Core aggiornato in ramo QA | **PASS** | Gallery [#45189960820](https://github.com/riccardopinato/GalleryDrift/actions/runs/45189960820) e [#45189949702](https://github.com/riccardopinato/GalleryDrift/actions/runs/45189949702), entrambi `completed/success` su Gallery PR [#15](https://github.com/riccardopinato/GalleryDrift/pull/15) `820cfb7bea0cc6e9bd623e0ef90a8317758efbe6`; Gallery main invariato |
| Canvas Android emulato, scorrimento | **SMOKE PASS**, non benchmark | [#45179716155](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45179716155), 48 gesti, immagine cambiata, zero crash fatali rilevati, *su precedente G2 SHA* |
| Nove superfici UI Android | **REVIEW PRELIMINARE**, non certificazione pixel-exact | [#45182960994](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45182960994), screenshot reali di ricerca, archivio, impostazioni, dettaglio, navigazione, targhetta, menu velocità e immersione, *su precedente G2 SHA* |
| Portale caricamento/errore | **COMPONENT RENDER PASS**, resta controllo rete | [#45188974485](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45188974485), font reali; successiva correzione ornamenti vettoriali coperta da HEAD CI |
| Transizione tessera→quadro | **COMPONENT STATIC PHASES PASS**, non motion-continuity | [#45194694125](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45194694125), [#45196348884](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45196348884), [#45196699834](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45196699834), fotogrammi 0/25/50/75/100% e cambio identità; stesso codice app SHA |
| Layout pubblicitario simulato senza SDK | **WIDGET TEST PASS** | Inclusi in CI HEAD: altezza 0/50/90dp e transizione senza spazio fantasma; **nessun AdMob reale** |

## Tracciabilità sintetica dei dieci mock-up

| UX | Stato per il candidato G2 |
| --- | --- |
| 1 Quiet Canvas | **Codice + CI PASS**; fade/immersione verificati a livello di test, non motion su device |
| 2 Targhetta museale | **Codice + CI PASS**, acquisizione Android preliminare |
| 3 Zoom contestuale e cornice | **Codice + CI PASS, phase stills PASS**, video continuo e reverse fisico non osservati |
| 4 Scheda di sala | **Codice + CI PASS**, espansione e resize da finire di accettare visivamente |
| 5 La mia collezione | **Codice + CI PASS**, screenshot dello stato vuoto; piena raccolta non catturata |
| 6 Atrio della ricerca | **Codice + CI PASS**, screenshot di ricerca aperta |
| 7 Regia dello scorrimento | **Codice + CI PASS**, menu 25/50/75/100 visibile |
| 8 Gabinetto curatore | **Codice + CI PASS**, sei lingue e sezioni esistenti |
| 9 Portale del museo | **Codice + CI PASS**, copy approvato e rendering testato |
| 10 Passeggiata tra i quadri | **Codice + CI PASS**, precedente/successivo e cornice stabile, screenshot preliminari |

**Esito G2: 10/10 superfici presenti e test tecnici verdi. Esito G3: controllo visivo preliminare positivo, NON approvazione definitiva dei dieci render.** Non inventare `10/10 VISUAL PASS` o `DEVICE VERIFIED`.

## Residui NON da nascondere

1. **Continuità temporale reale della transizione non dimostrata:** due tentativi di MP4 con emulatore falliti per ADB `offline/error: closed`, non per crash Art Drift dimostrato. I fotogrammi Flutter sono disponibili ma non equivalgono a un video Android 60/120Hz. Nessun nuovo run obbligatorio per questa certificazione **tecnica**; verificarlo prima di dichiarare `MOTION PASS`.
2. **G4 fisica non strumentata:** p95/p99, jank, PSS/termica di lunga durata non misurati su un telefono reale. `gfxinfo` con 2 frame **non** vale come benchmark. L'utente ha chiesto di accettare le verifiche eseguite autonomamente; registrarne la **dichiarazione**, non spacciarla per log acquisiti.
3. **G5 firma installata sconosciuta:** gli APK di CI hanno certificati Debug differenti tra alcune esecuzioni. Non esiste prova di una firma compatibile con l'APK installato. Vietato proporre questi APK per un aggiornamento in-place; niente disinstallazione automatica, sovrascrittura dati o promessa di retention.
4. **G3 pixel fidelity non certificata:** solo alcune risoluzioni/fontScale e prototipi visuali archiviati; nessun confronto esatto 10/10. Verifica delle schermate con un APK firmato in modo adeguato da eseguire prima della release.
5. **PR stack non promosso:** #33→#35, #36 e #37→#40 Draft; Gallery #15 QA-only. Nessun merge del Core nel consumer di produzione.

## Verdetto finale utilizzabile ora

- **CERTIFICAZIONE `PASS`**: correttezza tecnica verificata per il candidato **Art Drift G2@279ec531**, build/test e smoke di base, più compatibilità CI del consumer Gallery Drift.
- **CERTIFICAZIONE `WITH OPEN EXCEPTIONS`**: look & feel e flight in fase di review; gli screenshot non coprono tutte le permutazioni approvate.
- **RILASCIO/AGGIORNAMENTO `NO-GO`**: senza verifica dell'identità di firma dell'installazione e evidenza appropriata dei requisiti release, non si può certificare un aggiornamento sicuro.

**Questa certificazione è conclusiva per il solo ambito tecnico e non autorizza autonomamente il merge né ulteriore sviluppo estetico.**
