# Art Drift — Secondo lotto istituzionale CC0 · 27 novembre 2026

**Factory baseline** `f8b9f550c544735237f19cdd723bd2df667ceee6`, Master 27 / Golden Index 31. **Repo parent** `86abd0a91d86dee05dde544ee11e60b29a0c7b0c`, con 4 registrazioni ammesse da PR #97. Questo lotto non introduce nuove immagini con diritti incerti né altera il Drift Core condiviso con GalleryDrift.

## Nuove opere, licenze e prove primarie

### 1. Ludvig Karsten — Decorative Landscape (1909) · Finnish National Gallery / Ateneum

- Commons file **pageID 80538945**, SHA-1 storico **3fee3f38886a5d158113e35db113e4f20e9e6ed7**, immagine JPG 4000×3888, dipinto ad olio su tela, inv. **A II 1275**, museo **Finnish National Gallery / Ateneum Art Museum**.
- Pagina file digitale: https://commons.wikimedia.org/wiki/File:Ludvig_Karsten_-_Decorative_Landscape_-_A_II_1275_-_Finnish_National_Gallery.jpg. La pagina distingue opera originale PD e digitalizzazione **CC0 1.0**. Il file originale proviene dal profilo `CC0full` del servizio fotografico Finnish National Gallery, verificabile nella cronologia.
- Collezione ufficiale: https://kokoelma.kansallisgalleria.fi/en/object/400446 e catalogazione museo https://www.finna.fi/Record/kansallisgalleria.194AF2E90B96B4D3D5AE943808B51C6A ; la scheda è marcata **CC0**.
- Politica del museo: https://kansallisgalleria.fi/en/photographic-service/ chiarisce che le immagini segnalate **Copyright Free** possono essere scaricate e riutilizzate gratuitamente e che il museo ha reso oltre 36.000 immagini disponibili sotto CC0.
- Autore quadro 1876–1926: dipinto 1909; il termine ordinario dei diritti d'autore sul quadro è scaduto in Italia e in Finlandia. Crediti fattuali dell'artista e istituzione conservati nella UI.
- **Scelta immagine**: la fotografia ufficiale in formato JPEG, non il testo del museo né una fotografia secondaria; versione SHA-1 pinned. Nessuna cornice alternativa.

### 2. Claude Monet — Banks of the Seine, Vétheuil (1880) · National Gallery of Art, Washington

- Commons file **pageID 81308959**, SHA-1 storico **8f3f33e2b9387b296a06cb87f7ef80ec329d7dcf**, JPG 4000×2915, immagine donata da **National Gallery of Art**, licenza digitale esplicita **CC0 1.0**. Il precedente flag testuale `LICENSE_METADATA_CONFLICT` riflette un'etichetta PD nella ricerca iniziale vs CC0 nella pagina corrente; è riconciliato con file specifico, attribuzione e policy del donatore.
- Pagina Commons: https://commons.wikimedia.org/wiki/File:Claude_Monet,_Banks_of_the_Seine,_V%C3%A9theuil,_1880,_NGA_46652.jpg
- Scheda istituzionale https://www.nga.gov/artworks/46652-banks-seine-vetheuil ; autore Claude Monet, opera **1880**, inventario **1963.10.177**, donazione Chester Dale Collection. La pagina permette il download e dichiara espressamente *media free and in the public domain*.
- Politica NGA https://www.nga.gov/terms-and-notices : le immagini della collezione in **Open Access** sono CC0 e autorizzate anche per riusi **commerciali**; l'istituzione incoraggia credito di cortesia, che la UI Art Drift include.
- L'immagine NGA è distinta dall'altra riproduzione Flickr della stessa opera, con licenza CC BY 2.0: non importare la variante per non duplicare quadro e crediti.
- Questa è l'unica rappresentazione della specifica opera NGA 46652 ammessa nel lotto.

## Metodo massivo, non seriale

Il job GitHub riconcilia **485** record del lotto iniziale (escluso il primo Sisley), quindi verifica cinque shard disgiunti da 100/100/100/100/85: **5 approvati nel sottoinsieme** (3 già ammessi nel precedente lotto, 2 nuovi), **480 non ammessi o esclusi**, fra cui le 2 riproduzioni duplicate del Sisley. Aggiungendo il primo Sisley esterno al lotto dei 485, il catalogo conta **6 immagini in totale**; dei 486 file originali, **6 integrati**, **2 versioni duplicate escluse** e **478 in HOLD per diritti, provenienza o qualità**. Nessuna immagine HOLD/EXCLUDED entra nel catalogo Flutter.

La seconda wave approva 2 file con fonti indipendenti; per gli altri 480 del set di 485, rimangono i metadati/sorgenti precedenti e un HOLD conservativo. La priorità futura resta ricercare direttamente le banche dati aperte **NGA e Finnish National Gallery** a livello di file invece di controllare manualmente siti d'asta.

## Gates di distribuzione

- Catalogo `assets/museums/catalog_curated_commons.json`: ora 6 immagini, di cui 2 nuove.
- Build standard: flag `ARTDRIFT_ENABLE_CURATED_COMMONS=false` → 4.500 opere.
- Build test: flag `ARTDRIFT_ENABLE_CURATED_COMMONS=true` → 4.506 opere (se source/build QA PASS).
- Attribuzione e fonte visibili; wallpaper disabilitato sulle Commons; attribuzioni CC0 di cortesia. No scraping di contenuti testuali artistici.
- Non dichiarare certificazione Play Store, worldwide legal warranty o test fisico da CI. Non abilitare la release pubblica senza verificare il build e i requisiti commerciali generali.

Le dichiarazioni di provenienza/diritti derivano da fonti museali e licenze espressamente pubblicate, **non** da una deduzione indiscriminata dal solo periodo di morte degli artisti.
