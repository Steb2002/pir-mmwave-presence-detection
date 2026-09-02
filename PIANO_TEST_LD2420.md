# Piano di test del LD2420 — campagna parallela a quella del LD2410B

Documento gemello di [PIANO_TEST.md](PIANO_TEST.md), dedicato al secondo radar.
Stesse convenzioni: `data/<scenario>_T<numero>.csv`, 5 trial per scenario dove non
indicato diversamente, sessioni annotate in `HLK-LD2410x/data/REGISTRO_SESSIONI.md`.

Scritto il 26/08/2026 dopo la lettura della documentazione ufficiale
(`HLK-LD2420/Documentazione/`: manuale V1.2 + Protocol Document).

---

## 0. Cosa va rifatto e cosa no

L'impressione che "vada rifatto tutto" è comprensibile ma sbagliata. La campagna del
LD2410B ha prodotto tre categorie di risultati, e solo una dipende dal radar:

| categoria | esempi | va rifatta col LD2420? |
|---|---|---|
| **Proprietà del PIR** | jumper H/L, impulsi da 3,46 s, curva dose-risposta del PIR, cecità alla persona immobile | ❌ **No.** Il PIR non c'entra col radar. E nelle nuove sessioni viene registrato comunque, gratis |
| **Il risultato centrale della tesi** | PIR 98,5% di falsi negativi su persona immobile vs radar 0% | ❌ **No.** È già dimostrato. Il LD2420 semmai aggiunge un secondo punto di conferma |
| **Proprietà del radar** | distanza, latenze, selettività, due persone, falsi positivi | ✔ **Sì**, sono le uniche da ripetere |

Quindi: **10 test radar da rifare**, non 25. E costano meno della prima volta, perché
protocollo, script di acquisizione, script di analisi e convenzioni di scarto del
transitorio sono già scritti e validati — la prima campagna è servita anche a costruire
gli strumenti.

⚠️ **Tre test NON sono replicabili sul LD2420**, e il motivo è esso stesso un risultato
da mettere in tesi, non un buco:

1. **Distanza su bersaglio fermo** — il manuale §8 dice che il modulo *"does not support
   proximity ranging for stationary bodies"*. Tutto ciò che nel Test 1.3 e 1.4 riguarda
   `stationary_distance_cm` non ha equivalente
2. **Separazione moving/still** — il LD2420 ha **un solo canale**. Il Test 2.5, che sul
   LD2410B ha prodotto "un bersaglio per canale", qui misura una cosa diversa: quanto si
   perde avendone uno solo
3. **Respiro e indice di vitalità** — richiedono la serie temporale dell'energia per-gate,
   che l'interfaccia documentata non trasmette (Fase 4-2420, opzionale e non ufficiale)

---

## 1. Decisioni di metodo, da prendere prima di acquisire

### 1.1 🔴 Mai i due radar accesi insieme
Lavorano entrambi a 24 GHz e si disturbano. **Un radar alla volta.** Il confronto si fa
ripetendo gli stessi scenari in sessioni separate, non in simultanea. Il PIR è passivo e
può restare collegato sempre.

### 1.2 🔑 Un solo schema CSV per tutta la tesi
Il logger del LD2420 deve emettere **le stesse 9 colonne** del logger del LD2410B, così
`acquire.py`, `serie.py` e `analizza_test.py` funzionano senza modifiche. Mappatura:

| colonna | LD2410B | LD2420 |
|---|---|---|
| `radar_presence` | presenza | presenza (`ON`/`OFF`) |
| `moving_target` | bersaglio in movimento | **= presenza** (canale unico) |
| `stationary_target` | bersaglio fermo | **0 fisso** |
| `moving_distance_cm` | distanza movimento | `Range` convertito (vedi Test 0.5-bis) |
| `stationary_distance_cm` | distanza fermo | **0 fisso** (non esiste) |
| `moving_energy` | energia movimento | **0** in ASCII |
| `stationary_energy` | energia fermo | **0** in ASCII |
| `pir_presence` | PIR | PIR |

