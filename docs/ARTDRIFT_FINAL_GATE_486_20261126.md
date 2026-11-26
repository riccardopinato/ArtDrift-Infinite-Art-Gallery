# Art Drift — controlli finali delle 486 candidature (26 novembre 2026)

**Ambito:** 486 record esatti del lotto dei 7 artisti scelti. Le opere **non sono tutte distinte** finché i possibili duplicati e le varianti non sono esaminati. Nessun import nel canvas.

## Materiali verificati

- Ricerca: PR #84, commit `b82a4574db3d504141b6d2e95e403aa743c771e3`.
- QA immagini: [GitHub Actions 45905782588](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45905782588), 486/486: 447 anteprime tecnicamente decodificate, 39 Wikimedia 429 da riprovare separatamente (#90).
- Diritti: [GitHub Actions 45907246535](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45907246535), 486/486 documentazioni: 440 Public Domain, 6 CC0, 19 CC BY, 20 CC BY-SA e un caso Städel con incongruenza (metadati della fonte iniziale vs museo).
- [Direttiva (UE) 2019/790, art. 14](https://eur-lex.europa.eu/eli/dir/2019/790/oj), [legge 633/1941 art. 32-quater](https://def.finanze.it/DocTribFrontend/getAttoNormativoDetail.do?ACTION=getArticolo&id=%7B012E634A-9F52-4452-B7F7-980D83EDE0C6%7D), [Codice dei beni culturali art. 108](https://www.normattiva.it/atto/caricaDettaglioAtto?atto.articolo.numero=108&atto.codiceRedazionale=004G0066&atto.dataPubblicazioneGazzetta=2004-02-24).
- [Wikimedia Commons guide to reusing content](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia).

## Ulteriori controlli svolti

La revisione incrociata dei fascicoli (CSV/JSON caricati dal workflow originale) ha segnalato:
- 84 candidature collegate da almeno un titolo molto simile, per 74 coppie (solo indizi, **non** duplicati provati).
- 77 anteprime con lato corto inferiore a 300 pixel.
- 57 file Commons senza il pittore atteso nel campo autore normalizzato; il caso Städel è separato e documentato.
- 8 file Commons con flag `Copyrighted=True` associato a dichiarazioni Public Domain/CC0, da verificare.
- 3 titoli che sembrano fotografie non rappresentative di opere originali; 3 titoli che suggeriscono stampe/cornici/riproduzioni. Le categorie possono sovrapporsi.
- 39 file CC BY/BY-SA che richiedono implementazione esplicita di credito e collegamento alla licenza, oltre all'eventuale condizione ShareAlike applicabile a un adattamento.

**Attenzione:** il campo `Source` estratto dai Commons `extmetadata` era vuoto per tutti i 485 file, ma la descrizione completa della pagina può contenerlo. Il nuovo workflow acquisisce per ogni immagine `Source` e `Author` dalla pagina wikitext, lasciando in HOLD qualsiasi lacuna di origine.

## Compatibilità app: blocco tecnico

Nel file `lib/models/artwork.dart` il getter `displayedLicense` ricade su `CC0` per fonti non AIC se `rightsLicense` è vuota: questo fallback **non è idoneo** per i nuovi record. Anche `displayable` e la whitelist di URL/host non prevedono `commons` e `staedel`. Prima di qualsiasi import servono un modello esplicito di licenza, fonte, foto e URL verificato, una schermata di crediti completa, test e deduplicazione.

## Non autorizzare il rilascio senza queste evidenze

Identità della specifica opera (e versione), fonte primaria reale, autore del quadro e autore del file digitale, licenza attuale, condizioni museo/territorio, credito esposto in app, qualità immagine completa, controllo duplicati nelle opere già pubblicate e accettazione estetica. Nessun `commercially_approved=true` può essere determinato automaticamente da questa pipeline. **Niente merge diretto in main, niente APK o pubblicazione.**
