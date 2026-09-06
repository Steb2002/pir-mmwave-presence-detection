# Tesi Triennale — mmWave Presence Sensing con ESP32

## Contesto — Progetto UPRISE

La tesi si inserisce nel **progetto europeo UPRISE**, nato dopo il terremoto del 2016 nella zona di Camerino, con l'obiettivo di mitigare il rischio sismico. L'idea generale del progetto:

- Sensori IoT integrati negli **arredi** (es. banchi scolastici), che si attivano solo in "modalità terremoto" (trigger: accelerometro sul gateway, blackout, ecc.)
- Durante l'emergenza il sensore rileva se **c'è qualcuno rifugiato sotto l'arredo** e lo comunica all'esterno
- Comunicazione via **protocollo LoRa** (lunga portata); **droni** raccolgono i messaggi e costruiscono una **mappa di calore geolocalizzata offline** consultabile dal tablet dei soccorritori

**La tesi copre solo la parte di sensing**: caratterizzazione e confronto dei sensori di presenza (PIR vs mmWave). Slide del progetto generale: https://docs.google.com/presentation/d/11Q_Zet3aEtPZo2vcoM7_cvcTCbvLY-FBznCqPK37k3E/edit?usp=sharing

### Dettagli dell'ecosistema progetto (dalle slide "Sharper" del professore, 26/09/2025)

- **Professore**: Massimo Callisto — ricercatore RTD-A in Computer Science a UNICAM, membro del PROcess and Service lab e del progetto di ricerca VITALITY. Nel paper di riferimento il progetto è chiamato **SAFE**
- **Arredi salva-vita** (progettati dalla Scuola di Architettura e Design UNICAM — Gioiella, Galloppo, Micozzi):
  - Banco: telaio doppio spaziale, piano rinforzato con lamiera forata antisfondamento, elemento di base dissipativo, connessione strutturale tra banchi
  - Parete attrezzata autoportante anti-ribaltamento; pareti divisorie alluminio-vetro con dissipazione/isolamento sismico
- **Elettronica esistente** (partner: AM Microsystems, Piediripa MC):
  - **DIPME-COORDINATOR**: modulo LoRa
  - **DIPME-DEVICE**: modulo LoRa + **sensore PIR** + CO2, temperatura, umidità, pressione, accelerometro, Bluetooth, **sensore UWB**
  - ⚠️ Rilevante per la tesi: il DIPME-DEVICE attuale usa **PIR + UWB** per la presenza → la tesi valuta il mmWave come alternativa/complemento del PIR in questo dispositivo
- **Rete LoRa**: bande sub-GHz libere (433/868 MHz in Europa), portata 10-15 km rurale / 3-5 km urbano; architettura: DIPME DEVICE → DIPME COORDINATOR → gateway IoT Linux/Raspberry (DIPME DRIVER)
- **Dimostratori reali**: Polo Lodovici di Informatica (Ascoli Piceno) e IIS Fermi Sacconi Ceci (Ascoli Piceno, 2 aule + sala professori)
- **Digital Twin**: piattaforma https://pros.unicam.it/dtplatform/ per modellare, simulare e validare il sistema IoT prima dell'installazione (anche con VR) — Callisto et al., *"Design and Development of a Digital Twin Prototype for the SAFE Project"*, EDOC 2023
- **Piattaforma di monitoraggio** con due modalità: "tempo di pace" (monitoraggio ordinario) e "tempo di guerra" (emergenza sismica)

---

## Obiettivi della tesi (6 punti, definiti con il professore — call del 06/07/2026)

1. **Studio dei sensori** — chi li usa, come vengono usati, che dati producono (PIR e mmWave)
2. **Analisi dei dati forniti** — capire nel dettaglio che dati forniscono i sensori (PIR: solo movimento sì/no; mmWave: micromovimenti, distanza, potenzialmente battito/respiro)
3. **Comparazione con testing numerico** — confronto sperimentale PIR vs mmWave con misure quantitative
4. **Consumo energetico** — a titolo informativo (da datasheet, non si dispone di strumentazione di misura)
5. **User interface web** — l'ESP32 pubblica i dati → sito web per visualizzazione **in tempo reale** → la stessa app salva i dati con statistiche → **export CSV** → analisi numerica in Excel
6. **Indice di vitalità** (obiettivo avanzato / "ciliegina") — oltre a presenza sì/no, un algoritmo che quantifica quanto una persona si muove (es. 50/100) → classificazione tipo "vivo / moderatamente vivo"

Obiettivo di contorno: valutare anche altri tipi di sensori.

### Test sperimentali previsti (a supporto dei punti 2-3)
- Accuratezza, latenza, falsi positivi/negativi nel rilevamento presenza (una o più persone)
- Rilevamento del respiro tramite analisi dei micro-movimenti (engineering mode LD2410B + FFT)
- Superamento degli ostacoli — materiali comuni: cartongesso, legno, vetro, plastica

---

## Kit hardware disponibile

| Componente | Quantità | Note |
|---|---|---|
| ESP32 (scheda nera 30-pin) | 1 | Chip Espressif ESP32-WROOM-32, USB-C |
| HLK-LD2410B | 1 | ✅ **FUNZIONANTE (09/08/2026)**. Il "guasto" del 19/07/2026 era un errore di cablaggio: i colori dei cavi erano mappati al contrario. Mappatura corretta (datasheet Tabella 1): rosso=VCC, nero=GND, giallo=UART_Rx, verde=UART_Tx, blu=OUT |
| HLK-LD2420 | 1 | Scheda arancione/verde, portata 8 m dichiarata (manuale V1.2) |
| HLK-CH340E-V1.0 | 1 | Adattatore USB→Seriale, utile per connettere LD2420 direttamente al PC |
| PIR **HC-SR501** | 1 | Identificato dalle foto (`PIR HC-SR501/`): BISS0001 + regolatore HT7133, uscita 3.3V ok per ESP32, 2 trimmer + jumper H/L — dettagli in `analisi/ANALISI_PIR.md` §6 |
| Breadboard grande | 1 | |
| Cavo USB A-C | 1 | Per programmazione ESP32 |
| Cavi jumper M-F | vari | |
| Cavi jumper M-M | vari | |
| Cavi con clip a coccodrillo | vari | |
| Materiali per test ostacoli | vari | Cartongesso, legno, vetro, plastica |

