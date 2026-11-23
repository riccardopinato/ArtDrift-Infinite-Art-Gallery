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
| 2/10 | Home / anteprima opera | **Targhetta museale** — pressione prolungata su un'opera apre una targhetta discreta con titolo, autore, data, Apri opera e Preferiti; il tap breve mantiene il dettaglio completo | **APPROVATO** — conferma esplicita in chat 23/11/2026 | **NO** | Solo UX/visual proposta; nessuna modifica al catalogo o a preferiti reali |
| 3/10 | Home → apertura opera | **Zoom contestuale con cornice museale** — la tessera selezionata si ingrandisce dalla sua posizione reale fino a una card centrale; durante il passaggio compare la cornice raffinata in noce decorato con dettagli dorati; X in alto a destra, ritorno animato alla stessa tessera, cornice assente nel canvas | **APPROVATO** — conferma esplicita in chat 23/11/2026 dopo revisioni 2 e 3 | **NO** | Nessun cambio camera/layout, preview responsiva e fallback reduced-motion; verifica rendering e performance Android in fase implementativa |
| 4/10 | Scheda dell'opera incorniciata | **Cartellino di sala espandibile** — scheda editoriale avorio sotto il quadro con titolo, autore e anno; comando «Leggi la scheda» per espandere i soli metadati e descrizioni esistenti; impaginazione dinamica sopra il banner AdMob se presente | **APPROVATO** — conferma «procedi, approvo» in chat del 23/11/2026 dopo precisazione sul futuro banner | **NO** | Rispettare il vincolo AdMob documentato: assente = piena area, presente = bordo superiore del banner; nessuna pubblicità implementata |
| 5/10 | Home / Preferiti | **La mia collezione** — proposta estetica di galleria editoriale accessibile dal cuore in alto a destra; presentazione di opere salvate e ritorno al canvas senza perdere lo stato | **IN ATTESA** | **NO** | Mock-up interattivo in valutazione: non sostituisce automaticamente funzioni o navigazione esistenti |
| 6–10 | — | Da proporre uno alla volta | **NON PRESENTATI** | **NO** | Vietato anticipare le decisioni |

## Slot 1/10 — contratto di design approvato

- Identità: **Quiet Canvas**, evoluzione discreta del canvas già approvato.
- In modalità normale, ricerca, cuore, ingranaggio, brand, Auto e ricentratura conservano posizione e comportamento correnti.
- All'esplorazione o usando **Immersione**, i comandi e il suggerimento inferiore si attenuano/scompaiono con una transizione breve; il comando **Mostra comandi** resta raggiungibile.
- Il ritorno alla modalità normale fa comparire i controlli senza cambiare camera, zoom, selezione o navigazione.
- Mock-up dimostrativo, non collaudato come UX su Android; verificare TalkBack, tap target, reduced motion e gesto multi-touch in implementazione.
- Reference Design-App: `MOCK-STYLE-003` (Vintage) **ADATTATA** e Editorial UI **ADATTATA**; nessuna importazione di asset terzi e nessuna modifica della palette.

## Slot 2/10 — contratto di design approvato

- Identità: **Targhetta museale**, micro-interazione sull'opera senza lasciare il canvas.
- La **pressione prolungata** su una tessera, distinguibile dallo scorrimento, fa apparire una piccola targhetta editoriale con titolo, autore, data e azioni **Esplora l'opera** / **Preferiti**; mostrare solo metadati veri già disponibili.
- Il tap breve continua ad aprire la vista dettagli esistente; pan, pinch-to-zoom e Auto non cambiano semantica.
- La targhetta si chiude esplicitamente o al riprendere della navigazione; ripresa dello stato camera invariato.
- Compatibile con il mock-up 1/10 **Quiet Canvas**, già approvato; la targhetta non deve causare comandi duplicati o perdita di accessibilità.
- Ref Design-App: `MOCK-STYLE-003` Vintage **ADATTATA** (gerarchia da didascalia museale); no copie non autorizzate di asset, font o codice esterno.
- Implementazione differita: prototipare e misurare conflitto long-press vs drag/zoom, dimensione target e screen reader. Nessun widget o comportamento dell'app attualmente modificato.

