# Analisi alternativa — Sito "vero" su server esterno (Obiettivo 5, opzione B)

> **Perché questo documento.** L'obiettivo 5 dice: *"l'ESP32 pubblica i dati → sito
> web per visualizzazione in tempo reale → la stessa app salva i dati con statistiche
> → export CSV"*. In `ANALISI_WEB_UI.md` §1 è stata scelta l'opzione **A** (sito
> servito dall'ESP32 stesso). Esiste però il rischio che il professore, con "sito
> web", intenda un **sito vero e proprio**: un'applicazione web classica con un
> server, un database e uno storico — cioè l'opzione **B** della tabella di
> ANALISI_WEB_UI.md, lì scartata ma mai progettata. Questo documento la progetta
> **fino al livello implementativo**, così che se all'incontro il professore chiede
> la B, il progetto è già pronto e il cambio di rotta costa giorni, non settimane.
>
> **Questo documento non ribalta la decisione**: A resta la scelta di default.
> È il piano di riserva completo, più i criteri per decidere con il professore (§9).

---

## 1. Cosa significa "sito vero" e cosa cambia davvero

### 1.1 Le due letture della stessa frase

La frase del professore *"l'ESP32 pubblica i dati → sito web"* ammette due letture:

| Lettura | Architettura | "Pubblica" significa |
|---|---|---|
| **A — nodo autonomo** | il sito È dentro l'ESP32 | l'ESP32 serve una pagina web ai client sulla sua rete |
| **B — piattaforma** | l'ESP32 è solo una sorgente dati; il sito vive su un server | l'ESP32 *pubblica* (in senso MQTT/IoT) i dati verso un sistema esterno |

Il verbo "pubblicare" nel gergo IoT è il verbo di **MQTT** (*publish/subscribe*), e
l'ecosistema del professore è esattamente questo: DIPME-DEVICE → LoRa →
DIPME-COORDINATOR → **gateway Linux/Raspberry (DIPME DRIVER) → piattaforma di
monitoraggio** con modalità "tempo di pace" e "tempo di guerra" (slide Sharper,
26/09/2025). Nella lettura B, la web app della tesi è la **miniatura della
piattaforma di monitoraggio SAFE**, non del nodo.

### 1.2 Cosa cambia concettualmente (A → B)

| Aspetto | A (ESP32 self-hosted) | B (server esterno) |
|---|---|---|
| Dove vive lo storico | nel **browser** (RAM JS, perso al refresh) | in un **database** sul server (persistente) |
| Sessioni di test | gestite dal browser | gestite dal server (sopravvivono a refresh/crash) |
| Export CSV | generato client-side (Blob) | generato server-side da query SQL |
| Client simultanei | 2-4 (RAM ESP32) | decine (limite: il server) |
| Storico consultabile a posteriori | no (solo sessione corrente) | sì (query per data/sessione) |
| Multi-sensore | estensione difficile | nativo (ogni nodo pubblica su un topic) |
| Funziona senza infrastruttura | **sì** (AP mode) | no: servono broker + server accesi |
| Cosa dimostra rispetto a UPRISE | il nodo autonomo in emergenza | la piattaforma di monitoraggio in tempo di pace |
| Complessità (componenti da far parlare) | 2 (ESP32, browser) | 4 (ESP32, broker, server, browser) |

Il punto architetturale profondo: in A lo storico vive nel browser *perché non c'è
nessun altro posto dove metterlo*; in B esiste finalmente un posto giusto (il DB), e
di conseguenza sessioni, statistiche e CSV **migrano dal client al server**. Il
frontend si alleggerisce, il sistema si complica.

### 1.3 Argomento chiave: le due opzioni mappano due parti diverse del progetto UPRISE

Non è "una giusta e una sbagliata": mappano **due componenti reali** del sistema SAFE.

- **A** = il DIPME-DEVICE ideale: nodo che in emergenza, senza infrastruttura, espone
  da solo il dato salvavita.
- **B** = il DIPME-DRIVER + piattaforma: aggregazione, storico, monitoraggio ordinario.

Questa mappatura è l'argomento da portare all'incontro (§9): qualunque cosa scelga il
professore, la scelta si difende nel contesto del progetto — e con il frontend
condiviso (§7) si possono perfino fare **entrambe** a costo marginale contenuto.

---

## 2. Architettura proposta (opzione B)

```
                    ┌────────────────── PC/Raspberry "server" ──────────────────┐
                    │                                                            │
ESP32 ──WiFi(STA)──►│  Mosquitto        FastAPI (Python)          Browser(i)     │
 │  MQTT publish    │  (broker MQTT) ──► ├─ subscriber MQTT   ◄──WS──  dashboard │
 │  JSON @ 5 Hz     │   porta 1883       ├─ SQLite (storico)  ◄──HTTP─ export CSV│
 │                  │                    ├─ WebSocket /ws (live)                 │
 └─UART LD2410B     │                    └─ REST /api/* (sessioni, storico)      │
   (+ PIR GPIO)     └────────────────────────────────────────────────────────────┘
```

