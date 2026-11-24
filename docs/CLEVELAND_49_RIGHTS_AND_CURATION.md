# Art Drift — audit Cleveland, 49 opere D1 (24 novembre 2026)

## Ambito e stato

- Database Cloudflare D1 già popolato e verificato: `artdrift-moma-cc0`, tabella additiva `artdrift_museum_ingest`.
- Totale importato: 535 `HOLD` (233 Tate metadata-only, 253 MoMA metadata-only, 49 Cleveland immagini candidate). Nessun contenuto pubblicato: `artdrift_publishable_modern_art` = **0**.
- Le 49 opere Cleveland **erano già presenti nei cataloghi locali**. Questo audit non riguarda 49 nuove immagini; non scarica file multimediali.
- Registro per-oggetto prodotto da [GitHub Action 45298828623](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45298828623), artefatto `artdrift-cleveland-rights-review-45298828623`, ID `14877921473`. Ogni riga contiene identificativo, titolo, artista, fingerprint, URL scheda, URL API e flag di revisione.

## Fonti ufficiali

- API pubblica per singola opera: `https://openaccess-api.clevelandart.org/api/artworks/{id}`.
- Documentazione API: https://openaccess-api.clevelandart.org/ .
- Open Access ufficiale: https://www.clevelandart.org/open-access .
- Termini e condizioni: https://www.clevelandart.org/terms-and-conditions .

Il museo chiarisce che i metadati sono CC0, ma una fotografia è riutilizzabile secondo la sua policy quando il singolo record riporta `share_license_status=CC0`. La dedicazione CC0 del museo non è garanzia sui diritti dei terzi relativi all'opera originale.

## Esito acquisito dal primo registro completo

| Controllo su 49 | Risultato |
|---|---|
| Identità e titolo museo | **49/49 coerenti** |
| Classificazione `Painting` | **49/49 coerenti** secondo API |
| `share_license_status` attuale | **49/49 CC0** |
| Immagine `web` primaria e host CDN | **49/49 coerenti** |
| Autore e data di morte | **49/49 superano il gate automatico**; non sostituisce la verifica legale |
| URL `print` uguale al catalogo storico | **20/49** |
| URL `full_image_url` storico impostato come identico a `web` | **29/49** |
| Differenza aggiuntiva URL scheda opera | **1/49**, `cleveland:123953` |
| Approvazioni editoriali automatiche | **0** |
| Pubblicazioni nel canvas / view D1 | **0** |

Le 29 segnalazioni di alta risoluzione derivano dalla **mancanza del link `print` nei record storici**, per cui l'importatore ha usato la stessa immagine `web` anche come `full_image_url`. Il controllo corrente distingue ora il fallback da una revoca dei diritti, e registra l'URL `print` reperito dall'API ufficiale per un futuro intervento di rettifica. Non sono state fatte modifiche di immagine sul database da questo audit.

## Secondo gate: pertinenza editoriale

Il filtro originario sui nomi famosi ammetteva qualsiasi autore contenente il cognome `Rousseau`, anche quando il riferimento desiderato era **Henri Rousseau**. Nel registro sono presenti:

- **9** opere firmate da altri Rousseau (Pierre, Philippe, Théodore): da valutare e presumibilmente escludere dalla sezione dedicata ai grandi maestri moderni;
- tra queste, **7** opere presentano titoli riconducibili a porte o decorazioni architettoniche (`Double-Leaf Doors`, `Overdoor Painting`): non vanno proposte automaticamente come grandi dipinti;
- le 9 osservazioni sono **9 opere distinte**, non 16. I loro metadati possono restare in D1 in `HOLD`, ma non costituiscono accettazione curatoriale.

I flag sono informativi; non cancellano opere e non assegnano lo stato `REJECTED` senza revisione.

## Integrazione controllata: PR #43

La [PR #43](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/pull/43) contiene il Worker D1 con endpoint `GET /api/v1/modern-approved`, che interroga **esclusivamente la view `artdrift_publishable_modern_art`**. Finché tutte le opere sono in `HOLD`, restituisce una lista vuota. Rilettura dei dati non altera D1, non passa secret all'app, non esegue richieste al museo dall'utente e non pubblica file.

Il client Flutter è progettato con flag esplicito `ARTDRIFT_ENABLE_APPROVED_MODERN=true` **disabilitato per impostazione predefinita**. Senza Worker HTTPS + flag, la funzione non è attiva; non è stato eseguito alcun deploy.

## Condizioni prima di pubblicare opere

1. Correggere e registrare i link ufficiali `print` dove manca l'alta risoluzione, preservando fingerprint e log di provenienza, sempre in `HOLD`.
2. Esaminare i 9 casi fuori brief e i titoli di opere architettoniche; decidere separatamente inclusione/esclusione editoriale.
3. Convalidare i diritti delle opere sottostanti, dell'immagine, gli eventuali titolari terzi, le restrizioni territoriali e i crediti; verificare che il record API sia ancora CC0 prima di ogni singola approvazione.
4. Attivare `APPROVED` soltanto tramite revisione editoriale separata, per opera; non attraverso import massivo.
5. Verificare la view D1, testare Worker e Flutter su dispositivo e soltanto dopo valutare deploy/flag.

**Stato registrato:** SOURCE-AUDITED / EDITORIAL-HOLD. Nessuna certificazione legale globale né autorizzazione a pubblicare.
