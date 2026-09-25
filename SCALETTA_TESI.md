# Scaletta della tesi (Overleaf) — ancorata ai 6 obiettivi

Regola anti-deriva: **ogni attività del progetto deve finire in un capitolo di questa
scaletta**. Se non ci finisce, è fuori scope (l'ecosistema DIPME — LoRa, droni,
Digital Twin — vive solo nel §1.1, mezzo paragrafo ciascuno).

Struttura consigliata dei file Overleaf:

```
main.tex
capitoli/01-introduzione.tex ... 08-conclusioni.tex
img/          (foto setup, screenshot web UI, grafici Excel esportati in PDF)
bib/tesi.bib  (le fonti sono già raccolte in CLAUDE.md → convertire in BibTeX)
```

---

## Cap. 1 — Introduzione *(nessun obiettivo: inquadramento)*
- 1.1 Contesto: progetto DIPME/SAFE in breve — arredi salva-vita, nodo DIPME,
  emergenza sismica (≤2 pagine TOTALI di contesto: il resto è rimando alle fonti)
- 1.2 Il problema specifico: rilevare una persona **ferma** rifugiata sotto un arredo
  — il caso cieco del PIR montato oggi sul DIPME-DEVICE
- 1.3 Obiettivi della tesi (i 6 punti, dichiarati esplicitamente) e struttura del documento
- **Materiale già pronto**: CLAUDE.md §Contesto; slide Sharper

## Cap. 2 — I sensori di presenza: principi e stato dell'arte *(obiettivo 1)*
- 2.1 PIR: principio piroelettrico, lente di Fresnel, dati prodotti, applicazioni
- 2.2 Radar mmWave 24 GHz FMCW: principio, gate di distanza, energia riflessa,
  micro-movimenti e respiro
- 2.3 Cenni ad altre tecnologie: UWB (presente sul DIPME! preparare il "perché
  mmWave e non UWB"), ultrasuoni, CO2 — mezza pagina ciascuna
- 2.4 Tabella comparativa e posizionamento
- **Materiale già pronto**: analisi/ANALISI_PIR.md; CLAUDE.md (specifiche + tabella
  mmWave/PIR/UWB); letteratura in CLAUDE.md §Fonti

## Cap. 3 — I moduli in esame e i dati che producono *(obiettivo 2)*
- 3.1 HLK-LD2410B: specifiche, protocollo UART, engineering mode
- 3.2 HLK-LD2420: specifiche, differenze
- 3.3 Il PIR in dotazione: modello, configurazione
- 3.4 Piattaforma di acquisizione: ESP32, firmware logger (5 Hz, per-gate), formato
  CSV unico, pipeline dati (schema: firmware → seriale/web → CSV → analisi)
- 3.5 Analisi qualitativa dei dati: esempi di tracce (persona che entra, ferma, respiro)
- **Materiale già pronto**: CLAUDE.md (specifiche complete); firmware/ld2410b_logger;
  repo professore. **Dati necessari**: Fase 0-1 dei test (prime tracce)

## Cap. 4 — Confronto sperimentale PIR vs mmWave *(obiettivo 3 — IL capitolo centrale)*
- 4.1 Protocollo: scenari, metriche (accuratezza, FP/h, FN%, latenza), ground truth,
  ripetizioni, registro sessioni (temperatura!)
- 4.2 Risultati per scenario: stanza vuota, distanze, **persona ferma** (risultato
  chiave), sotto il banco, latenze, micro-movimenti, selettività spaziale
- 4.3 Penetrazione ostacoli: cartongesso, legno, vetro, plastica (+ PIR sempre bloccato)
- 4.4 Il respiro: engineering mode + FFT, spettri, controllo negativo
- 4.5 LD2410B vs LD2420 (versione ridotta)
- 4.6 Discussione: dove il mmWave vince, dove no, limiti del setup (1-2 soggetti,
  ambiente domestico vs aula)
- **Materiale già pronto**: PIANO_TEST.md (→ §4.1 quasi diretto); analisi/analizza_test.py,
  analizza_respiro.py. **Dati necessari**: Fasi 1-5 dei test

## Cap. 5 — Consumo energetico *(obiettivo 4 — capitolo breve)*
- 5.1 Consumi da datasheet, confronto nodi completi
- 5.2 Stime di autonomia e architettura ibrida PIR+mmWave per DIPME
- **Materiale già pronto**: analisi/ANALISI_CONSUMI.md (≈ capitolo già scritto;
  manca solo il modello PIR reale)

## Cap. 6 — Web UI: visualizzazione e raccolta dati *(obiettivo 5)*
- 6.1 Requisiti e scelta architetturale (self-hosted, offline, dimensionamento)
- 6.2 Realizzazione: firmware, WebSocket, dashboard, export CSV (stesso formato
  della pipeline di test → un solo formato dati in tutta la tesi)
- 6.3 Verifica: CSV web ≡ CSV seriale (test di accettazione step 4)
- **Materiale già pronto**: analisi/ANALISI_WEB_UI.md + PROGETTO_SITO_DETTAGLIO.md
  (≈ §6.1-6.2 già scritti). **Da fare**: implementazione + screenshot

## Cap. 7 — L'indice di vitalità *(obiettivo 6)*
- 7.1 Motivazione: dal "c'è qualcuno" al "in che condizioni è" (triage)
- 7.2 Algoritmo: doppia EWMA, classificazione, razionale
- 7.3 Taratura sui dati e validazione su trial separati (matrice di confusione)
- 7.4 Limiti e non-scopi (non è diagnosi medica)
- **Materiale già pronto**: analisi/ANALISI_VITALITA.md (≈ capitolo già impostato).
  **Dati necessari**: Fase 6 dei test

## Cap. 8 — Conclusioni e sviluppi futuri
- 8.1 Risposta sintetica: il mmWave può sostituire/affiancare il PIR nel DIPME-DEVICE?
  (la raccomandazione ibrida, con i numeri dei cap. 4-5 a supporto)
- 8.2 Sviluppi: test in aula reale/dimostratore, integrazione DIPME, lamiera forata,
  multi-banco, FFT a bordo

---

## Mappa obiettivi → capitoli (controllo di copertura)

| Obiettivo | Capitolo | Stato materiale |
|---|---|---|
| 1. Studio sensori | 2 | ~80% (manca modello PIR) |
| 2. Analisi dati | 3 | ~60% (mancano tracce reali) |
| 3. Testing numerico | 4 | protocollo pronto, dati 0% |
| 4. Consumi | 5 | ~90% |
| 5. Web UI | 6 | progetto 100%, implementazione 0% |
| 6. Indice vitalità | 7 | specifica 100%, dati 0% |

## Ordine di scrittura consigliato (≠ ordine dei capitoli)

1. **Subito** (prima ancora dei test): cap. 5, poi cap. 2 — sono già quasi interi nei
   documenti di analisi, e scriverli consolida lo studio fatto
2. **Durante i test**: cap. 4 §4.1 (protocollo) e cap. 3 — si scrivono man mano che
   i dati arrivano
3. **Dopo i test**: cap. 4 risultati, cap. 7, cap. 6
4. **Ultimi**: cap. 1 e 8 (si scrivono bene solo quando si sa cosa c'è nel mezzo)