Quattro componenti, un solo host per gli ultimi tre: **broker, backend e frontend
girano sulla stessa macchina** (il laptop durante lo sviluppo; opzionalmente un
Raspberry per la demo — che tra l'altro è lo stesso hardware del DIPME DRIVER).

### 2.1 Scelta del trasporto ESP32 → server

| Trasporto | Pro | Contro |
|---|---|---|
| **MQTT (publish)** ✅ | standard IoT (OASIS), è letteralmente "pubblicare i dati", disaccoppia sensore e server (il nodo non sa chi ascolta), multi-sensore gratis (un topic per nodo), LWT segnala il nodo offline, librerie mature (PubSubClient) | serve il broker (un processo in più) |
| HTTP POST dal nodo | zero broker, semplicissimo | 5 richieste/s = overhead TCP/HTTP inutile; il nodo deve conoscere l'URL del server; niente notifica di disconnessione; "posta" più che "pubblica" |
| WebSocket client dal nodo | connessione persistente, efficiente | librerie WS client su ESP32 meno mature del MQTT; riconnessione a carico nostro; nessun vantaggio su MQTT |

**Scelta: MQTT.** Motivazioni in ordine di peso:
1. È l'interpretazione letterale di "l'ESP32 pubblica i dati" nel lessico IoT
2. Coerenza con l'ecosistema del professore (architettura a gateway; in SAFE i nodi
   non parlano mai direttamente con la piattaforma)
3. In tesi si può scrivere un paragrafo serio su publish/subscribe vs request/response
4. Estensione multi-sensore (LD2420 su un secondo ESP32) = zero modifiche al backend

*Variante minimale B1* (se si vuole tagliare il broker): HTTP POST batch — l'ESP32
accumula 5 campioni e fa 1 POST/s a FastAPI. Funziona, ma si perde l'argomento 1-2-4;
citata qui per completezza, non sviluppata oltre.

### 2.2 Scelta del backend

| Opzione | Pro | Contro |
|---|---|---|
| **Python + FastAPI** ✅ | Python è GIÀ il linguaggio della tesi (acquire.py, analizza_test.py, analizza_respiro.py); FastAPI ha WebSocket nativi, validazione automatica, docs OpenAPI gratis su `/docs` (bello in demo); asyncio regge 5 Hz × N client senza pensarci | — |
| Node.js + Express | ecosistema web enorme | linguaggio in più nella tesi senza motivo |
| Flask | minimale | WebSocket non nativi (serve flask-sock/socketio), niente async |
| PHP + hosting condiviso | "sito classico" | nessun supporto sensato per dati push in tempo reale |

**Scelta: FastAPI.** Il punto decisivo è la coerenza: tutta la pipeline di analisi
della tesi è Python — il backend riusa perfino le convenzioni CSV già scritte.

### 2.3 Scelta del database

| Opzione | Pro | Contro |
|---|---|---|
| **SQLite** ✅ | zero installazione (modulo standard Python), un file = backup banale (regola backup dei CSV estesa al DB), transazionale, in WAL mode regge migliaia di insert/s — noi ne facciamo 5 | non concorrente multi-processo (irrilevante: un solo writer) |
| InfluxDB / TimescaleDB | time-series "vere", downsampling nativo | un servizio in più da installare e imparare, per volumi che non lo giustificano (§8) |
| PostgreSQL | robusto | server DB da amministrare, overkill totale |

**Scelta: SQLite in WAL mode.** Ai nostri volumi (§8) è sovrabbondante di 2-3 ordini
di grandezza, e "il database è un file nella cartella del progetto" è un vantaggio
concreto per backup e consegna della tesi.

### 2.4 Dove gira il server

| Host | Quando | Note |
|---|---|---|
| **Laptop Windows (sviluppo)** ✅ | tutta la fase di sviluppo e i test | Mosquitto ha l'installer Windows; Python già presente |
| Raspberry Pi (demo) | se si vuole la demo "da piattaforma" | stesso ruolo hardware del DIPME DRIVER — ottimo argomento; systemd per l'avvio automatico |
| VPS/cloud | mai, per questa tesi | contraddice lo scenario UPRISE (emergenza = niente internet), aggiunge auth/HTTPS obbligatori, costi |

Nota concettuale da scrivere in tesi: anche nell'opzione B il server resta **sulla
rete locale** — la "piattaforma" UPRISE è on-premise (gateway in loco), non un cloud.

---

## 3. Contratto dati: topic MQTT e payload

### 3.1 Topic

```
uprise/<node_id>/data     ← telemetria JSON a 5 Hz (QoS 0, no retain)
uprise/<node_id>/status   ← "online"/"offline" (retain + LWT, vedi §4)
```

`<node_id>` = `ld2410b-01` (hardcoded in config.h; un futuro LD2420 sarà `ld2420-01`
e il backend lo ingerisce senza modifiche).

### 3.2 Payload

**Identico al JSON dell'opzione A** (ANALISI_WEB_UI.md §2) — questa è la decisione
che rende A e B intercambiabili:

```json
{
  "t": 123456,
  "presence": 1, "moving": 1, "still": 0,
  "mdist": 145, "sdist": 0,
  "menergy": 72, "senergy": 0,
  "pir": 1,
  "gates_m": [0,5,60,10,0,0,0,0,0],
  "gates_s": [0,0,45,8,0,0,0,0,0],
  "vitality": 54, "vitality_class": "attivo"
}
```

