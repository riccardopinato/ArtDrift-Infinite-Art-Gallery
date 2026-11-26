# Art Drift — confronto percentuali zone scure (26 novembre 2026)

## Nuova regola proposta per le prossime wave

Il numero indica **la percentuale di pixel con luminosità inferiore al 31%** nell'area interna dell'immagine. **Non** significa luminosità media del quadro.

- Fino al **15%** di superficie molto scura: fascia **preferita**; conservare luminosità media almeno **55%**, saturazione media almeno **18%**, pixel vivaci almeno **18%**.
- Dal **15% al 20%**: fascia **condizionata**, accettabile solo con saturazione media almeno **24%** e almeno **30%** di pixel vivaci, oltre alla luminosità media 55%. Questi quadri passano un controllo visivo prioritario; niente scene cupissime.
- Oltre il **20%**: esclusione dalla wave colorata.
- Nessun allentamento per ritratti, opere senza immagine reale, duplicati, diritti, attribuzioni dubbie o immagini non realmente scaricabili.

## Replay dei dati storici dalle immagini vere
Workflow: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45822251877 (**PASS**). Python stdlib, 5 test, 22 artefatti da GHA storica, scala senza scaricare immagini una seconda volta.

| Fonte | 10% | 15% | 20% | Condizioni |
|---|---:|---:|---:|---|
| Commons, file tecnicamente color-pass | 113 | 120 | 127 | 874 ID con metriche salvate su 880 esaminati: conteggio 15/20 è MINIMO per 6 media senza metriche persistite |
| SMK, ID distinti nel campione metrico | 7 | 8 | 8 | +1 ID KMS7625, superficie scura 14,44%, saturazione 28,52%, vivacità 42,41% |
| Cleveland, ID nel campione metrico | 10 | 10 | 10 | Dato replay dei batch (8 precedenti nel catalogo aggregato, 2 erano ripetizioni cross-batch/source e non vanno conteggiati come nuovi) |
| NGA, shortlist estetica esistente | 27 | 29 | 29 | Recuperati due soli quadri tenuti in HOLD perché >10% scuri |
| Met | 21 esistenti | non misurabile dai report storici | non misurabile dai report storici | 257 respinti senza metriche persistite: necessario nuovo raster check, nessuna stima inventata |

In particolare le due opere NGA che ritornano eleggibili al 15%:
- **The Artist's Garden in Argenteuil** (Claude Monet), NGA 72138: **10,86%** pixel scuri.
- **Seascape (Gravelines)** (Georges Seurat), NGA 157929: **11,73%** pixel scuri.

Commons: +7 file a **15%**, +14 file a **20%** (rispetto al 10%); dei sette tra 15 e 20%, solo **2** superano anche la nuova soglia di saturazione alta e vivacità alta. Tra i sette tra 10 e 15%, **3** sono già molto vivaci. Totale **5 nuove immagini particolarmente colorate** nel campione con la policy a due fasce, oltre ai 113 precedenti. Non promuovere automaticamente i 14 a opere uniche: i record HOLD non includono tutti i metadati necessari.

## Evidenza e salvataggio
- Replay verificabile: `research/experiments/20261126/dark_threshold_10_15_20.json`.
- Codice riutilizzabile: `tools/artdrift_dark_threshold_ab.py`, funzioni `pixel_eligible` e `color_tier`.
- Test: `tools/test_artdrift_dark_threshold_ab.py`.
- Fonte report storici dei 10%: Commons GHA #45815982003, SMK #45814424944, CMA #45813706451, NGA `research/nga/20261126/nga_bright_combined_shortlist.json`.
- Nessuna modifica ai report d'origine, ai cataloghi di distribuzione o al canvas. Questa PR modifica **solo le regole di selezione per le future ricerche**, non i diritti o il risultato già distribuito.
- L'idea di usare 15 e 20% è motivata dall'esperimento. **Non è ancora stata effettuata la verifica visiva sui cinque recuperati**, né il loro eventuale inserimento.