⚠️ Le colonne a 0 fisso **non sono dati mancanti per sbaglio**: sono l'assenza documentata
di quella grandezza. Vanno dichiarate come tali in tesi, non presentate come zeri.

### 1.3 ⚖️ Parità di configurazione
Il LD2410B è stato caratterizzato **a soglie di fabbrica**, senza mai ricalibrare. Stessa
regola qui: si acquisisce con la configurazione di fabbrica del nostro esemplare
(`GateMax=12`, `ObjectDisappearDelayTime=30`, soglie del backup XML), che coincide con i
valori d'esempio del Protocol Document.

**Unica eccezione, e va dichiarata**: il ritardo di scomparsa. Il LD2410B ha timeout 5 s,
il LD2420 ne ha 30 di fabbrica. Confrontare le latenze di rilascio così sarebbe scorretto.
Il Test 2.2-2420 si esegue quindi **due volte**: a 5 (appaiato al LD2410B) e a 30
(comportamento fuori scatola).

### 1.4 Portata e geometria
Il LD2420 dichiara 8 m contro i ~6 m del LD2410B, ma la **stanza resta quella**: i test di
distanza arrivano a 5 m come prima. Il limite è logistico, già dichiarato come perimetro
sperimentale nel cap. 4 — non va riaperto qui.

---

## FASE 0-2420 — Preparazione

### Test 0.5 — Lettura di firmware e parametri (già in PIANO_TEST.md, ora eseguibile)
- **Serve per**: sapere cosa stiamo caratterizzando; la versione va in tesi
- Due strade, fare **entrambe** e confrontare (sul LD2410B il tool PC diede valori
  sbagliati e la verità venne dall'UART — vedi CLAUDE.md):
  - **tool PC**: LD2420 → CH340E → PC, `HLK-LD2420_TOOL - English`, baud 115200
  - **via UART**, sketch nuovo `firmware/test05_ld2420_info/`: comando `0x00` per la
    versione, poi `0x08` per rileggere `GateMax` (0x01), ritardo (0x04) e le 32 soglie
    (0x10-0x1F trigger, 0x20-0x2F maintain), come da Protocol Document
- **Esito atteso**: versione ≥ 1.5.3 (dedotta dal baud 115200 già osservato); soglie
  coincidenti col backup XML, cioè con l'esempio ufficiale
- 🔑 **Verifica utile**: il tool mostra le soglie in **dB = 10·log₁₀(grezzo)**. Se via UART
  leggi 60000 e il tool mostra 47,78, la corrispondenza è confermata sull'esemplare
- ✔ **Annotato (02/09/2026)**: firmware = **v1.6.1**, GateMax = **12**, ritardo = **30 s**,
  32 soglie lette via UART e coincidenti con l'XML di fabbrica (conversione dB→grezzo
  validata su tutti i parametri)

### Test 0.5-bis — 🔴 Taratura dell'unità del campo `Range` (BLOCCANTE)
- **Serve per**: qualunque test di distanza. Senza questo il Test 1.2-2420 non è
  interpretabile
- **Il problema**: leggiamo valori 7-37 camminando per la stanza. ESPHome dichiara
  centimetri (incompatibile: sarebbero 7-37 cm), i decimetri tornerebbero (0,7-3,7 m), ma
  **nessuno dei due documenti ufficiali definisce l'unità**
- **Procedura**: nastro a 1, 2, 3, 4, 5 m. Per ogni segno, stare in piedi e camminare sul
  posto 60 s, registrando il `Range` grezzo. Cinque punti bastano
- **Analisi**: regressione `Range_grezzo` vs distanza reale. Il coefficiente angolare dice
  l'unità: ~10 per metro = decimetri, ~100 = centimetri, ~1,43 = gate da 70 cm
- ⚠️ Se la relazione **non è lineare**, il campo non è una distanza e va trattato come
  indicatore ordinale. Sarebbe un risultato negativo pubblicabile, non un fallimento