~250-300 byte serializzati. QoS 0 (fire-and-forget): perdere un campione su 5 Hz non
è un errore, esattamente come nel broadcast WebSocket dell'opzione A — e QoS 1/2
introdurrebbero ritrasmissioni inutili.

⚠️ **Trappola nota di PubSubClient**: il buffer di default è **256 byte**
(`MQTT_MAX_PACKET_SIZE`) — il nostro payload NON ci sta e la publish fallirebbe
silenziosamente (ritorna `false`). Obbligatorio `mqtt.setBufferSize(512)` nel setup.

---

## 4. Lato firmware — `firmware/ld2410b_mqtt/`

### 4.1 Cosa cambia rispetto a `ld2410b_web` (opzione A)

| Componente | Opzione A | Opzione B |
|---|---|---|
| `radar_task.h` | lettura MyLD2410 → `RadarSample` | **identico** (riuso al 100%) |
| `vitality.h` | EWMA a bordo | **identico** (riuso al 100%) |
| `web_server.h` | ESPAsyncWebServer + WS + LittleFS | **sparisce** — sostituito da `mqtt_client.h` (più semplice) |
| `data/` (LittleFS) | pagina web a bordo | **sparisce** — la pagina vive sul server |
| WiFi | STA + fallback AP | **solo STA** (il server è sulla rete; l'AP non ha senso in B) |
| CSV seriale | attivo | attivo (invariato: resta il canale di riferimento dei test) |

Il firmware B è **più semplice** del firmware A: niente filesystem, niente server
HTTP, niente gestione client. Tutta la complessità trasloca sul server.

### 4.2 Sketch di riferimento

```cpp
// ld2410b_mqtt.ino — pubblica RadarSample via MQTT a 5 Hz
#include <WiFi.h>
#include <PubSubClient.h>      // knolleary/pubsubclient
#include <ArduinoJson.h>
#include "config.h"            // WIFI_SSID, WIFI_PASS, MQTT_HOST, NODE_ID
#include "radar_task.h"        // riuso da ld2410b_web: sensor + RadarSample
#include "vitality.h"          // riuso da ld2410b_web

WiFiClient   net;
PubSubClient mqtt(net);

char topicData[48], topicStatus[48];
uint32_t lastTick = 0, lastMqttRetry = 0;

void setup() {
  Serial.begin(115200);
  radarBegin();                              // Serial2 verso LD2410B + eng. mode
  snprintf(topicData,   sizeof(topicData),   "uprise/%s/data",   NODE_ID);
  snprintf(topicStatus, sizeof(topicStatus), "uprise/%s/status", NODE_ID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);          // solo STA: senza rete B non esiste

  mqtt.setServer(MQTT_HOST, 1883);
  mqtt.setBufferSize(512);                   // ⚠ default 256 B: payload non ci sta
}

// riconnessione NON bloccante: un tentativo ogni 5 s, il radar non si ferma mai
void mqttTick() {
  if (mqtt.connected()) { mqtt.loop(); return; }
  if (millis() - lastMqttRetry < 5000) return;
  lastMqttRetry = millis();
  // LWT: se il nodo sparisce, il broker pubblica "offline" (retained) per noi
  if (mqtt.connect(NODE_ID, topicStatus, 0, true, "offline")) {
    mqtt.publish(topicStatus, "online", true);
    Serial.println("# MQTT connesso");       // prefisso "# ": ignorato da acquire.py
  }
}

void publishSample(const RadarSample& s) {
  static JsonDocument doc;      // ArduinoJson 7: StaticJsonDocument è deprecato
  static char out[512];
  doc.clear();
  doc["t"] = s.t;  doc["presence"] = s.presence ? 1 : 0;
  doc["moving"] = s.moving ? 1 : 0;  doc["still"] = s.still ? 1 : 0;
  doc["mdist"] = s.mdist;   doc["sdist"] = s.sdist;
  doc["menergy"] = s.menergy; doc["senergy"] = s.senergy;
  doc["pir"] = s.pir ? 1 : 0;
  JsonArray gm = doc["gates_m"].to<JsonArray>();
  JsonArray gs = doc["gates_s"].to<JsonArray>();
  for (int i = 0; i < 9; i++) { gm.add(s.gatesM[i]); gs.add(s.gatesS[i]); }
  doc["vitality"] = s.vitality;
  doc["vitality_class"] = s.vitalityClass;
  size_t n = serializeJson(doc, out);
  mqtt.publish(topicData, (uint8_t*)out, n);  // QoS 0
}

void loop() {
  sensor.check();                            // UART a ogni giro, mai bloccare
  mqttTick();
  if (millis() - lastTick >= 200) {          // 5 Hz, come A
    lastTick = millis();
    aggiornaSample(lastSample);
    lastSample.vitality = vitalityUpdate(lastSample);
    stampaCSVSeriale(lastSample);            // canale seriale SEMPRE attivo
    if (mqtt.connected()) publishSample(lastSample);
  }
}
```

Punti di attenzione:
- **Mai bloccare il loop**: la riconnessione MQTT è a tentativo singolo ogni 5 s
  (il classico `while (!mqtt.connected()) { ... delay(1000); }` degli esempi
  PubSubClient fermerebbe la lettura radar — vietato)
- **LWT (Last Will and Testament)**: il broker pubblica `offline` su
  `uprise/<node>/status` se il nodo sparisce senza disconnessione pulita → la
  dashboard mostra il banner "nodo offline" senza watchdog custom
- Se il WiFi/MQTT è giù, i campioni **non si accumulano**: si perde il live ma il
  CSV seriale continua — stessa filosofia dell'opzione A (il canale dei test
  ufficiali è la seriale finché la Fase 2 non è chiusa)
