# Art Drift — registro decisioni mock-up estetici

Data apertura ciclo: **23 novembre 2026**  
Baseline app al momento della registrazione: `main@2dac51a6be98ed364d1e95983d1f330c84354ef7`  
Factory: `App-Factory-Core@ede07c491e586215598ff68daec43e17d699aa51`  
Ambito: **sola approvazione dei prototipi**, nessuna modifica al codice visivo o al motore Drift Core.  
Stato generale: **DESIGN REVIEW / NON IMPLEMENTATO**.

## Vincoli preesistenti confermati

- Conservare il canvas immersivo infinito esistente, le associazioni tile/opera, le coordinate e la disposizione delle tessere.
- Ricerca a pennello al centro in alto, esattamente 1/3 della larghezza; Favorites e Settings sulla destra in alto.
- Marchio e controlli di scorrimento Auto nell'area in alto a sinistra; pulsante di ricentratura in basso a destra.
- Palette scura con cornici avorio/oro; nessuna barra di navigazione inferiore e nessun annuncio sul canvas.
- Conservare il tap sulla tessera come apertura del dettaglio, pan e pinch-to-zoom; non compromettere la fluidità.
- Design-App prima delle proposte autonome, con vincoli Product Bible e licenze.
- Qualsiasi integrazione richiede fase separata e verifiche UI/accessibilità/performance sul codice reale.

## Registro 1–10

| Slot | Schermata | Proposta | Decisione utente | Implementato | Note |
| --- | --- | --- | --- | --- | --- |
| 1/10 | Home / canvas | **Quiet Canvas** — modalità Immersione: i controlli svaniscono dopo l'esplorazione, un comando discreto li richiama; conservare posizionamento e tema approvati | **APPROVATO** — conferma esplicita in chat 23/11/2026 | **NO** | Prototipo interattivo visto e approvato; comportamento visivo proposto, non funzionalità già esistente |
| 2/10 | Home / anteprima opera | **Targhetta museale** — proposta interattiva da valutare, dati dell'opera già disponibili, nessun nuovo catalogo | **IN ATTESA** | **NO** | Non integrare senza decisione esplicita |
| 3–10 | — | Da proporre uno alla volta | **NON PRESENTATI** | **NO** | Vietato anticipare le decisioni |

## Slot 1/10 — contratto di design approvato

- Identità: **Quiet Canvas**, evoluzione discreta del canvas già approvato.
- In modalità normale, ricerca, cuore, ingranaggio, brand, Auto e ricentratura conservano posizione e comportamento correnti.
- All'esplorazione o usando **Immersione**, i comandi e il suggerimento inferiore si attenuano/scompaiono con una transizione breve; il comando **Mostra comandi** resta raggiungibile.
- Il ritorno alla modalità normale fa comparire i controlli senza cambiare camera, zoom, selezione o navigazione.
- Mock-up dimostrativo, non collaudato come UX su Android; verificare TalkBack, tap target, reduced motion e gesto multi-touch in implementazione.
- Reference Design-App: `MOCK-STYLE-003` (Vintage) **ADATTATA** e Editorial UI **ADATTATA**; nessuna importazione di asset terzi e nessuna modifica della palette.

## Stato implementativo

**APPROVATO ≠ INTEGRATO.** Questo documento registra solo preferenze e decisioni; il codice Flutter attuale e le PR #33–#35 restano indipendenti. Il collaudo v0.3.8 e la relativa PR #35 non autorizzano la promozione estetica.

La prossima decisione è sullo slot **2/10**. Non avanzare allo slot 3/10 prima di approvare, modificare o scartare esplicitamente il 2/10.