- **Esito**: fattore di conversione = ______ → da cablare nel logger

### Test 0.6-2420 — Logger CSV
- Scrivere `firmware/ld2420_logger/ld2420_logger.ino`: Serial2 a 115200 su GPIO16/17,
  parsing delle righe ASCII, PIR su GPIO34, emissione CSV a **5 Hz** con le 9 colonne di §1.2
- ⚠️ **Perché 5 Hz e non 10**: il modulo aggiorna a 10 Hz, ma l'ASCII è asincrono (non
  emette una riga per campione). Campionare a 5 Hz lo stato corrente mantiene la cadenza
  identica al LD2410B, che è ciò che rende i due dataset confrontabili. I 10 Hz nativi
  servirebbero solo alla FFT del respiro, che qui non è in gioco
- **Verifica**: `python analisi/verifica_engineering.py` su un CSV di prova → cadenza
  5,00 Hz, jitter ~0, nessuna colonna mancante
- **Esito atteso**: `radar_presence` a 1 quando ti muovi davanti al sensore

### Test 0.7-2420 — Il pin OT2 serve davvero?
- **Serve per**: obiettivo 4 e architettura UPRISE. Sul LD2410B abbiamo dimostrato che il
  pin OUT coincide con la presenza in 1699/1699 campioni, cioè un nodo a basso consumo può
  fare a meno dell'UART
- Collegare OT2 a un GPIO libero, loggarlo come colonna extra per una sessione di 10 min
- **Esito atteso**: OT2 == `radar_presence`. Se coincide, stessa conclusione del LD2410B

**Costo Fase 0**: ~2,5 h, di cui buona parte è scrittura di firmware.

---

## FASE 1-2420 — Caratterizzazione

### Test 1.1-2420 — Stanza vuota (falsi positivi)
- **Metrica**: eventi/h di falso positivo, con limite superiore alla regola del tre (3/T)
- Una sessione **notturna** (stanza vuota, porta chiusa, ~7 h) + 30 min diurni
- ⚠️ Sospendere gli aggiornamenti di Windows (il 20/08/2026 un riavvio troncò una notturna)
- **Confronto atteso**: il LD2410B ha dato **0 eventi, limite 95% ≤ 0,43 eventi/h**. Per
  ottenere un limite confrontabile serve un tempo di osservazione simile: una notte
- **Analisi**: `analizza_test.py data\stanza_vuota_2420_*.csv`

### Test 1.2-2420 — Distanze note 1-5 m — 🎯 il test più importante della campagna
- **Metrica**: accuratezza della distanza, tasso di rilevamento
- **Perché conta**: il manuale dichiara **±0,35 m**; sul LD2410B abbiamo misurato una retta
  con R² = 0,99965 e residui ≤ 4,9 cm. È un ordine di grandezza di differenza, ed è **la
  ragione principale per cui il progetto sceglie un modulo invece dell'altro**
- Procedura identica al Test 1.2 originale: 5 distanze × 5 trial, 80 s per trial
  (20 di transitorio + 60 utili), camminata sul posto, soggetto in piedi
- Comando:
  ```powershell
  .venv\Scripts\python.exe serie.py --scenario mov2420_2m --gt-state moving
  ```
- **Analisi**: `python ..\analisi\analizza_test.py data\mov2420_*.csv --salta-inizio 20`
- **Da produrre**: la stessa regressione del LD2410B, sovrapposta nello stesso grafico.
  Due rette sullo stesso piano valgono più di due tabelle

### Test 1.3-2420 — Persona seduta immobile a 2,3 m — 🎯 il test che decide tutto
- **Metrica**: tasso di rilevamento su soggetto **immobile** (non la distanza: non esiste)
- **La domanda**: il LD2420 vede la persona ferma? La soglia *maintain* è definita dal
  manuale come "sensitivity for detecting human micro-movements and maintaining the
  presence of a person", quindi **dovrebbe**. Ma è una lettura del manuale, non una misura