- Libreria: **PubSubClient** (knolleary) — la più diffusa e documentata per ESP32;
  alternativa più moderna AsyncMqttClient, non necessaria a 5 Hz

---

## 5. Broker — Mosquitto

Eclipse Mosquitto, lo standard de facto open source (usato anche nella didattica IoT).

### 5.1 Installazione

- **Windows (sviluppo)**: installer ufficiale da mosquitto.org/download → servizio
  Windows già configurato
- **Raspberry/Linux (demo)**: `sudo apt install mosquitto mosquitto-clients`

### 5.2 Configurazione minima (`mosquitto.conf`)

```
listener 1883 0.0.0.0
allow_anonymous true
```

⚠️ **Da Mosquitto 2.0 il default è solo-localhost e senza anonimi**: senza queste due
righe l'ESP32 non si connette e il sintomo è un timeout silenzioso — è il primo posto
dove guardare in troubleshooting. `allow_anonymous true` è accettabile SOLO perché la
rete è locale/dedicata (stessa argomentazione no-auth dell'opzione A, §11).

### 5.3 Test di fumo (prima ancora di scrivere il backend)

```
mosquitto_sub -h localhost -t "uprise/#" -v
```

Se lo sketch §4.2 funziona, qui scorrono 5 JSON al secondo. Questo test isola il
firmware dal backend: metà del debugging diventa banale.

### 5.4 Trappole di rete note (da controllare PRIMA di sospettare il codice)

1. **Windows Firewall**: al primo avvio blocca le connessioni in ingresso sia verso
   Mosquitto (porta 1883, l'ESP32 non si connette) sia verso uvicorn (porta 8000,
   tablet/telefono non vedono la dashboard). Sintomo identico a "broker spento":
   timeout silenzioso. Consentire le due porte (o le app) in Windows Defender
   Firewall per reti private
2. **IP del server**: `MQTT_HOST` è scritto in config.h — se il laptop prende l'IP
   via DHCP, a ogni cambio l'ESP32 pubblica nel vuoto. Soluzioni: prenotazione DHCP
   nel router (preferita) o IP statico; l'mDNS (`nomepc.local`) NON è affidabile
   dall'ESP32 senza libreria dedicata
3. **WiFi di ateneo / eduroam**: la client isolation tipica delle reti universitarie
   blocca il traffico dispositivo↔dispositivo → ESP32 e server non si parlano
   anche se entrambi connessi. Per sviluppo e demo fuori casa: **hotspot del
   telefono o piccolo router dedicato**. (Nota: l'opzione A col suo AP mode è
   immune da questo problema — è un punto a suo favore nella tabella §9.1)

---

## 6. Backend — progetto di dettaglio (`server/`)

### 6.1 Struttura

```
server/
├── main.py            # FastAPI: REST + WebSocket + startup/shutdown
├── mqtt_ingest.py     # client paho-mqtt: subscribe → coda asyncio
├── db.py              # SQLite: schema, insert batch, query, export CSV
├── requirements.txt   # fastapi, uvicorn[standard], paho-mqtt
├── sensordata.db      # ← il database (creato al primo avvio; nel backup!)
└── static/            # LA STESSA pagina dell'opzione A (vedi §7)
    ├── index.html
    ├── style.css
    ├── app.js
    └── chart.umd.min.js
```

Avvio: `uvicorn main:app --host 0.0.0.0 --port 8000` (host 0.0.0.0 per raggiungere
la dashboard da tablet/telefono sulla stessa rete).

### 6.2 Schema del database

Le colonne dei campioni **ricalcano 1:1 il CSV di acquire.py** (gate espansi in 18
colonne, non JSON): così l'export CSV è una singola `SELECT` senza trasformazioni.

```sql
PRAGMA journal_mode=WAL;          -- scritture concorrenti alle letture

CREATE TABLE IF NOT EXISTS sessions (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  group_id      TEXT,             -- come acquire.py
  trial_id      INTEGER,
  scenario      TEXT NOT NULL,
  ground_truth_presence INTEGER,  -- 0/1
  ground_truth_state    TEXT,     -- es. "fermo", "movimento"
  started_s     REAL NOT NULL,    -- epoch time.time()
  ended_s       REAL              -- NULL finché la sessione è aperta
);

CREATE TABLE IF NOT EXISTS samples (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  node_id       TEXT NOT NULL,
  session_id    INTEGER REFERENCES sessions(id),   -- NULL fuori sessione
  server_time_s REAL NOT NULL,    -- epoch alla ricezione (≈ pc_time_s di acquire.py)
  timestamp_ms  INTEGER,          -- millis() ESP32 (campo "t" del JSON)
  radar_presence INTEGER, moving_target INTEGER, stationary_target INTEGER,
  moving_distance_cm INTEGER, stationary_distance_cm INTEGER,
  moving_energy INTEGER, stationary_energy INTEGER,
  pir_presence  INTEGER,
  menergy_gate0 INTEGER, /* ... */ menergy_gate8 INTEGER,   -- 9 colonne
  senergy_gate0 INTEGER, /* ... */ senergy_gate8 INTEGER,   -- 9 colonne
  vitality      INTEGER, vitality_class TEXT
);
CREATE INDEX IF NOT EXISTS idx_samples_session ON samples(session_id);
CREATE INDEX IF NOT EXISTS idx_samples_time    ON samples(server_time_s);
```

Decisione: **si registra sempre**, non solo in sessione. Il DB accumula tutto
(costa nulla, §8) e la sessione è solo un'etichetta su un intervallo — un vantaggio
concreto su A, dove fuori sessione i dati evaporano: "ah, quel test di 5 minuti fa
era buono" → in B si crea la sessione a posteriori sull'intervallo, in A è perso.
Perché la promessa sia vera serve l'endpoint dedicato (`POST /api/sessions/retro`
nella tabella §6.6): crea la riga in `sessions` e fa
`UPDATE samples SET session_id=? WHERE server_time_s BETWEEN ? AND ?` — senza
questo, l'etichettatura retroattiva resterebbe solo dichiarata.

