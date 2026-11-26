# Art Drift — Inventario cumulativo e revisione visiva (2026-11-26)

L'acquisizione di ogni museo ora deve preservare TRE sorgenti in ordine:
1. snapshot immutabile del primo inventario (se presente);
2. ultimo report conservato prima della nuova esecuzione;
3. risultati della nuova esecuzione (anche se limitati da HTTP 429).

Il reconciler `tools/artdrift_parallel_museum_reconcile.py` costruisce l'unione
deterministica per `museum_native_id`, mantenendo hash/metriche raster
già acquisite e registrando separatamente il conteggio dell'ultimo run,
quello cumulativo e gli identificativi effettivamente conservati.
Non somma i conteggi stimati restituiti dalle API.

Il file `lanes/reviews/<museo>_visual_shortlist.json` è una **coda di
valutazione umana**, non un manifest di opere approvate. Ordina
immagini cromaticamente idonee, near-miss ad alta vivacità e immagini con
metadati/diritti da approfondire; esclude dalle priorità PDF, ritratti,
contenuti estranei, provenienza contraddetta e anni fuori 1850–1960.
L'assenza dell'anno non equivale a verifica della data. Ogni voce resta HOLD.
Non si alterano il catalogo runtime, la galleria, asset app o APK.

Per HTTP 429 evitare nuove interrogazioni aggressive, salvare il parziale,
applicare controllo del numero di richieste per host e pianificare solo
i segmenti mancanti in un successivo lotto autorizzato. Test unitari
offline coprono riconciliazione idempotente, 429, conflitti di diritti,
provenienza e shortlist. Zero merge automatico.
