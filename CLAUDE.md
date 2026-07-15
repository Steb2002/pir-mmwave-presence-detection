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
| HLK-LD2410B | 1 | Modulo blu piccolo, PCB v1.3, ha Bluetooth, cavi già saldati |
| HLK-LD2420 | 1 | Scheda arancione/verde, range maggiore |
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

### Pinout (5 pin)
```
Pin 1: VCC  → 5V ESP32 (VIN)
Pin 2: GND  → GND ESP32
Pin 3: TX   → GPIO16 (RX2) ESP32
Pin 4: RX   ← GPIO17 (TX2) ESP32
Pin 5: OUT  → GPIO opzionale (presenza digitale HIGH/LOW)
```

### Colori cavi del connettore JST (verificati fisicamente sul modulo)
⚠️ Colori NON convenzionali — basarsi sul segno Pin 1 sul PCB, non sul colore!
```
Blu   = Pin 1 → VCC  (5V)
Verde = Pin 2 → GND
Giallo= Pin 3 → TX   → D16 ESP32
Nero  = Pin 4 → RX   → D17 ESP32
Rosso = Pin 5 → OUT  (non collegare per ora)
```

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

### Caratteristiche principali
- Frequenza: **24 GHz**
- Range: fino a **~12 m** (gate 0-14, 70 cm per gate)
- Alimentazione: **3.3V** (diverso dal LD2410B che vuole 5V!)
- Bluetooth: **assente**
- Calibrazione: **automatica** (firmware ≥ 1.5.4)

### ATTENZIONE — Pinout dipende dalla versione firmware

```
Firmware ≤ 1.5.2:              Firmware ≥ 1.5.3:
Pin 1: 3.3V                    Pin 1: 3.3V
Pin 2: GND                     Pin 2: GND
Pin 3: OT1 (presenza digitale) Pin 3: OT1 → TX seriale → ESP32 RX
Pin 4: RX  ← ESP32 TX          Pin 4: RX  ← ESP32 TX
Pin 5: OT2 → TX → ESP32 RX     Pin 5: OT2 (presenza digitale)
```

**Verificare sempre la versione firmware prima di collegare!**
Tool ufficiale: Google Drive HiLink → cartella `HLK-LD2420_TOOL - English`

### Baud rate per versione firmware
- Firmware < 1.5.3: **256000 baud**
- Firmware ≥ 1.5.3: **115200 baud**

### Parametri configurabili
| Parametro | Range | Default |
|---|---|---|
| Gate minimo | 0 a (max-1) | 1 |
| Gate massimo | 1-15 | 12 (~8.4m) |
| Timeout presenza | variabile | 120s |
| Soglia stazionario per gate | 0-1 | 0.5 |
| Soglia movimento per gate | 0-1 | 0.5 |

### Modalità operative
1. **Normal** — energy reporting (firmware ≥ 1.5.4)
2. **Calibrate** — raccoglie noise floor e peak energy per calibrazione automatica
3. **Simple** — retrocompatibilità firmware ≤ 1.5.3

### Dati in uscita
- Presenza binaria (moving o still)
- Distanza approssimativa al target
- Versione firmware
- Meno granularità per-gate rispetto al LD2410B

---

## Confronto LD2410B vs LD2420

| Caratteristica | LD2410B | LD2420 |
|---|---|---|
| Alimentazione | 5V | 3.3V |
| Range | ~5-6 m | ~12 m |
| Gate | 8 (0-8) | 15 (0-14) |
| Risoluzione gate | 0.75m o 0.2m | 70 cm fisso |
| Baud rate | 256000 fisso | 115200 o 256000 (dipende fw) |
| Bluetooth | ✓ | ✗ |
| Calibrazione | Manuale | Automatica (fw 1.5.4+) |
| Dati per-gate | Molto dettagliati | Limitati |
| Pinout fisso | ✓ | ✗ (cambia con fw) |
| Uso consigliato | Respiro, dettaglio | Range lungo, copertura |

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
- **D16** = RX2 (Serial2) — riceve dati dal sensore
- **D17** = TX2 (Serial2) — invia comandi al sensore