### 6.3 Ingest MQTT → coda asyncio (`mqtt_ingest.py`)

paho-mqtt gira su un suo thread; il passaggio al mondo asyncio di FastAPI avviene
con `loop.call_soon_threadsafe` su una coda:

```python
import json, time
import paho.mqtt.client as mqtt

def start_ingest(loop, queue, host="localhost"):
    def on_connect(client, userdata, flags, reason_code, properties):
        # ⚠ subscribe QUI, non dopo connect(): così le sottoscrizioni si
        # ristabiliscono da sole se il broker riavvia (auto-reconnect di paho)
        client.subscribe("uprise/+/data")
        client.subscribe("uprise/+/status")

    def on_message(client, userdata, msg):
        node_id = msg.topic.split("/")[1]
        if msg.topic.endswith("/status"):
            # ⚠ il payload LWT è testo nudo ("online"/"offline"), NON JSON:
            # va gestito PRIMA del json.loads o verrebbe scartato in silenzio
            evt = {"type": "status", "node_id": node_id,
                   "status": msg.payload.decode(errors="ignore")}
            loop.call_soon_threadsafe(queue.put_nowait, evt)
            return
        try:
            payload = json.loads(msg.payload)
        except json.JSONDecodeError:
            return                                    # frame corrotto: scarta
        payload["node_id"] = node_id
        payload["server_time_s"] = time.time()        # il PC fa fede (≈ pc_time_s)
        loop.call_soon_threadsafe(queue.put_nowait, payload)

    cli = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)   # paho-mqtt 2.x
    cli.on_connect = on_connect
    cli.on_message = on_message
    cli.connect(host, 1883)
    cli.loop_start()                                  # thread separato + auto-reconnect
    return cli
```

### 6.4 Cuore del backend (`main.py`)

```python
import asyncio, json, sqlite3, time
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
import db, mqtt_ingest

queue: asyncio.Queue = asyncio.Queue()
ws_clients: set[WebSocket] = set()
current_session_id: int | None = None
pending: list[dict] = []                    # batch di insert (flush 1/s)

async def consumer():
    """Unico consumatore: broadcast live + accumulo per il DB."""
    global pending
    last_flush = time.monotonic()
    while True:
        try:    # ⚠ timeout, non get() nudo: il flush deve avvenire anche se il
                # nodo smette di pubblicare (altrimenti l'ultimo secondo di
                # campioni resterebbe in RAM indefinitamente)
            sample = await asyncio.wait_for(queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            sample = None
        if sample is not None:
            sample["session_id"] = current_session_id
            # 1) broadcast live a tutti i browser (dati E status/LWT: il frontend
            #    usa i messaggi {"type":"status"} per il banner "nodo offline")
            text = json.dumps(sample)
            dead = set()
            for ws in ws_clients:
                try:    await ws.send_text(text)
                except Exception: dead.add(ws)
            ws_clients.difference_update(dead)
            # 2) accumulo; i messaggi status non vanno nel DB
            if "presence" in sample:
                pending.append(sample)
        # 3) flush su DB una volta al secondo (transazione unica)
        if pending and time.monotonic() - last_flush >= 1.0:
            db.insert_batch(pending); pending = []
            last_flush = time.monotonic()

@asynccontextmanager
async def lifespan(app):
    db.init()
    loop = asyncio.get_running_loop()
    cli = mqtt_ingest.start_ingest(loop, queue)
    task = asyncio.create_task(consumer())
    yield
    task.cancel(); cli.loop_stop()

app = FastAPI(lifespan=lifespan)

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept(); ws_clients.add(ws)
    try:
        while True: await ws.receive_text()      # non ci aspettiamo input
    except WebSocketDisconnect:
        ws_clients.discard(ws)

@app.post("/api/sessions")
async def start_session(meta: dict):
    global current_session_id
    current_session_id = db.create_session(meta)  # scenario, trial, gt...
    return {"id": current_session_id}

@app.post("/api/sessions/{sid}/stop")
async def stop_session(sid: int):
    global current_session_id
    db.close_session(sid); current_session_id = None
    return {"ok": True}

@app.get("/api/sessions")
async def list_sessions():
    return db.list_sessions()                    # id, scenario, trial, durata, n righe

@app.get("/api/sessions/{sid}/export.csv")
async def export_csv(sid: int):
    return StreamingResponse(db.export_csv(sid), media_type="text/csv",
        headers={"Content-Disposition":
                 f'attachment; filename="{db.session_filename(sid)}"'})

@app.get("/api/history")
async def history(minutes: int = 60, step: int = 1):
    """Serie storica (decimata con step) per il grafico 'storico' — capacità nuova di B."""
    return db.query_history(minutes, step)

@app.get("/api/info")
async def info():
    return {"queue": queue.qsize(), "ws_clients": len(ws_clients),
            "session": current_session_id, "db_rows": db.count_rows()}

app.mount("/", StaticFiles(directory="static", html=True))
```

