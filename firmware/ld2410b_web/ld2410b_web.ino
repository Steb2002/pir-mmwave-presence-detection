/*
 * ld2410b_web — dashboard self-hosted sull'ESP32 (obiettivo 5 della tesi).
 *
 * L'ESP32 crea la propria rete WiFi (Access Point "DIPME-Sensor", nessuna connessione
 * a reti esistenti), serve la pagina web dalla flash e spinge i dati del radar LD2410B
 * e del PIR al browser via WebSocket a 5 Hz. Il browser disegna i grafici, calcola le
 * statistiche e genera il CSV con le stesse colonne di acquire.py.
 * Progetto: analisi/ANALISI_WEB_UI.md e analisi/PROGETTO_SITO_DETTAGLIO.md.
 *
 * File:
 *   config.h        SSID/password dell'AP, pin, costanti
 *   radar_task.h    lettura LD2410B (MyLD2410, engineering mode) + PIR, CSV su seriale
 *   vitality.h      indice di vitalita' v3 (EWMA sull'energia netta del gate attivo, 3 classi)
 *   web_server.h    AP + DNS catch-all + HTTP statico + /info + WebSocket /ws
 *   web_assets.h    GENERATO da embed_web.py: i file di web/ compressi in gzip
 *   web/            sorgenti della pagina (index.html, style.css, app.js)
 *
 * Prerequisiti Arduino IDE:
 *   - librerie "ESP Async WebServer" e "Async TCP" di ESP32Async (Library Manager)
 *   - Strumenti -> Partition Scheme -> "Huge APP (3MB No OTA/1MB SPIFFS)":
 *     con lo schema di default (1,2 MB) WiFi + server asincrono non ci stanno
 *   - prima di compilare, dopo ogni modifica in web/:  python firmware/ld2410b_web/embed_web.py
 *
 * Cablaggio: identico a firmware/ld2410b_logger (vedi config.h).
 *
 * Seriale verso il PC a 115200: le stesse 29 colonne CSV del logger, quindi acquire.py
 * funziona in parallelo alla web UI. Ogni riga non-CSV inizia con "# ".
 *
 * Storico:
 *   BUILD 1 (06/09/2026) step 1: Access Point + pagina statica + /info
 *   BUILD 2 (06/09/2026) step 2: radar + PIR, CSV su seriale, WebSocket a 5 Hz, area A
 *   BUILD 3 (10/09/2026) step 3: storico 60 s a bordo inviato alla connessione, soglie in /info,
 *                        grafici C1/C2/C3 e gauge B nella pagina (Chart.js locale)
 *   BUILD 4 (10/09/2026) step 4: solo pagina — sessione con metadati, statistiche, export CSV
 *                        con le 29+6 colonne di acquire.py. Firmware invariato salvo il marcatore
 *   BUILD 5 (10/09/2026) log degli eventi WS spostato dal task di rete al loop (una riga CSV
 *                        veniva corrotta dalla stampa concorrente); avviso portale captive nella pagina
 *   BUILD 6 (10/09/2026) step 5: vitality.h a bordo (v3, fondo per gate, 3 classi), gauge collegata,
 *                        vitalita' in C1 e nel CSV web (colonne extra vitality_onboard*)
 *   BUILD 7 (23/09/2026) progetto rinominato: rete DIPME-Sensor / dipme2026, pagina "DIPME Sensor"
 */
#include "config.h"
#include "radar_task.h"
#include "vitality.h"
#include "web_server.h"

#define BUILD "ld2410b_web BUILD 7 - rete DIPME-Sensor"

static RadarSample campione;
static unsigned long ultimoCampione = 0;

void setup() {
  Serial.begin(SERIALE_BAUD);
  delay(300);
  Serial.println();
  Serial.println("# " BUILD);
  BUILD_TESTO = BUILD;

  pinMode(PIR_PIN, INPUT);

  webAvvia();
  Serial.print("# AP "); Serial.print(AP_SSID);
  Serial.print(" attivo, pagina http://"); Serial.print(WiFi.softAPIP());
  Serial.println("/ (o qualunque nome: DNS catch-all), WebSocket su /ws");
  Serial.print("# assets: "); Serial.print(WEB_ASSETS_N);
  Serial.print(" file, hash "); Serial.println(WEB_ASSETS_HASH);

  if (radarAvvia()) {
    Serial.print("# radar LD2410B rilevato, engineering mode attivo, parametri ");
    Serial.println(radarParametriLetti ? "letti" : "NON letti");
  } else {
    Serial.println("# ATTENZIONE: radar non rilevato - controllare verde->D25, giallo->D26, VIN 5V, GND. Ritento ogni 5 s");
  }
  Serial.print("# heap libero: "); Serial.println(ESP.getFreeHeap());

  // Intestazione CSV: come il logger, una volta sola in setup() (acquire.py la aspetta;
  // se la perde ricostruisce i nomi dal numero di colonne, 29 = engineering + light/out)
  csvIntestazione();
}

void loop() {
  radarLoop();      // parsing UART a ogni giro, mai bloccare
  webLoop();        // DNS + pulizia client WS

  unsigned long ora = millis();
  if (ora - ultimoCampione < PERIODO_CAMPIONE_MS) return;
  ultimoCampione = ora;

  radarLeggi(campione);
  vitalityUpdate(campione);  // indice di vitalita' a bordo (step 5), prima di storico/CSV/WS
  storicoAggiungi(campione); // ultimi 60 s, per chi si collega dopo
  csvRiga(campione);        // canale seriale SEMPRE attivo (test/debug/acquire.py)
  wsBroadcast(campione);    // -> tutti i browser collegati
}
