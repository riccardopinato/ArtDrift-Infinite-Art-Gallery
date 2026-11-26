# Art Drift — nuova rete museale NON USA, 26 novembre 2026

## Motivazione
Il catalogo investigato in precedenza ha riutilizzato ripetutamente NGA, Met, Cleveland Museum of Art, Art Institute of Chicago e SMK. Per la prossima fase questi cinque cataloghi sono **fuori scope**. Non ci sono nuove richieste API verso quelle istituzioni in questa pipeline. Rimane possibile la verifica locale di deduplicazione con il catalogo Art Drift esistente.

Filtri approvati: pittura e paesaggi/giardini/marine/fiori, modernità prevalentemente 1850–1960, **≤15% di pixel molto scuri preferito**, 15–20% solo con forte vivacità (saturazione ≥24%, pixel vivaci ≥30%, luminosità media ≥55%), >20% scartato. Limitare i ritratti e scartare le scene notturne. Medie cromatiche non equivalgono ad approvazione visiva.

## Musei indipendenti individuati

| Priorità | Fonte | Paese | Accesso agli oggetti | Diritti delle immagini | Sviluppo |
|---|---|---|---|---|---|
| P1 | Rijksmuseum, Amsterdam | Paesi Bassi | API Linked Art Search senza key, IIIF su micr.io | immagini per lo più PD/CC0 ma ogni object va controllato | Implementato e testato |
| P1 | Nationalmuseum, Stoccolma | Svezia | Categoria Commons istituzionale; 6.000 immagini PD dichiarate dall'istituto | verifica CC0/PDM per ogni file originale | Implementato e testato |
| P1 | Belvedere, Vienna | Austria | Public Open Content con circa 5.900 oggetti elencati al momento | solo opere PD realmente rilasciate CC0; non tutti i 5.900 | Programma verificato; HTTPS 403 alla richiesta automatica |
| P1 | Finnish National Gallery / Ateneum, Helsinki (con Kiasma/Sinebrychoff) | Finlandia | archivio pubblico, API da verificare e possibile credenziale | più di 36.000 immagini ufficialmente CC0; **non** tutte le opere in catalogo | Nuova fonte prioritaria, probe accesso |
| P1 | Birmingham Museums Trust | Regno Unito | portale immagini istituzionale | scaricamento CC0 degli oggetti fuori copyright, non di tutti | Nuova fonte prioritaria, probe accesso |
| P1 | Te Papa, Wellington | Nuova Zelanda | GET collections API disponibile, POST avanzato con chiave | metadata CC BY; **immagini eterogenee**, licenza per file obbligatoria | Nuova fonte prioritaria, probe accesso |
| P2 | Städel Museum, Francoforte | Germania | OAI LIDO/DC live, 100 record LIDO per richiesta | immagini **CC BY-SA 4.0**, richiedono crediti e gestione share-alike | Implementato, campione iniziale 200 record |
| P2 | Paris Musées (Petit Palais, Musée d'Art Moderne de Paris e altri) | Francia | public portal attivo; API JSON richiede token e registrazione | CC0 solo per opere effettivamente PD | Via portale; non aggirare token API |
| P2 | Nasjonalmuseet, Oslo | Norvegia | DigitaltMuseum API; verifica chiave | licenze file eterogenee | Fonte da integrare separatamente |

**Fuori dalla pipeline commerciale automatica:** National Gallery London (foto CC BY-NC-ND) e National Gallery of Victoria (programma download non-commercial). Nessuna richiesta di importazione immagini da queste due fonti.

## Evidence verificata e differenze tra fonti
- Rijksmuseum [API Search ufficiale](https://data.rijksmuseum.nl/tutorials/search/) e [IIIF a tre hop](https://data.rijksmuseum.nl/tutorials/iiif/). Nel primo probe la ricerca `type=painting&imageAvailable=true&title=landschap` ha restituito **246 corrispondenze metadata** (non immagini approvate).
- Belvedere [Open Content](https://sammlung.belvedere.at/opencontent/images) documenta CC0 per singole riproduzioni PD; la pagina HTML ufficiale è stata recuperata da ricerca web, ma GitHub Actions HTTP automatico ha risposto **403**. Nessun bypass.
- Nationalmuseum [programma immagini](https://www.nationalmuseum.se/en/explore-art-and-design/images) con 6.000 file PD diffusi attraverso Wikimedia.
- Städel [OAI](https://sammlung.staedelmuseum.de/en/oai/guide), metadata CC0 e immagini CC BY-SA 4.0; OAI Identify e ListRecords hanno risposto HTTP 200.
- Finnish National Gallery [Photographic service](https://kansallisgalleria.fi/en/photographic-service/) dichiara più di 36.000 immagini CC0 con identificazione individuale "Copyright Free".
- Birmingham [Picture Library](https://www.birminghammuseums.org.uk/collection/picture-library) permette download CC0 delle immagini fuori copyright.
- Te Papa [Collections API](https://data.tepapa.govt.nz/collection) documenta GET search e diritti individuali sulle immagini.
- Paris Musées [documentazione autenticazione](https://apicollections.parismusees.paris.fr/en) richiede account/token API.
- National Gallery London [licenze](https://www.nationalgallery.org.uk/documentation/ngacuk/licences) è CC BY-NC-ND **per immagini**.

## Lavoro effettivo nel repository
- `research/museums/20261126/non_us_museum_registry.json`: 11 sorgenti registrate, 9 con possibili percorsi di acquisizione / ricerca, 2 con esclusione per licenza commerciale.
- `research/museums/20261126/non_us_source_access_results.json`: test HTTP su cinque musei, tre percorsi API/OAI funzionanti e una limitazione Belvedere.
- `research/museums/20261126/eu_sample_object_schemas.json`: struttura Linked Art Rijks, Wikimedia-Sweden con licenze PD, OAI Städel.
- `tools/artdrift_eu_new_museums_batch.py` + test: batch su Rijksmuseum, Nationalmuseum e Städel con controllo del file immagine, SHA, colori ed esclusione ritratti.
- `research/museums/20261126/new_european_museum_bright_batch1.json`: 9 batch iniziali, **1 dipinto** Rijksmuseum ha superato il filtro raster nel primo campione; non è ancora liberato per uso commerciale. Il basso tasso di passaggio non va nascosto.
- `tools/artdrift_eu_source_probe.py` aggiornato con tre ulteriori fonti (Finlandia, Birmingham, Nuova Zelanda), 8 probe automatici indipendenti.

## Limiti e prossimo ordine d'intervento
Non attribuire a Art Drift migliaia di opere perché il museo possiede migliaia di riproduzioni. Una sorgente è **attiva** quando almeno un object ha dati completi, ID stabile, immagine realmente scaricabile, per-image rights, soggetto coerente, SHA e misure raster. I controlli legali devono tener conto della commercializzazione app e del territorio; CC BY-SA non è CC0. Autore, titolo e opera devono essere deduplicati tra musei (non soltanto gli URL).

**Ordine ricerca**: Finnish National Gallery → Paris Musées via fonti pubbliche/accesso token → Belvedere portale pubblico → Rijks approfondito e Nationalmuseum → Birmingham → Städel → Te Papa → Nasjonalmuseet.

**Stato**: indagine e test source completati, prime pipeline verificate e report registrati; **0 opere pubblicate in app, 0 merge, 0 APK aggiornato**. Questa ricerca è indipendente dal Master App Factory (baseline già fissata durante lo sviluppo precedente).
