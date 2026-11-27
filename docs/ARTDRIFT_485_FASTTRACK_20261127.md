# Art Drift — Fast Track massivo, 485 immagini

Questo PR abbandona la verifica seriale di una singola immagine per volta: **un solo processo rilegge le verifiche storiche, quindi tre corsie autonome con massimo 100 candidature a testa eseguono i gate in parallelo.**

## Fonti immutable
- Ricerca source pin: `b82a4574db3d504141b6d2e95e403aa743c771e3` (#84)
- QA pixel 45905782588 + retry HTTP429 45906699779: **459 OK, 27 HOLD**
- Licenze 45907246535 (#91): 485 file Commons/Museo; per-person claim, author credit, changed SHA
- Copyright/provenienza e possibili duplicati: 45908681652 (#92), lettura di 482 wikitext Commons e source per singolo file
- Prima opera Sisley approvata **solo per staging** in PR #94, `commons:57672559`; qui le altre 485 sono tutte HOLD.

## Criteri automatici del Fast Track
Il file è assegnato alla prima corsia soltanto se soddisfa **tutti** i criteri:
1. Preview realmente decodificata (compreso recupero 429) e SHA-1 del file stabile.
2. Dichiarazione per la foto digitale Public Domain o CC0 e nessun conflitto di metadati.
3. Nessun titolo già sospetto come versione duplicata, nessuna fotografia con licenza stratificata (dipinto PD ≠ foto CC BY), nessun sospetto di non-pittura.
4. Pittore confermato dai crediti estratti; campo `Source` recuperato dal testo completo della pagina Commons.
5. Le eccezioni note — due versioni duplicate di Sisley, due Monet Met non Open Access e lo Städel con dichiarazioni incongruenti — rimangono in HOLD separato.

Le opere prioritarie sono divise in **3 wave da 100 / 100 / residuo**. Il resto viene processato nella stessa esecuzione, ma non ritarda l'avanzamento delle wave.

**Attenzione:** la presenza di `Source` su Commons **non è prova indipendente** dell'autenticità del museo; un tag PD/CC0 non certifica automaticamente diritti e territori. I record generati sono tutti `commercially_approved=false`, `runtime_visible=false`; nessuna importazione, merge, App Store o APK commerciale viene effettuata.

## Output
Nell'artifact GitHub Actions `ArtDrift-485-FastTrack-ALL-with-3-Waves`:
`fasttrack_485.json`, `fasttrack_eligible.json`, `FAST_01/02/03.json`, `fasttrack_485.csv`, `fasttrack_summary.json`, con hash dei sei input storici e classificazione verificabile.

Il workflow tiene separati QA tecnico e decisioni editoriali. Le tre wave hanno verifiche indipendenti in CI e possono alimentare in seguito PR d'integrazione coordinate, senza ripetere da zero 485 controlli.
