# Progetto di dettaglio — Sito di visualizzazione dati (Obiettivo 5)

> Questo documento scende al livello implementativo: componenti della pagina,
> protocollo di comunicazione, strutture dati, algoritmi e criteri di accettazione.
> Le decisioni architetturali (perché self-hosted, perché WebSocket, dimensionamento)
> sono in `ANALISI_WEB_UI.md` — qui si assume tutto ciò come deciso.

---

## 1. Mappa dei file e responsabilità

```
firmware/ld2410b_web/
├── ld2410b_web.ino     # entry point: setup + loop
├── config.h            # SSID/password, pin, costanti (unico file da toccare per configurare)
├── radar_task.h        # lettura MyLD2410 → struct RadarSample (riuso da ld2410b_logger)
├── vitality.h          # calcolo indice vitalità → int 0-100 + classe
├── web_server.h        # HTTP statico + WebSocket /ws + broadcast JSON
└── data/               # → LittleFS (upload con plugin "ESP32 Sketch Data Upload")
    ├── index.html      # markup delle 4 aree (nessuna logica inline)
    ├── style.css       # tema scuro, layout grid, classi di stato
    ├── app.js          # TUTTA la logica client (WS, stats, buffer, CSV, grafici)
    └── chart.umd.min.js# Chart.js v4 locale (~70 KB) — NIENTE CDN
```

Regola: **una direzione sola dei dati** — il firmware pubblica, il browser elabora.
L'ESP32 non riceve comandi dal browser (v1): niente configurazione radar via web,
si usa l'app Bluetooth. Semplifica enormemente firmware e superficie di errore.

---

## 2. Lato firmware

### 2.1 Struttura dati condivisa

```cpp
// radar_task.h
struct RadarSample {
  uint32_t t;            // millis()
  bool     presence, moving, still;
  uint16_t mdist, sdist;      // cm
  uint8_t  menergy, senergy;  // 0-100
  bool     pir;
  uint8_t  gatesM[9], gatesS[9];  // engineering mode
  uint8_t  vitality;          // 0-100 (calcolato da vitality.h)
  const char* vitalityClass;  // puntatore a stringa statica
};
extern RadarSample lastSample;   // scritto dal loop, letto dal broadcast
```

