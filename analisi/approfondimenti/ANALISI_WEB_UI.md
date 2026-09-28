# Analisi progettuale — Web UI (Obiettivo 5)

> Requisiti dall'obiettivo 5: *"l'ESP32 pubblica i dati → sito web per visualizzazione
> in tempo reale → la stessa app salva i dati con statistiche → export CSV → analisi
> numerica in Excel"*. Integra anche la visualizzazione dell'indice di vitalità (obiettivo 6).

---

> 📝 **Revisione del 05/09/2026** (rilettura prima di iniziare l'implementazione). Sei
> decisioni, tutte riportate nelle sezioni marcate «rev. 05/09»: rete **solo Access
> Point** (l'ESP32 non si collega a nessun WiFi esistente: crea il suo); frontend in
> **JavaScript puro** (Angular valutato e scartato, §4); pagina incorporata nel firmware
> come **PROGMEM gzip** invece che su LittleFS; librerie server nei fork **ESP32Async**
> (le uniche che compilano sul core ESP32 3.x installato); schema di partizione **Huge
> APP**; indice di vitalità allineato alla **v3 a tre classi** con sottrazione del fondo;
> CSV a **29 colonne** come il logger attuale. Il documento di dettaglio
> (`PROGETTO_SITO_DETTAGLIO.md`) è stato aggiornato di conseguenza.

## 1. Scelta architetturale

### Opzioni considerate

| Architettura | Pro | Contro |
|---|---|---|
| **A. Sito servito dall'ESP32** (web server + WebSocket a bordo) | Zero infrastruttura, funziona offline, coerente col contesto DIPME (emergenza = niente internet), demo autonoma | RAM/flash limitate, max 2-3 client simultanei |
| B. ESP32 → MQTT → server Python/Node + DB | Scalabile, storico illimitato | Serve un broker + un server sempre accesi; troppa infrastruttura per una tesi di sensing |
| C. Cloud (ThingSpeak, Blynk…) | Pronto all'uso | Non offline, campionamento limitato (~15 s), dati fuori controllo, non difendibile in sede di tesi DIPME |

### Scelta: **A — tutto sull'ESP32**

✅ **CONFERMATA DAL PROFESSORE (incontro del 29/08/2026).** Non è più un default
nostro da validare: è la decisione presa. La motivazione data dal professore
coincide con la nostra prima: il sito self-hosted **è un'ottima casistica di
scenario senza connessione**, cioè esattamente lo scenario DIPME.

📌 **Conseguenze operative della conferma**:
- `analisi/approfondimenti/ANALISI_SITO_SERVER.md` (piano B, architettura MQTT + FastAPI) esce dal
  percorso realizzativo ma **non si butta**: diventa l'*alternativa valutata e
  scartata con motivazione*, che è materiale buono per il capitolo sulle scelte
  progettuali. Documentare un'alternativa scartata è più forte che non averla
  considerata
- l'**indice di vitalità va calcolato a bordo**, accanto ai grafici (richiesta
  esplicita del professore). Vedi `analisi/approfondimenti/ANALISI_VITALITA.md` §5: la v2 è tutta
  EWMA, quindi il costo computazionale sull'ESP32 è trascurabile e non serve
  ripensare l'architettura. La FFT del respiro resta invece **offline**, in
  `analizza_respiro.py`

Motivazioni:
1. **Coerenza col progetto DIPME**: in emergenza sismica non c'è internet; un nodo
   autonomo che serve la propria dashboard è la miniatura concettuale della
   "piattaforma di monitoraggio" del progetto (modalità tempo di pace/emergenza)
2. Il volume dati è piccolo: ~20 valori × 5 Hz ≈ 2 KB/s — ben dentro i limiti dell'ESP32
3. La persistenza lunga non serve a bordo: lo storico si accumula **nel browser**,
   che ha memoria abbondante e fa lui l'export CSV

### Modalità WiFi: **solo Access Point** (rev. 05/09/2026)

L'ESP32 **crea la propria rete** (`DIPME-Sensor`, WPA2, IP fisso `192.168.4.1`) e
non si collega a nessun WiFi esistente. È una scelta di coerenza col progetto, decisa
dall'autore il 05/09/2026: nello scenario DIPME la rete di casa **non esiste**, e un
firmware che la cerca prima di ripiegare sull'AP racconterebbe una storia diversa da
quella della tesi. Conseguenze:
- nessuna credenziale nel firmware → niente `config.h` da tenere fuori dal repo
- nessun timeout di connessione all'avvio: l'AP è su in ~1 s
- il PC/tablet di chi guarda la dashboard deve **collegarsi alla rete dell'ESP32**
  e perde internet nel frattempo. ⚠️ Alcuni telefoni, non vedendo internet, tornano
  da soli ai dati mobili o mostrano «rete senza internet»: si gestisce con un **DNS
  catch-all** a bordo (libreria `DNSServer`, già nel core) che risponde `192.168.4.1`
  a qualunque nome → si può scrivere `dipme.local` o qualsiasi indirizzo e si arriva
  alla dashboard, e il sistema operativo riconosce il portale
- la modalità Station (collegarsi a una rete esistente) resta nell'elenco delle
  estensioni (§8), non nel percorso realizzativo

---

## 2. Dati da pubblicare (mappati sugli output reali del firmware)

Il firmware `ld2410b_logger` produce già tutto ciò che serve. Il messaggio WebSocket
riprende le stesse grandezze del CSV, più i campi calcolati:

```json
{
  "t": 123456,                 // millis ESP32
  "presence": 1,               // radar_presence
  "moving": 1, "still": 0,     // stato target
  "mdist": 145, "sdist": 0,    // distanze cm
  "menergy": 72, "senergy": 0, // energia target 0-100
  "pir": 1,                    // sensore PIR (confronto live!)
  "gates_m": [0,5,60,10,0,0,0,0,0],   // energia per-gate moving (eng. mode)
  "gates_s": [0,0,45,8,0,0,0,0,0],    // energia per-gate stationary
  "light": 25, "out": 1,       // light_level e out_level del frame (rev. 05/09: come il logger)
  "vitality": 54,              // indice di vitalità 0-100 (obiettivo 6, calcolato a bordo)
  "vitality_class": "vitalita_moderata"  // vitalita_bassa | vitalita_moderata | vitalita_alta
                               // (rev. 05/09: TRE classi, ANALISI_VITALITA.md §4;
                               //  con presence = 0 il campo è "" e vitality = 0)
}
```

Frequenza di push: **5 Hz** (uguale al campionamento — nessun sottocampionamento,
così il CSV esportato dal browser è equivalente a quello di acquire.py).

Statistiche di sessione (calcolate nel browser, non sull'ESP32):
- tempo di sessione, % campioni con presenza (radar e PIR separati)
- numero eventi di attivazione (fronti 0→1) radar e PIR → stima falsi positivi live
- distanza min/media/max, energia media
- ultima rilevazione (secondi fa) — il dato "salvavita" nello scenario DIPME
- vitalità: valore corrente, media mobile, minimo/massimo di sessione

---

## 3. Struttura della pagina (single-page, 4 aree)

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER   ● PRESENZA RILEVATA      [dist. 1.45 m]   [⏺ REC] │  ← stato colore:
├──────────────────────────┬──────────────────────────────────┤    verde/giallo/rosso
│  A. STATO LIVE           │  B. INDICE DI VITALITÀ           │
│  radar: MOVING @ 145cm   │       ┌─── gauge 0-100 ───┐      │
│  PIR:   ATTIVO           │       │        54          │      │
│  energia mov:  ▓▓▓▓ 72   │       │      "attivo"      │      │
│  energia still:▓▓   30   │       └────────────────────┘      │
├──────────────────────────┴──────────────────────────────────┤
│  C. GRAFICI                                                  │
│  C1: serie temporale energia moving/still + soglia (scorre) │
│  C2: barre per-gate (9 gate × moving/still) = "dov'è"       │
│  C3: timeline presenza radar vs PIR (confronto visivo!)     │
├──────────────────────────────────────────────────────────────┤
│  D. SESSIONE & EXPORT                                        │
│  scenario:[________] trial:[__] gt:[0|1]   ← metadati test  │
│  [Avvia sessione] [Stop] [Scarica CSV] [Reset statistiche]  │
│  stats: durata 12:34 | radar 97.2% | PIR 41.0% | eventi 3   │
└──────────────────────────────────────────────────────────────┘
```

Scelte di visualizzazione, in ordine di valore per la tesi:

1. **C3 — timeline radar vs PIR sovrapposte**: è l'obiettivo 3 reso visibile in diretta.
   Una persona ferma davanti al sensore vede il PIR spegnersi e il radar restare acceso:
   questo grafico da solo racconta metà della tesi in demo
2. **C2 — barre per-gate**: mostra "dove" è la persona (gate × 0.75 m), è il dato
   che nessun PIR può dare, e visualizza in diretta il superamento degli ostacoli
3. **B — gauge vitalità**: la "ciliegina" dell'obiettivo 6 in primo piano
4. **C1 — serie energia**: con persona immobile si VEDE l'oscillazione del respiro
   a occhio nudo (0.1-0.5 Hz) — ottimo effetto in sede di discussione

### Il form metadati (area D) — decisione progettuale chiave

Il CSV esportato dal browser include le stesse colonne di metadati di `acquire.py`
(`scenario, trial_id, ground_truth_presence, ground_truth_state`), compilate dal form.
Conseguenza: **i CSV della web UI si analizzano con gli stessi script**
(`analizza_test.py`, `analizza_respiro.py`) e la web UI può sostituire acquire.py
nelle campagne di test. Un solo formato dati in tutta la tesi:

```
firmware CSV (superset)  ==  CSV acquire.py  ==  CSV export web  →  Excel / script analisi
```

---

## 4. Struttura progettuale del software

```
firmware/ld2410b_web/
├── ld2410b_web.ino          # setup AP + DNS catch-all, loop: radar → stato condiviso
├── radar_task.h             # lettura MyLD2410 (riuso logica di ld2410b_logger)
├── vitality.h               # indice di vitalità v3: fondo per gate sottratto, doppia
│                            #   EWMA sull'energia del gate attivo, 3 classi
├── web_server.h             # ESPAsyncWebServer: statiche da PROGMEM (gzip) + WebSocket /ws
├── web_assets.h             # GENERATO da embed_web.py: i file di web/ in gzip
└── web/                     # sorgenti della pagina (tutto locale, ZERO CDN)
    ├── index.html           # struttura pagina (aree A-D)
    ├── style.css            # dark theme (dashboard di monitoraggio)
    ├── app.js               # WebSocket client, statistiche, buffer, export CSV
    └── chart.umd.min.js     # Chart.js v4 (~200 KB in chiaro, ~70 KB in gzip)
firmware/ld2410b_web/embed_web.py # comprime web/* e scrive web_assets.h (rev. 05/09)
```

**Perché PROGMEM e non LittleFS (rev. 05/09/2026)**: il plugin «ESP32 Sketch Data
Upload» previsto in origine **non esiste per l'Arduino IDE 2.x**; l'alternativa è un
VSIX esterno da installare a mano. Incorporare i file compressi in un header evita
tutto questo: **un solo upload**, nessuno strumento in più, e il server risponde con
`Content-Encoding: gzip` (tutti i browser lo decomprimono). Costo: ogni modifica alla
pagina richiede di rilanciare lo script e ricompilare (~1 min). Accettabile.

### Stack e librerie (rev. 05/09/2026)

| Componente | Scelta | Perché |
|---|---|---|
| Server HTTP+WS | **ESP32Async/ESPAsyncWebServer** + **ESP32Async/AsyncTCP** | non blocca il loop radar; WebSocket integrato. ⚠️ Il core ESP32 installato è il **3.3.11**: la libreria originale di me-no-dev **non compila** sul core 3.x, servono questi fork (nel Library Manager con lo stesso nome, autore «ESP32Async»). Nessuna delle due è ancora installata |
| DNS catch-all | **DNSServer** (nel core) | qualunque nome → `192.168.4.1`; portale riconosciuto dai telefoni |
| JSON | **ArduinoJson 7** | già installata |
| Pagina in flash | **PROGMEM gzip** (header generato) | vedi sopra; niente plugin, un solo upload |
| Grafici | **Chart.js v4** (bundle locale, gzip) | leggero, niente dipendenze, funziona offline |
| Export CSV | **Blob + download lato browser** | zero carico sull'ESP32, storico illimitato |
| Partizione flash | **Huge APP (3 MB No OTA / 1 MB SPIFFS)** | lo schema di default dà 1,2 MB all'applicazione; WiFi + server asincrono + ArduinoJson + MyLD2410 stanno intorno a 1,0-1,2 MB → «Sketch too big». Da impostare in Strumenti → Partition Scheme **prima** di compilare |

### Framework frontend: Angular valutato e scartato (rev. 05/09/2026)

Proposta dell'autore: scrivere la pagina in **Angular**, «così c'è il caricamento in
tempo reale dei dati». Valutazione:

- **Il tempo reale non dipende dal framework**: lo dà il WebSocket. Venti righe di
  JavaScript puro ricevono il messaggio a 5 Hz e aggiornano il DOM nello stesso
  istante di un componente Angular. Su questo punto Angular non aggiunge nulla
- Angular è comunque **fattibile**: `ng build` produce file statici che l'ESP32 serve
  come qualsiasi altro, e il proxy del dev server (`proxy.conf.json` con `ws: true`)
  permette di sviluppare sul PC parlando con l'ESP32 vero
- Costi: bundle di **100-200 KB in più**, toolchain Node da mantenere, ogni modifica
  passa per build → script di embed → compilazione → upload; il debug sul
  microcontrollore si fa su codice minificato
- L'applicazione è **una pagina con quattro riquadri**, circa 500 righe di JS:
  l'architettura a componenti e RxJS risolvono problemi che qui non ci sono

**Decisione: JavaScript puro.** Angular resta documentato qui come alternativa
considerata, con la motivazione: è la stessa logica con cui `ANALISI_SITO_SERVER.md`
documenta il server esterno scartato. Se in futuro la UI crescesse (più sensori, più
pagine, configurazione dal browser), la valutazione andrebbe rifatta: il firmware non
cambierebbe, solo la cartella `web/`.

### Flusso dati

```
LD2410B ──UART 256000──► ESP32 ──┬── Serial USB: CSV (resta attivo: debug/acquire.py)
                                 │
                    vitality.h ──┤
                                 └── WebSocket JSON 5 Hz ──► browser
                                                              ├─ render live (A,B,C)
                                                              ├─ ring buffer 60 s (grafici)
                                                              ├─ array sessione (illimitato)
                                                              └─ Blob → download .csv
```

Decisione: il **logging seriale resta attivo** insieme al WiFi — la web UI non
sostituisce il canale di test finché la Fase 2 del piano non è chiusa, ci gira accanto.

### Punti di attenzione tecnici

- **RAM**: niente storico sull'ESP32 — solo l'ultimo campione + accumulatori statistici.
  Lo storico vive nel browser
- **UART vs WiFi**: la lettura radar via `sensor.check()` va chiamata a ogni loop;
  con ESPAsyncWebServer il networking gira su callback e non ruba il loop — è il
  motivo principale per cui NON usare WebServer sincrono
- **Client multipli**: broadcast WebSocket a tutti i client connessi; limite pratico
  2-3 browser, sufficiente (demo: tablet del relatore + tuo PC)
- **Ordine dei float**: inviare interi dove possibile (energie, cm) per tenere i
  messaggi < 512 byte → un frame TCP, niente frammentazione

---

## 5. Statistiche nella pagina vs analisi in Excel — divisione dei compiti

| Dove | Cosa | Perché |
|---|---|---|
| **Web UI (live)** | presenza %, eventi, ultima rilevazione, vitalità, min/max | feedback immediato durante i test e in demo |
| **Excel (offline)** | medie ± dev.std multi-trial, confronti tra scenari, grafici della tesi | l'aggregazione tra file resta a `analizza_test.py` + Excel, come da obiettivo 5 |

La web UI **non** rifà l'analisi numerica: mostra la sessione corrente e produce il
CSV. L'analisi vera resta nella pipeline già costruita.

---

## 6. Piano di sviluppo incrementale (dettaglia la Fase 7 di PIANO_TEST.md)

Ogni step è funzionante e dimostrabile da solo:

1. **Step 1 — Access Point + pagina statica** (mezza giornata)
   ESP32 in AP con DNS catch-all, pagina «hello» servita da PROGMEM gzip. Verifica:
   collegando il telefono alla rete `DIPME-Sensor`, la pagina si apre sia su
   `192.168.4.1` sia su un nome qualsiasi (rev. 05/09)
2. **Step 2 — WebSocket live** (mezza giornata)
   JSON a 5 Hz, area A (stato testuale). Verifica: valori cambiano muovendosi davanti al sensore
3. **Step 3 — Grafici** (1 giorno)
   C1 serie energia, C2 barre per-gate, C3 timeline radar vs PIR
4. **Step 4 — Sessioni, statistiche, export CSV** (1 giorno)
   form metadati, accumulo, download. Verifica di accettazione: CSV esportato dal
   browser analizzato con `analizza_test.py` → stessi numeri del CSV seriale equivalente
5. **Step 5 — Indice di vitalità** (algoritmo v3 già tarato e validato il 31/08/2026)
   `vitality.h` a bordo + gauge. Verifica: riproducendo davanti al sensore i tre
   scenari a 1 m (immobile / micro-movimenti / cammino sul posto) la gauge dà le tre
   classi attese, e la stanza vuota dà vitality 0 (rev. 05/09: tre classi, non quattro)

**Test di accettazione finale** (chiude l'obiettivo 5): sessione di 10 min con la web UI
in parallelo al logging seriale → i due CSV devono dare le stesse statistiche.

---

## 7. Dimensionamento — l'ESP32 regge? (verifica numerica)

**Sì, con margini di 2-3 ordini di grandezza.** Il design non accumula nulla a bordo:
l'ESP32 tiene solo l'ultimo campione, lo storico vive nel browser.

### Volumi dati (messaggio JSON ~250 byte, push a 5 Hz)

| Flusso | Volume | Capacità | Utilizzo |
|---|---|---|---|
| WebSocket → 1 client | ~1.25 KB/s | WiFi ESP32 ~1-2 MB/s reali | ~0.1% |
| WebSocket → 3 client | ~3.75 KB/s | idem | ~0.3% |
| CSV seriale in parallelo | ~0.55 KB/s | USB 115200 ≈ 11.5 KB/s | ~5% |

### Memoria

| Dove | Consumo | Disponibile | Note |
|---|---|---|---|
| ESP32 heap | ~80-100 KB (WiFi+server) + ~10 KB/client WS | ~200 KB | stabile: nessun accumulo |
| Browser | ~2-3 MB per 30 min di sessione | centinaia di MB | anche 8 h (~35 MB) ok |
| CSV esportato | ~2 MB/ora (18.000 righe) | Excel: 1.048.576 righe | ~58 h in un file |

Limite reale: **client simultanei** (~4-5 browser per la RAM delle connessioni TCP) —
sufficiente per demo e test. In modalità AP il limite dei client WiFi associati è
configurabile (default 4): coincide con quello dei client WebSocket.

⚠️ **Flash, non RAM, è il vincolo che morde per primo** (rev. 05/09/2026): non per i
dati ma per il **codice**. Con lo schema di partizione di default l'applicazione ha
1,2 MB e lo stack WiFi + server asincrono la riempie quasi tutta. Con «Huge APP» ne ha
3 MB e la pagina compressa (~80 KB con Chart.js) ci sta con ampio margine.

### Quando servirebbe un server esterno (nessuno dei casi riguarda la tesi)

1. Storico persistente di giorni senza browser collegato (flash ESP32: ~1 h di CSV)
2. Aggregazione multi-sensore — nel progetto DIPME reale la fa il gateway LoRa, non il nodo
3. Accesso remoto da internet — fuori scope, e in emergenza l'infrastruttura è assente

Argomento per la tesi: nel dominio DIPME il nodo DEVE essere autonomo (in emergenza
non c'è infrastruttura) — il server esterno sarebbe concettualmente sbagliato, non
solo superfluo.

---

## 8. Estensioni possibili (se avanza tempo — non necessarie alla tesi)

- Supporto secondo sensore (LD2420) con selettore nella UI
- Modalità "emergenza" simulata: sfondo rosso, solo dato salvavita ("persona viva
  sotto il banco: SÌ/NO + vitalità") → mockup del tablet soccorritore DIPME
- Grafico spettro FFT live del respiro (porting di analizza_respiro.py in JS)
- Salvataggio sessioni in LittleFS per funzionare senza browser collegato
- Modalità **Station** (l'ESP32 si collega a una rete esistente, con fallback all'AP):
  comoda in sviluppo, esclusa dalla v1 il 05/09/2026 per coerenza con lo scenario
  senza infrastruttura
- Frontend in Angular, se la UI crescesse oltre la pagina singola (valutazione in §4)

---

## 9. Riferimento esterno — "LD2410 Configurator" di Albert Nisbet

**https://ld2410.albert.nz/** — sorgenti: https://github.com/albertnis/ld2410-configurator

⚠️ **Non è uno strumento ufficiale Hi-Link**: è un progetto open source di comunità,
nato esplicitamente come *"easy-to-use, cross-platform alternative to the Windows-only
tooling provided by HiLink"*. Sotto la regola fonti vale come **riferimento di
UI/UX e di implementazione**, non come fonte autorevole di dati tecnici (per quelli
resta il datasheet).

### Come funziona (verificato 09/08/2026 ispezionando la pagina)
- **Nessun server**: è una SPA statica su Cloudflare Pages che parla **direttamente**
  al sensore dal browser via **Web Serial API** (`navigator.serial`) oppure
  **Web Bluetooth** (`navigator.bluetooth`) — il bundle JS è di soli ~49 KB e non
  contiene librerie di grafici (rendering fatto a mano)
- Solo browser Chromium (Chrome/Edge/Opera): Firefox e Safari non implementano Web Serial
- Supporta LD2410B e LD2410C; il baud è selezionabile (9600 → 460800, default 256000)
- Bluetooth: chiede la password del modulo (default `HiLink`)
- La schermata iniziale ha due card, **Serial** e **Bluetooth**, con le istruzioni di
  cablaggio, e in basso un pannello **Monitor** con il traffico grezzo **RX/TX**

### Cosa prendere per il nostro sito
1. **Pannello Monitor RX/TX** — un riquadro di debug col traffico seriale grezzo:
   costa poco e in fase di test fa risparmiare ore (equivale al nostro `ERROR: radar
   not detected` ma leggibile)
2. **Stato di connessione sempre visibile in alto** ("Disconnected"/"Connected"):
   nel nostro caso è lo stato del WebSocket — già previsto nella §3, conferma la scelta
3. **Zero dipendenze esterne**: nessuna CDN, nessuna libreria di grafici. Coerente col
   nostro vincolo di funzionare offline; conferma che i 3 grafici della §3 si possono
   disegnare in canvas/SVG a mano senza Chart.js
4. **Istruzioni di cablaggio dentro la UI** — utile per la demo al professore

### Cosa NON prendere
- È un **configuratore**, non un **logger**: non fa storico, statistiche di sessione,
  né export CSV. Sono esattamente i pezzi che l'obiettivo 5 richiede a noi
- La connessione diretta browser↔sensore esclude l'ESP32: perderemmo PIR, timestamp
  coerenti, indice di vitalità a bordo e il confronto PIR vs mmWave sulla stessa base tempi

### Nota architetturale — un'opzione D che non avevamo considerato
Web Serial apre una terza via: **browser → USB → ESP32** (la pagina legge le righe CSV
già prodotte dal firmware, senza WiFi né WebSocket). Pro: nessuno stack di rete da
scrivere, si riusa il logger così com'è. Contro: il cavo USB deve restare attaccato,
niente demo wireless "nodo autonomo", e si perde l'analogia con la piattaforma DIPME.
**La scelta resta A** (sito servito dall'ESP32), ma l'opzione D è un ottimo **piano di
riserva a basso costo** se il WiFi a bordo desse problemi: il frontend è lo stesso,
cambia solo la sorgente dei dati (una funzione `connect()` al posto del WebSocket).