## Slot 3/10 — contratto di design approvato

- Identità: **Zoom contestuale con cornice museale**, revisione 3 del precedente «Passaggio cinematografico». Questa revisione sostituisce integralmente l'idea iniziale di ingresso laterale.
- Nel canvas le opere rimangono **senza cornici** e non cambia la posizione, l'associazione tile/opera, il layout o lo zoom salvato.
- Un tap breve ingrandisce l'opera partendo **dal rettangolo visibile della tessera realmente toccata**, anche se collocata in alto a destra o in altre posizioni; la tessera si trasforma in una card centrale.
- **Durante l'ingrandimento** compare progressivamente una cornice realistica di **legno di noce scuro**, con intagli raffinati e discrete finiture dorate, non barocche. La cornice circonda soltanto la singola opera aperta, mai tutte le miniature.
- Il dipinto nella card rispetta le **proporzioni originali**, con `contain` ove occorre, senza tagli; presenza del canvas attenuata sullo sfondo.
- La **X ben visibile in alto a destra** richiude la card con animazione inversa verso **la stessa tessera di partenza**, mantenendo camera/zoom del canvas invariati; la cornice scompare durante il rientro.
- La targhetta museale approvata nello slot 2/10 resta disponibile con pressione prolungata; la modalità Quiet Canvas dello slot 1/10 resta compatibile.
- Specifiche candidate, NON certificate: breve animazione ~350–480 ms; percorso `reduced-motion` e focus accessibile; mantenere fluidità e basso overhead con un solo elemento animato, non cornici sulle altre opere.
- Reference Design-App: `MOCK-STYLE-003` Vintage **ADATTATA** e Editorial UI **ADATTATA** a cornice museale; nessun asset o componente esterno copiato.
- **Nota sullo stato:** approvazione estetica in chat non equivale a widget sorgente, CI, visual QA o collaudo fisico. Nessuna modifica Flutter effettuata.

## Slot 4/10 — contratto di design approvato

- Identità: **Scheda di sala**, cartellino avorio editoriale associato al quadro centrale incorniciato in noce (slot 3/10).
- Vista iniziale compatta: **titolo, autore, anno**, più comando esplicito **Leggi la scheda**; la card con il quadro resta visibile e l'immagine mantiene le proporzioni originali.
- L'espansione mostra soltanto le informazioni autentiche già disponibili nel catalogo: tecnica, provenienza, crediti, descrizione quando presenti. I campi assenti non vengono riempiti con dati fittizi.
- Chiusura/riapertura reversibile, dimensioni di lettura e target accessibili; su telefoni piccoli contenuto scrollabile all'interno della scheda, senza tagliare il quadro.
- **Vincolo aggiuntivo approvato prima della decisione**: `docs/ARTDRIFT_ADMOB_VIEWPORT_CONSTRAINT_2026-11-23.md`. Se **nessun banner AdMob è presente**, canvas, card e scheda usano tutta l'area disponibile; quando è **visibile**, la zona utile termina precisamente sul **bordo superiore del banner**, con altezza dinamica misurata e nessuno spazio inferiore vuoto fisso.
- Il banner NON è stato introdotto; nessun SDK o ID pubblicitario va aggiunto in questa fase. La gestione degli inset di Android resta requisito di implementazione futura.
- Continuità con i mock-up già approvati 1/10 Quiet Canvas, 2/10 Targhetta museale, 3/10 Zoom contestuale con cornice; nessuna modifica diretta alla home o alla logica del canvas.
- Stile Design-App Vintage `MOCK-STYLE-003` ed Editorial UI **ADATTATI**, non copia di asset/font esterni.

## Stato implementativo

**APPROVATO ≠ INTEGRATO.** Questo documento registra solo preferenze e decisioni; il codice Flutter attuale e le PR #33–#35 restano indipendenti. Il collaudo v0.3.8 e la relativa PR #35 non autorizzano la promozione estetica.

La prossima decisione è sullo slot **5/10**. Non avanzare allo slot 6/10 prima di approvare, modificare o scartare esplicitamente il 5/10.
