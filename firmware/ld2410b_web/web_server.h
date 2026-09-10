/*
 * web_server.h — Access Point, DNS catch-all, HTTP statico da flash, /info, WebSocket.
 *
 * Librerie: ESP Async WebServer + Async TCP, entrambe di ESP32Async (i fork che
 * compilano sul core ESP32 3.x). DNSServer e WiFi sono nel core.
 *
 * I file della pagina stanno in web_assets.h, generato da tools/embed_web.py: ogni
 * file e' un array gzip in flash e viene servito con Content-Encoding: gzip.
 *
 * WebSocket /ws:
 *   - a ogni campione (5 Hz) il JSON con lo stato del radar va a tutti i client
 *     (`wsBroadcast`; schema in ANALISI_WEB_UI.md §2)
 *   - alla connessione il client riceve lo storico degli ultimi 60 s in messaggi
 *     `{"hist":[[...],...],"fine":0|1}` con righe compatte (step 3), cosi' il grafico
 *     parte pieno. Ordine dei campi in HIST_CAMPI, ripetuto in app.js
 *   - il 5° client viene rifiutato; `ws.cleanupClients()` gira ogni secondo
 */
#pragma once

#include <WiFi.h>
#include <DNSServer.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>
#include "config.h"
#include "web_assets.h"
#include "radar_task.h"

static AsyncWebServer  server(80);
static AsyncWebSocket  ws("/ws");
static DNSServer       dns;
static const char*     BUILD_TESTO = "?";   // impostato dallo sketch, finisce in /info
static uint32_t        wsMessaggiInviati = 0;

// Ordine dei campi di una riga compatta dello storico (deve coincidere con app.js)
static const char HIST_CAMPI[] =
  "t,presence,moving,still,mdist,sdist,menergy,senergy,pir,light,out,gates_m[9],gates_s[9]";

static void serviAsset(AsyncWebServerRequest* req, const WebAsset& a) {
  AsyncWebServerResponse* r = req->beginResponse(200, a.mime, a.data, a.len);
  r->addHeader("Content-Encoding", "gzip");
  // no-cache: il browser richiede sempre la versione in flash. I file pesano poco e
  // cosi' una pagina modificata e ricaricata sull'ESP32 si vede al primo refresh.
  r->addHeader("Cache-Control", "no-cache");
  req->send(r);
}

static void serviInfo(AsyncWebServerRequest* req) {
  JsonDocument doc;
  doc["build"]        = BUILD_TESTO;
  doc["uptime_s"]     = millis() / 1000;
  doc["heap_libero"]  = ESP.getFreeHeap();
  doc["heap_minimo"]  = ESP.getMinFreeHeap();
  doc["client_ap"]    = WiFi.softAPgetStationNum();
  doc["client_ws"]    = ws.count();
  doc["ws_inviati"]   = wsMessaggiInviati;
  doc["radar_ok"]     = radarPronto ? 1 : 0;
  doc["storico_n"]    = storicoConteggio;
  doc["assets_hash"]  = WEB_ASSETS_HASH;
  doc["assets_n"]     = WEB_ASSETS_N;
  doc["ip"]           = WiFi.softAPIP().toString();
  // Parametri del modulo, letti via UART all'avvio (soglie di fabbrica del nostro
  // esemplare: mov 50 50 40 30 20 15 15 15 15, still - - 40 40 30 30 20 20 20)
  doc["parametri_letti"] = radarParametriLetti ? 1 : 0;
  if (radarPronto && radarParametriLetti) {
    doc["gate_max"]  = sensor.getRange();
    doc["timeout_s"] = sensor.getNoOneWindow();
    JsonArray sm = doc["soglie_mov"].to<JsonArray>();
    JsonArray ss = doc["soglie_still"].to<JsonArray>();
    const MyLD2410::ValuesArray& tm = sensor.getMovingThresholds();
    const MyLD2410::ValuesArray& ts = sensor.getStationaryThresholds();
    for (int i = 0; i < 9; i++) {
      sm.add(i <= tm.N ? tm.values[i] : 0);
      ss.add(i <= ts.N ? ts.values[i] : 0);
    }
  }
  String out;
  serializeJson(doc, out);
  AsyncWebServerResponse* r = req->beginResponse(200, "application/json", out);
  r->addHeader("Cache-Control", "no-cache");
  req->send(r);
}

// Riga compatta dello storico: solo interi, serializzata a mano (niente ArduinoJson:
// 300 righe x 31 valori sarebbero ~40 KB di documento per un messaggio solo)
static void appendiRigaCompatta(String& s, const RadarSample& c) {
  char b[96];
  snprintf(b, sizeof(b), "[%lu,%d,%d,%d,%u,%u,%u,%u,%d,%u,%d,[",
           (unsigned long)c.t, c.presence, c.moving, c.still,
           c.mdist, c.sdist, c.menergy, c.senergy, c.pir, c.light, c.outLevel);
  s += b;
  for (int i = 0; i < 9; i++) { if (i) s += ','; s += c.gatesM[i]; }
  s += "],[";
  for (int i = 0; i < 9; i++) { if (i) s += ','; s += c.gatesS[i]; }
  s += "]]";
}

// Spedisce lo storico a UN client, a blocchi di 50 righe (~3 KB l'uno): sei messaggi,
// sotto il limite della coda WS e senza grosse allocazioni.
static void wsInviaStorico(AsyncWebSocketClient* client) {
  const size_t BLOCCO = 50;
  size_t n = storicoConteggio;
  if (n == 0) { client->text("{\"hist\":[],\"fine\":1}"); return; }
  for (size_t da = 0; da < n; da += BLOCCO) {
    size_t a = min(da + BLOCCO, n);
    String s;
    s.reserve(3600);
    s += "{\"hist\":[";
    for (size_t i = da; i < a; i++) { if (i > da) s += ','; appendiRigaCompatta(s, storicoAt(i)); }
    s += "],\"fine\":";
    s += (a == n) ? '1' : '0';
    s += '}';
    client->text(s);
  }
}