### Collegamento ESP32 ↔ LD2410B (con colori reali)
```
Cavo BLU    (Pin 1 VCC) → VIN  ESP32  (5V, lato dx primo in alto)
Cavo VERDE  (Pin 2 GND) → GND  ESP32
Cavo GIALLO (Pin 3 TX)  → D16  ESP32
Cavo NERO   (Pin 4 RX)  → D17  ESP32
Cavo ROSSO  (Pin 5 OUT) → non collegare per ora
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
- PIR su GPIO23, LED su GPIO2, seriale verso PC a 115200 baud
- CSV: `timestamp_ms,radar_presence,moving_target,stationary_target,moving_distance_cm,stationary_distance_cm,moving_energy,stationary_energy,pir_presence`

**Script `acquire.py`** (solo pyserial): legge la seriale e aggiunge a ogni riga i metadati sperimentali da CLI: `pc_time_s, group_id, trial_id, scenario, ground_truth_presence, ground_truth_state`. La ground truth è **statica per file** → per la latenza serve la convenzione "evento a t=10s" (vedi PIANO_TEST.md, Test 2.1)

**Adattamenti fatti per la tesi** (cartella `firmware/` e `analisi/`):
- `firmware/ld2410b_logger/ld2410b_logger.ino` — logger riscritto con MyLD2410: 5 Hz, engineering mode (colonne extra `menergy_gate0..8`, `senergy_gate0..8`), pin corretti per il nostro cablaggio, CSV retro-compatibile con acquire.py (da compilare e verificare su hardware)
- `analisi/analizza_test.py` — metriche automatiche dai CSV: accuratezza, FP eventi/h, FN%, latenza (--event-time), statistiche distanza/energia, aggregazione per scenario (media ± dev.std). Solo libreria standard
- `analisi/analizza_respiro.py` — FFT della serie di energia, picco in banda 0.1-0.5 Hz, stima atti/min, export spettro CSV per Excel. Richiede numpy
- `analisi/ANALISI_CONSUMI.md` — obiettivo 4 completato in bozza (consumi da datasheet + stime autonomia + argomentazione architettura ibrida PIR+mmWave)
- `analisi/ANALISI_WEB_UI.md` — progetto della web UI (obiettivo 5): architettura ESP32 self-hosted (ESPAsyncWebServer + WebSocket + LittleFS, tutto offline), formato JSON, layout pagina, struttura codice `firmware/ld2410b_web/`, piano di sviluppo in 5 step. Decisione chiave: il CSV esportato dal browser usa le stesse colonne di acquire.py → un solo formato dati in tutta la tesi
- `analisi/PROGETTO_SITO_DETTAGLIO.md` — progetto di dettaglio implementativo del sito: struct/pseudocodice firmware, protocollo WS con riconnessione, strutture dati JS, config dei 3 grafici, export CSV client-side, gestione errori, criteri di accettazione per step
- `analisi/ANALISI_VITALITA.md` — specifica dell'indice di vitalità (obiettivo 6, documento autonomo): algoritmo v1 (doppia EWMA movimento+respiro), classificazione a 4 classi per il triage, percorso di taratura Python-prima sui CSV della Fase 6 con validazione su trial separati, casi limite, collocazione nella tesi
- `analisi/ANALISI_PIR.md` — analisi teorica del PIR (obiettivo 1-2): principio piroelettrico differenziale, lente di Fresnel, perché è fisicamente cieco alla persona ferma, dati prodotti (1 bit + ritenuta/trigger), sensibilità alla temperatura, sezione 6 DA COMPLETARE col modello reale (Test 0.3)
- `SCALETTA_TESI.md` — scaletta Overleaf in 8 capitoli con mappa obiettivi→capitoli, materiale già pronto per ciascuno e ordine di scrittura consigliato (cap. 5 e 2 scrivibili subito)
- `INCONTRO_PROFESSORE.md` — agenda per l'incontro: cosa mostrare (PIANO_TEST, scaletta, consumi) e domande consolidate (validazione protocollo, montaggio sensore/lamiera, scadenza, UPRISE vs SAFE, ruolo UWB)
- `PIANO_TEST.md` — piano di test completo in ordine di esecuzione (fasi 0-7)

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
- Datasheet HC-SR501 (PIR in dotazione): https://www.electronicoscaldas.com/datasheet/HC-SR501.pdf (mirror; altra copia su mpja.com/download/31227sc.pdf)
- Datasheet BISS0001 (chip del PIR): https://cdn-shop.adafruit.com/datasheets/BISS0001.pdf
- Adafruit PIR guide (principio piroelettrico/Fresnel): https://learn.adafruit.com/pir-passive-infrared-proximity-motion-sensor
- ESP32-WROOM-32 datasheet (consumi): https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32_datasheet_en.pdf
- Manuale HLK-LD2410 V1.03 (consumi/specifiche verificate): https://seengreat.com/upload/file/86/HLK+LD2410+Life+Presence+Sensor+Module+Manual+V1.03(220629).pdf

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
- Il pinout del LD2420 **cambia con la versione firmware** — verificare prima di collegare con HLK-CH340E
- Entrambi i sensori usano **TX/RX incrociati** rispetto all'ESP32
- Il baud rate 256000 richiede UART hardware dell'ESP32 (D16/D17), non softserial
- Per il respiro serve **engineering mode** sul LD2410B (byte comando `0x62`)
- Il LD2410B non distingue due persone alla stessa distanza (no array di antenne)
- Penetrazione ostacoli: funziona su legno/cartongesso/vetro/plastica; non su metallo o cemento armato spesso
- I cavi del LD2410B hanno colori NON convenzionali (blu=VCC, verde=GND) — non fidarsi del colore, usare il segno Pin 1 sul PCB
- Il CH340E può essere usato per collegare il LD2420 direttamente al PC (senza ESP32) per leggere il firmware

## Note di processo

- **REGOLA FONTI (richiesta esplicita, 15/07/2026)**: ogni dato tecnico inserito nei documenti deve avere la fonte citata, preferibilmente certificata o autorevole (datasheet del produttore > manuale ufficiale > guide riconosciute tipo Adafruit/ESPHome > blog). Ogni documento di analisi ha la sua sezione "Fonti"; le fonti confluiranno in `bib/tesi.bib` su Overleaf. Se una fonte riporta valori sospetti (es. refusi mA/µA), annotarlo e far fede al datasheet
- **La tesi si scrive in Overleaf (LaTeX)** — impostare lo scheletro dei capitoli presto e scrivere durante i test, non dopo: i documenti in `analisi/` sono già bozze di capitoli
- **Validare PIANO_TEST.md col professore PRIMA della campagna di test** (~10 h di acquisizioni: se il protocollo non va bene si rifà tutto)
- **Backup dei dati prima di iniziare le acquisizioni**: i CSV sono l'asset insostituibile della tesi — git init + repo privato, o cartella sincronizzata su Drive/OneDrive
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
- [ ] Verificare firmware LD2420 con CH340E + tool HiLink

### Sensori (obiettivi 1-2)
- [ ] Primo sketch test LD2410B
- [ ] Sketch logging dati LD2410B
- [ ] Setup e test LD2420
- [x] Identificazione PIR: HC-SR501 (foto + datasheet, `analisi/ANALISI_PIR.md` §6 completata)
- [ ] Configurazione e test PIR HC-SR501 (jumper H, ritenuta al minimo, sensibilità a metà — Test 0.3)

### Testing comparativo (obiettivo 3)
- [ ] Definire il protocollo di test (scenari, metriche: accuratezza, latenza, FP/FN)
- [ ] Test comparativo PIR vs mmWave con numeri
- [ ] Test penetrazione ostacoli (cartongesso, legno, vetro, plastica)
- [ ] Engineering mode + rilevamento respiro LD2410B

### Web UI e dati (obiettivo 5)
- [x] Progetto architetturale della web UI (`analisi/ANALISI_WEB_UI.md`)
- [ ] ESP32 pubblica i dati (WiFi)
- [ ] Sito web visualizzazione tempo reale
- [ ] Salvataggio dati + statistiche
- [ ] Export CSV → analisi in Excel

### Indice di vitalità (obiettivo 6)
- [x] Specifica dell'algoritmo (`analisi/ANALISI_VITALITA.md` — v1 da tarare sui dati)
- [ ] Prototipo Python (`vitalita_proto.py`) + taratura sui CSV della Fase 6
- [ ] Validazione (matrice di confusione su trial separati)
- [ ] Porting su ESP32 (`vitality.h`)

### Processo
- [x] Scaletta della tesi (`SCALETTA_TESI.md` — da trasporre in Overleaf)
- [x] Agenda incontro professore (`INCONTRO_PROFESSORE.md`)
- [x] Analisi teorica PIR (`analisi/ANALISI_PIR.md` — sezione 6 da completare col modello reale)
- [ ] Incontro col professore: validazione protocollo + domande (lamiera, scadenza, UPRISE/SAFE, UWB)
- [ ] Setup backup dati (git init + repo privato, o Drive/OneDrive)
- [ ] Scheletro capitoli tesi in Overleaf (da SCALETTA_TESI.md)
- [ ] Cronoprogramma (dopo aver saputo la scadenza)

### Chiusura
- [x] Consumo energetico da datasheet (obiettivo 4 — bozza in `analisi/ANALISI_CONSUMI.md`; da completare col modello PIR reale dopo Test 0.3)
- [ ] Analisi dati e scrittura tesi