**Non disponibili**: multimetro, resistenze shunt — il consumo energetico sarà trattato con dati da datasheet (coerente con l'obiettivo 4: "a titolo informativo").

---

## HLK-LD2410B — Specifiche tecniche

### Caratteristiche principali
- Frequenza: **24 GHz FMCW**
- Range: fino a **5-6 m**
- Campo visivo: **±60°**
- Alimentazione: **5V**, corrente media **80 mA** (alimentatore >200 mA richiesto — manuale Hi-Link V1.03)
- Interfaccia: **UART 256000 baud**, 8N1
- Bluetooth integrato (variante B) — password default: `HiLink`
- Dimensioni: ~35mm × 7mm

### Pinout (5 pin) — datasheet ufficiale, Tabella 1
Fonte: https://assets.super.so/79c0d2a8-d37a-438f-8fbe-c44778f3b0dd/files/7c3607bd-f703-43f5-9f22-f369f00c37bd.pdf (Figura 1 + Tabella 1)
```
Pin 1: OUT      → presenza digitale (HIGH = persona, LOW = nessuno)
Pin 2: UART_Tx  → GPIO25 (RX2) ESP32   [il radar parla]
Pin 3: UART_Rx  ← GPIO26 (TX2) ESP32   [il radar ascolta]
Pin 4: GND      → GND ESP32
Pin 5: VCC      → 5V ESP32 (VIN)
```
Questa è **l'unica numerazione valida** (quella del datasheet). Nella figura del datasheet,
guardando il modulo con il connettore a destra, l'ordine dall'alto verso il basso è
**VCC, GND, UART_Rx, UART_Tx, OUT**.

### Colori cavi del connettore JST — ✅ CORRETTO (verificato 09/08/2026)
⚠️ Una mappatura sbagliata dei colori è stata la causa del presunto "guasto" del
19/07/2026: il modulo **funziona**, era cablato male. Mappatura corretta:
```
Rosso  = Pin 5 → VCC     → VIN ESP32 (5V)
Nero   = Pin 4 → GND     → GND ESP32
Giallo = Pin 3 → UART_Rx ← D26 ESP32 (TX2: l'ESP32 parla)
Verde  = Pin 2 → UART_Tx → D25 ESP32 (RX2: l'ESP32 ascolta)
Blu    = Pin 1 → OUT     (presenza digitale; non collegare per ora)
```
Regola mnemonica: rosso = corrente, nero = massa (convenzione standard), blu = OUT;
i due in mezzo sono la seriale, sempre **incrociata** (Tx radar → Rx ESP32).

### Dati in uscita
- Stato presenza: moving / still / none
- Distanza target in cm (moving e still separati)
- Energia per-gate 0-8 (valori 0-100) — sia per movimento che stazionario
- Lettura sensore luce (solo engineering mode)
- Versione firmware + MAC Bluetooth

### Parametri configurabili
| Parametro | Range | Default |
|---|---|---|
| Gate massimo (movimento) | 2-8 | 8 |
| Gate massimo (stazionario) | 2-8 | 8 |
| Risoluzione gate | 0.75m o 0.2m | 0.75m |
| Soglia movimento per gate | 0-100 | varia per gate |
| Soglia stazionario per gate | 0-100 | varia per gate |
| Timeout presenza | secondi | 5s |
| Soglia luce | 0-255 | 128 |

### Protocollo UART (frame struttura)
- **Comandi** — header: `{0xFD, 0xFC, 0xFB, 0xFA}`, footer: `{0x04, 0x03, 0x02, 0x01}`
- **Dati** — header: `{0xF4, 0xF3, 0xF2, 0xF1}`, footer: `{0xF8, 0xF7, 0xF6, 0xF5}`
- Byte 8: stato target (bitmask: 0x01=moving, 0x02=still)
- Engineering mode (byte 6 = 0x01): sblocca dati per-gate ai byte 19-37

### Comandi chiave
| Byte | Funzione |
|---|---|
| `0xFF` | Entra in modalità configurazione |
| `0xFE` | Esci da modalità configurazione |
| `0x62` | Attiva engineering mode |
| `0x63` | Disattiva engineering mode |
| `0xA0` | Leggi versione firmware |
| `0xAA` | Imposta risoluzione distanza |
| `0xA1` | Imposta baud rate |

---

## HLK-LD2420 — Specifiche tecniche

📄 **Documentazione ufficiale scaricata il 26/08/2026** in `HLK-LD2420/Documentazione/`:
`HLK-LD2420-Product-Manual V1.2.pdf` (16 pagine) e `HLK-LD2420 Protocol Document.pdf`
(5 pagine). Fino a quella data le specifiche qui sotto venivano da fonti secondarie e
**diverse erano sbagliate** (portata, numero di gate, soglie): i valori attuali sono
quelli del manuale.

### Caratteristiche principali (manuale V1.2, Tabella 2-1)
- Frequenza: **24-24.25 GHz** FMCW, banda di sweep 0.25 GHz, EIRP 11 dBm
- Portata: **8 m** a parete su bersaglio in movimento, **6 m** su micro-movimento;
  a soffitto **5 m** / **4 m**. ⚠️ Il valore "~12 m" scritto qui in precedenza era
  errato: nasceva dal conto 15 gate × 70 cm, che è il campo *indirizzabile*, non la
  portata dichiarata
- **Accuratezza di distanza: ±0.35 m** (§8 *Cautions*: valore teorico, fluttua con
  corporatura e RCS del bersaglio). Da confrontare con la dispersione di **1.5 cm**
  misurata sul LD2410B da fermo a 2.3 m: è la differenza più pesante fra i due moduli
- **Cadenza dati: 10 Hz** (il nostro logger LD2410B gira a 5 Hz)
- Zona morta: nessuna, rilevamento dichiarato da **0.2 m**
- Alimentazione: **3.0-3.6 V**, tipica **3.3V** (diverso dal LD2410B che vuole 5V!)
- **Corrente media 50 mA** (LD2410B: 80 mA) — rilevante per l'obiettivo 4
- Dimensioni 20 × 20 mm, temperatura -40/+85 °C
- Bluetooth: **assente**
- ⚠️ **Contraddizione interna al manuale sull'angolo**: §1.1 dichiara "±60°",
  §5.2 dichiara "±45° in orizzontale e in elevazione" per il montaggio a parete.
  In tesi vanno citate entrambe, non una sola
- ⚠️ "Calibrazione automatica da firmware ≥ 1.5.4" è informazione **ESPHome**, non
  compare nella documentazione ufficiale. Il manuale descrive solo la procedura
  manuale di *bottom noise scan* dal tool PC (§4.2.2-4.2.3)

### ✅ VERIFICATO SU HARDWARE (17/07/2026) — il nostro esemplare

Testato collegando il LD2420 ai pin **GPIO16/17 dell'ESP32** (sketch
`firmware/ld2420_monitor/`, ESP32 su COM3):
- **Firmware ≥ 1.5.3** (dedotto dal baud): TX seriale su **Pin 3 (OT1) → GPIO16**
- **Baud: 115200** (confermato: a 256000 si legge solo poltiglia, stesso alfabeto
  di byte del boot-log dell'ESP32 letto al baud sbagliato)
- **Modalità di fabbrica = ASCII "semplice"** (vedi sotto), NON il protocollo binario
- Alimentazione 3.3V OK, il sensore risponde ai movimenti
- ⚠️ Versione firmware ESATTA e unità del "Range" ancora da leggere col tool HiLink (Test 0.5)

### Pinout — connettore J2 (manuale V1.2, Tabella 3-2)

Il manuale ufficiale documenta **una sola** mappatura, che coincide con quella che
usiamo e con il comportamento osservato sul nostro esemplare:

```
J2 Pin 1: 3V3   alimentazione 3.0-3.6 V
J2 Pin 2: GND
J2 Pin 3: OT1   UART_TX (0-3.3 V)  → GPIO16 ESP32
J2 Pin 4: RX    UART_RX (0-3.3 V)  ← GPIO17 ESP32
J2 Pin 5: OT2   uscita di presenza: alto = occupato, basso = libero
```

C'è anche un connettore **J1** (GND, DIO, CLK, 3V3): è l'interfaccia **SWD** per la
programmazione dell'MCU — non va toccata.

⚠️ La variante "firmware ≤ 1.5.2 con OT1 e OT2 invertiti" (baud 256000) è
informazione di **comunità (ESPHome)**, non compare nel manuale V1.2. Resta utile
saperlo per moduli più vecchi, ma non è citabile come dato ufficiale.
Tool ufficiale: Google Drive HiLink → cartella `HLK-LD2420_TOOL - English`

### Formato dati in modalità di fabbrica (ASCII, verificato)
Di default il nostro LD2420 trasmette testo a righe (terminate `\r\n`) a 115200 baud:
```
ON            → presenza rilevata
OFF           → nessuna presenza
Range NN      → distanza del target (valore GREZZO, unità non documentata)
```
- 🔑 **Questa È la modalità documentata, non un ripiego (verificato 26/08/2026).**
  Il `Protocol Document` ufficiale descrive **solo i comandi di configurazione**
  (0xFF/0xFE apri-chiudi modalità comandi, 0x00 versione, 0x68 riavvio, 0x07/0x08
  scrivi/leggi parametri): **non documenta alcun frame di uscita dei dati**. Il
  manuale §4.1 passo 3 dice di aprire un terminale a 115200 e "view the current radar
  detection results", cioè proprio queste righe ASCII. Quindi, ufficialmente, il
  LD2420 riporta **presenza + una distanza, e nulla più**
- Limiti di questa modalità: solo presenza + un "range"; **niente energia per-gate,
  niente distinzione moving/still**
- ⚠️ **L'energia per-gate esiste, ma non è documentata da Hi-Link.** Nella
  documentazione ufficiale compare solo come valore *Peak* salvato su file dal *bottom
  noise scan* del tool PC (manuale §4.2.2-4.2.3). La modalità che la trasmette in
  continuo sulla seriale è **ricostruita dalla comunità** — vedi il blocco
  "Modalità binaria (energy)" qui sotto
- 📌 **Conseguenza per la tesi**: con l'interfaccia **documentata** il LD2420 non dà
  la serie temporale dell'energia, quindi respiro e indice di vitalità (obiettivi 2 e 6)
  restano sul LD2410B. Con la modalità binaria di comunità sarebbero tecnicamente
  possibili — e per certi versi *meglio* (vedi sotto) — ma il dato non sarebbe citabile
  come specifica ufficiale e andrebbe validato da noi
- ⚠️ L'unità del "Range" NON è documentata **in nessuno dei due documenti ufficiali**:
  i valori osservati (7–37 muovendosi in stanza) sono compatibili con decimetri
  (~0.7–3.7 m) ma va confermato prima di usarlo come distanza in metri (regola fonti).
- Collegamento diretto al PC via CH340E: script `HLK-LD2420/Test LD2420/ld2420_diag.py`
  (annusa-byte a 115200/256000). Lettura via ESP32: `firmware/ld2420_monitor/`.

### Modalità binaria "energy" — NON ufficiale, ma dà molti più dati
Ricostruita dal componente ESPHome `ld2420` (sorgenti `ld2420.h` / `ld2420.cpp`,
consultati il 26/08/2026). ⚠️ **Fonte di comunità, non Hi-Link**: utilizzabile come
scelta implementativa, **non** come dato tecnico citabile in tesi (regola fonti).

- Si commuta con il comando **0x0012** (`CMD_WRITE_SYS_PARAM`):
  valore **0x0004** = energy mode, **0x0064** = simple mode (l'ASCII di fabbrica)
- Frame dati da **45 byte**, con **le stesse intestazioni del LD2410B**:
  header `F4 F3 F2 F1`, footer `F8 F7 F6 F5`
- Contenuto: **presenza** (1 byte, offset 6) + **distanza** (uint16, offset 7) +
  **16 energie per-gate** (16 × uint16, offset 9)
- 🔑 **Le energie sono uint16 (0-65535), non uint8 0-100 come nel LD2410B.** È
  potenzialmente decisivo: il nostro problema più serio sul LD2410B è la
  **saturazione a 100** (92% dei campioni stazionari clippati), che nessuna soglia e
  nessuna auto-calibrazione risolvono. Un canale a 16 bit non satura. Sommato ai
  **10 Hz** contro i nostri 5 Hz, il LD2420 in questa modalità sarebbe **più adatto
  del LD2410B alla FFT del respiro**, non meno
- ⚠️ Restano però i limiti strutturali, questi sì ufficiali: **un solo canale**
  (niente separazione moving/still) e **nessuna distanza sul bersaglio fermo**
- ⚠️ ESPHome documenta la distanza in **centimetri**; i valori che leggiamo in ASCII
  sono 7-37 camminando per la stanza, incompatibili con i cm. O il formato ASCII è
  diverso dal campo binario, o il nostro parser sbaglia riga. **Da chiarire con una
  misura a distanza nota** (Test 0.5), non per deduzione

### Baud rate per versione firmware
- Firmware < 1.5.3: **256000 baud**
- Firmware ≥ 1.5.3: **115200 baud** ← il nostro esemplare (verificato 17/07/2026)

### Parametri configurabili (manuale §4.2.1 + Protocol Document Tabella 2)
| Parametro | Nome cmd | Range ufficiale | Nostro esemplare |
|---|---|---|---|
| Gate minimo | 0x00 | 0-15 (0x00-0x0F) | non nel backup |
| Gate massimo | 0x01 | 0-15, ≥ minimo | **12** |
| Ritardo di scomparsa | 0x04 | 0-65535 ⚠️ | **30** |
| Soglia **Trigger** per gate | 0x10-0x1F | 0-65535 | 16 valori |
| Soglia **Maintain** per gate | 0x20-0x2F | 0-65535 | 16 valori |

- **16 gate (0-15)**, risoluzione **70 cm** ciascuno. ⚠️ Il "15 gate (0-14)" scritto
  qui in precedenza era errato: il protocollo indirizza 0x10-0x1F, cioè 16 soglie
- ❓ **Portata di "gate max = N": N × 70 cm oppure (N+1) × 70 cm? NON documentato**
  (03/09/2026). Sul LD2410B la regola e' documentata e misurata: *"maximum of 8
  distance gates"*, range 1-8, gate 2 → 1,5 m, cioe' **portata = N × 0,75 m** e il gate 0
  del frame di engineering non conta. Il manuale LD2420 (Tab. 4-2) da' solo "0~15" per
  gate minimo e massimo, senza esempi. Indizi contrari: l'analogia col LD2410B e il
  valore di fabbrica 12 = 840 cm (~8 m dichiarati) dicono N × 70; il gate 0 selezionabile
  come minimo e "max = 0" ammesso dicono (N+1) × 70. **Da misurare** con persona ferma a
  4,5 m e gate max 6: vista → 490 cm, non vista → 420 cm. Fino ad allora **non scrivere
  in tesi la portata in metri del gate massimo del LD2420** senza questa riserva.
  Ricerca web del 03/09/2026 (solo fonti di comunita', nessuna primaria): ESPHome dice
  `min_gate_distance` 0..max-1 e `max_gate_distance` 1..15, "15 ≈ 12 m, 12 ≈ 9 m"
  (numeri arrotondati: 13 × 0,7 = 9,1 fa pensare a (N+1) × 70); esp32.co.uk mette il
  gate 1 a 0,7 m, quindi gate 0 = 0-70 cm. Nessuno dice esplicitamente se il gate
  massimo e' incluso. **Propende per 490 cm, ma resta da misurare**
- **Trigger** = soglia libero→occupato, consigliata > 5× il rumore di fondo;
  **Maintain** = soglia per rilevare i micro-movimenti e *mantenere* la presenza,
  consigliata 2-5× il rumore. **Non sono i canali moving/still del LD2410B**: sono
  un'isteresi su un unico bersaglio
- ⚠️ **Contraddizione fra i due documenti ufficiali sul ritardo**: il manuale §4.2.1
  dà 0-65535, la Tabella 2 del protocollo dà `0x00-0x0F` — ma gli esempi del
  protocollo stesso impostano 30 (0x1E) e 26 (0x1A), fuori da quel range. Il nostro
  backup ha 30. In tesi va citata la discrepanza

### 🔑 Le soglie del tool PC sono in dB: valore mostrato = 10·log₁₀(grezzo)
Scoperto il 26/08/2026 incrociando `HLK-LD2420/Backup config/ld2420_config_fabbrica.xml`
con gli esempi del Protocol Document (pagg. 4-5). I valori del **nostro** esemplare
coincidono esattamente con quelli d'esempio del documento ufficiale:

| gate | XML (dB) | grezzo | esempio ufficiale |
|---|---|---|---|
| 0 | 47.78 | 60000 | `60 EA 00 00` ✓ |
| 1 | 44.77 | 30000 | `30 75 00 00` ✓ |
| 2 | 34.77 | 3000 | `B8 0B 00 00` ✓ |
| 3 | 33.01 | 2000 | `D0 07 00 00` ✓ |

Coerente anche con `appConfig.xml` del tool, che ha `TriggerSensingScale="5.0"` e
`HoldSensingScale="3.5"`, cioè proprio i moltiplicatori del rumore consigliati dal
manuale. **Il nostro modulo ha le soglie di fabbrica documentate.**

⚠️ **Errore aritmetico nel Protocol Document (pag. 2)**: legge `40 9C 00 00` e scrive
"the value is 60000". È **40000** (0x9C40). Da non ricopiare.

### Dati in uscita — quello che il LD2420 dà davvero
Con l'interfaccia **documentata** (ASCII di fabbrica):
- Presenza binaria (`ON`/`OFF` su UART, più il pin OT2)
- **Distanza del solo bersaglio in MOVIMENTO**
- Versione firmware (comando 0x00)
- ❌ Niente energia per-gate, niente distinzione moving/still, niente sensore di luce

Con la modalità binaria **di comunità**: in più le **16 energie per-gate a 16 bit**
(vedi il blocco dedicato). Restano assenti la separazione moving/still, la distanza
sul bersaglio fermo e il sensore di luce — quelle sono limitazioni del modulo, non
dell'interfaccia.

🚨 **Limite decisivo per UPRISE** (manuale §8 *Cautions*, citazione): il radar riporta
la distanza dei corpi in movimento entro 8 m e *"does not support proximity ranging for
stationary bodies at this time"*. Cioè: **sulla persona ferma il LD2420 dice se c'è, ma
non dove**. È esattamente lo scenario del progetto (persona immobile sotto l'arredo),
dove invece il LD2410B riporta distanza ed energia stazionarie.

---

## Confronto LD2410B vs LD2420

Tabella allineata ai manuali ufficiali dei due moduli (26/08/2026).

| Caratteristica | LD2410B | LD2420 |
|---|---|---|
| Alimentazione | 5V | 3.0-3.6V (tip. 3.3V) |
| Corrente media | 80 mA | **50 mA** |
| Portata dichiarata | ~5-6 m | **8 m** movimento / 6 m micro-movimento (a parete) |
| Accuratezza distanza | ~1.5 cm misurati (fermo, 2.3 m) | **±0.35 m** dichiarati |
| Cadenza dati | 5 Hz (nostro logger) | **10 Hz** |
| Gate | 9 (0-8) | **16 (0-15)** |
| Risoluzione gate | 0.75m o 0.2m | 70 cm fisso |
| Canali bersaglio | **2** (moving + stationary, separati) | **1** |
| Distanza su bersaglio fermo | ✓ | ✗ (§8 del manuale) |
| Energia per-gate | ✓ 9+9, **uint8 0-100 (satura)** | 16 valori **uint16** solo in modalità non ufficiale |
| Sensore di luce | ✓ | ✗ |
| Baud rate | 256000 fisso | 115200 |
| Bluetooth | ✓ | ✗ |
| Soglie | 0-100 interi, movimento + stazionario | 0-65535, Trigger + Maintain (isteresi) |
| Uso consigliato | Respiro, dettaglio, **scenario UPRISE** | Portata lunga, copertura di ambienti |

---

## Confronto mmWave vs PIR vs UWB

| Parametro | PIR | mmWave 24GHz (LD2410B/2420) | UWB (3-10 GHz) |
|---|---|---|---|
| Rilevamento fermo | ✗ | ✓ (micromovimenti) | ✓ |
| Conteggio persone | ✗ | Limitato (no angolazione) | Limitato |
| Distanza | ✗ | ✓ | ✓ |
| Rilevamento respiro | ✗ | ✓ parziale | ✓ |
| Penetrazione ostacoli | ✗ | Parziale (no metallo/cemento) | Buona |
| Consumo | ~0.05 mA | ~50-80 mA (datasheet) | < 10 mW |
| Privacy (GDPR) | Assente | Alta (no immagini) | Alta |
| Costo | ~1-3€ | ~5-15€ | ~20-50€ |
| Alimentazione | Batteria ok | Fisso preferibile | Batteria ok |

### Prestazioni mmWave in condizioni ottimali
- Latenza rilevamento movimento: **< 500 ms**
- Conferma persona ferma: **2-5 secondi**
- Conferma stanza vuota: **20-60 secondi**
- Falsi positivi: **< 0.05 eventi/ora**
- Falsi negativi: **< 0.02 eventi/ora**

---

## Rilevamento del respiro — come funziona

Il respiro genera micro-movimenti a **0.1-0.5 Hz** rilevabili dal radar 24 GHz.

Con LD2410B il metodo pratico è:
1. Attivare **engineering mode** per ottenere l'energia per-gate nel tempo
2. Campionare l'energia del gate corrispondente alla distanza della persona
3. Applicare **FFT** sulla serie temporale per estrarre la frequenza respiratoria
4. Il picco nello spettro tra 0.1 e 0.5 Hz corrisponde al respiro (~6-30 atti/min)

**Aspettativa realistica per hardware consumer**: rilevare la *presenza* di respiro (persona ferma viva vs assente) è affidabile; misurare la frequenza esatta richiede post-processing e condizioni controllate.

---

## Stack di sviluppo

### Ambiente scelto — Arduino IDE 2.3.9
- Board: **ESP32 Dev Module** (esp32 by Espressif Systems)
- Porta seriale: **COM3**
- Librerie installate:
  - **MyLD2410** — parsing protocollo LD2410B
  - **ArduinoJson 7.4.3** — serializzazione dati JSON per logging
- LD2420: gestito a mano via Serial2 raw (nessuna libreria matura disponibile)

### ESP32 — Pinout fisico della scheda (verificato)
```
Lato SINISTRO (dall'alto, lato USB):
3V3, GND, D15, D2, D4, D16, D17, D5, D18, D19, D21, RX0, TX0, D22, D23

Lato DESTRO (dall'alto, lato USB):
VIN, GND, D13, D12, D14, D27, D26, D25, D33, D32, D35, D34, VN, VP, EN
```
- **VIN** = 5V in ingresso (lato destro, primo pin in alto) — usare per alimentare LD2410B
- **3V3** = 3.3V (lato sinistro, primo pin in alto) — usare per alimentare LD2420
- **D25** = RX2 (Serial2) — riceve dati dal sensore (← TX del radar)
- **D26** = TX2 (Serial2) — invia comandi al sensore (→ RX del radar)

### Collegamento ESP32 ↔ LD2410B (colori reali, verificato 09/08/2026)
```
Cavo ROSSO  (Pin 5 VCC)     → VIN  ESP32  (5V, lato dx primo in alto)
Cavo NERO   (Pin 4 GND)     → GND  ESP32
Cavo GIALLO (Pin 3 UART_Rx) → D26  ESP32  (TX2: l'ESP32 parla)
Cavo VERDE  (Pin 2 UART_Tx) → D25  ESP32  (RX2: l'ESP32 ascolta)
Cavo BLU    (Pin 1 OUT)     → non collegare per ora
```

### Collegamento ESP32 ↔ LD2420 (firmware ≥ 1.5.3, da verificare)
```
Pin 1 (3V3) → 3V3  ESP32  (lato sx primo in alto)
Pin 2 (GND) → GND  ESP32
Pin 3 (OT1) → D16  ESP32  (TX seriale del sensore)
Pin 4 (RX)  → D17  ESP32  (RX seriale del sensore)
Pin 5 (OT2) → non collegare per ora
```
⚠️ Verificare prima il firmware con HLK-CH340E + tool HiLink!

---

## Repository di riferimento del professore

**https://github.com/massimocallisto/HLK-LD2410x** — progetto completo di acquisizione dati dal LD2410B, da usare come base/riferimento per la tesi:

- **Firmware ESP32** (C++, cartella `LD2410B/`) — legge il radar via UART (GPIO16 RX / GPIO17 TX, stesso pinout già usato qui) e invia su seriale righe **CSV** con: timestamp, stati di rilevamento (presenza, movimento, target), distanze, livelli energetici
- **Script Python** di acquisizione e salvataggio dati (richiede `pyserial`, consigliato virtualenv)
- Supporta componenti opzionali: **display OLED SSD1306 I2C** e **sensore PIR** (utile per l'obiettivo 3, confronto PIR vs mmWave)
- README con guide di setup, troubleshooting e immagini di pinout

Nota: supporta solo il **LD2410B**, non il LD2420. Il formato CSV del repo è un buon punto di partenza per la pipeline dati dell'obiettivo 5 (web UI → CSV → Excel).

### Risultati dello studio del codice (repo clonato in `HLK-LD2410x/`)

**Firmware** (`LD2410B/src/main.cpp`, PlatformIO, libreria `ncmreynolds/ld2410@^0.2.2`):
- ⚠️ **PINOUT INVERTITO rispetto al nostro cablaggio**: il professore usa radar TX→GPIO17 e radar RX→GPIO16 (noi: TX→16, RX→17). Se si usa il suo firmware così com'è, scambiare i cavi giallo/nero; il nostro sketch `firmware/ld2410b_logger/` usa invece il nostro cablaggio
- ⚠️ **Campionamento a 1 Hz** (samplePeriodMs=1000): troppo lento per misurare la latenza con precisione e insufficiente per la FFT del respiro (Nyquist = 0.5 Hz, proprio il limite della banda respiratoria)
- **Niente engineering mode**: logga solo energia del target, non i 9+9 valori per-gate
- PIR su GPIO23 (nel **nostro** logger è su **GPIO34**, vedi sotto), LED su GPIO2, seriale verso PC a 115200 baud
- CSV: `timestamp_ms,radar_presence,moving_target,stationary_target,moving_distance_cm,stationary_distance_cm,moving_energy,stationary_energy,pir_presence`

**Script `acquire.py`** (solo pyserial): legge la seriale e aggiunge a ogni riga i metadati sperimentali da CLI. ⚠️ **La nostra copia diverge dal repo del professore**: l'originale scrive righe solo dopo aver visto la riga di intestazione (stampata dall'ESP32 una volta sola in `setup()`), quindi se il reset all'apertura della porta non scatta il CSV esce **vuoto senza avvisi**. Abbiamo aggiunto la ricostruzione dell'intestazione dal numero di colonne della riga di dati (9 = base, 27 = engineering, 29 = engineering + light/out): `pc_time_s, group_id, trial_id, scenario, ground_truth_presence, ground_truth_state`. La ground truth è **statica per file** → per la latenza serve un evento a istante noto. Abbiamo aggiunto `--beep-at SEC` (fase 2): beep grave alla prima riga di dati, beep acuto SEC secondi dopo = istante dell'evento. ⚠️ Un timer sul telefono **non** va bene: tra l'apertura della porta e la prima riga passano 2-3 s (reset ESP32 + setup logger + `time.sleep(2)`), errore sistematico maggiore della latenza misurata. Il beep conta dalla prima riga, cioè dalla stessa origine dei tempi usata da `analizza_test.py`. `serie.py` lo inoltra con lo stesso nome

**Adattamenti fatti per la tesi** (cartella `firmware/` e `analisi/`):
- `firmware/ld2410b_logger/ld2410b_logger.ino` — logger riscritto con MyLD2410: 5 Hz, engineering mode (colonne extra `menergy_gate0..8`, `senergy_gate0..8`, più `light_level` e `out_level` — quest'ultimo è lo **stato del pin OUT del radar, letto dal frame UART**: il cavo blu non va collegato), pin corretti per il nostro cablaggio, CSV retro-compatibile con acquire.py (da compilare e verificare su hardware)
- `analisi/analizza_test.py` — metriche automatiche dai CSV: accuratezza, FP eventi/h, FN%, latenza di rilevamento (`--event-time`, con la differenza appaiata `latenza_delta_s` radar−PIR e il flag dei trial in cui un sensore era già attivo prima dell'evento), latenza di **rilascio** (`--release-time`, Test 2.2: riporta anche le riaccensioni nella coda e distingue i casi `MAI`/`PRIMA`), statistiche distanza/energia, aggregazione per scenario (media ± dev.std). Solo libreria standard
- `firmware/test04_set_gate/` — configurazione del **gate massimo** via UART per il Test 2.4 (selettività spaziale / banchi adiacenti): imposta, **rilegge sempre per conferma**, avvisa quando la configurazione è diversa da quella di fabbrica, e col comando `d` riscrive le 9+9 soglie di fabbrica del nostro esemplare + gate 8/8 + timeout 5 s. Ha anche un monitor live per trovare la portata effettiva prima di acquisire
- 🚨 **Marcatore "dato assente" per il PIR (06/09/2026)** — nei test del solo LD2420 il
  PIR non viene cablato, e un pin in pull-down leggerebbe 0 per tutto il file: gli script
  ne ricaverebbero `fn_pir_% = 100,0` **con una persona davanti**, un numero finto che
  sembra una misura. Peggio, `esporta_excel.py > foglio_tutti` scandisce **tutti** i CSV
  della cartella con una glob, quindi il valore entrerebbe da solo nel foglio da cui si
  fanno le pivot. Catena di guardia, dal dato all'uscita:
  `ld2420_logger_bin` ha `#define PIR_COLLEGATO` (default **0**) e scrive **-1** invece
  di 0 → `analizza_test.py` omette *tutte* le metriche del PIR (rate, accuratezza, falsi
  positivi/negativi, latenza, rilascio, impulsi) e marca `pir_stato = NON COLLEGATO` →
  in Excel le celle del PIR restano **vuote** e la colonna `pir_stato` dice perché.
  ✔ Verificato che sui file con PIR cablato non cambi nulla: `fermo_1m_H` resta
  98,48 ± 1,03 di falsi negativi, le latenze 5,36 / 5,96 / −0,60 s, i rilasci 18,36 / 12,96 s.
  📌 **Regola generale**: un dato mancante va marcato **alla sorgente**, non annotato in un
  registro che gli script non leggono
- `analisi/verifica_engineering.py` — controllo di qualità di un CSV del logger prima di
  usarlo: cadenza reale e jitter, presenza delle colonne per-gate, % di saturazione a 100,
  coerenza gate di picco↔distanza, rumore di fondo per-gate a stanza vuota, transizioni di
  presenza. Solo libreria standard. Da lanciare a ogni sessione di acquisizione
- `analisi/analizza_respiro.py` — FFT della serie di energia, picco in banda 0.1-0.5 Hz, stima atti/min, export spettro CSV per Excel. Richiede numpy. Modalità **`--scan`**: prova tutti i 20 canali di energia, scarta saturi e piatti, ordina per SNR e riporta la mediana delle stime concordi — nata dal pilota respiro del 18/08/2026, dove il canale di default (`stationary_energy`) era saturo al 100% mentre il respiro era leggibile benissimo su `menergy_gate2`
- 🔑 **`analisi/rigenera_tutto.py` — un comando solo per rifare tutti i materiali derivati**
  (26/08/2026). Esegue in ordine i tre script qui sotto e poi la stampa in PDF; ~13 s.
  L'ordine è obbligato (la pagina incorpora i PNG, il PDF stampa la pagina) e lo script si
  ferma al primo errore senza sovrascrivere i passi successivi. Opzioni `--salta-figure`
  (riusa i PNG esistenti, utile se cambia solo il testo) e `--senza-pdf`.
  Trova Chrome o Edge da solo; se non c'è, dice come stampare a mano invece di piantarsi
- `analisi/grafici_tesi.py` — le **13 figure della tesi** in `tesi-unicam/figures/`, sia
  `.pdf` (vettoriale, per `\includegraphics`) sia `.png` 300 dpi (slide/anteprima).
  🔑 **Importa le funzioni di `analizza_test.py`** invece di ricalcolare: i numeri nei
  grafici coincidono per costruzione con quelli del capitolo 4. Applica le convenzioni di
  scarto del transitorio (20/40/120 s, più **60 s a stanza vuota**: a 20 s la coda
  dell'operatore che esce vale ancora 0,6 % e non è un falso positivo).
  ⚠️ Il R² = 0,99965 del capitolo 4 è calcolato sulle **5 medie** per distanza, non sui 25
  trial singoli (che darebbero 0,99949 e un residuo massimo di 6,0 cm invece di 4,9): la
  fig. 4 mostra entrambi e lo dichiara
- `analisi/esporta_excel.py` — `analisi/dati_tesi.xlsx`, 11 fogli. Il foglio
  `tutti_i_trial` ha **una riga per trial** con tutte le metriche (è quello da cui fare
  pivot a mano); gli altri hanno i dati già aggregati per figura, con 6 grafici Excel
  nativi modificabili. Stesse funzioni e stesse convenzioni di `grafici_tesi.py`
- `analisi/genera_pagina.py` — `RIEPILOGO_INCONTRO.html`, pagina unica di riepilogo per
  l'incontro col professore: stato dei 6 obiettivi, le 13 figure con didascalie che
  spiegano cosa dimostrano, domande da porre. Le immagini sono incorporate come data URI
  WebP, quindi **la pagina si apre offline e si manda per mail così com'è**. Ha un foglio
  di stile per la stampa (tema chiaro forzato, figure che non si spezzano fra pagine) →
  il PDF a 10 pagine A4 esce da qui.
  ⚠️ La stampa headless vuole `--virtual-time-budget=20000`: senza, Chrome stampa prima
  che arrivino i font da Google Fonts e l'impaginazione cambia
- ⚠️ **I materiali generati NON sono versionati** (regola aggiunta al `.gitignore` di
  radice il 26/08/2026): figure, xlsx, HTML e PDF si rifanno in 13 s dai CSV e pesano ~8 MB
  a ogni rigenerazione. I **CSV restano tracciati**: sono l'unico dato non ricostruibile.
  Il filtro è `tesi-unicam/figures/fig*`, quindi `LEGGIMI.txt` e un futuro
  `logo_unicam.png` continuano a entrare nel repo
- `analisi/ANALISI_CONSUMI.md` — obiettivo 4 completato in bozza (consumi da datasheet + stime autonomia + argomentazione architettura ibrida PIR+mmWave)
- `analisi/ANALISI_WEB_UI.md` — progetto della web UI (obiettivo 5): architettura ESP32 self-hosted (**solo Access Point**, nessuna connessione a reti esistenti — decisione 05/09/2026; fork ESP32Async di ESPAsyncWebServer + WebSocket + pagina in PROGMEM gzip, JavaScript puro con Angular valutato e scartato, tutto offline), formato JSON, layout pagina, struttura codice `firmware/ld2410b_web/`, piano di sviluppo in 5 step. Decisione chiave: il CSV esportato dal browser usa le stesse colonne di acquire.py → un solo formato dati in tutta la tesi. §9: analisi del riferimento UI "LD2410 Configurator" (cosa prendere/cosa no) + opzione D di riserva via Web Serial
- `analisi/PROGETTO_SITO_DETTAGLIO.md` — progetto di dettaglio implementativo del sito: struct/pseudocodice firmware, protocollo WS con riconnessione, strutture dati JS, config dei 3 grafici, export CSV client-side, gestione errori, criteri di accettazione per step
- `analisi/ANALISI_SITO_SERVER.md` — piano B dell'obiettivo 5 (19/07/2026): progetto completo del sito "vero" su server esterno nel caso il professore intenda una piattaforma e non il sito self-hosted. Architettura ESP32→MQTT (Mosquitto)→FastAPI+SQLite→browser, codice firmware/backend di riferimento, export CSV compatibile acquire.py, confronto A vs B e domanda di decisione per l'incontro (aggiunta a INCONTRO_PROFESSORE.md, domanda 7). Frontend condiviso ~85% con l'opzione A → cambiare rotta costa ~2-3 giorni. Default resta l'opzione A
- `analisi/ANALISI_VITALITA.md` — specifica dell'indice di vitalità (obiettivo 6, documento autonomo): algoritmo v1 (doppia EWMA movimento+respiro), classificazione a 4 classi per il triage, percorso di taratura Python-prima sui CSV della Fase 6 con validazione su trial separati, casi limite, collocazione nella tesi
- `analisi/ANALISI_PIR.md` — analisi teorica del PIR (obiettivo 1-2): principio piroelettrico differenziale, lente di Fresnel, perché è fisicamente cieco alla persona ferma, dati prodotti (1 bit + ritenuta/trigger), sensibilità alla temperatura, sezione 6 DA COMPLETARE col modello reale (Test 0.3)
- `SCALETTA_TESI.md` — scaletta Overleaf in 8 capitoli con mappa obiettivi→capitoli, materiale già pronto per ciascuno e ordine di scrittura consigliato (cap. 5 e 2 scrivibili subito)
- `INCONTRO_PROFESSORE.md` — agenda per l'incontro: cosa mostrare (PIANO_TEST, scaletta, consumi) e domande consolidate (validazione protocollo, montaggio sensore/lamiera, scadenza, UPRISE vs SAFE, ruolo UWB)
- `PIANO_TEST.md` — piano di test completo in ordine di esecuzione (fasi 0-7)
- `PIANO_TEST_LD2420.md` — piano di test dedicato al secondo radar (26/08/2026), scritto
  dopo l'acquisizione della documentazione ufficiale. Distingue i **10 test radar da
  ripetere** dai risultati che **non vanno rifatti** (tutto ciò che riguarda il PIR e il
  risultato centrale della tesi, che non dipendono dal radar) e dai **3 non replicabili**
  sul LD2420 (distanza su bersaglio fermo, separazione moving/still, respiro/vitalità).
  Contiene lo schema CSV unico per far girare gli script esistenti senza modifiche, il
  test nuovo sul **gate minimo** (funzione assente nel LD2410B) e la taratura bloccante
  dell'unità del campo `Range`. Stima: ~9,5 h essenziali + 1 notturna

---

## Fonti consultate

### Documentazione tecnica
- Repo professore HLK-LD2410x (firmware ESP32 + script Python CSV): https://github.com/massimocallisto/HLK-LD2410x
- Slide progetto UPRISE (terremoto): https://docs.google.com/presentation/d/11Q_Zet3aEtPZo2vcoM7_cvcTCbvLY-FBznCqPK37k3E/edit?usp=sharing
- Slide "Sharper - Informatica 26 settembre 2025.pptx" (file locale, 76 slide): contesto completo — arredi salva-vita, DIPME, LoRa, Digital Twin
- Paper Digital Twin del progetto: Callisto et al., "Design and Development of a Digital Twin Prototype for the SAFE Project", EDOC 2023 (Springer)
- Piattaforma Digital Twin UNICAM: https://pros.unicam.it/dtplatform/
- ESPHome LD2410: https://esphome.io/components/sensor/ld2410.html
- ESPHome LD2420: https://esphome.io/components/sensor/ld2420.html
- espboards.dev LD2410 guide: https://www.espboards.dev/sensors/ld2410/
- esp32.co.uk LD2410+HA: https://esp32.co.uk/esp32-ld2410-mmwave-presence-sensor-with-home-assistant/
- tastethecode.com guida pratica: https://www.tastethecode.com/human-presence-detection-with-millimeter-wave-sensors
- Google Drive HiLink LD2420 (datasheet + tool): https://drive.google.com/drive/folders/1IggDH6ejNSOs8EklQbAXcqUI7KENSZLt
- **Copie locali ufficiali LD2420** (scaricate 26/08/2026, in `HLK-LD2420/Documentazione/`)
  — da citare in `bib/tesi.bib` come fonti primarie:
  - `HLK-LD2420-Product-Manual V1.2.pdf` — manuale ufficiale, 16 pagine (specifiche
    Tabella 2-1, piedinatura J1/J2 Tabelle 3-1/3-2, parametri del tool §4.2.1, bottom
    noise scan §4.2.2-4.2.3, portate e montaggio §5, *Cautions* §8). ⚠️ Il frontespizio
    dice "Version V1.0, Feb 24 2023" e lo storico si ferma alla V1.1, mentre il file
    distribuito si chiama V1.2: incongruenza del produttore, da citare come "manuale
    V1.2 (frontespizio V1.0)"
  - `HLK-LD2420 Protocol Document.pdf` — protocollo seriale, 5 pagine. ⚠️ Copre **solo
    i comandi di configurazione**: non documenta il frame dei dati in uscita. Contiene
    un errore aritmetico a pag. 2 (`40 9C 00 00` letto come 60000 anziché 40000)
- Google Drive HiLink **LD2410B** (manuale V1.04, protocollo seriale V1.07, tool PC `LD2410 Tool EN (英文版).zip`): https://drive.google.com/drive/folders/16zI-fium_BZeP08EyQke0rWp0BJTMvw3 — linkata dalla pagina prodotto ufficiale https://www.hlktech.net/index.php?id=1090. ⚠️ NON usare `HLK-LD2420_TOOL` col LD2410B: protocolli diversi, errore "Failed to set data transfer mode" (17/08/2026)
- **Copie locali ufficiali LD2410B** (scaricate 18/08/2026, in `HLK-LD2410x/Documentazione/`) — da citare in `bib/tesi.bib` come fonti primarie:
  - 🚨 **I FRONTESPIZI DI ENTRAMBI SONO SBAGLIATI** (accertato 29/08/2026 leggendo le
    tabelle di *revision records* con `pypdf`). Con Hi-Link la versione va letta **dalla
    tabella di revisione, mai dalla copertina** — vale per tutti e tre i documenti
    ufficiali che abbiamo, LD2420 compreso:
    | documento | frontespizio | verità dalla tabella | PDF CreationDate |
    |---|---|---|---|
    | Manuale LD2410B | V1.04, "Revised date: 2022-6-29" | V1.04 = **2022-08-19** (il 2022-6-29 è la **V1.03**) | 2022-08-30 |
    | Protocollo LD2410B | V1.07, "Revised date: 2024-8-5" | contiene una riga **1.08 del 2024-11-22** | 2024-11-26 |
    | Manuale LD2420 | V1.0, Feb 24 2023 | file distribuito come V1.2 | — |
  - `HLK LD2410B Life Presence Sensing Module Manual V1.04.pdf` — manuale ufficiale
    (specifiche, consumi, pinout), 17 pagine. **Data reale: 2022-08-19.** Storico:
    1.01 (2022-5-26) → 1.02 (2022-6-8) → 1.03 (2022-6-29) → 1.04 (2022-8-19,
    "Modification of bluetooth description"). La V1.04 è l'**ultima** versione del
    manuale: non è stato più revisionato
  - `LD2410B Serial communication protocol V1.07.pdf` — protocollo seriale completo
    (frame, comandi, engineering mode), 23 pagine.
    🚨 **Il contenuto è in realtà la revisione 1.08 del 2024-11-22**: la tabella a p.22
    la elenca, il frontespizio la ignora, e il piè di pagina della copertina dice
    "Page 1 / **19**" mentre tutte le altre pagine dicono "/ **23**" — residuo di
    un'edizione da 19 pagine mai rigenerata. Tre indizi indipendenti concordi
    - ⚠️ **Rilevante per noi**: la 1.08 dichiara *"Modify some instruction reply errors
      and **add engineering mode data parsing**"*. Noi citiamo **§2.3.2 *Target data
      composition*** (p.19) per spiegare `senergy_gate0/1 = 0`: quella sezione **c'è**
      nella nostra copia, ma un V1.07 autentico potrebbe non contenerla. Citare quindi
      come "frontespizio V1.07, contenuto rev. 1.08 del 2024-11-22"
    - la rev. **1.07 (2024-08-05)** è quella che introduce i comandi di *background noise
      detection* e *sensitivity automatic configuration*, cioè l'auto-calibrazione del
      firmware V2.44: i due documenti si datano a vicenda coerentemente
  - `LD2410B V2.44 (24073110)- introduction of new features.pdf` — novità del firmware V2.44: **rilevamento automatico del rumore di fondo** (auto-calibrazione delle soglie movimento+stazionario). Procedura: pulsante "Auto" nell'app, 10 s per uscire dal campo + 60 s di misura = 70 s totali, restando fuori dal range. Richiede app Android ≥ V1.5.12 / iOS ≥ V1.5.4. Da non confondere con il "Detect noise floor" della schermata parametri, che è **solo** una funzione dell'app (mostra i valori, non li applica). Il documento NON descrive alcuna procedura di aggiornamento del firmware
- Tool PC ufficiale `LD2410 Tool (v1.0.0.0)` — copia locale in `HLK-LD2410x/LD2410 Tool/LD2410 Tool.exe`. ⚠️ Non mostra la versione firmware e **non** ha funzione di flash/update
- App mobile Bluetooth `HLKRadarTool` (Android/iOS, password `HiLink`): cercare "HLKRadarTool" negli app store, oppure download ufficiale https://www.hlktech.com/Mobile/App/12.html (link dal documento V2.44)
- Datasheet HC-SR501 (PIR in dotazione): https://www.electronicoscaldas.com/datasheet/HC-SR501.pdf (mirror; altra copia su mpja.com/download/31227sc.pdf)
- Datasheet BISS0001 (chip del PIR): https://cdn-shop.adafruit.com/datasheets/BISS0001.pdf
- Adafruit PIR guide (principio piroelettrico/Fresnel): https://learn.adafruit.com/pir-passive-infrared-proximity-motion-sensor
- ESP32-WROOM-32 datasheet (consumi): https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32_datasheet_en.pdf
- Manuale HLK-LD2410 V1.03 (consumi/specifiche verificate): https://seengreat.com/upload/file/86/HLK+LD2410+Life+Presence+Sensor+Module+Manual+V1.03(220629).pdf
- Datasheet LD2410B (pin definition Tabella 1, protocollo seriale): https://assets.super.so/79c0d2a8-d37a-438f-8fbe-c44778f3b0dd/files/7c3607bd-f703-43f5-9f22-f369f00c37bd.pdf
- LD2410 Configurator (Albert Nisbet) — configuratore web open source via Web Serial/Web Bluetooth, riferimento UI per l'obiettivo 5: https://ld2410.albert.nz/ · sorgenti https://github.com/albertnis/ld2410-configurator · ⚠️ progetto di comunità, non ufficiale Hi-Link: vale come riferimento UI/implementativo, non come fonte di dati tecnici (analisi in `analisi/ANALISI_WEB_UI.md` §9)

### Articoli e confronti
- mmWave Occupancy Sensors - Smart Buildings: https://mmwave-radar.dev/applications/occupancy-sensing
- UWB vs PIR vs mmWave comparison: https://www.rfwireless-world.com/terminology/uwb-radar-vs-passive-ir-vs-mmwave-radar-comparison

### Letteratura scientifica
- Non-Contact Vital Signs Monitoring (UPM): https://oa.upm.es/85091/
  - Dimostra rilevamento apnea notturna con FMCW radar; confronto CW vs FMCW
- mmWave Sensing for Vital Signs + User ID (UTS): https://opus.lib.uts.edu.au/handle/10453/194445
  - Neural ODE + TCN per estrazione HR/RR/pressione; ISAR per identificazione
- Comparison 24GHz vs 60GHz mmWave sensors (Theseus): https://www.theseus.fi/handle/10024/850734
  - 24GHz: portata maggiore, risoluzione inferiore; 60GHz: risoluzione alta, portata ridotta
- mmWave Multi-Object Tracking (UTS): https://opus.lib.uts.edu.au/handle/10453/192530
  - mmCLAE per tracking multi-target; applicazioni automotive e robotica
- mmWave-RM Respiration Monitoring (MDPI): https://www.mdpi.com/1424-8220/24/13/4315
  - **Non accessibile (paywall)** — recuperare via accesso universitario o Sci-Hub

### Video
- YouTube - Human presence detection LD2410+ESP32: https://www.youtube.com/watch?v=oJZS8c9oyjg

---

## Note e avvertenze pratiche

- Il LD2420 si alimenta a **3.3V**, non 5V come il LD2410B
- Il manuale V1.2 del LD2420 documenta **una sola** piedinatura J2 (OT1 = UART_TX,
  OT2 = presenza); la variante invertita per firmware ≤ 1.5.2 è informazione di comunità
  (ESPHome) — verificare comunque prima di collegare con HLK-CH340E
- Il LD2420 **non riporta la distanza dei bersagli fermi** (manuale §8): sulla persona
  immobile dice se c'è, non dove. Limite decisivo per lo scenario UPRISE
- Entrambi i sensori usano **TX/RX incrociati** rispetto all'ESP32
- Il baud rate 256000 richiede UART hardware dell'ESP32 (D25/D26), non softserial
- Per il respiro serve **engineering mode** sul LD2410B (byte comando `0x62`)
- Il LD2410B non distingue due persone alla stessa distanza (no array di antenne)
- Penetrazione ostacoli: funziona su legno/cartongesso/vetro/plastica; non su metallo o cemento armato spesso
- I cavi del LD2410B seguono la convenzione standard: **rosso=VCC, nero=GND, blu=OUT**, i due centrali (giallo=Rx, verde=Tx) sono la seriale. Fare sempre riferimento alla Tabella 1 del datasheet, non a ipotesi sull'ordine dei pin: un'inversione qui ha già fatto perdere ~3 settimane facendo credere il modulo guasto
- Il CH340E può essere usato per collegare il LD2420 direttamente al PC (senza ESP32) per leggere il firmware

## Note di processo

- **REGOLA FONTI (richiesta esplicita, 15/07/2026)**: ogni dato tecnico inserito nei documenti deve avere la fonte citata, preferibilmente certificata o autorevole (datasheet del produttore > manuale ufficiale > guide riconosciute tipo Adafruit/ESPHome > blog). Ogni documento di analisi ha la sua sezione "Fonti"; le fonti confluiranno in `bib/tesi.bib` su Overleaf. Se una fonte riporta valori sospetti (es. refusi mA/µA), annotarlo e far fede al datasheet
- **La tesi si scrive in Overleaf (LaTeX)** — impostare lo scheletro dei capitoli presto e scrivere durante i test, non dopo: i documenti in `analisi/` sono già bozze di capitoli
- **Validare PIANO_TEST.md col professore PRIMA della campagna di test** (~10 h di acquisizioni: se il protocollo non va bene si rifà tutto)
- ✔ **Backup dei dati: fatto (26/08/2026)** — i CSV sono l'asset insostituibile della
  tesi ed è la ragione per cui il repo esiste. Sono su GitHub
  (`Steb2002/Tesi-Presence-Sensing`), verificati 116 su 116 nel remoto. **Pushare dopo
  ogni sessione di acquisizione**: un commit locale non è un backup
- **Confronto con UWB da preparare a livello argomentativo** (il DIPME-DEVICE ha già un sensore UWB): la commissione può chiedere "perché mmWave e non UWB?" — rispondere da letteratura/datasheet (costo, maturità moduli consumer, dati per-gate), partendo dalla tabella comparativa qui sopra
- Ogni sessione di test va annotata in `HLK-LD2410x/data/REGISTRO_SESSIONI.md` (temperatura stanza, soggetto, alimentazione)

## Stato avanzamento progetto

### Setup
- [x] Arduino IDE 2.3.9 installato
- [x] Supporto ESP32 installato (esp32 by Espressif Systems)
- [x] Librerie installate: MyLD2410, ArduinoJson 7.4.3
- [x] ESP32 testato e funzionante su COM3
- [x] Cavi LD2410B identificati e mappati
- [x] Call col professore: obiettivi definiti in 6 punti, contesto UPRISE, repo di riferimento
- [x] Studiare il repo del professore (clonato in `HLK-LD2410x/`, codice analizzato — vedi sezione dedicata)
- [x] Piano di test completo scritto (`PIANO_TEST.md`)
- [x] Script di analisi pronti (`analisi/analizza_test.py`, `analisi/analizza_respiro.py`)
- [x] Firmware logger esteso scritto (`firmware/ld2410b_logger/` — da compilare e verificare su hardware)
- [~] Primo contatto LD2420 fatto via ESP32 (GPIO16/17, 115200, modalità ASCII) — resta
      da leggere versione firmware esatta + unità "Range" col tool HiLink (Test 0.5)
- [x] **Documentazione ufficiale LD2420 acquisita (26/08/2026)** — manuale V1.2 +
      Protocol Document in `HLK-LD2420/Documentazione/`. Specifiche di CLAUDE.md e del
      cap. 3 corrette di conseguenza (portata 8 m non 12, 16 gate non 15, ±0.35 m di
      accuratezza, 10 Hz, 50 mA)

### Sensori (obiettivi 1-2)
- [x] LD2410B FUNZIONANTE (09/08/2026) — il "guasto" del 19/07 era cablaggio invertito.
      Cablaggio corretto: rosso→VIN, nero→GND, giallo(Rx)→D26, verde(Tx)→D25. Test 0.1,
      0.2, 0.6 e fasi 1-3/5-6 sbloccati
- [x] LD2410B verificato dal PC col tool ufficiale (18/08/2026): `LD2410 Tool (v1.0.0.0)`,
      COM3 @ 256000, **Engineering Mode attivo** — grafici energia per-gate Moving/Motionless
      e distanza rilevata funzionanti (letti 41 cm). Parametri di fabbrica letti: 1 RG = 0.75 m,
      Moving/Motionless Max RG = 8, Abs. Report Delay = 3 s, Stat. Time = 120 s,
      sensibilità Moving/Motionless = 100. Conferma che i dati per-gate necessari agli
      obiettivi 2/3/6 (respiro compreso) sono già disponibili senza toccare il firmware.
      ⚠️ **RISOLTO (18/08/2026)**: il "sensibilità = 100" letto dal LD2410 Tool era una
      lettura sbagliata. Le soglie vere, lette col comando 0x0061 via
      `firmware/test00_ld2410_info/`, sono la scala di fabbrica decrescente:
      movimento **50 50 40 30 20 15 15 15 15**, stazionario **0 0 40 40 30 30 20 20 20**
      (gate 0-8). Coerente col protocollo V1.07 §1.2.2 (target riconosciuto solo se
      energia > soglia) e col comportamento osservato. **Non fidarsi del LD2410 Tool per
      i valori numerici: usare la lettura via UART**
- [x] **Test 0.1 SUPERATO (18/08/2026)** — `firmware/test01_ld2410_base/`: baud **256000**
      confermato, presenza/distanza/energia leggibili, moving e still distinti
- [x] **Parametri di fabbrica letti via UART (18/08/2026)** — `firmware/test00_ld2410_info/`:
      MAC Bluetooth **5E:E4:93:22:B9:3F**, risoluzione 75 cm/gate, range 675 cm,
      timeout presenza **5 s**, soglie movimento **50 50 40 30 20 15 15 15 15** e
      stazionario **0 0 40 40 30 30 20 20 20**. Tabella completa con confronto
      soglia↔rumore in `HLK-LD2410x/data/REGISTRO_SESSIONI.md`
- [x] **Decisione: NON ricalibrare adesso.** Confrontando le soglie di fabbrica col
      rumore di fondo misurato, il margine più stretto è il gate 6 in movimento
      (soglia 15 vs rumore max 11) e i falsi positivi osservati sono zero: la taratura
      di fabbrica regge nel nostro ambiente. Le soglie restano il **riferimento fisso**
      per tutta la campagna fasi 1-3 (cambiarle a metà renderebbe i trial non
      confrontabili). L'auto-calibrazione (cmd 0x000B) va usata dopo, come esperimento
      a sé con confronto prima/dopo — è materiale da sezione della tesi, non un
      prerequisito
- [x] Versione firmware letta: **2.44.25070917** — è l'ultima Hi-Link, quindi il nostro
      esemplare **ha l'auto-calibrazione delle soglie** del V2.44 (esempio
      `MyLD2410 > auto_thresholds`). Annotata in `HLK-LD2410x/data/REGISTRO_SESSIONI.md`.
      Resta da leggere il MAC Bluetooth
- [x] **Test 0.1 passo B + Test 0.2 SUPERATI (18/08/2026)** — logger `ld2410b_logger`
      validato su 673 campioni / 134 s (`HLK-LD2410x/data/20260818_test01B_ld2410b_engineering.csv`,
      analizzato con `analisi/verifica_engineering.py`):
      - cadenza **5.00 Hz esatti**, dt = 200 ms su tutti i 672 intervalli (jitter zero) →
        serie temporale uniforme, adatta alla FFT del respiro
      - engineering mode attivo: 18 colonne per-gate popolate
      - **mappa gate↔distanza validata: 97.1%** dei campioni in movimento ha il gate di
        picco entro ±1 dal gate atteso (distanza/0.75 m), su tutto il range 0-6 m
      - rumore di fondo a stanza vuota (29 s): moving gate0 ≈ 17 (max 26), gate1 ≈ 13
        (max 21), gate2-8 ≤ 11; stationary tutti ≤ 7
      - **zero falsi positivi** nei 29 s di stanza vuota
- ⚠️ **Tre osservazioni metodologiche dal Test 0.1/0.2** (da tenere presenti in fase 1-3 e 6):
      1. **Saturazione**: l'energia *stazionaria* è a fondoscala (100) nel **92%** dei
         campioni con target fermo, la *moving* nel 41%. Un segnale clippato non porta
         informazione. ⚠️ **Le soglie NON risolvono la saturazione**: l'energia è un valore
         normalizzato 0-100 e la soglia interviene solo sulla *decisione* di rilevamento
         (protocollo V1.07 §1.2.2), non sul valore riportato. Nemmeno l'auto-calibrazione
         (cmd 0x000B) la risolve, perché anch'essa tara soglie, non la scala. L'unico
         rimedio è **geometrico**: allontanare il soggetto (≥1.5-2 m), disallineare il
         sensore o attenuare. Vale per respiro e indice di vitalità
      2. **`senergy_gate0` e `senergy_gate1` sono sempre 0** (673/673 campioni). Anche
         l'esempio ufficiale del protocollo V1.07 §2.3.2 mostra `00 00` per i primi due
         gate statici, quindi non è un difetto del nostro esemplare.
         ⚠️ Attenzione a non trarre la conclusione sbagliata: il radar **riporta comunque
         bersagli fermi sotto 1.5 m** (nei dati: `stationary_distance` 70-89 cm con
         `stationary_energy` = 100). A mancare è solo il **dettaglio per-gate** dello
         stazionario nei primi due gate. Conseguenza pratica: respiro e indice di vitalità,
         che si basano sulla serie di energia per-gate, per un soggetto a < 1.5 m non
         possono usare il canale stazionario → usare il canale **moving** o i gate ≥ 2.
         **Rilevante per lo scenario UPRISE** (persona sotto il banco, quindi vicina):
         da verificare esplicitamente in fase 6
      3. **Coda di presenza**: dopo l'uscita il radar ha tenuto `presence=1` per ~10 s con
         un target fermo fantasma a ~5.2 m ed energia in decadimento. È il comportamento
         atteso ("no-one duration", protocollo §1.2.2), ma va misurato come **latenza di
         rilascio** in fase 1 e non confuso con un falso positivo
      4. 🔑 **Il fantasma stazionario compare anche DURANTE il movimento** (scoperto col
         Test 1.5, 29/08/2026 — estende il punto 3, che lo dava solo nella coda). Con la
         scena occupata da **un solo bersaglio in movimento continuo**, il canale
         stazionario riporta un target **saturo** (`senergy` = 100) a distanza sbagliata:
         a 3 m riporta **436,8 cm con 113,4 cm di dispersione**, mentre la persona e' a
         3 m e non si ferma mai. Riproducibile su due sessioni indipendenti e in
         condizioni ambientali diverse.
         📌 **Conseguenza pratica: `sdist_*` e `senergy` non vanno letti quando il
         bersaglio e' in moto.** Non tocca la presenza (`radar_rate_%` resta 100 %, la
         porta il canale moving), ma e' un limite citabile del modulo
- [~] Setup e test LD2420 — collegato e letto (presenza + range in modalità ASCII,
      sketch `firmware/ld2420_monitor/`)
- 🔑 **SESSIONE LD2420 DEL 01-02/09/2026 — cosa e' stato accertato** (dettagli riga per riga
      nel registro):
      - **firmware v1.6.1** (Test 0.5 chiuso); `GateMax=12`, ritardo 30 s; **32 soglie lette
        via UART** con `firmware/test06_ld2420_set_gate/` e coincidenti tutte con l'XML di
        fabbrica → conversione `grezzo = 10^(dB/10)` validata su ogni parametro
      - logger `firmware/ld2420_logger/` scritto: stesse 9 colonne del LD2410B, 5 Hz,
        **presenza da OT2 (GPIO19)**, PIR su GPIO21 (non su 34: irraggiungibile sulla
        breadboard attuale). ⚠️ OT2 NON su GPIO15: e' di strapping e blocca l'upload
      - ❌ **la presenza ASCII e' inutilizzabile**: dump grezzo (`test05_ld2420_raw`) = 2528
        `ON`, 0 `OFF` in 4 min, stanza vuota inclusa. La notturna a stanza vuota
        (`stanza_vuota_2420_T01`, 79,4 % di presenza) e' **NON VALIDA** per questo motivo
      - ❌ **nemmeno OT2 rilascia** a configurazione di fabbrica: 100 % con stanza vuota per
        120 s. Causa plausibile e documentata da ESPHome ("a wall within the gate max range
        can result in signal reflections"): 840 cm di campo in una stanza di ~5 m, con soglie
        *hold* di fabbrica a **100** sui gate 7-15
      - `Range`: **centimetri** quando c'e' un bersaglio (105 a ~1 m, 414-425 a ~4,5 m,
        130 a ~1,3 m), **valore di riposo 0-6** quando non c'e'. I "7-37" del 17/07 erano
        il riposo. Aggiorna di rado (5 cambi in 60 s) e va letto solo con OT2 alto
      - ⚠️ **la scrittura dei parametri via UART e' accettata ma NON persistente**: riletta
        correttamente, sopravvive alla chiusura/riapertura della modalita' comandi, ma il
        riavvio `0x68` la scarta. Nessun comando di salvataggio nel Protocol Document
      - ❓ **APERTO**: nei due test con gate 8 impostato via UART il `Range` e' rimasto
        congelato per tutti i 180 s, persona a 1-2 m compresa. Ipotesi: **qualunque
        sessione di comandi ferma il rilevamento finche' il modulo non viene riavviato** —
        e il riavvio scarta la configurazione. Se confermata, via UART il gate non e'
        configurabile e resta il tool PC (mai riuscito a collegarsi al modulo, finora: i 5
        tentativi del 02/09 alle 18:43 parlavano con l'ESP32 sulla COM3)
      - 📌 **Il confronto sta prendendo una direzione precisa**: il LD2410B funziona fuori
        scatola con soglie di fabbrica (0 falsi positivi in 6,55 h); il LD2420 nella stessa
        stanza dichiara presenza permanente e richiede una taratura per installazione. Per
        centinaia di banchi e' una differenza operativa sostanziale — ma va **misurato dopo
        la taratura**, non concluso dal fallimento di fabbrica
- 🚨 **STATO LD2420 AL 04/09/2026: l'esemplare vede una persona solo fino a ~2 m** (dettagli
      riga per riga nel registro, sessioni 03-04/09). Cosa e' accertato:
      - **modalita' binaria (energy) funzionante** via `firmware/ld2420_logger_bin/` (BUILD 4:
        16 energie uint16 a 10 Hz, presenza e distanza dal frame, gate max opzionale a ogni
        avvio, **niente OT2**: tolto il 04/09, non serviva). Il tool PC mostra gli stessi
        numeri in dB = 10·log10(grezzo): parser assolto
      - **le soglie in flash erano quelle di fabbrica, mai tarate** (i due XML del 17/07 e
        03/09 sono identici agli esempi del Protocol Document). Tarate col tool il 03-04/09
        (`Calc. Thres.` = bottom noise scan del manuale §4.2.2-4.2.3: trigger 5x rumore, hold
        3,5x, scarto costante 1,55 dB). Con gate max 6 il modulo **rilascia** (il muro a ~5 m
        stava nel gate 7 e teneva l'hold nel 4 % dei campioni). Backup:
        `ld2420_config_tarato_max_6.xml` (e `_max_8.xml` per la prima taratura)
      - **portata misurata** (`portata2420_g8_T01/T02`, tacche 100-480 cm, oscillazione e
        cammino sul posto): 100 cm → dist 105, gate 2 x4; 200 cm → dist **204**, gate 3
        appena sopra il fondo; **da 300 cm in su energie identiche alla stanza vuota**. Stesso
        risultato in ASCII (`Range` max 206) e nel tool (`Range VS Time` ≤ 2 m)
      - **diagnosi**: ricevitore a norma (rumore ai gate 12-15 = 35 grezzi, esattamente il
        progetto delle soglie di fabbrica 200/100), **accoppiamento TX→RX al gate 0 = 110
        contro ~12000 di progetto** (e `Avg 8656` nell'esempio ESPHome) → trasmettitore
        ~20-25 dB sotto → portata 8 m / 10^(25/40) ≈ **1,9 m**, che e' quanto misurato.
        Escluse con misure: soglie, gate, firmware (1.6.1 e' l'ultimo, Hi-Link non pubblica
        i .bin), parser, orientamento, geometria, cavo corto sull'adattatore, danno visibile,
        5 V (mai). Non provata: alimentazione da pile (non disponibili). **Conclusione:
        esemplare difettoso dall'origine, con ogni probabilita'**
      - ⚠️ **la "prova" del 02/09 01:25 (Range 414-425 a 4,5 m) era il MURO**: valore
        costante per 50 s mentre il soggetto camminava; lo stesso riflettore compare nel tool
        come "5 m fisso" con gate 7-8 e sparisce con gate 6. Non c'e' evidenza che il modulo
        abbia mai visto oltre 2 m
      - **convenzione dei gate, due punti coerenti**: 105 cm → gate 2, 204 cm → gate 3, cioe'
        il gate che copre (N−1)·70…N·70 come nel LD2410B → **portata = N × 70 cm**, gate 6 =
        420 cm. Da confermare con un esemplare sano
      - **decisione** *(la sospensione della Fase 4 e' SUPERATA dalla voce successiva,
        05/09/2026)*: ordinare un secondo esemplare; nel frattempo si
        passa all'obiettivo 5 (sito). Tenere il pezzo attuale: il confronto fra i due sulla
        stessa tacca e' un dato di tesi (variabilita' fra esemplari). Nuovi strumenti:
        `acquire.py --tappe` (annunci vocali a istanti prefissati) e `analisi/portata2420.py`
        (analisi per finestre temporali)
- 🔑 **RISPOSTA DEL PROFESSORE (05/09/2026) E DECISIONE CONSEGUENTE**: il modulo non era
      mai stato provato prima, quindi nessuno sa se il difetto sia noto. Indicazione:
      *"Nella tesi riporterei esattamente quello che scrivi qui, descrivi i test, riporti i
      risultati. Se hai riscontrato problemi o limitazioni e hai fatto differenti prove su
      pc/esp32 allora va bene."* → il limite dell'esemplare **è materiale di tesi, non un
      buco da tappare prima di scrivere**.
      📌 **La Fase 4 non resta sospesa: si esegue una CAMPAGNA RIDOTTA ENTRO 2 m**, cioè
      dentro la zona in cui l'esemplare funziona (piano dettagliato in
      `PIANO_TEST_LD2420.md` §0-bis). Restano fuori solo i test che *richiedono* più di
      2 m; entrano invariati i due più preziosi — **dose-risposta a 1 m** (tre sensori sulla
      stessa scala di movimento) e **sotto il banco a 60 cm** (scenario UPRISE). Vincoli:
      modalità binaria obbligatoria, **gate max 6 + soglie tarate** (deroga dichiarata alla
      parità di configurazione: a soglie di fabbrica il modulo non rilascia), e ogni numero
      attribuito **all'esemplare**, mai al modello. ~9,5 h + 1 notturna
- 🎯 **TEST 1.3-2420 COMPLETATO (06/09/2026): il LD2420 MANTIENE la persona in piedi
      immobile a 1 m in 5 trial su 5** — `radar_rate_%` = 100,00 ± 0,00 su 202 s × 5, zero
      fronti. Riga a tre sensori a geometria identica: **LD2410B 100 % · LD2420 100 % ·
      PIR 1,52 %**. Non e' coda: sul gate 2 l'hold e' superato nel 17-44 % dei campioni con
      intervallo massimo 5,8-16 s (< 30 s di ritardo), energia 30-51 contro fondo 13.
      🚨 **Ma la strada per arrivarci e' essa stessa un risultato**: la taratura del tool
      del 04/09 **non rilasciava** a stanza vuota, e nemmeno **due nuove scansioni** — l'hold
      del gate 5 esce **13,84 / 13,82 / 13,84 dB in tre scansioni indipendenti** (rumore
      stimato ~7) contro una **media misurata di 15 e massimo 34** su 120 s. Il *bottom noise
      scan* ufficiale sottostima le code in modo ripetibile su questo esemplare. Soglie
      finali `ld2420_config_fondo120s_max_6.xml`: **formula del manuale** (5× / 3,5×) su
      **rumore = media a 120 s** del nostro file. Deroga piu' ampia di quella del piano, da
      dichiarare cosi'. Meccanismo verificato con simulazione sul file stesso prima di
      caricare: gap max 52,6 s > 30 s
      - **§8 del manuale misurato**: `dist_raw` a riposo (2-5 cm) con presenza al 100 % in
        4/5 trial; T04 riporta **133 cm costanti per 202 s**. Dice *se*, non *dove*
      - ⚠️ **il gate 2 NON distingue immobile da cammino sul posto**: positivo a 105 cm
        media 29 / p95 68, persona ferma media 30-51 / p95 80-121. Sul LD2410B le stesse
        condizioni davano `menergy` 68,6 vs 99,3. Ipotesi (non dimostrata): dinamica
        dell'esemplare ~6,5 dB, esaurita a 1 m → **la dose-risposta 2.3-2420 puo' uscire
        piatta**; farla comunque
      - rilascio a stanza vuota **~55 s** (LD2410B: 9-12 s con timeout 5 s). Scarto dei
        trial da fermo alzato a **90 s** (`--duration 292 --transitorio 90`)
      - abbassare il gate max **non** avrebbe risolto il mancato rilascio (simulato: a gate
        2 il gate 2 stesso teneva l'hold, gap max 24,4 s). Se in futuro si scende a gate 2,
        il gemello LD2410B e' `sel_dentro_1m`, non `fermo_1m_H`
- 📉 **DOSE-RISPOSTA A 1 m SUL LD2420: PIATTA (06/09/2026)** — `micromovimenti2420_1m`
      5/5 al 100 %, ma gate 2: vuoto 13,4 · immobile **41,0 ± 9,3** · micro **34,8 ± 1,0** ·
      cammino **31,0**. Ordine **rovesciato** rispetto al LD2410B (68,6 → 84,4 → 99,3) e
      condizioni sovrapposte. Il canale separa vuoto/occupato e poi non gradua: **su questo
      esemplare non esiste la grandezza continua per l'indice di vitalita'** (obiettivo 6
      resta sul LD2410B, e il confronto va scritto come limite dell'esemplare). Curiosita':
      i micro-movimenti sono la condizione piu' ripetibile (dev 1,0), l'immobile la meno
      (9,3) — l'inverso del PIR. `dist_raw` valida 0-9 → 25-86 → 100 % col movimento, ma
      con valori **stantii** (133 cm ricorre in tre trial diversi con la persona a 105):
      distanza usabile solo su bersaglio in moto continuo, come dice il §8
- 🚪 **Seconda richiesta del professore, stessa mail: quantificare l'attenuazione**
      *("se prima arrivava a 5 mt, con una porta di mezzo quanto si attenua il segnale?")*.
      Non è una rilettura dei dati della Fase 3: quelli sono in punti percentuali di
      `menergy`, che **non è una potenza** e non si converte in dB. Due misure nuove,
      complementari:
      1. **Portata residua in metri** sul LD2410B — `PIANO_TEST.md` **Test 3.6**: stessa
         geometria della Fase 3 ma percorrendo 1-5 m, per ogni materiale. Risposta in
         un'unità fisica e senza ipotesi sullo strumento. Priorità: **porta interna chiusa**
         (l'esempio del professore, e copre tutto il campo → cade l'avvertenza "attenuazioni
         come limiti inferiori"), poi legno, vetro, **cartongesso** (richiesto di nuovo:
         procurare uno sfrido, costa pochi euro)
      2. **Attenuazione in dB** sul LD2420 — `PIANO_TEST_LD2420.md` §0-ter: è l'unica cosa
         che il LD2420 misura **meglio**, perché le sue energie sono `uint16` grezzi e il
         tool le mostra come 10·log₁₀(grezzo). ⚠️ Ipotesi dichiarata (Hi-Link non documenta
         il campo) e dinamica dell'esemplare limitata a ~6,5 dB sopra il rumore: quantifica
         gli attenuatori deboli, satura sui forti
- ⚠️ **Lezione di processo (02/09/2026)**: tre giri di prove sono stati attribuiti al
      modulo mentre l'ESP32 eseguiva un **binario vecchio** — lo sketch non compilava (una
      stringa spezzata) e l'IDE non caricava nulla. Da allora gli sketch stampano un
      **marcatore `BUILD n`** all'avvio: verificarlo prima di interpretare qualsiasi output
- ⚠️ **L'"engineering mode binario" del LD2420 non è documentato da Hi-Link (accertato
      26/08/2026)**: il Protocol Document copre solo i comandi di configurazione e il
      manuale indica le righe ASCII come l'uscita normale. **Esiste però** una modalità
      binaria ricostruita dalla comunità (ESPHome, cmd 0x0012 valore 0x0004) che
      trasmette 16 energie per-gate a 16 bit a 10 Hz — potenzialmente **migliore** del
      LD2410B per il respiro, perché non satura. Decisione da prendere: tentarla come
      esperimento dichiaratamente non ufficiale, o lasciarla fuori perimetro. Nel
      frattempo respiro e vitalità restano sul LD2410B
- [x] Identificazione PIR: HC-SR501 (foto + datasheet, `analisi/ANALISI_PIR.md` §6 completata)
- [x] Configurazione e test PIR HC-SR501 (Test 0.3, 19/07/2026) — pinout verificato
      GND|OUT|+Power (visto dal lato trimmer), **OUT→D34** (18/08/2026: D25 è ora RX2 del
      radar e D23 sta sul lato opposto della scheda; D34 è solo-input senza pull-up, ok
      perché l'HC-SR501 pilota attivamente l'uscita), **jumper su L** (creduto H
      fino al 22/08/2026),
      ritenuta al minimo (~3.4 s misurati), sensibilità a metà. Sketch:
      `firmware/test03_pir_base/`. Funziona: rileva/rilascia pulito, no falsi positivi

### Testing comparativo (obiettivo 3)
- [x] **PIR cablato su GPIO34** (18/08/2026) — non D23: sta sul lato opposto della scheda.
      GPIO34 è solo-input e senza pull-up, ma va bene perché l'HC-SR501 pilota
      attivamente l'uscita a 3.3V/0V
- [x] **PILOTA PIR vs mmWave riuscito (18/08/2026)** — `HLK-LD2410x/data/pir_vs_radar_T01.csv`,
      1699 campioni / 339.6 s. **È il risultato centrale della tesi, già misurato**:
      - **PIR: 80.4% di falsi negativi** sulla presenza reale (attivo in 254/1298 campioni);
        radar: 0%
      - tratto **immobile di 93.2 s continuativi a ~2.9 m**: radar presente nel **100%** dei
        campioni, PIR nello **0.2%** (1 campione su 466)
      - **zero falsi positivi** per entrambi in 80.2 s di stanza vuota
      - mappa gate↔distanza confermata al **98.3%** su 663 campioni (gate 0-7)
      - rumore di fondo riproducibile tra sessioni: gate0 max 27 (era 26), gate1 max 21
        (era 21) → i margini soglia↔rumore calcolati restano validi
- [~] *(SUPERATO dalla correzione qui sotto)* **Il PIR sbaglia anche con la persona IN MOVIMENTO (Test 1.2 a 1 m, 20/08/2026)**:
      cammino sul posto a 1 m, condizione teoricamente ideale per un PIR → **80.46 ± 6.22 %
      di falsi negativi**, praticamente identico al caso della persona ferma. In 62 s di
      cammino continuo ha emesso solo **1-4 impulsi** per trial, di durata 3.6-3.8 s.
      Spiegazione: il piroelettrico risponde al *transito* del flusso IR attraverso le zone
      della lente di Fresnel, non al movimento in sé — chi si muove *sul posto* non
      attraversa le zone. **Rilevantissimo per UPRISE**: una persona intrappolata si muove
      sul posto, non attraversa la stanza. È il caso peggiore per un PIR
- [x] **⚠️ CORREZIONE IMPORTANTE (22/08/2026): l'80.5% di falsi negativi del PIR con
      persona in movimento a 1 m era un artefatto della modalita' L.** Ripetuta la stessa
      serie con jumper su **H** (stesso movimento, stessa posizione, 5 trial):
      | configurazione | fn_PIR | pir_rate |
      | L (non ripetibile) | **80.46 ± 6.22 %** | 19.54 % |
      | H (repeat trigger) | **14.80 ± 11.52 %** | 85.20 % |
      Con il ritrigger attivo il PIR **rileva bene** una persona che si muove a 1 m.
      La frase "il PIR sbaglia anche con la persona in movimento" **non e' piu' sostenibile**
      cosi' com'e': va riferita esplicitamente alla configurazione L
- [x] **Controllo di comparabilita' fra le due serie, fatto col radar come testimone**:
      `menergy_media` 98.96 (L) vs 99.30 (H) e `mdist_dev_cm` 10.38 vs 10.40 → il movimento
      del soggetto e' stato riprodotto quasi identico. Resta uno scarto di ~4 cm sulla
      distanza media (99.5 vs 103.6 cm) dovuto al rimontaggio del setup fra le due serie:
      da dichiarare, ma non intacca il confronto sul PIR
- ⚠️ **Cosa resta valido e cosa no**:
      - **intatti** i due risultati portanti: persona **immobile** a 2.3 m (99.78% FN) e
        sotto il banco (99.90% FN). Li' il PIR non ha generato alcun trigger, e il jumper
        agisce solo *dopo* un trigger
      - **da rifare in H**: `sotto_banco_movimenti` (era 64.1% FN in L)
      - ✔ **verificato in H a 2 m (22/08/2026)**: `fn_PIR = 100.00 ± 0.00 %`, identico
        alla serie in L. Conferma sperimentalmente la deduzione — dove non ci sono trigger
        il jumper non cambia nulla — e la estende per deduzione a 3-5 m
- [x] 🎯 **ESPERIMENTO CENTRALE DELLA TESI (22/08/2026): a parita' di tutto, cambia solo
      il movimento.** A 1 m, jumper su **H** (configurazione migliore del PIR), stesso
      setup, stessa postura in piedi, 5 trial per condizione:
      | condizione | rilevamento PIR | fn PIR | fn radar |
      | cammino sul posto | **85.20 ± 11.52 %** | 14.80 % | 0.00 % |
      | **immobile** | **1.52 ± 1.03 %** | **98.48 %** | 0.00 % |
      Struttura degli impulsi: in movimento **6 impulsi da 14.1 s in media, fino a 29.8 s**
      (il ritrigger li concatena); da fermo **2 soli impulsi in 1000 s complessivi**.
      **Una sola variabile cambia fra le due righe.** Il fallimento del PIR non e' dovuto
      alla distanza (a 1 m funziona benissimo), ne' alla configurazione (e' in H), ne' alla
      taratura: e' dovuto **all'immobilita' del soggetto**. Il radar resta a 0.00% in
      entrambe le condizioni
- ⚠️ Effetto collaterale interessante sul **radar**: con soggetto fermo `menergy_media`
      scende da 99.3 a 68.6 e la dispersione della distanza sale da 10.4 a 21.3 cm. Il
      bersaglio immobile da' un ritorno piu' debole, quindi la stima di distanza e' piu'
      rumorosa — pur restando il rilevamento al 100%
- [x] 🎯 **La stessa dimostrazione nello scenario UPRISE reale (22/08/2026)**: persona
      sotto il banco a ~60 cm, jumper su **H**, 5 trial per condizione:
      | condizione | rilevamento PIR | fn PIR | fn radar |
      | con micro-movimenti | **96.52 ± 3.60 %** | 3.48 % | 0.00 % |
      | immobile (rifatto in H) | **1.32 ± 0.86 %** | **98.68 %** | 0.00 % |
      (la serie immobile in L dava 0.10% / 99.90%: il ritrigger allunga di poco i rari
      impulsi isolati, ma non cambia la sostanza. **Entrambe le righe sono ora in H**,
      quindi la coppia e' perfettamente appaiata)
      Il contrasto e' ancora piu' netto che a 1 m (96.5% contro 0.1%). A 60 cm il PIR e'
      un rilevatore di movimento quasi perfetto — e resta **completamente cieco** alla
      persona ferma
- 📌 **La tesi in tre frasi, come emerge dai dati**: (1) il PIR, configurato correttamente
      e entro ~1 m, e' un ottimo rilevatore di **movimento**; (2) e' praticamente cieco
      alla persona **immobile**, a qualunque distanza e in qualunque configurazione;
      (3) il radar mmWave rileva entrambe le condizioni al 100% in tutti i test svolti.
      Per UPRISE, dove la persona intrappolata puo' essere incosciente o esausta e quindi
      immobile, il PIR non e' adeguato e il mmWave e' necessario. **Non "il PIR e' scarso",
      ma "il PIR fa bene un lavoro che non e' questo"**
- ✔ **Residuo di comparabilita' CHIUSO (22/08/2026)**: rifatta anche `sotto_banco_immobile_H`.
      Le due coppie della tesi sono ora **entrambe interamente in modalita' H**, a due
      distanze diverse e in due geometrie diverse, e dicono la stessa cosa:
      | | movimento | immobile |
      | 1 m, in piedi | 85.20 % | 1.52 % |
      | 0.6 m, sotto il banco | 96.52 % | 1.32 % |
      Nessun asterisco da mettere in tesi
- [x] **Portata utile del PIR con movimento sul posto: sotto i 2 metri.** In modalità H
      (la piu' favorevole) rileva l'85.2% del tempo a 1 m e **lo 0.0% a 2 m**. Non e' un
      degrado graduale: fra 1 e 2 metri passa da "funziona bene" a "non vede niente".
      Con persona **immobile** e' cieco a ogni distanza
- 🚨 **NON generalizzare la riga precedente a "il PIR arriva a 2 m": e' FALSO, smentito
      dal Test 1.5 (29/08/2026).** Quel limite vale **soltanto** per il movimento *sul
      posto*. Con movimento di **attraversamento** lo stesso sensore, alla stessa
      sensibilita' e nella stessa configurazione, rileva fino a 5 m:
      | distanza | cammino sul posto | attraversamento |
      | 2 m | 0,0 % | **100,00 ± 0,00 %** |
      | 3 m | 0,0 % | **100,00 ± 0,00 %** |
      | 4 m | 0,0 % | **98,83 ± 2,02 %** |
      | 5 m | 0,0 % | **98,73 ± 1,94 %** |
      (3 trial per distanza, jumper H, trimmer a meta' corsa, radar `fn_radar_%` = 0,00
      in tutte e dodici le acquisizioni)
- 📌 **Formulazione corretta della caratterizzazione del PIR**: la variabile che decide
      se il PIR vede **non e' mai la distanza, e' il tipo di movimento**. La portata
      dichiarata di 3-7 m e' reale. A parita' di distanza — qualunque fra 2 e 5 m — si
      passa da 0 % a ~99 % cambiando solo la **direzione** del movimento. E' un
      esperimento a variabile singola piu' pulito di quello immobile-vs-movimento, dove
      cambiava la *quantita'* di movimento. Ed e' esattamente l'argomento che serve a
      UPRISE: la persona intrappolata si muove **sul posto**, che e' il caso cieco a ogni
      distanza
- ✔ **Il confondente "il trimmer di sensibilita' era troppo basso" e' CHIUSO** senza aver
      dovuto toccare il trimmer: un sensore che rileva un attraversamento a 5 m nel 98,7 %
      dei campioni non e' poco sensibile. Il trial facoltativo a sensibilita' massima
      previsto dal Test 1.5 **non serve piu'** — ed evitarlo protegge la comparabilita'
      di tutta la campagna
- ⚠️ **Conseguenza sulla Fase 8**: sul PIR non abbiamo ancora trovato il limite. La prova
      di portata massima va iniziata da **6 m**, non da 2
- ⚠️ **`errore_cm` dei file `attraversamento_*` NON e' utilizzabile** e resta fuori dalla
      regressione del Test 1.2: a 3 m e' passato da +9,5 a +19,2 cm fra due sessioni a
      pochi minuti di distanza. La spazzata trasversale (larghezza ~1 m) spiega solo
      **1-8 cm** secondo il calcolo geometrico, il resto non e' spiegato. In questo test
      la grandezza d'interesse e' `pir_rate_%`, non la distanza
- [x] 🔑 **A STIMOLO RADAR COSTANTE, IL TIPO DI MOVIMENTO DECIDE IL PIR (30/08/2026).**
      Quattro prove a 1 m nella stessa sessione, stessa stanza, stessa temperatura:
      | movimento | `menergy` (testimone radar) | PIR |
      | braccia, in piedi | 96,5 | **2,0 %** |
      | braccia, "corsetta" | 98,1 | 23,9 % |
      | braccia, seduto | 98,0 | 4,4 % |
      | **busto laterale, seduto** | 96,5 | **100,0 %** |
      **Per il radar sono lo stesso movimento** — energia fra 96,5 e 98,1, uno scarto di
      1,6 punti. Per il PIR vanno dal 2 % al 100 %.
      📌 **Non e' che un sensore sia piu' sensibile dell'altro: misurano due grandezze
      diverse.** Il radar misura la velocita' radiale; il PIR i **transiti attraverso le
      zone della lente di Fresnel**. Il movimento laterale del busto e' una traversata in
      miniatura e attraversa le zone; quello delle braccia resta dentro una zona sola.
      E' la dimostrazione piu' pulita del meccanismo finora, perche' il testimone radar
      certifica che la *quantita'* di movimento era costante e cambiava solo il suo
      **carattere** — piu' stringente della curva dose-risposta, dove variava la quantita'
- ⚠️ **Ipotesi TEMPERATURA sollevata e SMENTITA** (30/08/2026): davanti al 4,4 % avevo
      proposto che i 28 °C della stanza (contro i 25-27 di agosto) avessero azzerato il
      contrasto termico contro la superficie degli indumenti. **Falso**: stessa
      temperatura e stessa sessione, il solo cambio di movimento ha riportato il PIR al
      100 %. Il sensore non e' degradato. La prova termica vera resta da fare, ma va fatta
      **in piedi**, replicando esattamente `movimento_1m_H`, altrimenti misura la postura
- ⚠️ **Nel confrontare serie del PIR, la postura e' una variabile al pari della
      distanza**: seduto con le braccia e in piedi camminando sul posto **non sono lo
      stesso stimolo**, anche se il radar li registra identici. Annotare sempre la postura
- ⚠️ **Non mescolare le serie `_H` con quelle originali nella regressione della distanza**:
      il setup e' stato smontato e rimontato, e il sensore risulta spostato di ~4-7 cm
      (errore a 2 m: +11.22 cm nella serie originale, +18.68 cm in quella nuova). La retta
      `misurata = 1.0381 x reale - 1.32` resta quella dei 25 trial originali
- [x] **Durata degli impulsi PIR: 183 impulsi su tre sessioni, TUTTI fra 3.4 e 3.8 s**
      (153 solo nello scenario "sotto banco con movimenti", dev.std 0.09 s, **zero impulsi
      oltre 5 s**). Prova definitiva che l'uscita è un monostabile a durata fissa: non si
      allunga nemmeno con movimento continuo. Il PIR non misura presenza né durata del
      movimento, **conta eventi** — e il suo apparente "tasso di rilevamento" è il prodotto
      fra numero di eventi e tempo di ritenuta impostato col trimmer
- [x] **Il jumper H/L FUNZIONA, e tutta la fase 1 era in L (22/08/2026).**
      Il ponticello era sui due pin lato "L". Spostandolo su "H" e ripetendo la prova della
      mano: **un unico impulso continuo di >= 9.2 s**, ancora alto a fine acquisizione,
      contro i 3.4-3.8 s di tutti i 196 impulsi precedenti. Il ritrigger e' reale.
      ⚠️ Due errori miei corretti qui: (a) avevo concluso che il jumper fosse inerte, ma le
      due prove precedenti erano state fatte fra due posizioni entrambe non-H;
      (b) `impulsi_pir()` scartava gli impulsi **troncati** dai bordi della finestra, cioe'
      proprio quelli lunghi: su questo file riportava "nessun impulso" mentre conteneva la
      prova. Ora i troncati sono riportati a parte con il loro limite inferiore
- ⚠️ **Conseguenza sui dati della fase 1: tutti acquisiti in modalita' L.** Va dichiarato.
      Cosa ne risente:
      - **niente** su stanza vuota, immobile a 2.3 m, sotto banco immobile, movimento a
        2-5 m: il PIR ha prodotto zero o pochissimi eventi **isolati**, e il ritrigger non
        puo' allungare un impulso che non esiste o che non riceve un secondo trigger entro
        3.5 s. I due risultati portanti (99.78% e 99.90% di falsi negativi) sono intatti
      - **solo** `movimento_1m` (80.5% FN) e `sotto_banco_movimenti` (64.1% FN) vanno
        rifatti in H: sono gli unici scenari con eventi ripetuti durante movimento continuo
- ⚠️ **Nota operativa**: dopo aver tolto e rimesso l'USB il PIR resta cieco per ~60 s
      (stabilizzazione). Nella verifica del jumper il primo impulso e' arrivato a t=33 s
      benche' il movimento fosse continuo dall'inizio: non era un guasto
- ⚠️ **Come va interpretato l'80.4%**: dipende dal trimmer di ritenuta, che teniamo al
      minimo. Il PIR ha prodotto **14 impulsi di durata costante 3.4-3.6 s** invece di un
      segnale continuo: la sua uscita è un **monostabile a durata fissa** (ritenuta), non una
      misura di presenza. Con la ritenuta al massimo il PIR *sembrerebbe* rilevare molto di
      più, ma starebbe solo trattenendo l'ultimo evento. Il dato robusto e non contestabile
      è l'altro: nei 93 s di immobilità il PIR **non ha rilevato alcun evento di movimento**
- [x] **Il cavo blu (OUT) è definitivamente inutile**: `out_level` letto dal frame UART
      coincide con `radar_presence` in **1699/1699** campioni. Utile anche per UPRISE: un
      dispositivo che vuole solo la presenza binaria può usare il solo pin OUT senza UART
- [x] **Il sensore di luce funziona**: `light_level` 21-29 di giorno e **0-1 di notte**
      (sessione 6.5 h del 20-21/08/2026), nonostante il comando 0x01AE (config ausiliaria)
      non risponda. I due fatti sono indipendenti: il valore fotosensibile viaggia nel
      frame di engineering mode e segue davvero l'illuminazione ambientale
- [x] **Falsi positivi: limite 95% ≤ 0.43 eventi/h** (20-21/08/2026) — 6.55 h di stanza
      vuota notturna + 29 min diurni, **zero eventi** per radar e PIR. Con zero eventi non
      si può scrivere "0 eventi/h": si riporta il limite superiore, che dipende dal tempo
      di osservazione (regola del tre, 3/T)
- [x] **Rumore di fondo stabile su 6.5 h**: gate0 media 17.4 → 17.8, gate1 13.3 → 13.1 tra
      prima e seconda metà della notte; massimo gate0 = 34 contro soglia 50. Conferma su
      tempi lunghi la decisione di non ricalibrare le soglie
- [x] Protocollo di test definito — `PIANO_TEST.md`, fasi 0-8 con metriche e comandi
- [x] **TEST 1.3 COMPLETATO (18/08/2026, 27 °C) — il risultato centrale della tesi**.
      5 trial × 302 s puliti, soggetto immobile a 2.30 m, ground truth dichiarata
      dall'operatore via `acquire.py` (`data/fermo_seduto_T01..T05.csv`):
      - **falsi negativi PIR: 99.78 ± 0.49 %** — su 4 trial su 5 è **100.0%**, cioè zero
        rilevamenti in 5 minuti con una persona viva a 2.3 m
      - **falsi negativi radar: 0.00 ± 0.00 %** — presenza rilevata nel 100% dei 7554 campioni
      - distanza: **229.78 ± 2.38 cm** tra trial, con stabilità **entro** il trial di
        1.48 ± 0.77 cm → la variabilità di come il soggetto si siede (~2.4 cm) è maggiore
        di quella del sensore (~1.5 cm): scomposizione utile al capitolo sull'accuratezza
- [x] **TEST 1.2 COMPLETATO 1-5 m (20/08/2026, 25 trial)** — accuratezza della distanza,
      `data/movimento_{1,2,3,4,5}m_T01..T05.csv`:
      - **regressione: misurata = 1.0381 × reale − 1.32 cm, R² = 0.99965**. Il radar è
        quindi **estremamente lineare** ma ha un errore di **scala del +3.81%**, con offset
        praticamente nullo. Residui dalla retta ≤ 4.9 cm su tutto il range
      - conseguenza pratica: l'errore grezzo cresce con la distanza (−0.5 cm a 1 m,
        +18.2 cm a 5 m = 3.6%), ma è **correggibile con un solo coefficiente**: dividendo
        per 1.0381 l'errore residuo scende sotto i 5 cm a tutte le distanze
      - ⚠️ la **causa** del +3.81% non è attribuibile con questi dati: può essere la
        calibrazione interna del modulo o il riferimento con cui è stato misurato il
        pavimento. Servirebbe un riferimento di distanza indipendente (metro laser)
      - dispersione **entro** il trial 10-26 cm: è l'oscillazione del busto camminando sul
        posto, non rumore del sensore (da seduto fermo era 1.5 cm)
      - energia media del bersaglio: 99 → 85 → 54 → 35 → 28 da 1 a 5 m. Il decadimento è
        molto più lento di 1/D⁴: **non** interpretarlo con l'equazione del radar, è un
        valore normalizzato 0-100 con elaborazione interna
      - **PIR: 0.0% di rilevamento a 2, 3, 4 e 5 m** — 20 trial, tutti al 100% di falsi
        negativi, con soggetto in movimento continuo. Rileva qualcosa solo a 1 m (19.5%)
      - ⚠️ **Range coperto: 1-5 m**, non 6. Limite della stanza disponibile, non del
        sensore. Da dichiarare in tesi come perimetro sperimentale: la retta di
        regressione è costruita su 5 punti e 25 trial, e l'extrapolazione dell'energia
        (~27 a 6 m contro soglia 15) indica che il sensore avrebbe funzionato anche là.
        Per lo scenario UPRISE il limite è irrilevante: la distanza d'interesse è
        **sotto il metro** (persona sotto il banco), coperta dal Test 1.4
- [x] **TEST 1.4 — persona sotto il banco, scenario immobile COMPLETATO (22/08/2026)**.
      5 trial x 302 s, soggetto rannicchiato a ~50 cm, sensore fissato sotto il piano:
      - **fn_PIR = 99.90 ± 0.22 %, fn_radar = 0.00 ± 0.00 %** → nello scenario reale del
        progetto il radar vede la persona sempre, il PIR praticamente mai. È il risultato
        che giustifica la tesi
      - distanza 62.7 ± 4.2 cm, dispersione entro trial 13-14 cm: **~9x peggio** che da
        seduto a 2.3 m (1.5 cm). Sotto l'arredo il radar **rileva benissimo ma localizza
        male** — irrilevante per UPRISE, dove serve sapere *se* c'è qualcuno
      - `senergy_gate0/1` = 0 come atteso, ma la presenza è portata dai **gate 2-3**
        benché il bersaglio sia a ~60 cm: la distribuzione per-gate dello stazionario non
        corrisponde alla distanza riportata. Osservazione aperta, verosimilmente cammini
        multipli sotto il piano
      - **respiro estraibile in 4 trial su 5**: 21.0 ± 2.5 atti/min dai canali moving.
        Più alto e più disperso che da seduto (18-20), plausibile per postura rannicchiata
      - **analisi di sensibilità alle soglie** (T04 era l'unico fallimento): abbassando la
        soglia di accettazione da SNR>3 a SNR>2.5 si recuperano **5 trial su 5**, e le
        stime dei quattro trial già validi restano **identiche** (17.9 / 20.9 / 23.9 / 21.4).
        Cambia solo l'aggregato: 21.9 ± 2.9 invece di 21.0 ± 2.5. Il segnale in T04 c'era
        (9 canali moving su 10 fra 22 e 27.5 atti/min): a scartarlo era la soglia, non il
        sensore. **Nella tesi va dichiarato il criterio usato e riportata questa sensibilità**
- ⚠️ **Correzione metodologica sul criterio di consenso del respiro** (22/08/2026): scegliere
      il *gruppo più numeroso* di canali concordi premiava sistematicamente l'artefatto
      stazionario a ~6-7 atti/min, che è compatto perché sistematico. `analizza_respiro.py`
      ora riporta **tutti** i gruppi con la loro composizione (moving/stazionari) e segnala
      quelli implausibili; la stima aggregata usa i **soli canali moving**
- [x] **TEST 2.1 COMPLETATO (23/08/2026) — latenza di rilevamento all'ingresso.**
      10 trial, evento a 30 s annunciato a voce da `acquire.py --beep-at --evento entra`;
      tutti e 10 validi (`pre_radar_%` = `pre_pir_%` = 0.00):
      | | latenza |
      | radar | **5.36 ± 0.30 s** |
      | PIR | **5.96 ± 0.31 s** |
      | differenza appaiata radar-PIR | **-0.60 ± 0.35 s** |
      - **Il radar rileva per primo in 10 trial su 10.** Errore standard della media 0.11 s,
        cioe' il vantaggio e' 5.4 volte l'incertezza; test dei segni 10/10, p ~ 0.002
      - ⚠️ Le latenze **assolute** (~5-6 s) sono dominate dal tragitto di rientro e dal tempo
        di reazione all'annuncio: vanno dichiarate come **latenza operativa**, limite
        superiore di quella del sensore. La grandezza pulita e' la differenza appaiata,
        dove tragitto e reazione si cancellano perche' identici per i due sensori
      - ⚠️ **Previsione smentita**: si era ipotizzato che qui il PIR andasse alla pari o
        meglio, perche' attraversare una porta e' lo stimolo per cui la lente di Fresnel e'
        progettata. Non e' andata cosi'. Spiegazione plausibile (da verificare, non
        dimostrata): il radar ha 6 m di portata e aggancia il soggetto mentre e' ancora in
        avvicinamento, mentre il PIR richiede che il flusso IR attraversi le zone della
        lente, cosa che avviene piu' tardi e piu' vicino
- ⚠️ **Il LD2410B rileva oltre i ±60° dichiarati, di lato** (osservato il 23/08/2026
      preparando il 2.1): mettendosi **di lato-dietro** rispetto al modulo il PIR non vedeva
      nulla (`pre_pir_%` = 0) mentre il radar rilevava al 100%. **Precisazione del soggetto
      che ha eseguito la prova: non era esattamente dietro, ma lateralmente arretrato**;
      dietro in asse il radar non lo vedeva.
      ⚠️ Quindi il dato accertato e' che **la copertura eccede il lobo principale sui lati**,
      non che il modulo sia omnidirezionale. Il comportamento esattamente alle spalle NON e'
      stato misurato: e' un'osservazione qualitativa, non una caratterizzazione.
      **Rilevante per il Test 2.4**: se la copertura laterale supera i ±60°, un sensore sotto
      un banco puo' vedere la persona sotto il banco **accanto**, e ridurre il gate massimo
      (che limita la distanza, non l'angolo) non basta a isolarli. Servirebbe una misura
      angolare dedicata prima di concludere
- [x] ✅ **MISURA ANGOLARE FATTA (30/08/2026, 01:00-03:10, 28 °C) — l'osservazione
      qualitativa era corretta.** Soggetto **seduto** su arco di raggio 100 cm, sedia
      orientata verso il sensore a ogni azimut (cosi' il bersaglio presenta sempre la
      stessa faccia e resta l'angolo come unica variabile), oscillazione **laterale** del
      busto, gate massimo 2:
      | azimut | radar | PIR | energia radar |
      | 0° | **100 %** | 100,0 % | 96,5 |
      | 45° | **100 %** | 77,7 ± 38,6 % | 95,3 |
      | 60° | **100 %** | 67,8 ± 16,7 % | 95,7 |
      | 75° | **100 %** | 76,7 ± 32,8 % | 94,1 |
      | 90° | **100 %** | 12,0 ± 10,1 % | 94,3 |
      | 120° | **6,6 ± 11,4 %** | 0,0 % | 59,6 |
      **Il radar copre almeno ±90°**, con l'energia che cala di appena 2 punti fra asse e
      90°; il crollo sta fra 90 e 120°. La copertura **eccede nettamente i ±60°** del
      diagramma di p.11 del manuale
- 🚨 **CONSEGUENZA: la selettivita' spaziale per configurazione NON e' ottenibile.**
      Incrociando `angolo_090` con `sel_laterale_1m` (stessa distanza, stesso angolo,
      stesso gate 2):
      | vicino a 1 m, 90° | rilevato |
      | **fermo** | 0 % (a regime) |
      | **in movimento** | **100 %** |
      Quello che nel Test 2.4 sembrava selettivita' era la **debolezza dell'eco di un
      bersaglio immobile**, non il diagramma di irradiazione. Ridurre il gate non protegge
      perche' limita la distanza e non l'angolo. Per UPRISE: **un banco vuoto accanto a una
      persona che si muove risulta occupato** → la separazione fra arredi adiacenti va
      cercata nel **montaggio fisico** (orientamento verso il basso, schermatura del lobo
      laterale), non nei parametri del modulo. Il paragrafo del cap. 4 §selettivita' e'
      stato corretto di conseguenza
- ⚠️ **Il PIR ha un campo piu' stretto, ma soprattutto NON e' ripetibile**: fra 45 e 75°
      la dispersione fra trial e' dello stesso ordine dell'effetto (a 45°: 100/100/33 %;
      a 75°: 39/91/100 %). In quell'intervallo l'andamento angolare **non e' risolvibile**.
      Sostenibili solo i tre estremi: 100 % sull'asse, collasso a 90°, zero a 120°.
      E' la **terza occorrenza indipendente** della stessa irripetibilita' dopo la zona
      grigia dei micro-movimenti (±21,7 su 51,6)
- ⚠️ **La distanza fuori asse e' sottostimata**: 108 / 107 / 95 / 94 / 85 cm da 0 a 90°,
      con il soggetto sempre sull'arco a raggio 100 cm. Verosimilmente il modulo aggancia
      la porzione di corpo piu' vicina invece del centro di massa
- [x] **TEST 2.2 COMPLETATO (23/08/2026) — latenza di rilascio all'uscita.** 5 trial,
      evento a 30 s (`--evento esci`), tutti e 5 misurati:
      | | tempo di rilascio |
      | radar | **18.36 ± 0.54 s** |
      | PIR | **12.96 ± 1.40 s** |
      | riaccensioni | **0** per entrambi |
      - il radar impiega **5.4 s in piu'** del PIR a dichiarare la stanza vuota. Effetto
        enorme rispetto alla dispersione: **8.0 sigma gia' con 5 trial** (nel 2.1 servivano
        10 trial perche' l'effetto era 0.60 s contro una dispersione di 0.35)
      - **zero riaccensioni**: rilascio netto in tutti i trial, a differenza del bersaglio
        fantasma in decadimento visto nel Test 0.2
      - 🔎 **Stima della coda propria del radar, usando il PIR come cronometro**: il PIR si
        spegne 3.5 s dopo l'ultimo trigger (196 impulsi, dev.std 0.09 s), quindi il tempo di
        uscita dal campo e' ~12.96 - 3.5 = **9.5 s** e la coda del radar ~18.36 - 9.5 =
        **≈ 8.9 s**, contro i **5 s** di timeout letti via UART. ⚠️ E' una stima: i due
        sensori hanno campi diversi, quindi i rispettivi istanti di "uscita" non coincidono
        esattamente. Ma concorda con i ~10 s del Test 0.2 e i ~12 s di un trial preliminare
      - 📌 **Il parametro dichiarato non descrive il comportamento osservato**: tre
        osservazioni indipendenti danno 9-12 s contro i 5 s configurati. Per UPRISE
        significa che una stanza appena svuotata risulta occupata per quasi 10 s
- [x] 🎯 **TEST 2.3 COMPLETATO (23/08/2026) — la curva dose-risposta del PIR.** A 1 m, in
      piedi, jumper H, stesso setup per tutte e tre le condizioni: cambia solo la quantita'
      di movimento.
      | condizione | rilevamento PIR | dev.std | dev. relativa | radar |
      | immobile | **1.52 %** | ±1.03 | 68% | 100 % |
      | micro-movimenti | **51.60 %** | ±21.72 | **42%** | 100 % |
      | cammino sul posto | **85.20 %** | ±11.52 | 13% | 100 % |
      - il PIR e' **monotono** con la quantita' di movimento, il radar resta al 100% ovunque
      - ⚠️ **La dispersione esplode nella zona intermedia**: ±21.72 su 51.60. Vicino alla
        soglia il PIR non e' solo meno sensibile, e' **imprevedibile** — due trial identici
        per l'operatore danno risultati molto diversi. Per un'applicazione salvavita
        l'imprevedibilita' e' peggio di un limite noto e dichiarato
- [x] 🔑 **Il radar fornisce due indicatori GRADUATI del movimento** (rilevante per
      l'obiettivo 6, indice di vitalita'): sulle tre condizioni entrambi sono monotoni
      | | immobile | micro | cammino |
      | `menergy_media` | 68.6 | 84.4 | 99.3 |
      | `mdist_dev_cm` | 21.3 | 16.4 | 10.4 |
      L'energia cresce col movimento; la dispersione della distanza cala perche' un eco piu'
      forte da' una stima piu' stabile. **Sono due grandezze continue, non binarie**: e'
      esattamente la base che serve all'indice di vitalita', e ora e' misurata su tre livelli
      di movimento a geometria costante invece che ipotizzata
- [x] **La regola `portata = gate x 75 cm` e' DOCUMENTATA dal costruttore** (verificato
      23/08/2026, manuale V1.04 §5.2 p.8): *"Including the farthest door for motion detection
      and the farthest door for static detection, the setting range is 1 to 8. For example,
      if the farthest door is set to 2, only if there is a human body within 1.5m will it
      effectively detect and output the result."* La nostra misura (gate 2 -> 150 cm) coincide
      esattamente con l'esempio del manuale. Quindi:
      | gate max | portata | fonte |
      | 2 | 150 cm | manuale V1.04 p.8 + misurato |
      | 1 | 75 cm | regola del manuale + misurato |
      | 8 (fabbrica) | **600 cm** | regola del manuale; i 675 di `getRange_cm()` sono errati |
- 🔑 **La contraddizione sul range configurabile e' INTERNA al protocollo** (accertato
      29/08/2026 estraendo il testo dei PDF con `pypdf`; la stesura precedente, che la
      descriveva come "manuale contro protocollo", era incompleta):
      | fonte | range dichiarato |
      |---|---|
      | Protocollo **p.5, §1.2.2** *The role of configuration parameters* | *"the range can be set **from 1 to 8**"* |
      | Protocollo **p.8, §2.2.3** *Maximum distance gate…command* (cmd 0x0060) | *"(configuration range **2~8**)"* |
      | Manuale V1.04 p.8, §5.2 (stesso titolo di sezione) | *"the setting range is **1 to 8**"* |
      Il paragrafo del manuale §5.2 e' lo **stesso testo copiaincollato** del §1.2.2 del
      protocollo (quest'ultimo aggiunge solo l'inciso sulla risoluzione 0.2/0.75 m).
      Quindi non ci sono due documenti che divergono: c'e' **un paragrafo descrittivo
      duplicato in due file** contro **una parentesi nella specifica del comando**
- 🚫 **L'argomento della recenza non ha oggetto**: le due frasi stanno nello stesso
      documento, nella stessa versione, a tre pagine di distanza — non sono ordinabili
      per data. In tesi **non** scrivere ne' "una versione precedente lo permetteva" ne'
      "i due documenti divergono": citare la **contraddizione interna** e il dato misurato
- ⚖️ **Come pesare le due letture**: a favore di 1-8 ci sono due sezioni descrittive,
      l'esempio numerico *"if the farthest door is set to 2, only… within 1.5m"* presente
      in entrambe e **coincidente con la nostra misura** (gate 2 → 150 cm), e gate 1 che
      da' esattamente i 75 cm previsti dalla regola. A favore di 2~8 c'e' la sola
      parentesi di §2.2.3 — che pero' e' la sezione **normativa** per "quale valore posso
      scrivere via UART". Gate 0 e' escluso da tutte e tre le formulazioni ed e' quello
      che sul nostro esemplare si e' rotto (distanza fissa 72 cm, presenza sempre 1)
- ⚠️ **"Il modulo lo ha accettato" non prova nulla da solo: il firmware non valida
      l'input.** Gate 0 e' stato accettato senza errore e ha prodotto comportamento rotto.
      Prova qualcosa solo la *differenza*: gate 0 accettato e **sbagliato**, gate 1
      accettato e **conforme alla regola documentata**. Impostazione completa e paragrafo
      gia' redatto in `PIANO_TEST.md`, Test 2.4, blocco "Gate 1"
- [x] **Le soglie di fabbrica lette via UART coincidono con la Tabella 7 del protocollo
      V1.07 (p.13)**, valore per valore: movimento 50 50 40 30 20 15 15 15 15 (gate 0-8),
      stazionario 40 40 30 30 20 20 20 (gate 2-8).
      La tabella ha due colonne distinte, e vanno tenute separate:
      | | gate 0 | gate 1 | gate 2-8 |
      | *Motion Sensitivity* | **50** | **50** | 40 40 30 30 20 20 20 |
      | *Rest Sensitivity* | `-(cannot be set)` | `-(cannot be set)` | 40 40 30 30 20 20 20 |
      Quindi la sensibilita' di **movimento** dei gate 0 e 1 vale 50 ed e' impostabile; e'
      la sola sensibilita' **Rest** (stazionaria) che il documento riporta come non
      impostabile per quei due gate. Questo spiega perche' `senergy_gate0` e `senergy_gate1`
      risultino sempre 0 nei nostri dati: il canale stazionario non e' configurabile sotto
      1.5 m. E' una spiegazione coerente col documento, non una citazione di una frase che
      dica esplicitamente "il canale non esiste"
- [x] 🔑 **TEST 2.5 COMPLETATO (24/08/2026) — il LD2410B riporta DUE persone insieme, una
      per canale.** 3 trial x 102 s utili, A ferma a 2 m e B che cammina a 4 m, sfalsate di
      ~50 cm di lato per evitare l'ombra reciproca:
      | canale | mediana | corrisponde a |
      | stazionario | **212 cm** | A, ferma a 2 m |
      | moving | **389 cm** | B, in movimento a 4 m |
      - **entrambi i canali attivi contemporaneamente nel 79.2% dei campioni** (1452/1833),
        con separazione di 177 cm fra le due distanze riportate
      - `menergy_media` = 38.4, coerente col valore misurato a 4 m nel Test 1.2 (35.1):
        conferma indipendente che il canale moving stava inseguendo la persona lontana
      - `senergy` saturo a 100, coerente con un bersaglio fermo a 2 m
      📌 **Il limite del sensore va riformulato**: non e' "riporta un solo bersaglio", ma
      **"riporta un bersaglio per canale"**. Separa bene due persone in **stati diversi**;
      con due nello **stesso stato** la separazione degrada ma non si annulla — vedi la
      quantificazione nel blocco successivo, che corregge questa frase. E' un paragrafo migliore per il capitolo sui limiti, e ha una conseguenza
      pratica per UPRISE: sotto due banchi vicini, una persona ferma e una che si muove
      verrebbero contate entrambe; due ferme no
- ⚠️ Precisazione sul metodo: le due persone erano **sfalsate lateralmente di ~50 cm**
      (14° fuori asse a 2 m, 7° a 4 m: entrambe dentro i ±60° del diagramma di p.11 del
      manuale). In fila una dietro l'altra il corpo davanti fa da schermo e il test non
      distinguerebbe "non separa i bersagli" da "il secondo era in ombra"
- [x] 🔑 **Variante IN FILA del Test 2.5 (24/08/2026): un corpo ne nasconde completamente
      un altro.** Stesse distanze (A ferma a 2 m, B cammina a 4 m) ma allineate sull'asse
      del sensore, B esattamente dietro A. Confronto con il caso sfalsato:
      | | sfalsate di lato | in fila |
      | entrambi i canali attivi | 79.2 % | **42.4 %** |
      | distanza stazionaria | 212 cm | 215 cm |
      | distanza moving | **389 cm** | **215 cm** |
      | differenza fra le due (mediana) | 176 cm | **3 cm** |
      | differenza < 30 cm | 12 % | **99 %** |
      | `menergy_media` | 38.4 | 58.1 |
      | `mdist_dev_cm` | 49.1 | 14.2 |
      - in fila i due canali riportano **lo stesso bersaglio**: la persona dietro non e'
        riportata in nessuna forma. Energia piu' alta e dispersione piu' bassa confermano
        che il radar ha agganciato saldamente un solo bersaglio vicino
      - ⚠️ **`radar_rate_%` resta 100 % in entrambe le geometrie**: il radar non sbaglia mai
        a dire "c'e' qualcuno". Quello che perde e' il **conteggio**, non la presenza
      📌 **Conseguenza per UPRISE**: un singolo sensore non puo' censire piu' persone in
      una stanza — chi sta dietro a qualcun altro e' invisibile. Questo **rafforza**
      l'architettura del progetto (un sensore per banco, ciascuno che guarda il proprio
      occupante) invece di indebolirla: e' un limite che l'architettura distribuita gia'
      aggira. Ma va dichiarato, perche' esclude l'uso di un sensore singolo come contatore
      di presenze in aula
- [x] 🔑 **Capacita' di separare due persone: quantificata su tre geometrie (24/08/2026).**
      Controllo preliminare superato: B **da sola** ferma a 4 m e' rilevata al 100% con
      distanza 388.9 ± 3.7 cm ed energia stazionaria 99.3 — quindi il confondente "non vede
      una ferma a 4 m" e' escluso.
      | scenario | entrambi i canali | B riportata |
      | B cammina, sfalsate di lato | 79.2 % | **73.8 %** |
      | entrambe ferme, sfalsate | 21.2 % | **19.6 %** |
      | B cammina, in fila dietro A | 42.4 % | **0.4 %** |
      - ⚠️ **Correzione di un'affermazione precedente**: avevo scritto che due persone nello
        stesso stato "non vengono separate". E' **troppo assoluto**: con entrambe ferme B
        compare comunque nel 19.6% dei campioni — nel 7% sul canale stazionario e per il
        resto sul canale moving, quando i suoi micro-movimenti involontari la registrano
      - il meccanismo: **i due canali SONO lo strumento di separazione**. Funzionano quando
        le due persone sono in stati diversi; con entrambe ferme competono per lo stesso
        canale e **la piu' vicina vince nel 92.3% dei campioni** (istogramma delle distanze
        stazionarie: 92.3% nella banda di A, 7.2% in quella di B)
      - la dispersione lo conferma: `sdist_dev` passa da 3.7 cm (una sola persona ferma) a
        40.9 cm (due ferme) — non e' rumore, sono le escursioni verso il bersaglio lontano
      📌 **Il caso peggiore non e' "due ferme" ma "in fila"**: 0.4% contro 19.6%. Una persona
      dietro un'altra e' praticamente invisibile; una ferma accanto a un'altra ferma e'
      intermittente. In entrambi i casi `radar_rate_%` resta 100%: si perde il conteggio,
      mai la presenza
- [x] **Il vicino laterale NON sporca la lettura del proprio occupante (24/08/2026).**
      Gate massimo 2 (portata 150 cm), occupante fermo a 1 m sull'asse, vicino fermo a 1 m
      **perpendicolare** all'asse. Confronto appaiato con lo stesso soggetto nella stessa
      posizione, 3 trial per scenario:
      | grandezza | da solo | con vicino | significativita' |
      | `sdist_media_cm` | 102.37 | 106.93 | 1.1 sigma |
      | `sdist_dev_cm` | 14.47 | 16.07 | 1.7 sigma |
      | `mdist_media_cm` | 101.73 | 105.70 | 0.9 sigma |
      | `menergy_media` | 87.73 | 83.87 | 2.0 sigma |
      Nessuna differenza supera le 2 sigma con 3 trial: la perturbazione e' al piu' di
      pochi cm. `radar_rate_%` resta 100% in entrambi i casi
- 🔎 **Il confronto con il caso a 2+4 m indica che conta l'ANGOLO, non la distanza**: la
      dispersione della distanza era passata da 3.7 a 40.9 cm con due persone sfalsate di
      soli 50 cm (14° e 7° fuori asse, entrambe in pieno lobo), mentre qui passa da 14.5 a
      16.1 cm con il secondo corpo a **90°**. Un bersaglio molto fuori asse e' attenuato dal
      diagramma di irradiazione e non compete con l'occupante che satura il canale.
      ⚠️ Da questi dati **non** si puo' concludere che il radar non veda il vicino a 90°:
      con l'occupante presente e saturo un eco debole sarebbe mascherato comunque. Lo
      decide lo scenario `sel_laterale_1m`, con il solo vicino presente
- [x] 🔑 **Domanda chiusa (25/08/2026): a regime il radar NON riporta il vicino a 90°.**
      Rileggendo `sel_laterale_1m` nel tempo invece che come media: in tutti e 3 i trial
      il radar è attivo **dall'istante zero**, si spegne **una sola volta** (dopo 65,6 /
      29,4 / 100,8 s) e **non si riaccende mai più** nei restanti 100-170 s, con una
      persona viva a 1 m. Zero fronti di salita in tutti i trial.
      ⚠️ Quindi il **24,83 ± 19,55 %** calcolato con lo scarto standard di 20 s **non è
      un rilevamento**: è la coda di presenza residua dalla fase di posizionamento che
      decade. Scartando 120 s (oltre la coda più lunga) il quadro è netto:
      | scenario (gate max 2) | finestra std. 20 s | a regime 120 s |
      | occupante 1 m sull'asse | 100,00 % | **100,00 %** |
      | persona a 3 m sull'asse | 0,00 % | **0,00 %** |
      | persona a 1 m a 90° | 24,83 % | **0,00 %** |
      | occupante + vicino a 90° | 100,00 % | **100,00 %** |
- ⚠️ **Osservazione metodologica generale**: il transitorio di 20 s adottato negli altri
      scenari **non basta** in quelli di selettività, dove la coda dal posizionamento
      supera i 100 s. La deviazione standard enorme rispetto alla media (±19,55 su 24,83)
      era il primo indizio. **Negli scenari di selettività usare `--salta-inizio 120`**
- ⚠️ **Resta aperto**: in scenari 3 e 4 il vicino era **fermo**. Il vicino **in
      movimento** a 90° non è stato provato, ed è il caso in cui il canale moving —
      libero — potrebbe agganciarlo (è proprio il meccanismo visto in `due_persone`).
      Prima estensione da fare su questo scenario
- 📌 **Convenzioni di scarto del transitorio, ricostruite e da usare sempre** (riproducono
      esattamente i numeri del registro): **20 s** negli scenari ordinari, **40 s** sotto
      il banco (il soggetto deve anche posizionarsi), **120 s** negli scenari di
      selettività. Con scarto sbagliato i numeri non coincidono con quelli pubblicati
- [x] 🎯 **TEST 2.4 COMPLETATO (24/08/2026) — con gate massimo 2 la selettivita' spaziale
      FUNZIONA, ma solo sul vicino immobile.** Portata tagliata a 150 cm, tutti gli scenari
      con soggetto fermo, 3 trial ciascuno:
      | scenario | `radar_rate_%` finestra intera | in regime (dopo 120 s) |
      | occupante a 1 m sull'asse | **100 %** | 100 % |
      | persona a 3 m sull'asse (oltre il taglio) | **0 %** | 0 % |
      | persona a 1 m **di lato** (90°) | 24.8 ± 19.6 % | **0 %** |
      - il **gate taglia davvero**: a 3 m zero rilevamenti, nemmeno un campione
      - il vicino a 90° **non viene rilevato da fermo**: il 24.8% della finestra intera e'
        interamente il **transitorio d'ingresso** (un unico tratto continuo da t=0, mai un
        fronte di salita successivo). Il diagramma di irradiazione fa il lavoro che il gate
        non puo' fare, perche' il gate limita la distanza e non l'angolo