// ⚠️ Gli eventi WS arrivano sul task di rete, NON nel loop(): stampare qui sulla seriale
// si intreccia con la riga CSV che il loop sta scrivendo (successo il 10/09/2026: riga
// corrotta a meta'). I messaggi vanno in una coda FreeRTOS e li stampa webLoop().
static QueueHandle_t codaLog = nullptr;
struct RigaLog { char testo[72]; };

static void logDaTask(const char* prefisso, uint32_t id, const IPAddress& ip) {
  if (!codaLog) return;
  RigaLog r;
  snprintf(r.testo, sizeof(r.testo), "# WS client %s: %lu da %s", prefisso, (unsigned long)id, ip.toString().c_str());
  xQueueSend(codaLog, &r, 0);                  // se piena, il messaggio si perde: e' solo log
}

static void wsEvento(AsyncWebSocket* srv, AsyncWebSocketClient* client, AwsEventType tipo,
                     void* arg, uint8_t* data, size_t len) {
  (void)srv; (void)arg; (void)data; (void)len;
  if (tipo == WS_EVT_CONNECT) {
    if (ws.count() > AP_MAX_CLIENT) {          // il nuovo e' gia' contato
      client->text("{\"errore\":\"troppi client\"}");
      client->close();
      logDaTask("rifiutato (troppi)", client->id(), client->remoteIP());
    } else {
      logDaTask("connesso", client->id(), client->remoteIP());
      wsInviaStorico(client);
    }
  } else if (tipo == WS_EVT_DISCONNECT) {
    logDaTask("disconnesso", client->id(), IPAddress());
  }
  // La v1 non riceve comandi dal browser: WS_EVT_DATA ignorato di proposito.
}

// Serializza e spedisce il campione a tutti i client. Buffer statico, nessuna
// allocazione nel loop; ~330 byte per messaggio, sotto il singolo frame TCP.
static void wsBroadcast(const RadarSample& s) {
  if (ws.count() == 0) return;
  static JsonDocument doc;
  static char out[512];
  doc.clear();
  doc["t"]        = s.t;
  doc["radar_ok"] = s.radarOk ? 1 : 0;
  doc["presence"] = s.presence ? 1 : 0;
  doc["moving"]   = s.moving ? 1 : 0;
  doc["still"]    = s.still ? 1 : 0;
  doc["mdist"]    = s.mdist;
  doc["sdist"]    = s.sdist;
  doc["menergy"]  = s.menergy;
  doc["senergy"]  = s.senergy;
  doc["pir"]      = s.pir ? 1 : 0;
  JsonArray gm = doc["gates_m"].to<JsonArray>();
  JsonArray gs = doc["gates_s"].to<JsonArray>();
  for (int i = 0; i < 9; i++) { gm.add(s.gatesM[i]); gs.add(s.gatesS[i]); }
  doc["light"]    = s.light;
  doc["out"]      = s.outLevel ? 1 : 0;
  doc["vitality"] = s.vitality;
  doc["vitality_class"] = s.vitalityClass;
  size_t n = serializeJson(doc, out, sizeof(out));
  ws.textAll(out, n);
  wsMessaggiInviati++;
}

// Avvia AP + DNS + HTTP + WS. Da chiamare una volta in setup().
static void webAvvia() {
  codaLog = xQueueCreate(8, sizeof(RigaLog));
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASSWORD, AP_CANALE, 0 /* visibile */, AP_MAX_CLIENT);
  delay(100);                                    // lascia salire l'interfaccia prima del DNS

  // DNS catch-all: qualunque nome -> IP dell'AP. Serve anche a far riconoscere la rete
  // come "portale" ai telefoni, che altrimenti la scartano perche' non ha internet.
  dns.setTTL(60);
  dns.start(53, "*", WiFi.softAPIP());

  // Una rotta per file. "/index.html" risponde anche su "/".
  for (size_t i = 0; i < WEB_ASSETS_N; i++) {
    const WebAsset* a = &WEB_ASSETS[i];
    server.on(a->path, HTTP_GET, [a](AsyncWebServerRequest* req) { serviAsset(req, *a); });
    if (strcmp(a->path, "/index.html") == 0) {
      server.on("/", HTTP_GET, [a](AsyncWebServerRequest* req) { serviAsset(req, *a); });
    }
  }
  server.on("/info", HTTP_GET, serviInfo);

  ws.onEvent(wsEvento);
  server.addHandler(&ws);

  // Tutto il resto (compresi i controlli di connettivita' dei telefoni:
  // connectivitycheck.gstatic.com/generate_204, captive.apple.com, msftconnecttest.com)
  // viene rimandato alla dashboard.
  server.onNotFound([](AsyncWebServerRequest* req) {
    req->redirect("http://" + WiFi.softAPIP().toString() + "/");
  });

  server.begin();
}

// Da chiamare a ogni giro di loop(): il DNSServer del core non e' asincrono, e la
// pulizia dei client WS va fatta periodicamente.
static inline void webLoop() {
  dns.processNextRequest();
  // log degli eventi WS, stampato qui fra una riga CSV e l'altra (mai dal task di rete)
  RigaLog r;
  while (codaLog && xQueueReceive(codaLog, &r, 0) == pdTRUE) Serial.println(r.testo);
  static unsigned long ultimaPulizia = 0;
  if (millis() - ultimaPulizia >= 1000) {
    ultimaPulizia = millis();
    ws.cleanupClients();
  }
}
