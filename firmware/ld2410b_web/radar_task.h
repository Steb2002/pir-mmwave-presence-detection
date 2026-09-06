/*
 * radar_task.h — lettura del LD2410B (MyLD2410, engineering mode) e del PIR.
 *
 * Copia la logica di firmware/ld2410b_logger, validata sul Test 0.1/0.2, con una sola
 * differenza: se il radar non risponde all'avvio NON si blocca (la dashboard deve
 * comunque partire), ritenta ogni 5 s e lo segnala nel JSON (`radar_ok`).
 *
 * Il CSV su seriale e' identico a quello del logger, 29 colonne: acquire.py e
 * analizza_test.py funzionano senza modifiche. E' il canale di test "ufficiale" che
 * gira accanto alla web UI (PROGETTO_SITO_DETTAGLIO.md §2.2).
 */
#pragma once

#include <MyLD2410.h>
#include "config.h"

struct RadarSample {
  uint32_t t = 0;                 // millis()
  bool     radarOk = false;       // il modulo risponde
  bool     presence = false, moving = false, still = false;
  uint16_t mdist = 0, sdist = 0;  // cm
  uint8_t  menergy = 0, senergy = 0;   // 0-100
  bool     pir = false;
  uint8_t  gatesM[9] = {0}, gatesS[9] = {0};
  uint8_t  light = 0;             // light_level 0-255
  bool     outLevel = false;      // out_level (pin OUT del radar, letto dal frame)
  uint8_t  vitality = 0;          // step 5
  const char* vitalityClass = ""; // step 5: vitalita_bassa | vitalita_moderata | vitalita_alta
};

static MyLD2410 sensor(Serial2);
static bool     radarPronto = false;
static unsigned long radarUltimoTentativo = 0;

// Prova ad avviare il radar. Ritorna true se risponde. Idempotente: si puo' richiamare.
static bool radarAvvia() {
  radarUltimoTentativo = millis();
  if (!radarPronto) {
    Serial2.begin(RADAR_BAUD, SERIAL_8N1, RADAR_RX_PIN, RADAR_TX_PIN);
    delay(200);
  }
  if (!sensor.begin()) {
    radarPronto = false;
    return false;
  }
  sensor.enhancedMode(true);
  radarPronto = true;
  return true;
}

// Da chiamare a ogni giro di loop(): processa i frame UART. Se il radar non e'
// partito, ritenta ogni 5 s.
static inline void radarLoop() {
  if (radarPronto) {
    sensor.check();
  } else if (millis() - radarUltimoTentativo >= 5000) {
    if (radarAvvia()) Serial.println("# radar rilevato al ritentativo");
  }
}

static void radarLeggi(RadarSample& s) {
  s.t = millis();
  s.radarOk = radarPronto;
  s.pir = digitalRead(PIR_PIN) == HIGH;
  if (!radarPronto) {
    s.presence = s.moving = s.still = false;
    s.mdist = s.sdist = 0; s.menergy = s.senergy = 0;
    for (int i = 0; i < 9; i++) { s.gatesM[i] = 0; s.gatesS[i] = 0; }
    s.light = 0; s.outLevel = false;
    return;
  }
  s.moving   = sensor.movingTargetDetected();
  s.still    = sensor.stationaryTargetDetected();
  s.presence = sensor.presenceDetected();
  s.mdist    = s.moving ? sensor.movingTargetDistance() : 0;
  s.sdist    = s.still  ? sensor.stationaryTargetDistance() : 0;
  s.menergy  = s.moving ? sensor.movingTargetSignal() : 0;
  s.senergy  = s.still  ? sensor.stationaryTargetSignal() : 0;
  if (sensor.inEnhancedMode()) {
    const MyLD2410::ValuesArray& gm = sensor.getMovingSignals();
    const MyLD2410::ValuesArray& gs = sensor.getStationarySignals();
    for (int i = 0; i < 9; i++) {
      s.gatesM[i] = (i <= gm.N) ? gm.values[i] : 0;
      s.gatesS[i] = (i <= gs.N) ? gs.values[i] : 0;
    }
    s.light    = sensor.getLightLevel();
    s.outLevel = sensor.getOutLevel() != 0;
  }
}

// ---- CSV su seriale, 29 colonne come firmware/ld2410b_logger ----
static void csvIntestazione() {
  Serial.print("timestamp_ms,radar_presence,moving_target,stationary_target,"
               "moving_distance_cm,stationary_distance_cm,moving_energy,"
               "stationary_energy,pir_presence");
  for (int i = 0; i <= 8; i++) { Serial.print(",menergy_gate"); Serial.print(i); }
  for (int i = 0; i <= 8; i++) { Serial.print(",senergy_gate"); Serial.print(i); }
  Serial.println(",light_level,out_level");
}

static void csvRiga(const RadarSample& s) {
  Serial.print(s.t);
  Serial.print(','); Serial.print(s.presence ? 1 : 0);
  Serial.print(','); Serial.print(s.moving ? 1 : 0);
  Serial.print(','); Serial.print(s.still ? 1 : 0);
  Serial.print(','); Serial.print(s.mdist);
  Serial.print(','); Serial.print(s.sdist);
  Serial.print(','); Serial.print(s.menergy);
  Serial.print(','); Serial.print(s.senergy);
  Serial.print(','); Serial.print(s.pir ? 1 : 0);
  for (int i = 0; i < 9; i++) { Serial.print(','); Serial.print(s.gatesM[i]); }
  for (int i = 0; i < 9; i++) { Serial.print(','); Serial.print(s.gatesS[i]); }
  Serial.print(','); Serial.print(s.light);
  Serial.print(','); Serial.println(s.outLevel ? 1 : 0);
}