Un solo campione condiviso, aggiornato nel loop: nessuna coda, nessun mutex necessario
(il broadcast legge sempre e solo l'ultimo stato — perdere un campione non è un errore).

### 2.2 Loop principale (pseudocodice)

```cpp
void loop() {
  sensor.check();                          // parsing UART a ogni giro (mai bloccare!)
  if (millis() - lastTick >= 200) {        // 5 Hz
    lastTick = millis();
    aggiornaSample(lastSample);            // legge MyLD2410 → struct
    lastSample.vitality = vitalityUpdate(lastSample);   // EWMA, vedi 2.4
    stampaCSVSeriale(lastSample);          // canale seriale SEMPRE attivo (test/debug)
    wsBroadcast(lastSample);               // → tutti i client connessi
  }
}
```

Niente `delay()`. ESPAsyncWebServer gestisce HTTP/WS su callback: il loop resta
dedicato al radar.

### 2.3 Serializzazione JSON (ArduinoJson 7)

```cpp
// web_server.h — buffer riusato, mai allocazioni nel loop
JsonDocument doc;   // ArduinoJson 7: StaticJsonDocument<N> è deprecato
char out[512];

void wsBroadcast(const RadarSample& s) {
  if (ws.count() == 0) return;      // nessun client: zero lavoro
  doc.clear();
  doc["t"] = s.t;  doc["presence"] = s.presence ? 1 : 0;
  // ... campi come da schema in ANALISI_WEB_UI.md §2 ...
  JsonArray gm = doc["gates_m"].to<JsonArray>();
  for (int i = 0; i < 9; i++) gm.add(s.gatesM[i]);
  // idem gates_s
  size_t n = serializeJson(doc, out);
  ws.textAll(out, n);
}
```

### 2.4 Indice di vitalità (vitality.h)

L'algoritmo è un **obiettivo di tesi a sé** (obiettivo 6) e ha il suo documento di
specifica: **`ANALISI_VITALITA.md`** (algoritmo, razionale, taratura sui CSV della
Fase 6, validazione, casi limite). Qui interessa solo il contratto verso il sito:

- `vitality.h` implementa l'algoritmo di ANALISI_VITALITA.md §3 con le costanti
  tarate in Python — il porting avviene SOLO a soglie validate (step 5)
- output per il JSON: `vitality` (int 0-100) e `vitality_class` (stringa)
- mappatura classe → colore nella UI: `nessun_segno`=grigio, `vitalita_bassa`=giallo,
  `moderato`=arancio, `attivo`=verde (stesse variabili CSS di §3.7)
- se `presence == 0` → vitality = 0 (forzatura, definita nella specifica)

### 2.5 Endpoint HTTP

| Rotta | Risposta | Note |
|---|---|---|
| `GET /` | index.html da LittleFS | |
| `GET /style.css`, `/app.js`, `/chart.umd.min.js` | statici LittleFS | cache header 1h |
| `GET /ws` | upgrade WebSocket | max 4 client: il 5° viene rifiutato |
| `GET /info` | JSON: versione fw, uptime, heap libero, client WS | diagnostica |

### 2.6 WiFi (config.h)

```
1. prova STA con SSID/password di config.h, timeout 15 s
2. fallback AP: SSID "UPRISE-Sensor", password "uprise2026", IP 192.168.4.1
3. stampa su seriale l'IP effettivo (unica riga NON-CSV, prefissata con "# " così
   acquire.py e analizza_test.py la ignorano)
```

---

## 3. Lato browser (app.js)

### 3.1 Strutture dati

```js
const state = {
  live: null,                 // ultimo messaggio ricevuto (render aree A e B)
  ring: [],                   // ultimi 300 campioni (60 s @ 5 Hz) → grafici C1/C3
  session: {                  // null se non in registrazione
    meta: {scenario, trial, gt, gtState},  // dal form area D
    rows: [],                 // TUTTI i campioni della sessione (per il CSV)
    t0: null,                 // Date.now() all'avvio
  },
  stats: {                    // accumulatori, aggiornati incrementalmente O(1)
    n: 0, radarOn: 0, pirOn: 0,          // → percentuali
    radarEvents: 0, pirEvents: 0,        // fronti 0→1 (serve lastRadar/lastPir)
    lastDetection: null,                 // timestamp ultima presenza
    distSum: 0, distN: 0, distMin: ∞, distMax: 0,
    vitMin: 100, vitMax: 0,
  }
};
```

Il ring buffer è troncato a 300 (`if (ring.length > 300) ring.shift()`); l'array
`session.rows` invece cresce libero — 2-3 MB/30 min, nessun limite pratico.

### 3.2 WebSocket con riconnessione

```js
function connect() {
  ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onmessage = (e) => onSample(JSON.parse(e.data));
  ws.onclose   = () => { setStatoUI('disconnesso');        // banner rosso
                         setTimeout(connect, 2000); }      // retry infinito ogni 2 s
  ws.onopen    = () => setStatoUI('connesso');
}
```

Watchdog dati: se non arrivano messaggi per >3 s con WS aperto → banner giallo
"sensore non risponde" (WS vivo ma radar muto = problema UART/alimentazione).

### 3.3 Pipeline di ogni campione

```js
function onSample(m) {
  state.live = m;
  updateStats(m);                    // O(1), niente ricalcoli su array
  state.ring.push(m); trimRing();
  if (state.session) state.session.rows.push(m);
  renderLive(m);                     // aree A+B: textContent + classi CSS
  if (++frame % 2 === 0) renderCharts();  // grafici a 2.5 Hz: fluido e leggero
}
```

I grafici si aggiornano a metà frequenza (2.5 Hz) con `chart.update('none')`
(niente animazioni): su tablet resta fluido.

### 3.4 I tre grafici (Chart.js)

| ID | Tipo | Serie | Config chiave |
|---|---|---|---|
| C1 energia | `line` | menergy, senergy vs tempo (ring) | y: 0-100 fisso; x: time scale 60 s scorrevole |
| C2 gate | `bar` | 9 gate × 2 dataset (moving/still) | x: etichette "0-0.75m", "0.75-1.5m", …; y: 0-100 |
| C3 presenza | `line` stepped | radar_presence e pir+offset | y: {0,1} radar, {1.5,2.5} PIR → due tracce parallele leggibili |

C3 è il grafico-tesi (radar vs PIR in diretta): il PIR è disegnato traslato in alto
per non sovrapporsi al radar — si legge come due timeline parallele.

### 3.5 Sessioni ed export CSV

- **Avvia sessione**: valida il form (scenario non vuoto, gt ∈ {0,1}) → azzera stats
  e rows, `t0 = Date.now()`, bottone diventa "⏺ REC hh:mm:ss"
- **Stop**: congela; i dati restano in memoria finché non si avvia una nuova sessione
- **Scarica CSV**: genera client-side e scarica — **stesse colonne di acquire.py**:

```js
const HEADER = "timestamp_ms,radar_presence,moving_target,stationary_target," +
  "moving_distance_cm,stationary_distance_cm,moving_energy,stationary_energy," +
  "pir_presence," + gateCols() +                       // menergy_gate0..8,senergy_gate0..8
  ",pc_time_s,group_id,trial_id,scenario,ground_truth_presence,ground_truth_state";

function scaricaCSV() {
  const righe = state.session.rows.map(r => [ /* campi in ordine */ ].join(","));
  const blob = new Blob([HEADER + "\n" + righe.join("\n")], {type: "text/csv"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${meta.scenario}_${meta.trial}.csv`;    // stessa convenzione del piano
  a.click(); URL.revokeObjectURL(a.href);
}
```

`pc_time_s` = `t0/1000 + (r.t - rows[0].t)/1000` — coerente con acquire.py.
Nome file = `<scenario>_<trial>.csv` → gli script di analisi aggregano senza modifiche.

### 3.6 Comportamento dei componenti UI (aree A-D)

**Header (sempre visibile)**
- Pallone di stato: 🟢 presenza / 🟡 solo stazionario / ⚫ vuoto / 🔴 disconnesso
- Distanza corrente in metri (target prioritario: moving se presente, altrimenti still)
- Badge REC lampeggiante quando la sessione è attiva

**A — Stato live**: valori testuali con classi CSS di stato (`.on`/`.off`);
barre orizzontali per menergy/senergy (div con width %, niente librerie)

**B — Gauge vitalità**: arco SVG 0-100 (niente librerie: `stroke-dasharray`),
colore = classe vitalità, etichetta classe sotto il numero

**C — Grafici**: come §3.4; sotto C2 una riga di testo "persona nel gate N (~X m)"

**D — Sessione**: form (scenario, trial, gt presenza sì/no, stato) + 4 bottoni;
riquadro statistiche aggiornato 1 volta/s: durata, radar %, PIR %, eventi radar/PIR,
ultima rilevazione X s fa, distanza min/med/max, vitalità min/max

### 3.7 Stile (style.css) — regole essenziali

- Tema scuro (`#121417` fondo, testo `#e8eaed`) — dashboard di monitoraggio, riduce
  affaticamento in demo e fa risaltare i colori di stato