- ⚠️ **Due limiti da dichiarare, entrambi importanti per UPRISE**:
      1. la selettivita' vale per un vicino **immobile**. Mentre si muove viene rilevato
         eccome: e' proprio il transitorio a produrre quel 24.8%
      2. la coda dopo che il vicino si ferma e' durata **29, 66 e 101 s** nei tre trial —
         molto piu' dei ~9 s di coda misurati nel Test 2.2. Il radar tiene agganciato un
         bersaglio laterale fermo per decine di secondi prima di perderlo. Quindi un banco
         vuoto puo' risultare occupato fino a un minuto e mezzo dopo che qualcuno gli e'
         passato accanto
- ⚠️ **Lezione metodologica**: `--salta-inizio 20` non bastava. Negli scenari dove il
      soggetto deve raggiungere una posizione, la finestra da scartare va dimensionata sulla
      **coda del radar**, non sul tempo di spostamento. Qui servivano 120 s. Il sintomo che
      lo rivela e' `fp_radar_eventi_h = 0` insieme a `radar_rate_%` alto: nessun fronte di
      salita significa che la presenza era gia' attiva all'inizio della finestra
- [x] **Test comparativo PIR vs mmWave con numeri** — fasi 1, 2, 3 e 5 complete
- [x] 🎯 **FASE 3 COMPLETATA (30/08/2026) — il radar attraversa tutto tranne il metallo,
      il PIR e' bloccato da tutto.** Baseline mediata sui 6 trial di inizio e fine
      (**53,45 ± 3,58**; vedi sotto perche' va mediata), soggetto in movimento sul posto,
      pannello a 20 cm dal sensore:
      | materiale | spessore | copertura | attenuazione radar | PIR a 1 m |
      | nessuno | — | — | — | **79,6 %** |
      | plastica (tanica cava) | 2x5 mm + aria | ±42° | **-7,5 %** | 0 % |
      | cartone (scatola) | 2x5 mm + aria | ±54° | **-17,2 %** | 0 % |
      | vetroresina | **1 mm** | ±70° | **-19,6 %** | 0 % |
      | vetro | 5 mm | ±61° | **-40,9 %** | ~0 % |
      | legno | 10 mm | ±54° | **-41,6 %** | ~0 % |
      | metallo | 1 mm | ±50° | **blocca del tutto** | 0 % |
      `radar_rate_%` resta **100 %** con tutti i dielettrici. Il caso del **vetro** e' la
      dimostrazione piu' immediata che i due sensori misurano fenomeni diversi:
      trasparente alla luce, attraversato dal radar, **completamente opaco al PIR**
      (il vetro comune non trasmette oltre 4-5 um, l'emissione del corpo e' a ~10 um)
- ⚠️ **Serve un soggetto IN MOVIMENTO, non fermo** (correzione al piano originale): su
      bersaglio immobile `senergy` satura a 100 anche a 4 m, quindi l'attenuazione non
      sarebbe osservabile. E servono **due distanze**: 3 m per il radar (energia a meta'
      scala) e 1 m per il PIR (a 3 m non rileva il movimento sul posto, quindi partirebbe
      gia' da zero e la misura sarebbe vuota)
- 🔑 **Controllo col metallo, da fare per SECONDO** (subito dopo la baseline): con la
      lastra interposta il radar riporta un bersaglio a **30,0 cm con dispersione 0,00**
      in tutti i trial — e' il pannello, e della persona a 3 m non resta traccia. Prova
      che l'aggiramento e' sotto soglia e che la geometria a 20 cm regge. Farlo presto
      permette di correggere la geometria prima di acquisire tutto il resto
- ⚠️ **`radar_rate_%` non basta a dire se il radar vede la persona**: col metallo era
      100 % ma riferito al pannello. **Guardare sempre `mdist_media_cm` prima di
      `menergy_media`**: ~320 cm = segue la persona (energia valida), ~30 cm con
      dispersione 0 = segue il pannello (energia priva di significato)
- 🔑 **La BASELINE e' la misura meno riproducibile della serie**: 6 trial senza ostacolo
      da 47,8 a 57,3 (quasi 10 punti), mentre 6 trial con la tanica — presi negli stessi
      due istanti — stanno fra 48,4 e 50,5. Le tendenze interne ai due gruppi sono
      **opposte**, quindi non e' deriva ma rumore; verosimilmente senza pannello arrivano
      anche i cammini multipli dell'ambiente. **Va mediata sui trial di inizio e fine**,
      non presa una volta sola. La ripetizione `ostacolo_plastica_fine` (49,47 contro
      49,37) ha confermato che l'ambiente era stabile e ha salvato il dato piu' fragile
- ⚠️ **`menergy` NON e' una potenza**: e' un indice normalizzato 0-100 con elaborazione
      interna (lo prova il decadimento con la distanza, molto piu' lento di 1/D^4). Le
      percentuali **non vanno convertite in dB** ne' confrontate con i coefficienti di
      trasmissione teorici. La graduatoria fra materiali e' valida, i valori assoluti sono
      in unita' dello strumento
- ⚠️ **Il pannello deve essere RIGIDO**: una lastra di cartone 105x71x0,4 mm ha dato
      letture instabili (distanza oscillante di oltre 1 m *dentro* il singolo trial),
      mentre una lastra di vetroresina ancora piu' ampia e' stata stabilissima. Non e' la
      dimensione: un foglio sottile e largo flette e diventa **bersaglio in movimento**.
      File conservati come `ostacolo_cartone_lastra_*`, esclusi dai risultati
- ⚠️ **I pannelli avevano coperture diverse (±42° … ±70°)**, quindi parte della differenza
      fra materiali e' geometria: le attenuazioni sono **limiti inferiori**. Il confronto
      piu' pulito e' legno vs cartone, entrambi a ±54°
- ⚠️ **Cartongesso non provato** (non disponibile): e' il materiale piu' rilevante per le
      pareti di un'aula ed e' la lacuna principale della fase, da dichiarare in tesi
- 📌 **Conseguenza per UPRISE**: il sensore puo' essere **incassato nell'arredo** — dietro
      legno o dentro un guscio di vetroresina — e continuare a funzionare. E' una liberta'
      di progetto che il PIR non concede: per funzionare deve affacciarsi direttamente
      sull'ambiente. Il metallo resta l'unico vincolo assoluto, e nel banco reale la
      lamiera sta **dietro** al modulo, non davanti
- [x] 🎯 **FASE 5 COMPLETATA (31/08/2026) — respiro validato contro ritmo imposto.**
      E' la **prima misura di respiro con ground truth** della tesi: tutte le stime
      precedenti poggiavano sulla concordanza fra canali, che e' un indizio, non una
      verifica. Seduto a **2 m** rivolto al sensore (a 1 m i canali moving saturano),
      metronomo al doppio del ritmo, 5 trial per ritmo da 162 s utili:
      | ritmo imposto | trial concordi | stima | errore |
      | 10 atti/min | 4/5 | **10,00 ± 0,00** | 0,00 |
      | 15 atti/min | 4/5 | **14,95 ± 0,30** | −0,05 |
      | 20 atti/min | 5/5 | **19,64 ± 0,09** | −0,36 |
      | stanza vuota | — | **nessuna stima in 3/3** | — |
      Errore assoluto medio **0,22 atti/min**, massimo 0,4. Il controllo negativo pulito
      dimostra che i picchi non sono artefatti di banda
- 🔑 **AMBIGUITA' DI OTTAVA: nei 2 trial non concordi la stima e' ESATTAMENTE il doppio**,
      mai un valore intermedio. Quindi la stima di frequenza e' precisa e ambigua e' solo
      la scelta dell'ottava. **La ragione e' fisica, non algoritmica**: l'energia per-gate
      risponde all'*entita'* dello spostamento e non al suo verso, quindi un ciclo
      completo (inspirazione + espirazione) produce **due** escursioni di energia, cioe'
      una componente a 2f che puo' superare la fondamentale. Non e' risolvibile dallo
      spettro di un canale singolo: serve un criterio esterno
- [x] ⚠️ **`analizza_respiro.py`: due regole di selezione riscritte, smentite dalla ground
      truth** (31/08/2026). Erano entrambe nella versione del 22/08:
      1. **I gruppi misti non vanno scartati.** La regola "solo canali moving" buttava via
         le stime migliori: a 20 atti/min sette canali moving e sette stazionari
         concordavano su 19,6 e il gruppo veniva scartato in blocco. La concordanza fra i
         due tipi di canale e' **corroborazione, non contaminazione** — l'artefatto
         stazionario noto sta a 6-7 atti/min, cioe' a un'altra frequenza. Ora serve solo
         che il gruppo contenga >= N canali moving
      2. **Fra due gruppi in rapporto armonico vince il piu' basso**, non il piu' numeroso:
         a 15 atti/min in 3 trial su 5 vinceva l'armonica a 29,6
      \+ **soglia di plausibilita' a 8 atti/min** applicata in modo uniforme: senza, un
      trial di stanza vuota dava una stima spuria a 7,0 atti/min. ⚠️ E' un'assunzione
      dichiarata (adulto sveglio), e rende il metodo **cieco a una respirazione molto
      lenta**: da citare come limite
- ✔ **Verificato che la revisione NON cambi i risultati gia' pubblicati**:
      `sotto_banco_immobile` passa da 21,0 ± 2,5 a **21,3 ± 2,3** atti/min. Le nuove regole
      non riscrivono nulla, poggiano i numeri precedenti su un criterio validato
- ⚠️ **Nuove opzioni**: `--salta-inizio SEC` (obbligatoria nei test del respiro: i secondi
      del posizionamento dominano la FFT) e `--min-canali N` (default 3; con 2 i trial
      concordi passano da 11 a 13 su 15 e **le stime dei trial gia' concordi non cambiano**
      — varia la copertura, non l'accuratezza)
- ⚠️ **Il metronomo approfondisce il respiro**: l'SNR di questi trial e' verosimilmente
      migliore di quello spontaneo. La validazione riguarda l'accuratezza della
      **frequenza**, non l'ampiezza del segnale in condizioni realistiche

### Web UI e dati (obiettivo 5)
- [x] Progetto architetturale della web UI (`analisi/ANALISI_WEB_UI.md`)
- [x] **Revisione dei due documenti prima dell'implementazione (05/09/2026)**: rete solo
      AP con DNS catch-all; JS puro; PROGMEM gzip al posto di LittleFS (il plugin di upload
      non esiste per l'IDE 2.x); librerie **ESP32Async** (il core 3.3.11 non compila
      l'originale); partizione **Huge APP** (lo schema di default da' 1,2 MB, troppo poco);
      `ws.cleanupClients()` nel loop; vitalita' v3 a 3 classi con fondo per gate; CSV a
      29 colonne con `light_level`/`out_level`
- [~] **`firmware/ld2410b_web/` avviato (06/09/2026) — step 1-2 di 5 fatti** (BUILD 2):
      Access Point + DNS catch-all + pagina statica + `/info`; lettura radar e PIR, CSV
      sulla seriale con le stesse 29 colonne del logger (quindi `acquire.py` gira in
      parallelo alla web UI) e spinta WebSocket a 5 Hz. La pagina sta in `web/`
      (index.html, style.css, app.js) e `tools/embed_web.py` la comprime in gzip dentro
      `web_assets.h`. ⚠️ **`web_assets.h` e' GENERATO ma versionato di proposito**: l'IDE
      Arduino non esegue passi di build, quindi senza il file committato lo sketch non
      compila su un'altra macchina. Rigenerarlo dopo ogni modifica in `web/` con
      `python tools/embed_web.py`
- [x] ESP32 pubblica i dati (Access Point proprio, WebSocket)
- [ ] Sito web visualizzazione tempo reale
- [ ] Salvataggio dati + statistiche
- [ ] Export CSV → analisi in Excel

### Indice di vitalità (obiettivo 6)
- [x] **Pilota respiro riuscito (18/08/2026)** — `HLK-LD2410x/data/20260818_respiro_40cm_prova.csv`:
      soggetto fermo a ~40 cm, 91 s. **7 gate moving indipendenti concordano su 0.264 Hz =
      15.8 atti/min** (SNR fino a 12.8x su `menergy_gate2`), valore fisiologicamente
      plausibile per un adulto a riposo. Prova che il respiro è rilevabile con questo
      hardware e con la nostra catena 5 Hz + engineering mode + FFT.
      ⚠️ **Non è una misura valida per la tesi**: manca la ground truth (non sappiamo il
      ritmo reale), l'89% dei campioni moving è saturo e 40 cm non è uno scenario
      realistico. Da rifare in fase 6: ≥1.5 m, soglie tarate, **respiro a metronomo** a
      ritmo noto (il confronto stima↔ritmo imposto è la vera prova)
- ⚠️ I canali **stazionari** in questo pilota sono inutilizzabili: gate 2-3 saturi al 100%,
      gate 0-1 sempre a zero, e i gate 4-8 danno 6.6-9.2 atti/min in disaccordo tra loro e
      col canale moving (0.132 Hz è esattamente metà di 0.264 → sospetta subarmonica).
      Conferma che a distanza ravvicinata il respiro va cercato sul canale **moving**
- [x] **Confermato su una seconda sessione a 2.31 m** (Test 1.3 T01, 302 s): stessa
      spaccatura. I gate **moving** 2-8 concordano su 0.30 Hz = **18.2 atti/min**
      (plausibile per adulto seduto) e **non sono saturi** (0-1%); i gate **stazionari**
      danno 6.5-7.8 atti/min, troppo pochi per un adulto a riposo, e i gate vicini al
      bersaglio sono saturi (gate3 100%, gate4 97%). Due sessioni a distanze molto diverse
      dicono la stessa cosa: **per il respiro usare i gate moving**. Il ~7/min stazionario
      è verosimilmente un artefatto del filtraggio interno del canale, non respirazione —
      ma senza ground truth resta un'ipotesi: lo decide il test a metronomo della fase 6
- [x] **Buona notizia per la fase 6**: a 2.3 m i canali moving non saturano, quindi il test
      del respiro si può fare a distanza realistica senza accorgimenti geometrici
- [x] Specifica dell'algoritmo (`analisi/ANALISI_VITALITA.md` — v1 da tarare sui dati)
- [~] **Prototipo Python `analisi/vitalita_proto.py` SCRITTO (26/08/2026)** — implementa
      la v2 della specifica, calcola vitality(t), distribuzioni per scenario e matrice di
      confusione. Resta da fare la **taratura** (α, k, soglie) e la validazione
- [x] **I dati della Fase 6 esistono gia'**: la serie dose-risposta del Test 2.3 copre i
      quattro scenari previsti a geometria costante (1 m, jumper H, 5 trial ciascuno) —
      `stanza_vuota` / `fermo_1m_H` / `micromovimenti_1m_H` / `movimento_1m_H`. In piu'
      `sotto_banco_*_H` come insieme di validazione su geometria diversa
- [x] ⚠️ **La v1 della specifica non era applicabile**: costruiva la componente di
      micro-vitalita' sulla variazione dell'energia **stazionaria**, che e' satura a 100
      con dev.std **0,0** in ogni scenario occupato -> termine identicamente nullo. La v2
      usa i canali **moving** per entrambe le componenti
- [x] 🔑 **Il rumore di fondo va sottratto, altrimenti l'indice non distingue una stanza
      vuota da una persona immobile**: senza correzione la stanza vuota (6,5 h) da' 19,1 e
      una persona immobile a 2,3 m da' 21,2. Sottraendo il fondo per-gate (g0≈18, g1≈13,
      g2-8 = 3-5) e riscalando: **2,4** contro **11,4**. Con i parametri di default la
      scala a 1 m diventa 2,4 / 30,9 / 77,3 / 99,7 sui quattro livelli di movimento
- ⚠️ **Trasferibilita' fra geometrie da risolvere in taratura**: `sotto_banco_immobile_H`
      da' **65,6**, vicino ai micro-movimenti a 1 m (77,3). Una sola terna di soglie non
      copre entrambe le geometrie
- [x] 🎯 **TARATURA E VALIDAZIONE FATTE (31/08/2026).** Parametri scelti sui trial
      **T01-T03** dei tre scenari a 1 m e prestazione misurata su **T04-T05**, mai usati
      per tarare. Configurazione: **α_m = 0,05 · α_v = 0,01 · k = 0,5 · soglie 45 e 95**,
      **3 classi** + gate di presenza:
      | insieme | recall media per classe |
      | taratura (T01-T03, 1 m) | 95,1 % |
      | **validazione (T04-T05, 1 m)** | **88,0 %** |
      | validazione su **geometria diversa** (sotto il banco) | 51,2 % |
      | 🔑 **discriminazione immobile vs in movimento**, entrambe le geometrie | **96,1 %** |
- 🔑 **v3 DELL'ALGORITMO: la componente di livello usa la SOLA energia del gate attivo.**
      La v2 faceva `max(moving_energy, menergy_gate[g])`, ed **era la causa del
      fallimento di trasferibilita' fra geometrie** (recall 8,8 % sotto il banco):
      `moving_energy` e' l'energia **aggregata** del bersaglio, a distanza ravvicinata
      satura a 100 e vince il `max` **qualunque gate si scelga** — verificato provando
      tutti i criteri di selezione, saturazione fra 94 e 97 % in ogni caso.
      Con la sola energia di gate:
      | scenario | v2 | **v3** |
      | fermo 1 m | 25,3 | 25,8 |
      | micro 1 m | 66,2 | 65,4 |
      | movimento 1 m | 98,5 | 98,4 |
      | **sotto banco immobile** | **50,2** | **22,1** |
      | **sotto banco movimenti** | 99,9 (97 % saturo) | **97,0 (1 % saturo)** |
      Gli scenari a 1 m **non cambiano**, quello sotto il banco rientra in scala. Opzione
      `--sorgente gate|max` nel prototipo per riprodurre la v2
- 📌 **Il 51,2 % sulla geometria diversa e' dominato da UN solo scenario**: 4 su 5 sono
      corretti, e fra questi **la persona immobile sotto il banco al 97,5 %** — cioe'
      proprio il caso della vittima incosciente, in una geometria su cui nulla e' stato
      tarato. Il caso che fallisce e' `sotto_banco_movimenti_H`, classificato *alta*
      invece di *moderata*: ⚠️ ma quell'etichetta era stata assegnata **per analogia** col
      caso a 1 m e **non poggia su ground truth**. A 60 cm una persona che si aggiusta
      da' un ritorno molto forte, e non e' dimostrato che "moderata" sia giusto
- ⚠️ **Le soglie restano specifiche della geometria di installazione.** Per UPRISE e'
      gestibile — ogni sensore sta fisso sotto il proprio arredo e si tara una volta —
      ma sarebbe un problema su un dispositivo portatile. Via naturale: **auto-taratura
      all'installazione** (fondo a stanza vuota + un riferimento di movimento)
- [ ] Porting su ESP32 (`vitality.h`)

### Processo
- [x] Scaletta della tesi (`SCALETTA_TESI.md` — da trasporre in Overleaf)
- [x] Agenda incontro professore (`INCONTRO_PROFESSORE.md`)
- [x] Analisi teorica PIR (`analisi/ANALISI_PIR.md` — sezione 6 da completare col modello reale)
- [x] **INCONTRO COL PROFESSORE FATTO (29/08/2026) — tre decisioni**:
      1. **Test di portata massima su tutti e tre i sensori**, da fare **per ultimi**
         perche' richiedono di spostare PC e sensori in corridoio: LD2410B oltre i 5 m,
         PIR con **sensibilita' al massimo** per ottenere il range dichiarato, LD2420
         fino agli 8 m di documentazione. Piano in `PIANO_TEST.md`, **Fase 8**
      2. **Il sito si fa self-hosted sull'ESP32** (opzione A di `ANALISI_WEB_UI.md`,
         confermata). Motivazione del professore: e' un'ottima casistica di **scenario
         senza connessione**, che e' esattamente lo scenario UPRISE. `ANALISI_SITO_SERVER.md`
         (piano B) resta come **alternativa valutata e scartata**, con la motivazione —
         e' materiale buono per la tesi, non lavoro sprecato
      3. **L'indice di vitalita' va calcolato a bordo**, dentro il sito, accanto ai
         grafici. Il porting su ESP32 passa quindi da opzionale a **richiesto**
         (per fortuna la v2 e' tutta EWMA, niente FFT: e' portabile a costo quasi zero)
- 📌 **Come il professore vuole che si parli dell'indice di vitalita'**: NON dire "misura
      il movimento toracico", ma presentarlo come **indice generico** con **3 classi**
      (erano 4 nella specifica). Vedi `analisi/ANALISI_VITALITA.md` §4 per i nomi
      proposti e per la ragione **metodologica** per cui questa scelta e' anche la piu'
      difendibile: senza ground truth non possiamo validare una frequenza respiratoria,
      quindi definire l'indice per quello che **calcola** evita di sovradichiarare
- [x] **Setup backup dati COMPLETATO (26/08/2026)** — repo GitHub
      `Steb2002/Tesi-Presence-Sensing`, allineato al remoto. Verificato per conteggio:
      **116 CSV sperimentali su disco, 116 tracciati, 116 presenti in `origin/main`**,
      più `REGISTRO_SESSIONI.md`; 28 MB in `HLK-LD2410x/data/`. Nessun file non
      tracciato in quella cartella
- 🚨 **CORREZIONE (26/08/2026): la frase «nessuna regola ignora i CSV» era SBAGLIATA.**
      `HLK-LD2410x/.gitignore` riga 66 contiene `*.csv` (eredità del repo del professore) e
      la riga 72 lo annulla con `!data/*.csv`. Verificato con `git check-ignore -v`:
      | percorso | esito |
      | `HLK-LD2410x/data/prova.csv` | tracciato ✔ |
      | `HLK-LD2410x/data/**sotto**/prova.csv` | **IGNORATO** ✗ |
      | `HLK-LD2410x/prova.csv` | **IGNORATO** ✗ |
      | `HLK-LD2420/Test LD2420/prova.csv` | tracciato ✔ |
      | `analisi/prova.csv` | tracciato ✔ |
      ⚠️ **Il negativo `!data/*.csv` non copre le sottocartelle**: un CSV messo in una
      sottocartella di `data/` sparisce dal repo **senza un avviso**. Vale la pena saperlo
      prima della campagna LD2420, non dopo. Se si vogliono organizzare i dati in
      sottocartelle, cambiare la riga 72 in `!data/**/*.csv` **prima** di acquisire
- ⚠️ Fuori da `HLK-LD2410x/` non c'è alcuna regola sui CSV, quindi i dati del LD2420
      entrano nel repo per default. Rovescio della medaglia: con `git add -A` entra
      **tutto**. Tenere gli eventuali CSV intermedi o di scarto **fuori** da
      `HLK-LD2410x/data/`, altrimenti si mescolano ai trial buoni nella storia
- ⚠️ Un `find . -name "*.csv"` grezzo ne conta 146, non 116: i 30 in più sono fixture di
      test di numpy dentro `HLK-LD2410x/.venv/`, ignorate correttamente. Non sono dati
      sperimentali
- [x] Scheletro capitoli in Overleaf — `tesi-unicam/`: 8 capitoli + 2 appendici, ~4200 righe
- [x] **Capitolo 4 "Confronto sperimentale" SCRITTO (25/08/2026)** —
      `tesi-unicam/capitoli/04-confronto-sperimentale.tex`, da 612 a ~1450 righe, 13
      tabelle. Copre fasi 1 e 2 complete. Restano marcate *in corso* solo: penetrazione
      ostacoli, respiro a metronomo, confronto LD2420, misura angolare.
      ⚠️ **Storico**: per un periodo sono esistite DUE cartelle LaTeX divergenti,
      `tesi-unicam/` e `tesi/`.
      ✔ **Duplicazione risolta (25/08/2026)**: la cartella `tesi/` è stata **cancellata**.
      L'unica cartella LaTeX è ora `tesi-unicam/` (classe ufficiale `unicam-diss.cls`).
      Verificato prima di cancellare che nulla andasse perso: `bib/tesi.bib` era
      identico e i tre file `00-*` avevano già il loro equivalente adattato in
      `tesi-unicam/frontmatter/` (`titlepage`, `proposte-titolo`, `abstract`). In ogni
      caso il contenuto resta nella storia git fino al commit 2568d7b
- 📌 **Numeri chiave del capitolo, tutti riverificati dai CSV il 25/08/2026** (se
      compaiono valori diversi altrove in questo file, fanno fede questi):
      distanza 1-5 m errore grezzo **-0,52 / +11,22 / +9,76 / +11,84 / +18,20 cm**,
      dispersione entro trial **10,4 / 14,3 / 17,5 / 26,4 / 11,7 cm**, energia
      **99,0 / 85,1 / 54,4 / 35,1 / 27,6**; residui dalla retta ≤ 4,9 cm.
      ⚠️ L'errore **relativo** non è monotono: il massimo è a **2 m (+5,6 %)**, non a 5 m
- 📌 **Struttura degli impulsi PIR, il dato che regge l'interpretazione**: in **L**
      195 impulsi, media **3,46 ± 0,09 s**, nessuno oltre 5 s. In **H** a 1 m con cammino:
      6 impulsi completi (media 14,1 s, max 29,8 s) **più 5 troncati, il più lungo ≥ 61,6 s**
      (cioè l'intero trial). In **H** da fermo: **2 impulsi in 1010 s**. Il contrasto fra
      queste tre righe è più convincente della percentuale
- [x] **13 figure della campagna generate (26/08/2026)** — `analisi/rigenera_tutto.py`.
      Coprono gli obiettivi 1-4: dose-risposta PIR vs radar, scenario sotto il banco,
      accuratezza della distanza, energia e portata, latenze, impulsi PIR, due persone,
      selettività spaziale, dati per-gate in engineering mode, saturazione, respiro,
      consumi. Da inserire nel cap. 4 con `\includegraphics{figures/figNN_...}`
- [x] **Materiali per l'incontro pronti**: `RIEPILOGO_INCONTRO.pdf` (10 pagine A4, stato
      dei 6 obiettivi + tutte le figure con didascalie + domande da porre) e
      `analisi/dati_tesi.xlsx` (una riga per trial, per le pivot in Excel). Entrambi
      rigenerabili in 13 s, entrambi fuori dal repo per scelta (vedi `.gitignore`)
- [ ] Cronoprogramma (dopo aver saputo la scadenza)

### Chiusura
- [x] Consumo energetico da datasheet (obiettivo 4 — bozza in `analisi/ANALISI_CONSUMI.md`; da completare col modello PIR reale dopo Test 0.3)
- [ ] Analisi dati e scrittura tesi
