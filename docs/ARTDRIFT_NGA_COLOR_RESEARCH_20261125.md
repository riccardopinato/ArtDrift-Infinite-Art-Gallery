# Art Drift — National Gallery of Art / bright scenic works (25 November 2026)

## Requisiti di selezione (user-defined)
- Arte postimpressionista / moderna, principalmente dipinti databili 1870–1955, con paesaggi, campi, giardini, coste, marine, fiori o viste naturali.
- Escludere i quadri prevalentemente SCURI, le foto, le stampe/monocromie e i ritratti. Obiettivo 0 ritratti in questa wave.
- Preservare sempre rapporto dell'originale e artwork ID stabili. Nessun cambiamento al canvas, ai preferiti, a GalleryDrift o a Drift Core.
- SOLO NGA published_images.openaccess == 1 e fotografia primaria ufficiale. A pagina visibile non corrisponde sempre una licenza per il download.

## Dataset NGA verificato
- Official policy https://www.nga.gov/artworks/free-images-and-open-access
- Official documentation https://github.com/NationalGalleryOfArt/opendata/blob/main/documentation/Data%20Dictionary.txt
- NGA Open Data source pinned at commit 2470472572fdca2a24a741bb50eaba7301c47fa9 (2026-11-25).
- Join ufficiale `objects.objectID = published_images.depictstmsobjectid`; `classification` contiene Painting, `viewtype=primary`, `openaccess=1`, URL HTTPS su api.nga.gov.
- Rimuovere preventivamente i NGA object IDs già presenti in main nel catalogo degli oltre 4.000 dipinti.
- Il campo Open Access NGA vale solo per le immagini con `openaccess=1`: le immagini restricted/fair use sono escluse. L'ente permette uso commerciale del set OA, ma non offre garanzie assolute contro diritti di terzi.

## Campione di pagine NGA con download Open Access, per ispezione estetica
1. The Bend in the Road — Paul Cézanne: https://www.nga.gov/artworks/66406-bend-road
2. Farmhouse in Provence — Vincent van Gogh: https://www.nga.gov/artworks/52178-farmhouse-provence
3. The Artist's Garden at Vétheuil — Claude Monet: https://www.nga.gov/artworks/52189-artists-garden-vetheuil
4. The Artist's Garden in Argenteuil — Claude Monet: https://www.nga.gov/artworks/72138-artists-garden-argenteuil-corner-garden-dahlias
5. The Lighthouse at Honfleur — Georges Seurat: https://www.nga.gov/artworks/61383-lighthouse-honfleur
6. The Blue River — Auguste Renoir: https://www.nga.gov/artworks/52219-blue-river
7. Study for La Grande Jatte — Georges Seurat: https://www.nga.gov/artworks/52225-study-la-grande-jatte
8. Green Wheat Fields, Auvers — Vincent van Gogh: https://www.nga.gov/artworks/163323-green-wheat-fields-auvers
9. The Artist's Garden at Eragny — Camille Pissarro: https://www.nga.gov/artworks/52198-artists-garden-eragny
10. Orchard in Bloom, Louveciennes — Camille Pissarro: https://www.nga.gov/artworks/52195-orchard-bloom-louveciennes
11. Farmhouse at Le Pouldu — Paul Sérusier: https://www.nga.gov/artworks/116570-farmhouse-le-pouldu
12. Brittany Landscape — Paul Gauguin: https://www.nga.gov/artworks/46623-brittany-landscape
13. The Valley of the Seine, from the Hills of Giverny — Theodore Robinson: https://www.nga.gov/artworks/166468-valley-seine-hills-giverny
14. The Island of Raguenez, Brittany — Henri Moret: https://www.nga.gov/artworks/52190-island-raguenez-brittany
15. Flower Beds in Holland — Vincent van Gogh: https://www.nga.gov/artworks/61371-flower-beds-holland

Questi 15 riferimenti sono una SHORTLIST VISIVA, non un conteggio di opere nuove: l'ingestione dati ufficiali deve determinare se già incluse in main.

## Esempi non importabili tramite NGA Open Access
- Henri Matisse, Open Window, Collioure: https://www.nga.gov/artworks/106384-open-window-collioure — pagina dichiara che la riproduzione NON è scaricabile.
- Pierre Bonnard, Table Set in a Garden: https://www.nga.gov/artworks/52152-table-set-garden — immagine NON scaricabile.
- Raoul Dufy, Saint-Jeannet: https://www.nga.gov/artworks/46618-saint-jeannet — immagine NON scaricabile.
- Raoul Dufy, Le Golfe Juan: https://www.nga.gov/artworks/38993-le-golfe-juan — immagine NON scaricabile.
- Paul Signac, Evening (Le soir): https://www.nga.gov/artworks/53073-evening-le-soir — immagine OA, ma è una stampa a colori, non un dipinto e rimane fuori dal filtro Painting.

## Pipeline codice
`tools/artdrift_nga_color_research.py` legge i due CSV ufficiali da GitHub al commit immutabile, filtra classificazione/dati/temi, verifica `openaccess=1`, esclude duplicati su main, verifica i byte della miniatura originale dal server NGA e calcola luminosità, percentuale buia e vivacità sul raster vero.

Limiti falsificabili (euristici, non valutazione umana):
- luminosità media >= 0.50;
- pixel scuri < 28%;
- pixel vivaci >= 16%;
- nessun ritratto per titolo;
- primo campione massimo 130 immagini in 4 corsie.
Questi limiti possono essere ulteriormente corretti dopo collaudo visivo su immagini e mosaico, ma non vengono bypassati silenziosamente per riempire il numero.

Report `.artdrift_research/nga_color/nga_bright_review.json` e contact sheet destinati alla CI. Solo i record con `openaccess=1` e verifica immagine entreranno come CANDIDATE, non come MAIN_LIVE o PLAY_READY. Le immagini sono richieste in basso peso solo per selezione, MAI inserite automaticamente in APK/D1/R2.

## QA visivo aggiuntivo (25 novembre 2026)
Il foglio con 25 immagini reali della prima wave ha individuato tre falsi positivi: NGA 46622 (The Basket of Flowers, figura femminile grande), NGA 164936 (The Watering Can, natura morta industriale e poco vivace) e NGA 164950 (Landscape, Ile-de-France, tavolozza quasi beige). Questi tre ID sono bloccati esplicitamente dal motore di ricerca e vengono esclusi dalla nuova selezione, senza alterare le immagini o il catalogo runtime. Il conteggio finale va letto dalla CI successiva a questa correzione.

Stato: RESEARCH_PENDING_CI; 0 nuove opere integrate da questa PR. La precedente wave SMK è autonoma in PR #68. Nessun merge/deploy senza gate pertinenti.
