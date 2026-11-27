# Art Drift — Primo rilascio candidato: Sisley / Met CC0 (27 novembre 2026)

**Obiettivo:** primo dipinto delle 486 candidature pronto sul piano documentale, *solo su ramo di rilascio candidato*. La PR #93 mantiene il catalogo `[]`; il contenuto pubblico di `main` resta invariato.

## Opera, fonte e identificazione

- Titolo: **The Bridge at Villeneuve-la-Garenne**.
- Autore: **Alfred Sisley**, 1872, olio su tela, 49,5 × 65,4 cm. Autore morto nel 1899: termine ordinario dei diritti sul quadro scaduto da tempo in UE e negli Stati Uniti.
- Museo proprietario: **The Metropolitan Museum of Art**, numero inventario **64.287**, numero oggetto digitale Met **437680**, donazione Mr. and Mrs. Henry Ittleson Jr., 1964.
- Scheda ufficiale museo: https://www.metmuseum.org/art/collection/search/437680 (etichetta `Public Domain` e pulsante `Download Image`).
- Programma ufficiale di riutilizzo CC0 e usi commerciali: https://www.metmuseum.org/hubs/open-access
- Fonte del **file digitale specifico**: https://commons.wikimedia.org/wiki/File:The_Bridge_at_Villeneuve-la-Garenne_MET_DT1040.jpg. Commons identifica Met 437680, attestazione della donazione del file da The Met, 3.811 × 2.911 px, attribuzione CC0 1.0 e numerazione inventario 64.287. Altre versioni incluse quelle con cornice devono restare escluse.
- La licenza CC0 1.0 indica la rinuncia, per quanto consentito dalle leggi applicabili, anche ai diritti affini e per uso commerciale: https://creativecommons.org/publicdomain/zero/1.0/.
- L'originale digitale attuale ha SHA-1 Wikimedia **16cff2d3a048f6b4b5b1d58077ef4d7296a8ade2**, identico alla precedente verifica di provenienza; il thumbnail 500px è stato decodificato nel QA [#45905782588](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45905782588), dimensioni 500×382, luminosità media 0,5978.
- Risultati preliminari di deduplicazione [PR #92](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/pull/92): nessun collegamento sospetto tra questo file e le 4.500 opere presenti. Un controllo automatico rigido confronta anche titolo e identificativo museo prima dell'uso.

## Decisione di documentazione dei diritti

Per **questa immagine Met CC0**, e solo per essa, la provenienza primaria, il diritto sul quadro, il diritto di riproduzione fotografica e la copertura commerciale in ambito internazionale risultano sufficientemente documentati dalle fonti indicate. Si registrano nel catalogo di stage i flag `commercially_approved`, `source_provenance_verified`, `worldwide_distribution_reviewed` e una traccia di review. Non si estendono questi flag per analogia ad altre opere del Met, immagini con restrizioni o file esterni.

Il file è conservato come URL immagine su infrastruttura Wikimedia, senza importazione di testo descrittivo museale, e viene mostrato con attribuzione fattuale e link alla licenza e fonte. **La licenza CC0 non richiede giuridicamente un credito ma Art Drift lo mostra volontariamente.**

## Blocchi di rilascio e QA

- Default build: `ARTDRIFT_ENABLE_CURATED_COMMONS=false`, **4.500 opere**: la nuova entry non entra nella home.
- Solo build di test specifica: `--dart-define=ARTDRIFT_ENABLE_CURATED_COMMONS=true`. **Atteso: 4.501 opere**, incluso esattamente un `commons:57672559`.
- Staging PR separata e non rilasciata su `main`; nessun merge/sideload automatico; firmata solo internamente per test.
- Escludere `commons:57670806` e `commons:57670842` dalla prima release perché il sito museo indica che l'immagine non è attualmente ingrandibile/scaricabile, nonostante il claim CC0 sul file Commons; sarà verificata la ragione del conflitto.
- I 483 file rimanenti tra i 486 continuano nel fascicolo del precedente audit, senza false approvazioni.

Questo è un **giudizio documentale sul file esplicito** basato sulle condizioni pubblicate, non una dichiarazione che ogni immagine in pubblico dominio sia automaticamente riutilizzabile in ogni contesto.
