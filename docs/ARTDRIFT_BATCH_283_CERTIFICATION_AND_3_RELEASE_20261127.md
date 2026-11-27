# Art Drift — Certificazione massiva 283 e integrazione delle 3 nuove immagini con fonte istituzionale

Data di verifica: 27 novembre 2026. **Questa è una revisione per documenti e condizioni pubblicate, non una garanzia legale per ogni giurisdizione.** La parte tecnica precede il merge e la distribuzione.

## Punto 2 — verifica massiva 100 + 100 + 83

Fonte input immutabile: workflow #45962610069 e PR #95. 283 candidature, 3 wave indipendenti. La certificazione controlla una per una la presenza di autore, titolo, metadati della licenza, stabilità del file digitale, presenza della fonte e anomalie. La dichiarazione Commons PD senza fonte primaria non è sufficiente. Le PR #91/#92 contengono le licenze individuali e le descrizioni originali.

Distribuzione delle 283 sotto l'approccio conservativo:
- **3** file con fonte istituzionale identificata, opera in pubblico dominio, politica del museo compatibile, riproduzione digitale PD e versione Commons tracciata;
- **188** provenienti da fonti commerciali, aste o secondarie: HOLD per origine e condizioni del file;
- **48** fonte primaria o condizioni di diritto incomplete: HOLD;
- **25** foto di uploader o autore del file da riconciliare: HOLD;
- **18** fonti museali presenti ma senza prova specifica della licenza della riproduzione: HOLD;
- **1** Met Monet escluso dal rilascio, per `isPublicDomain=false` e immagine primaria vuota nella Collection API.

Totale **280** non approvate. Tutte mantengono `commercially_approved=false`.

## Punto 3 — integrazione in un unico catalogo di 3 nuove opere

L'immagine Met/Sisley `commons:57672559` era già stata certificata nella PR #94, e non cambia. Si aggiungono:

| Commons pageID | Opera | Fonte primaria, licenza immagine e prova |
|---|---|---|
| `52129968` | Claude Monet, *View over the Sea* (1882) | Nationalmuseum, [record #19182](https://collection.nationalmuseum.se/en/collection/item/19182/); [file Commons](https://commons.wikimedia.org/wiki/File:View_over_the_Sea_(Claude_Monet)_-_Nationalmuseum_-_19182.tif) donato dall'istituzione; dichiarazione foto PD |
| `52132342` | Harald Sohlberg, *Winter Night in the Mountains. Study* | Nationalmuseum, [record #25961](https://collection.nationalmuseum.se/en/collection/item/25961/); [Commons file](https://commons.wikimedia.org/wiki/File:Winter_Night_in_the_Mountains._Study_(Harald_Sohlberg)_-_Nationalmuseum_-_25961.tif), attribuzione della foto a Nationalmuseum e dichiarazione PD |
| `80548151` | Claude Monet, *The Artist’s Garden in Giverny* (1900) | Yale University Art Gallery, inventario 1983.7.12, [opera #25976](https://artgallery.yale.edu/collections/objects/25976); [file Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_The_Artist%E2%80%99s_Garden_in_Giverny_-_1983.7.12_-_Yale_University_Art_Gallery.jpg) riproduzione PD |

Documentazione primaria delle condizioni:
- [Nationalmuseum: Rights and reproductions](https://www.nationalmuseum.se/en/explore-art-and-design/images/rights-and-reproductions): le immagini PD sono riutilizzabili e il museo chiede volontariamente crediti dell'artista e del fotografo.
- [Yale University's Policy on Open Access, spiegata da Yale Library](https://guides.library.yale.edu/openaccess): immagini di opere PD della collezione libere da restrizioni.
- [Creative Commons Public Domain Mark](https://creativecommons.org/publicdomain/mark/1.0/).
- [MET Open Access](https://www.metmuseum.org/hubs/open-access), per il Sisley già staged.

Sono escluse esplicitamente le riproduzioni con due licenze (PD quadro/CC BY fotografia) che non possono essere equiparate a PD, come Karsten Blue Kitchen; e la riproduzione Monet *Garden at Sainte-Adresse* (Met 437133), che l'API corrente [Met](https://collectionapi.metmuseum.org/public/collection/v1/objects/437133) indica non Open Access.

## Regola tecnica e release

Catalogo passato da 1 a **4 immagini Commons**, nessuna delle altre 280 è presente. **Build normale:** `ARTDRIFT_ENABLE_CURATED_COMMONS=false` e galleria **4.500** opere inalterate. **Build Android di collaudo con flag esplicito:** `--dart-define=ARTDRIFT_ENABLE_CURATED_COMMONS=true` e galleria **4.504** opere.

Tutte le immagini aggiunte hanno attribuzione della fotografia, link alla pagina sorgente, dichiarazione della licenza e niente esportazione wallpaper. Thumbnail Wikimedia JPG (500px, uno a 330px) già testati ma la qualità a massima risoluzione e la disponibilità della CDN vanno collaudate su dispositivo: la certificazione di copyright non certifica un download di qualità. Il file originale TIFF non è usato direttamente in Flutter per evitare formati non decodificabili dal dispositivo.

**Distribuzione commerciale:** la compatibilità è valutata sui termini istituzionali e sull'uso previsto prevalentemente in Italia/UE e USA; non è garanzia per qualsiasi Paese che applichi termini di protezione diversi. Non pubblicare su Play Store a diffusione globale senza impostare e verificare territori e condizioni. Il flag tecnico `worldwide_distribution_reviewed=true` significa che le condizioni di distribuzione sono state esaminate per le release previste, non che una garanzia legale planetaria sia stata ottenuta.

La pipeline GitHub in questa PR:
1. certifica le 3 wave in parallelo e registra tutti i 283 esiti nel job di riconciliazione;
2. confronta gli identificativi e gli SHA-1 dei 3 approvati con il catalogo effettivamente committato;
3. cerca duplicati negli altri 5 cataloghi;
4. esegue Flutter analyze, test di regressione Web/Android, test con flag di release abilitato;
5. compila un APK ARM64 di test con 4.504 opere.

Le altre 280 rimangono in coda, non in runtime.