- 5 trial × 302 s, stessa postura e stessa distanza del Test 1.3 originale
- **Confronto atteso**: LD2410B `fn_radar = 0,00 ± 0,00 %`
- ⚠️ **Se il LD2420 fallisce qui, la campagna può fermarsi**: un sensore che non vede la
  persona immobile è inutile per UPRISE, e i test successivi diventano accademici. È il
  punto di decisione naturale del piano
- 📌 Attenzione a **non** riportare `stationary_distance_cm`: sarà 0 per costruzione

### Test 1.4-2420 — Persona sotto il banco (~60 cm)
- **Metrica**: tasso di rilevamento nello scenario reale del progetto
- 5 trial × 302 s, sensore fissato sotto il piano, soggetto rannicchiato
- ⚠️ **Scartare 40 s di transitorio**, non 20: il soggetto deve anche posizionarsi
  (convenzione già fissata nella prima campagna)
- **Confronto atteso**: LD2410B `fn_radar = 0,00 %`, distanza 62,7 ± 4,2 cm
- 🔎 **Domanda specifica del LD2420**: il manuale dichiara rilevamento da **0,2 m** senza
  zona cieca. A 60 cm siamo nel primo gate (0-70 cm). Il gate 0 del LD2410B, forzato, si
  era rotto — qui il gate 0 è di serie e va provato

**Costo Fase 1**: ~3 h presidiate + 1 notturna non presidiata.

---

## FASE 2-2420 — Confronto dinamico

### Test 2.1-2420 — Latenza di rilevamento all'ingresso
- 10 trial, evento a 30 s annunciato da `serie.py --beep-at 30 --evento entra`
- **Grandezza pulita**: la differenza appaiata radar−PIR (tragitto e reazione si cancellano)
- **Confronto atteso**: LD2410B 5,36 ± 0,30 s, PIR 5,96 ± 0,31 s, differenza −0,60 ± 0,35 s
- ⚠️ Validare ogni trial con `pre_radar_%` = `pre_pir_%` = 0: se un sensore era già attivo
  prima dell'evento il trial va scartato

### Test 2.2-2420 — Latenza di rilascio — 🔑 doppia esecuzione
- 5 trial con ritardo impostato a **5** (appaiato al LD2410B) + 5 trial a **30** (fabbrica)
- Comando: `serie.py --scenario rilascio2420_d5 --beep-at 30 --evento esci`
- **Confronto atteso**: LD2410B 18,36 ± 0,54 s con timeout dichiarato di 5 s — cioè il
  parametro dichiarato **non descriveva** il comportamento, con una coda propria stimata
  in ~8,9 s
- 🔑 **Questo test determina anche l'unità del parametro di ritardo**, che nessuno dei due
  documenti ufficiali dichiara: se passando da 5 a 30 il rilascio si allunga di ~25 s,
  l'unità è il secondo. Due misure che chiudono una domanda aperta di documentazione
- Riportare anche le **riaccensioni** nella coda (sul LD2410B: zero)

### Test 2.3-2420 — Curva dose-risposta
- 3 condizioni × 5 trial a 1 m, in piedi: **immobile / micro-movimenti / cammino sul posto**
- **Confronto atteso** (LD2410B sempre 100% in tutte e tre; PIR 1,52% → 51,60% → 85,20%):
  la domanda è se il LD2420 resta piatto al 100% come il LD2410B o se degrada verso il basso
- 📌 Se degrada, si colloca **fra** PIR e LD2410B: sarebbe il grafico più efficace di tutta
  la tesi, tre sensori sulla stessa scala di movimento

### Test 2.4-2420 — Selettività spaziale (banchi adiacenti)
- Gate massimo ridotto a **2** → portata 140 cm (70 cm/gate, contro i 150 cm del LD2410B:
  non identici, va dichiarato)
- 4 scenari × 3 trial: occupante a 1 m sull'asse / persona a 3 m sull'asse / persona a 1 m
  a 90° / occupante + vicino a 90°