### 6.5 Export CSV (`db.py`, funzione chiave)

L'export riproduce **esattamente** le colonne di acquire.py — stesso header
dell'opzione A (PROGETTO_SITO_DETTAGLIO.md §3.5). I metadati (`scenario, trial_id,
group_id, ground_truth_*`) escono dal JOIN con `sessions`; `pc_time_s` =
`server_time_s`; nome file = `<scenario>_<trial>.csv` come da convenzione del
PIANO_TEST. **Criterio di accettazione identico ad A**: il CSV esportato dal server
deve dare in `analizza_test.py` gli stessi numeri del CSV seriale acquisito in
parallelo.

```
un solo formato in tutta la tesi (invariante che sopravvive ad A e B):
firmware CSV  ==  CSV acquire.py  ==  CSV export web(A)  ==  CSV export server(B)
```

### 6.6 Tabella endpoint (riassunto)

| Metodo e rotta | Fa | Sostituisce (in A) |
|---|---|---|
| `WS /ws` | push live JSON 5 Hz al browser | WS dell'ESP32 |
| `POST /api/sessions` | apre sessione con metadati | form + stato JS `session` |
| `POST /api/sessions/{id}/stop` | chiude sessione | bottone Stop client-side |
| `POST /api/sessions/retro` | etichetta a posteriori un intervallo già registrato (from/to → UPDATE samples) | — (impossibile in A) |
| `GET /api/sessions` | elenco sessioni passate | — (impossibile in A) |
| `GET /api/sessions/{id}/export.csv` | CSV compatibile acquire.py | Blob client-side |
| `GET /api/history?minutes=&step=` | storico decimato per grafici | — (impossibile in A) |
| `GET /api/info` | diagnostica (coda, client, righe) | `/info` dell'ESP32 |
| `GET /` | dashboard statica | LittleFS |

### 6.7 Dove calcolare l'indice di vitalità — un'opportunità specifica di B

In A l'indice di vitalità DEVE girare a bordo (`vitality.h` in C++): non esiste
altro posto. In B compare un'alternativa che merita attenzione: **calcolarlo sul
server, in Python**.

ANALISI_VITALITA.md prevede già il percorso "Python-prima": prototipo
`vitalita_proto.py` tarato sui CSV della Fase 6, e solo DOPO il porting in C++.
Se si sceglie B, il porting può **sparire del tutto**: il backend applica
direttamente il prototipo Python tarato, campione per campione, prima del broadcast
e dell'insert. Conseguenze:

- si elimina lo step più rischioso dell'obiettivo 6 (tradurre in C++ un algoritmo
  ancora in taratura) e ogni ritocco alle soglie è un riavvio del server, non un
  reflash del firmware
- il payload MQTT perde i campi `vitality`/`vitality_class` (li aggiunge il server
  al volo, il frontend non nota la differenza)
- contro: il nodo da solo non sa più dire "vivo/non vivo" — nel racconto UPRISE
  l'intelligenza si sposta dal DIPME-DEVICE alla piattaforma. Difendibile (nel
  sistema reale il gateway ha più risorse del nodo), ma indebolisce l'argomento
  "nodo autonomo"

Raccomandazione: se B, vitalità sul server (v1) e porting C++ solo come estensione
"il nodo autonomo" se avanza tempo. Se A, resta il piano di ANALISI_VITALITA.md.

---

## 7. Frontend — cosa si riusa dall'opzione A e cosa cambia

**La pagina è la stessa al ~85%.** Layout 4 aree, tema scuro, i 3 grafici Chart.js
(C1 energia, C2 per-gate, C3 radar vs PIR), la gauge vitalità: tutto invariato, e il
JSON live è identico. Questa è la polizza assicurativa dell'intera analisi: *il
frontend si costruisce una volta sola e serve entrambe le opzioni*.

Differenze puntuali in `app.js`:

| Punto | A | B |
|---|---|---|
| URL WebSocket | `ws://<ip-esp32>/ws` | `ws://<server>:8000/ws` (stesso `location.host`: la pagina arriva dal server → **il codice non cambia**) |
| Avvia/Stop sessione | manipola stato JS locale | `fetch POST /api/sessions` / `.../stop`; il buffer `session.rows` locale sparisce |
| Scarica CSV | genera Blob dai rows in RAM | `<a href="/api/sessions/{id}/export.csv">` — 3 righe al posto di 30 |
| Refresh durante REC | **perde la sessione** (edge case accettato in A) | non perde nulla: la sessione vive nel server |
| Watchdog "sensore muto" | silenzio WS > 3 s | messaggio `status: offline` dal topic LWT (più preciso: distingue "nodo giù" da "server giù") |
| Ring buffer 60 s per i grafici | invariato | invariato |
| Statistiche live | accumulate in JS | invariate in JS (per il live) — le statistiche *storiche* si aggiungono via `/api/history` |

