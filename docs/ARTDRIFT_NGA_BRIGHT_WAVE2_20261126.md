# Art Drift — NGA Wave 2: paesaggi luminosi senza quadri scuri

Data: **26 novembre 2026**. Seconda ricerca sulla National Gallery of Art, Washington, alla ricerca di dipinti brillanti e soprattutto paesaggistici.

## Ricerca effettuata
- NGA Open Data ufficiale, source pinned a commit `2470472572fdca2a24a741bb50eaba7301c47fa9`.
- Scansione **146.592** schede opere nel dataset + join con le immagini primarie Open Access; deduplica verso **799 NGA già presenti in main** e verso le **22** selezionate nella wave precedente.
- **110** nuove immagini NGA Open Access scaricate, decodificate e campionate effettivamente sul raster. **7** dipinti ammessi dopo soglie cromatiche e revisione visiva, **103** scartati o tenuti in sospeso.
- Soglie della nuova wave: luminanza media >= **0,55**, area molto scura <= **10%**, pixel vivaci >= **18%**, saturazione media >= **18%**. Gli elementi scuri sono esclusi anche se hanno piccole zone accese.
- Periodo di ricerca: **1850–1965**, tecnica: solo **Painting**; solo immagini NGA ufficiali con `openaccess=1` e view primaria, nessun ritratto come soggetto principale.
- Collaudo CI riuscito: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45810819500.

## 7 nuovi candidati, senza duplicati
| ID NGA | Titolo | Artista | Data | Scuri (%) |
|---|---|---|---|---:|
| 46677 | Spring Woods | Henry Ward Ranger | c. 1910 | 5,65 |
| 52957 | Southern Resort Town | Dana Smith | c. 1880 | 0,13 |
| 56574 | Beach at Beverly | John Frederick Kensett | c. 1869/1872 | 6,25 |
| 46523 | The Houses of Parliament, Sunset | Claude Monet | 1903 | 0,00 |
| 59886 | Bucks County Farm Outside Doylestown, Pennsylvania | American 19th Century | c. 1890 | 9,73 |
| 72328 | Roses | Vincent van Gogh | 1890 | 2,66 |
| 51139 | Composite Harbor Scene with Castle | Jurgan Frederick Huge | c. 1875 | 9,62 |

Si tratta di una selezione per criteri estetici di Art Drift; non si pretende che ogni dipinto rispetti una definizione accademica stretta di “arte moderna” (sono inclusi dipinti tardo-ottocenteschi).

### Esempi selezionati, fonti NGA
- https://www.nga.gov/artworks/46677-spring-woods
- https://www.nga.gov/artworks/52957-southern-resort-town
- https://www.nga.gov/artworks/56574-beach-beverly
- https://www.nga.gov/artworks/72328-roses

## QA visivo, esclusioni aggiuntive
Cinque candidati passavano i soli numeri ma **non** le preferenze estetiche: 46481 (On the Beach, figure in primo piano), 157923 (East Hampton Beach, persone prominenti), 61364 (Beach Scene at Trouville, folla protagonista), 89681 (View of the Louvre, grigi e beige) e 195170 (On the Coast of New Jersey, tavolozza quasi priva di colori vivaci). Identificativi esclusi direttamente dal filtro in `tools/artdrift_nga_bright_wave2.py`.

Retroattivamente i 22 precedenti sono stati confrontati con la soglia di area scura del 10%: **2** vengono posti in `HOLD_DARK_AREA_ABOVE_10_PERCENT` e **20** restano eleggibili per la shortlist estetica:
- NGA 157929, *Seascape (Gravelines)* (11,73% area scura)
- NGA 72138, *The Artist’s Garden in Argenteuil* (10,86% area scura).

Questo non cancella i report originari. La shortlist combinata è quindi **20 vecchi + 7 nuovi = 27 candidati esteticamente ammessi**, nel documento tracciabile `research/nga/20261126/nga_bright_combined_shortlist.json`.

## Dati di evidenza e limiti
- `research/nga/20261125/nga_bright_review.json`: 22 opere della prima selezione, immutato.
- `research/nga/20261126/nga_bright_wave2_review.json`: 7 ulteriori opere, hash dei file e misure cromatiche.
- `research/nga/20261126/nga_bright_combined_shortlist.json`: shortlist estetica con 2 HOLD.
- Contact sheet delle sette opere verificabile come artifact workflow **NGA-Bright-Wave2-Raster-QA**.
- Policy NGA: https://www.nga.gov/artworks/free-images-and-open-access — Open Access per i singoli record `openaccess=1`, senza garanzia di ogni potenziale diritto di terzi; mantenere gate territoriali e di pubblicazione.

**Stato:** conclusa la ricerca di questa wave, approvazione esclusivamente estetica algoritmica + revisione contact sheet; **nessuna immagine integrata automaticamente nel runtime, nessun merge, nessun APK/deploy**, perché la PR resta in modalità ricerca e i diritti richiedono gli usuali controlli prima della distribuzione commerciale.