- ⚠️ 🔴 **Scartare 120 s di transitorio**, non 20. Negli scenari di selettività la coda del
  radar dopo il posizionamento è durata 29, 66 e 101 s: con `--salta-inizio 20` si misura
  il transitorio e lo si scambia per rilevamento. È l'errore che nella prima campagna ha
  prodotto un falso "24,83 ± 19,55 %"
- **Confronto atteso**: LD2410B a regime → 100% / 0% / 0% / 100%

### Test 2.5-2420 — Due persone
- 3 scenari × 3 trial: A ferma a 2 m + B che cammina a 4 m **sfalsate di 50 cm**; entrambe
  ferme sfalsate; B **in fila** dietro A
- ⚠️ Sfalsare lateralmente è obbligatorio nei primi due: in fila il corpo davanti fa da
  schermo e non si distingue "non separa" da "era in ombra"
- **Previsione, da verificare**: avendo un canale solo, il LD2420 non dovrebbe riprodurre
  il risultato del LD2410B (79,2% di campioni con due bersagli riportati insieme). Ma
  `radar_presence` dovrebbe restare al 100% in tutti gli scenari, come lì
- 📌 Serve una **seconda persona**: da programmare quando è disponibile, non all'ultimo

### Test 2.6-2420 — 🆕 Gate MINIMO: una funzione che il LD2410B non ha
- **Non è una replica**: è un test nuovo, possibile solo su questo modulo
- Il LD2420 permette di impostare un gate **minimo** (comando `0x00`), cioè di **escludere
  il campo vicino**. Il LD2410B non lo prevede
- Impostare gate minimo 2 e verificare che una persona a 1 m **non** venga rilevata mentre
  una a 3 m sì
- 📌 **Perché è rilevante per UPRISE**: un sensore sotto un banco potrebbe ignorare la
  gamba del proprio occupante e sorvegliare una fascia più lontana. È un argomento
  architetturale a favore del LD2420 che vale la pena avere in tesi accanto ai suoi limiti
- 2 scenari × 3 trial

**Costo Fase 2**: ~4 h, di cui ~45 min richiedono una seconda persona.

---

## FASE 3-2420 — Penetrazione ostacoli (da fare in coppia col LD2410B)

Non ancora svolta per **nessuno** dei due moduli. Conviene farla nella stessa giornata,
alternando i radar sullo stesso allestimento: cartongesso, legno, vetro, plastica.

- Baseline senza ostacolo + un blocco per materiale, 3 trial ciascuno, soggetto immobile
  a distanza fissa
- **Metrica**: tasso di rilevamento e (solo LD2410B) attenuazione dell'energia
- ⚠️ Un radar alla volta (§1.1). Segnare a terra le posizioni e **non spostare nulla** fra
  i due giri, altrimenti il confronto salta
- 📌 È l'unico punto in cui il LD2420 può risultare **superiore** in modo netto: più
  potenza utile e portata maggiore significano più margine attraverso un ostacolo

**Costo**: ~3 h per entrambi i moduli.

---

## FASE 4-2420 — Modalità binaria non ufficiale (OPZIONALE)

⚠️ Fonte di comunità (ESPHome), **non** Hi-Link. Da trattare come esperimento dichiarato,
mai come specifica citabile.

- Comando `0x0012` con valore `0x0004` (energy) / `0x0064` (simple). Frame da 45 byte,
  header `F4 F3 F2 F1`, footer `F8 F7 F6 F5`; presenza a offset 6, distanza a offset 7,
  **16 energie per-gate a 16 bit** da offset 9
- 🔑 **Perché tentarlo**: le energie sono `uint16`, non `uint8` 0-100. Il limite più serio
  del LD2410B è la **saturazione a 100** (92% dei campioni stazionari clippati), che
  nessuna soglia risolve. Un canale a 16 bit non satura, e la cadenza nativa è 10 Hz
  contro i nostri 5. Per la FFT del respiro sarebbe **migliore**, non peggiore
