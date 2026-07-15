# Incontro col professore — cosa mostrare e cosa chiedere

## Cosa mostrare (in quest'ordine, ~10 min)

1. **PIANO_TEST.md** — il pezzo forte: protocollo completo con scenari, metriche,
   ground truth, ripetizioni, comandi pronti. Chiedergli la validazione (vedi domande)
2. **SCALETTA_TESI.md** — la struttura della tesi con la mappa obiettivi→capitoli:
   dimostra che i 6 punti concordati sono TUTTI coperti e niente di più
3. **analisi/ANALISI_CONSUMI.md** — obiettivo 4 già in bozza: dati datasheet
   verificati + argomentazione architettura ibrida PIR+mmWave per UPRISE
4. Accenno rapido al resto già pronto: studio del suo repo (con firmware adattato:
   5 Hz + engineering mode), script di analisi già testati, progetto completo della
   web UI, specifica dell'indice di vitalità

## Domande da fare

### Bloccanti (servono per procedere bene)
1. **Valida il protocollo di test?** Scenari, metriche e ripetizioni di PIANO_TEST.md
   vanno bene? Manca qualche scenario che vuole vedere? (Farla PRIMA della campagna:
   sono ~10 ore di acquisizioni)
2. **Dove si monta fisicamente il sensore nel banco salva-vita?** Il piano del banco
   ha la lamiera forata antisfondamento e il radar non attraversa il metallo: sotto
   il piano puntato in basso? Su un montante? Ha senso aggiungere un test di
   penetrazione della lamiera forata?
3. **Scadenza e sessione di laurea prevista?** (serve per il cronoprogramma)

### Importanti (non bloccanti)
4. Nome del progetto nella tesi: **UPRISE o SAFE?** (le slide/paper dicono SAFE)
5. Il DIPME-DEVICE ha già l'UWB per la presenza: come inquadrare il mmWave rispetto
   all'UWB nella tesi? C'è un motivo di progetto per cui l'UWB non basta?
6. Requisiti formali della tesi: numero pagine indicativo, template Overleaf
   dell'ateneo, lingua (IT/EN)?
7. La web UI: conferma che basta "un minimo di interfaccia" come da call, o si
   aspetta qualcosa di specifico?

### Se c'è tempo
8. Possibilità di fare qualche test in un'aula vera (o al dimostratore di Ascoli)?
   Anche una sola sessione darebbe validità "sul campo" ai risultati
9. Il timeout di presenza e le soglie per-gate del radar: nel DIPME reale chi li
   configurerebbe? (rilevante per il test di selettività spaziale multi-banco)

## Aggiornare dopo l'incontro
- [ ] Riportare le risposte in CLAUDE.md (nome progetto, scadenza, montaggio sensore)
- [ ] Aggiornare PIANO_TEST.md se il protocollo cambia
- [ ] Costruire il cronoprogramma con la data di consegna