Novità possibile solo in B (facoltativa, alto valore in demo): una **vista
"storico"** — dropdown delle sessioni passate + grafico dell'andamento presenza/
energia su ore o giorni, servita da `/api/history`. In A non esiste un posto da cui
tirarla fuori.

---

## 8. Dimensionamento — il server regge? (verifica numerica)

Sì, con margini ancora più larghi che in A (un laptop non è un ESP32).

### Volumi

| Grandezza | Valore | Note |
|---|---|---|
| Campioni | 5 Hz × 86.400 s = **432.000 righe/giorno** | registrazione continua (§6.2) |
| Riga DB | ~150 byte | 30 colonne quasi tutte INTEGER |
| Crescita DB | **~65 MB/giorno** | un mese di acquisizione continua ≈ 2 GB — irrilevante su disco |
| Insert | 5/s, flushati in **1 transazione/s** | SQLite in WAL regge migliaia di insert/s: fattore di sicurezza > 100× |
| Banda MQTT | 300 B × 5 Hz = **1,5 KB/s** | invisibile su qualunque WiFi |
| Broadcast WS | 1,5 KB/s × client | 10 client = 15 KB/s: nulla |

### Query

L'export di una sessione da 30 min = SELECT di 9.000 righe con indice su
`session_id`: millisecondi. Lo storico a 24 h decimato (`step=25` → 1 punto/5 s) =
17.280 punti: sotto il secondo. Nessuna ottimizzazione necessaria oltre ai due indici
di §6.2.

### Manutenzione (assente in A, va nominata in B)