- **Criterio di abbandono, da fissare prima di iniziare**: se dopo **una sessione da 3 h**
  non si ricevono frame validi, si chiude. Il reverse engineering è un pozzo senza fondo e
  non è l'oggetto della tesi
- Se funziona: ripetere il pilota respiro (soggetto fermo, ≥1,5 m, **respiro a metronomo a
  ritmo noto**) e confrontare la stima con quella del LD2410B. Il confronto
  saturato-vs-non-saturato sarebbe un ottimo paragrafo

**Costo**: 3 h a tetto fisso, o zero se si decide di lasciarlo fuori.

---

## 5. Ordine di esecuzione e stima complessiva

| # | blocco | ore | note |
|---|---|---|---|
| 1 | Fase 0 (0.5, 0.5-bis, 0.6, 0.7) | 2,5 | 0.5-bis è **bloccante** |
| 2 | Test 1.3-2420 | 0,75 | 🔴 **anticipato**: è il punto di decisione |
| 3 | Test 1.2-2420 | 1,5 | il confronto ±0,35 m vs cm |
| 4 | Test 1.4-2420 | 0,75 | scenario UPRISE |
| 5 | Test 1.1-2420 | notturna | non presidiata |
| 6 | Fase 2 (2.1-2.4, 2.6) | 3,25 | |
| 7 | Test 2.5-2420 | 0,75 | serve 2ª persona |
| 8 | Fase 3 (entrambi i moduli) | 3 | |
| 9 | Fase 4 (opzionale) | 0-3 | tetto fisso |
| | **totale essenziale (1-7)** | **~9,5 h** | + 1 notturna |
| | **con ostacoli e binario** | ~15,5 h | |

⚠️ **Il Test 1.3-2420 va spostato in testa**, prima di 1.2 e 1.4. È l'unico che può
rendere inutile il resto: se il modulo non vede la persona immobile, spendere 8 h a
caratterizzarne la distanza è tempo buttato. Nella prima campagna l'ordine numerico
andava bene perché il LD2410B era già stato validato dal pilota.

---

## 6. La tabella che deve uscire da questa campagna

È l'obiettivo finale: una riga per grandezza, tre colonne di sensori. Materiale diretto
per il cap. 4 e per le conclusioni.

| grandezza | PIR HC-SR501 | LD2410B | LD2420 |
|---|---|---|---|
| persona immobile, 2,3 m | 1,52 % | 100 % | da misurare (1.3) |
| persona immobile, sotto banco | 1,32 % | 100 % | da misurare (1.4) |
| errore di distanza | — | ≤ 4,9 cm dalla retta | da misurare (1.2) |
| latenza ingresso vs PIR | rif. | −0,60 s | da misurare (2.1) |
| coda di rilascio | 3,46 s fissi | ~18,4 s | da misurare (2.2) |
| falsi positivi | ≤ 0,43 ev/h | ≤ 0,43 ev/h | da misurare (1.1) |
| due persone separate | ✗ | parziale, per canale | da misurare (2.5) |
| esclusione campo vicino | ✗ | ✗ | ✔ da misurare (2.6) |
| ostacoli | — | da misurare | da misurare |

---

## 7. Fonti

- `HLK-LD2420/Documentazione/HLK-LD2420-Product-Manual V1.2.pdf` — Tab. 2-1 (specifiche),
  Tab. 3-2 (piedinatura J2), §4.2.1 (parametri), §5 (portate), §8 (*Cautions*: assenza di
  telemetria sui bersagli fermi)
- `HLK-LD2420/Documentazione/HLK-LD2420 Protocol Document.pdf` — Tab. 1 (comandi),
  Tab. 2 (parametri), esempi pagg. 3-5
- `HLK-LD2420/Backup config/ld2420_config_fabbrica.xml` — configurazione dell'esemplare
- ESPHome, componente `ld2420` (fonte di comunità, non ufficiale) —
  https://github.com/esphome/esphome/tree/dev/esphome/components/ld2420
