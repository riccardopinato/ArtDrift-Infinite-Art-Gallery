# Art Drift — vincolo layout dinamico per futuro banner AdMob

Data: 23 novembre 2026  
Stato: **REQUISITO CONFERMATO DALL'UTENTE — SOLO DOCUMENTAZIONE**  
Ambito: tutti i mock-up di Art Drift e la futura implementazione, incluso lo slot estetico 4/10 «Scheda di sala», approvato dopo la definizione di questo vincolo.

## Decisione richiesta dall'utente

Un futuro banner AdMob sarà collocato **in basso nell'app**. La superficie utile per canvas infinito, quadro aperto, cornice in noce, cartellino di sala, sfondi attenuati, X e controlli flottanti deve adattarsi alla **presenza effettiva** del banner.

- **Senza banner visibile** (AdMob disattivato, assente, non disponibile o non caricato): il limite inferiore del layout è **l'intera area schermo utilizzabile** dopo gli inset di sistema; nessuno spazio pubblicitario vuoto riservato in modo permanente.
- **Con banner visibile**: il limite inferiore dell'area di Art Drift è **il bordo superiore del banner**. Non sovrapporre immagini, cornici, schede, X o controlli al banner.
- **Al cambiare della visibilità o dell'altezza del banner**: ricalcolare dinamicamente il viewport disponibile, non usare un padding inferiore fisso né presumere un'altezza unica. AdMob adaptive banner può avere altezze differenti.
- **Operazioni sul canvas**: mantenere il riferimento alla tessera e lo stato di pan/zoom; il ricalcolo del viewport non deve azzerare la posizione dell'utente.
- **Zoom contestuale 3/10**: centro e bounding box della card sono calcolati nello spazio utile **sopra** il banner; ingresso e ritorno restano ancorati alla posizione effettiva della tessera. Evitare tagli dell'opera e della cornice, conservare accessibilità e area raggiungibile della X.
- **Scheda di sala 4/10**: il cartellino compatto/espanso deve usare soltanto il viewport disponibile, senza scivolare dietro il banner. Per schermi piccoli prevedere contenuto scorrevole interno o ridimensionamento della card, non tagli dell'immagine.
- **Quiet Canvas 1/10 / Targhetta museale 2/10**: controlli inferiori, targhetta e relativi touch target si posizionano rispetto al bordo inferiore del viewport utile, non rispetto al bordo inferiore del banner.
- Il banner appartiene a uno **slot separato**, esterno alla superficie gestuale del canvas; il suo tocco non deve essere intercettato dal canvas e viceversa.
- Inset Android, gesture bar, orientamento e resize devono essere rispettati, con almeno uno scenario col banner e uno senza nel futuro collaudo UI.
- **Nessuna pubblicità introdotta ora**: nessuna integrazione SDK, manifest, codice Dart, ID annunci, unità pubblicitarie o modifica APK è autorizzata da questo documento.

## Contratto geometrico

`viewportArtDrift = areaDisponibileSopraSystemInset - altezzaBannerEffettivamenteVisibile`

Il bordo inferiore del contenuto è:
- **fondo dell'area di app utilizzabile**, se il banner non è visibile;
- **bordo superiore del banner**, se è visibile.

**Non assumere che l'altezza del banner sia 50 px o 60 px**; leggere dimensione effettiva quando sarà implementato.

## Stato decisioni estetiche — fonte unica

Al 23 novembre 2026, il ciclo interattivo dei **10 mock-up è stato interamente APPROVATO (10/10)**; **nessuno è implementato nel codice Flutter (0/10)**. La PR documentale #36 rimane Draft e non è stata fusa in `main`.

Lo **stato aggiornato di ogni slot**, incluso l'esatto copy del mock-up 9/10, è mantenuto in `docs/ARTDRIFT_INTERACTIVE_MOCKUP_DECISIONS_2026-11-23.md`. Questo file resta il contratto di geometria per la futura monetizzazione; non contiene uno snapshot autonomo dei singoli slot, per evitare divergenze.

**Nessuna pubblicità reale, modifica Flutter o APK è stata effettuata.**
