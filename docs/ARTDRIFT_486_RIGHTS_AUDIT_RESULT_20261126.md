# Art Drift — esito ufficiale del controllo documentale diritti per 486 immagini

Data audit: 26 novembre 2026
Fonte: PR #84 commit `b82a4574db3d504141b6d2e95e403aa743c771e3`.
Pipeline: [GitHub Actions 45907246535](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45907246535) — **6/6 PASS**.
Report individuale nel relativo artifact `ARTDRIFT-486-LICENSE-RIGHTS-EVIDENCE-REPORT`: `rights_486_per_item.json`, `rights_486_review.csv`, `rights_486_summary.json`.

## Esiti evidenza di licenza, per ogni file

| Fonte/licenza corrente | File | Interpretazione di lavoro |
|---|---:|---|
| Commons Public Domain | 440 | Dichiarazione PD attuale da scheda del file; verificare autore, origine, riuso, territori |
| Commons CC0 | 6 | Dichiarazione CC0 attuale da scheda del file; verificare origine/identità e territori |
| Commons CC BY | 19 | Riuso commerciale permesso **alle condizioni** della licenza; credito, link e modifiche |
| Commons CC BY-SA | 20 | Riuso commerciale permesso **alle condizioni**; attribuzione e ShareAlike dove applicabile |
| Städel Museum | 1 | Quadro Sisley con «Picture Copyright: Public Domain», a fronte di una precedente dichiarazione CC BY-SA; riconciliazione necessaria |
| **Totale** | **486** | **485 schede file Commons interrogate dal vivo; 1 scheda ufficiale museo esaminata** |

**Altre verifiche:** 0 file Commons con SHA-1 cambiato; 0 dichiarazioni correnti NonCommercial rilevate; 3 rettifiche del precedente `UNVERIFIED_OR_RESTRICTED` rilevate da Commons come 2 CC0 + 1 CC BY-SA.

### Discrepanze precise

- `commons:141575821` — Sisley, «Les Coteaux de la Celle…», etichetta precedente sconosciuta, scheda attuale CC0
- `commons:42282652` — Sisley, «MAMCS Sisley Les Coteaux», etichetta precedente sconosciuta, scheda attuale CC0
- `commons:79292696` — Monet, «Eine Allee in Monets Garten…», etichetta precedente sconosciuta, scheda attuale CC BY-SA
- `staedel:DE-MUS-048017/lido/1350` — Sisley «Bank of the Seine in Autumn»: fonte ufficiale [Städel](https://sammlung.staedelmuseum.de/en/work/bank-of-the-seine-in-autumn) indica Public Domain nella voce Picture Copyright, inventario 1350; lo staging diceva CC BY-SA

### Attribuzione e provenienza

- **57 file:** il rilevamento testuale automatico non ha trovato il nome normalizzato del pittore nel campo Artist/Credit. Molti sono fotografie del quadro con il nome del fotografo, oppure presentano traslitterazioni alternative (specie Vasylkivskyi). Non è una prova di falsa attribuzione: controllare titolo, template Commons e scheda museo
- **485 file Commons:** il campo `Source` estratto da Commons extmetadata è vuoto. Questo **non dimostra** assenza di fonte nella descrizione integrale; le informazioni nel `Credit`, pagina file e template devono essere ricontrollate individualmente
- 0 identità perse; 0 nuove opere importate; 0 licenze rese «commercially_approved» senza revisione

## Significato per il rilascio

**Audit delle dichiarazioni di licenza: COMPLETATO 486/486.**
**Autorizzazione commerciale e territoriale finale: NON COMPLETATA.**
Le licenze CC BY/BY-SA non sono vietate in un'app commerciale, ma richiedono crediti e conformità.
Un'opera del pittore in pubblico dominio in Italia/UE non autorizza automaticamente un particolare file fotografico, né garantisce condizioni identiche in tutti i Paesi.

Per l'Italia/UE: durata generale vita autore + 70 anni; direttiva UE 2019/790 art. 14 e LDA art. 32-quater per riproduzioni non originali di arte visiva di pubblico dominio, salve le norme sui beni culturali (Codice artt. 107-108).
Fonti:
- https://eur-lex.europa.eu/eli/dir/2019/790/oj
- https://www.normattiva.it/atto/caricaDettaglioAtto?atto.codiceRedazionale=21G00192&atto.dataPubblicazioneGazzetta=2021-11-27
- https://www.normattiva.it/atto/caricaDettaglioAtto?atto.articolo.numero=108&atto.codiceRedazionale=004G0066&atto.dataPubblicazioneGazzetta=2004-02-24
- https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia
- https://creativecommons.org/licenses/by/4.0/
- https://creativecommons.org/licenses/by-sa/4.0/

## Gate approvazione

Prima di una PR per il canvas: provenienza e artista della singola opera; scelta della fotografia/versione; licenza attuale con crediti corretti; compatibilità con trasformazioni WebP; condizioni museali e territoriali; controllo duplicati di opera (non soltanto SHA); verifica estetica, poi test e rilascio. **Niente merge diretto da questa PR di audit.**
