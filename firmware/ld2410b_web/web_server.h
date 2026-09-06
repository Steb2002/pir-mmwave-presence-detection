/*
 * web_server.h — Access Point, DNS catch-all, HTTP statico da flash, /info, WebSocket.
 *
 * Librerie: ESP Async WebServer + Async TCP, entrambe di ESP32Async (i fork che
 * compilano sul core ESP32 3.x). DNSServer e WiFi sono nel core.
 *
 * I file della pagina stanno in web_assets.h, generato da tools/embed_web.py: ogni
 * file e' un array gzip in flash e viene servito con Content-Encoding: gzip.
 *
 * WebSocket /ws (step 2): a ogni campione (5 Hz) il JSON con lo stato del radar viene
 * spedito a tutti i client collegati (`wsBroadcast`). Schema del messaggio in
 * ANALISI_WEB_UI.md §2. Il 5° client viene rifiutato. `ws.cleanupClients()` gira
 * ogni secondo in webLoop(): senza, i client chiusi male (refresh, tab chiuse)
 * restano contati e si esaurisce il limite.
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
  doc["assets_hash"]  = WEB_ASSETS_HASH;
  doc["assets_n"]     = WEB_ASSETS_N;
  doc["ip"]           = WiFi.softAPIP().toString();
  String out;
  serializeJson(doc, out);
  AsyncWebServerResponse* r = req->beginResponse(200, "application/json", out);
  r->addHeader("Cache-Control", "no-cache");
  req->send(r);
}

static void wsEvento(AsyncWebSocket* srv, AsyncWebSocketClient* client, AwsEventType tipo,
                     void* arg, uint8_t* data, size_t len) {
  (void)srv; (void)arg; (void)data; (void)len;
  if (tipo == WS_EVT_CONNECT) {
    if (ws.count() > AP_MAX_CLIENT) {          // il nuovo e' gia' contato
      client->text("{\"errore\":\"troppi client\"}");
      client->close();
      Serial.print("# WS client rifiutato (troppi): ");
    } else {
      Serial.print("# WS client connesso: ");
    }
    Serial.print(client->id()); Serial.print(" da "); Serial.println(client->remoteIP());
  } else if (tipo == WS_EVT_DISCONNECT) {
    Serial.print("# WS client disconnesso: "); Serial.println(client->id());
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
  static unsigned long ultimaPulizia = 0;
  if (millis() - ultimaPulizia >= 1000) {
    ultimaPulizia = millis();
    ws.cleanupClients();
  }
}