- Il DB va nel **backup** insieme ai CSV (regola già in CLAUDE.md: i dati sono
  l'asset insostituibile) — essendo un file, si copia
- Pulizia: non necessaria per la durata della tesi; eventuale
  `DELETE WHERE server_time_s < ...` + `VACUUM` documentata e basta

---

## 9. Confronto finale A vs B e criteri di decisione col professore

### 9.1 Tabella di sintesi

| Criterio | A — ESP32 self-hosted | B — server esterno |
|---|---|---|
| Fedeltà alla frase dell'obiettivo 5 | "sito web" ridotto al minimo | "l'ESP32 **pubblica**" preso alla lettera (MQTT) |
| Cosa dimostra di UPRISE | nodo autonomo in emergenza | piattaforma di monitoraggio in tempo di pace |
| Demo senza infrastruttura | ✅ (AP mode, ovunque) | ❌ serve laptop/Raspberry acceso e configurato |
| Storico persistente e consultabile | ❌ | ✅ (DB + vista storico) |
| Sessioni robuste (refresh/crash) | ❌ (accettato) | ✅ |
| Multi-sensore (LD2420 futuro) | difficile | nativo |
| Componenti da far funzionare insieme | 2 | 4 |
| Contenuto "sistemistico" in tesi | networking embedded, RAM, LittleFS | MQTT, REST, DB, architettura a servizi |
| Indice di vitalità (ob. 6) | porting C++ obbligatorio | può restare in Python sul server (§6.7): niente porting |
| Reti universitarie (client isolation) | immune (AP proprio) | serve hotspot/router dedicato (§5.4) |
| Sforzo stimato | ~3-4 giorni (piano §6 di ANALISI_WEB_UI) | ~5-7 giorni (piano §10 qui sotto) |
| Rischio tecnico principale | RAM/stabilità ESP32 con WS | integrazione a 4 componenti (mitigato dal test §5.3) |

### 9.2 La domanda da fare all'incontro (da aggiungere a INCONTRO_PROFESSORE.md)

> *"Per l'obiettivo 5, intende una dashboard servita direttamente dal nodo ESP32
> (autonoma, senza infrastruttura — modello 'emergenza') oppure una piattaforma con
> server e database che riceve i dati pubblicati dal nodo e mantiene lo storico
> (modello 'piattaforma di monitoraggio SAFE')? Ho il progetto pronto per entrambe."*

Formulata così, la domanda mostra che si è capito il progetto SAFE meglio di quanto
la domanda "che sito vuole?" farebbe mai.

### 9.3 Strategia a rischio minimo (raccomandazione)

1. **Costruire subito ciò che è comune**: firmware di lettura (`radar_task.h`,
   `vitality.h`) e frontend (le 4 aree + 3 grafici) servono identici a entrambe
2. Default su **A** finché il professore non si esprime (già deciso, resta valido)
3. Se all'incontro esce B: il delta è broker + backend (§5-6), **~2-3 giorni** grazie
   al frontend condiviso e al contratto dati unico
4. Se avanza tempo: fare **entrambe** e presentarle come le due modalità della
   piattaforma UPRISE (tempo di pace = B, emergenza = A) — da estensione §8 di
   ANALISI_WEB_UI.md a punto di forza della tesi

---

## 10. Piano di sviluppo incrementale (solo se si sceglie B)

Ogni step funzionante e dimostrabile da solo, con criterio di accettazione:

| Step | Contenuto | Accettazione (verificabile) |
|---|---|---|
| 1 | Mosquitto installato + sketch `ld2410b_mqtt` | `mosquitto_sub -t "uprise/#"` mostra 5 JSON/s; staccando il nodo appare `offline` (LWT) entro ~30 s |
| 2 | Backend: ingest MQTT + SQLite | dopo 10 min, `SELECT COUNT(*)` ≈ 3.000 righe (±1%); nessuna crescita anomala della coda in `/api/info` |
| 3 | WS live + frontend riusato da A | dashboard aggiornata < 0,5 s dal movimento; 2 browser simultanei coerenti |
| 4 | Sessioni REST + export CSV | **CSV di 5 min esportato dal server analizzato con `analizza_test.py` = stessi numeri (±1 campione) del CSV seriale in parallelo** |
| 5 | Vista storico (`/api/history`) | grafico 24 h si carica < 2 s; una sessione di ieri è ritrovabile e riesportabile |

Lo step 4 è lo stesso "cuore" dell'opzione A: dimostra che il sito e la pipeline
dati della tesi sono un sistema solo. Gli step 1-2 sono testabili **senza scrivere
una riga di frontend** — è il vantaggio dell'architettura a componenti.

---

## 11. Cosa resta fuori (v1) — deciso, non dimenticato

- **Autenticazione e HTTPS**: rete locale dedicata, stessa argomentazione di A;
  su un VPS pubblico sarebbero obbligatori — altro motivo per non usare il cloud
- **Docker/docker-compose**: comodo ma è un'astrazione in più da spiegare; su
  Raspberry basta un servizio systemd per uvicorn + il pacchetto mosquitto
- **Grafana/InfluxDB**: farebbero "piattaforma" a costo zero di codice, ma
  sostituirebbero proprio la parte di lavoro (la dashboard) che la tesi deve
  dimostrare di saper costruire
- **Configurazione del radar dal sito**: invariata da A — si usa l'app Bluetooth
- **Selettore multi-nodo nel frontend**: il backend ingerisce già più nodi
  (topic `uprise/+/data`, colonna `node_id`) ma la dashboard v1 mostra un nodo
  solo; il dropdown di selezione è un'estensione (speculare al "supporto LD2420"
  di ANALISI_WEB_UI.md §8)
- **Ridondanza/cluster broker**: fuori scala per una tesi triennale

---

## 12. Fonti

Regola fonti (CLAUDE.md, 15/07/2026): ogni dato tecnico con fonte citata.

- MQTT 3.1.1 — standard OASIS (publish/subscribe, QoS, LWT, retained):
  https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html
- Eclipse Mosquitto (download, doc, cambio default 2.0 listener/anonymous):
  https://mosquitto.org/documentation/ e migrazione 2.0: https://mosquitto.org/documentation/migrating-to-2-0/
- PubSubClient (knolleary) — limite `MQTT_MAX_PACKET_SIZE` 256 B e `setBufferSize()`:
  https://pubsubclient.knolleary.net/api
- paho-mqtt 2.x (CallbackAPIVersion): https://eclipse.dev/paho/files/paho.mqtt.python/html/index.html
- FastAPI — WebSocket, StaticFiles, lifespan: https://fastapi.tiangolo.com/
- Uvicorn: https://www.uvicorn.org/
- SQLite — WAL mode: https://sqlite.org/wal.html ; limiti (dimensioni, insert rate):
  https://sqlite.org/limits.html e https://sqlite.org/faq.html#q19
- ArduinoJson 7 (serializzazione su buffer statico): https://arduinojson.org/
- Chart.js v4 (bundle locale, riuso da opzione A): https://www.chartjs.org/docs/latest/
- Architettura DIPME/SAFE (nodi → gateway → piattaforma): slide "Sharper -
  Informatica 26 settembre 2025" (file locale) e paper Callisto et al., EDOC 2023
- Documenti interni collegati: `ANALISI_WEB_UI.md` (decisione originale, opzione A),
  `PROGETTO_SITO_DETTAGLIO.md` (dettaglio implementativo A, frontend riusato qui),
  `ANALISI_VITALITA.md` (contratto vitality invariato), `PIANO_TEST.md` (convenzioni
  CSV e nomi file)