- CSS Grid: 2 colonne desktop/tablet landscape, 1 colonna sotto 700 px (telefono)
- Colori di stato centralizzati in variabili CSS (`--ok`, `--warn`, `--alert`, `--off`)
  = stessi colori in grafici, gauge e badge
- Zero framework CSS: ~150 righe scritte a mano bastano e pesano nulla su LittleFS

---

## 4. Gestione errori ed edge case

| Caso | Comportamento |
|---|---|
| WS cade (ESP32 riavvia, WiFi perso) | banner rosso + retry 2 s; ring/session INTATTI (si riprende ad accumulare) |
| Radar muto >3 s con WS vivo | banner giallo "sensore non risponde" |
| 5° client WS | rifiutato dal firmware; pagina mostra "troppi client" |
| Refresh pagina durante sessione | dati di sessione PERSI (stanno in RAM JS) → warning `beforeunload` se REC attivo |
| Heap ESP32 basso (<20 KB) | `/info` lo espone; il firmware chiude il client WS più vecchio |
| Valori mancanti nel frame radar (engineering off) | gates a 0 nel JSON; C2 mostra barre vuote, il resto vive |

Il refresh che perde la sessione è accettato in v1 (i test "ufficiali" hanno comunque
il canale seriale in parallelo); l'alternativa (persistenza in localStorage/IndexedDB)
è nell'elenco estensioni.

---

## 5. Sequenza di implementazione con criteri di accettazione

Riprende i 5 step di ANALISI_WEB_UI.md §6, con il "definition of done" di ciascuno:

| Step | Contenuto | Accettazione (verificabile) |
|---|---|---|
| 1 | config.h, WiFi STA+fallback AP, LittleFS, index statico | pagina raggiungibile da telefono in entrambe le modalità; IP stampato su seriale |
| 2 | WS + broadcast JSON + area A testuale | valori cambiano <0.5 s dopo un movimento; riconnessione automatica dopo reset ESP32 |
| 3 | Chart.js locale + C1/C2/C3 + gauge B | 10 min di run senza rallentamenti su tablet; C3 mostra PIR che cade e radar che resta con persona ferma |
| 4 | form sessione, stats, export CSV | **CSV web di 5 min analizzato da analizza_test.py = stessi numeri (±1 campione) del CSV seriale acquisito in parallelo** |
| 5 | vitality.h a bordo + gauge collegata | i 4 scenari `vitalita_*` della Fase 6 producono le 4 classi attese |

L'accettazione dello step 4 è il cuore: dimostra che web UI e pipeline dati della tesi
sono lo stesso sistema, non due sistemi paralleli.

---

## 6. Cosa resta fuori (v1) — deciso, non dimenticato

- Configurazione del radar dal browser (si usa l'app Bluetooth HLKRadarTool)
- Persistenza sessioni su ESP32/localStorage
- Autenticazione (rete locale/AP dedicato: superflua per la tesi)
- HTTPS/WSS (l'ESP32 lo reggerebbe a fatica; inutile su rete propria)
- Supporto LD2420 nella UI (estensione, vedi ANALISI_WEB_UI.md §8)
