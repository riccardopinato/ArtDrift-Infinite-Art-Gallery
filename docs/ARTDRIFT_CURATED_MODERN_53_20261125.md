# Art Drift — Modern masters 53 / 109, acquisizione controllata (25 novembre 2026)

**Factory baseline:** 842dfa073451ec247308ccb4afb8ead5349bcbd4. **Art Drift main di partenza:** 594e6e612fbefee731d96c436ceaf6e981776e75.

## Inventario realmente registrato
- 109 artisti in research/modern_artists_109_20261125.json; 53 opere in research/modern_masters_53_20261125.json, con tutti gli ID dei musei, URL e classificazioni di partenza.
- 32 dichiarazioni museali Free to Use (fase pre-import), 16 media da verificare, 4 diritti esplicitamente protetti, 1 immagine assente.
- Stato iniziale di ogni record: HOLD. Le immagini non sono state inserite nel catalogo runtime senza le verifiche individuali.
- Le opere bloccate sono Picasso The Embrace, Kandinsky Watercolor No. 10, Kandinsky Sounds: Two Riders, John Marin Lower Manhattan; il libro illustrato di Dufy non ha immagine verificata.
- Non confondere tecnica con tipologia: Zulma è un collage, Allo Paris è una litografia; l'attuale canvas ha un filtro Painting e richiede un'eventuale collezione ampliata progettata espressamente.

## Pipeline realmente implementata
Il file tools/artdrift_modern_masters.py introduce:
- modalità inventory: audit deterministico 53 record + stati;
- modalità target: fetch puntuale dalle API ufficiali SMK sui numeri d'inventario, controllo di identificativo esatto, public_domain, has_image, licenza PDM/CC0, autore, tipo opera, host IIIF, download reale di una miniatura, controllo dei byte e SHA256; JSON di evidenze;
- modalità discover: ricerche indipendenti sugli artisti cromatici già noti presso SMK, con controlli museali e deduplica contro catalogo in main e inventario 53; risultati SOLO per revisione;
- tutte le esecuzioni producono report locali in .artdrift_research/modern_masters, nessun upload cloud, nessuna scrittura degli assets di produzione e nessun nuovo provider a pagamento.

## Comandi
    python -m unittest discover -s tools -p test_artdrift_modern_masters.py -v
    python tools/artdrift_modern_masters.py --mode inventory
    python tools/artdrift_modern_masters.py --mode target --max-records 48 --workers 3
    python tools/artdrift_modern_masters.py --mode discover --max-artists 30 --max-records 100 --workers 3

Le ultime due modalità interrogano la rete: registrare esiti parziali, errori HTTP, prove di download, duplicati. La ricerca non è stata eseguita live in questa PR fino all'esecuzione esplicita dei job API.

## Regola di pubblicazione
Un'indicazione Free to use/PD UE o CC0 sulla fotografia non dimostra automaticamente il pubblico dominio dell'opera negli USA. Neanche anno di creazione = data di prima pubblicazione. Il record tecnicamente verificato diventa HOLD_TERRITORY_AND_CURATORIAL. Dopo esame di diritti per Paese, provider policy, fonte/crediti, asset e controlli di immagini, si può integrarlo in catalogo a ID stabili senza spostare coordinate del canvas. Nessun nuovo record è stato approvato automaticamente come worldwide commercial.

Sono lasciate indipendenti le PR #42, #44, #45, #55, #61, #66, #67, lo stato user-owned, e GalleryDrift/Drift Core. Build CI non equivale ad approvazione visiva, giuridica o hardware. La presente PR è un intake ART_ONLY, non una release.

## Fonti ufficiali
- https://open.smk.dk/en/artwork/image/KMSr189
- https://www.clevelandart.org/open-access
- https://www.clevelandart.org/art/1963.234
- https://www.euipo.europa.eu/en/news/copyright-artworks-entering-the-public-domain-in-2026
- https://guides.library.cornell.edu/copyright/publicdomain

**Stato:** RESEARCH_REGISTERED e CODE_IMPLEMENTED; MEDIA_FETCH_LIVE = NOT VERIFIED; RUNTIME_INTEGRATION = 0 nuove opere; DISTRIBUTION_APPROVED = 0.
