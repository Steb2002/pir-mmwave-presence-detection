/*
 * Logger CSV per LD2410B + PIR — versione estesa per la tesi.
 *
 * Basato sul firmware del professore (massimocallisto/HLK-LD2410x) con tre modifiche:
 *   1. campionamento a 5 Hz invece di 1 Hz (serve per latenza e FFT del respiro)
 *   2. engineering mode opzionale: energia per-gate (9 gate moving + 9 still)
 *   3. libreria MyLD2410 (installata in Arduino IDE) invece di ncmreynolds/ld2410
 *
 * Il formato CSV è un SUPERSET di quello del professore: le prime 9 colonne sono
 * identiche, quindi acquire.py funziona senza modifiche.
 *
 * Cablaggio (come da CLAUDE.md — verificato sul modulo):
 *   LD2410B TX (giallo) -> GPIO16 (RX2)      PIR OUT -> GPIO23
 *   LD2410B RX (nero)   -> GPIO17 (TX2)      LED interno -> GPIO2
 *   LD2410B VCC (blu)   -> VIN 5V            LD2410B GND (verde) -> GND
 *
 * NOTA: il firmware del professore usa i pin INVERTITI (radar TX->17, RX->16).
 * Questo sketch usa i pin del NOSTRO cablaggio. Se si usa il firmware del
 * professore senza modifiche, scambiare i cavi giallo e nero.
 */

#include <MyLD2410.h>

// ---- Configurazione ----
#define ENGINEERING_MODE 1        // 1 = energia per-gate nel CSV (serve per respiro/vitalità)
const unsigned long samplePeriodMs = 200;  // 5 Hz (professore: 1000 ms)

#define RADAR_RX_PIN 16           // ESP32 riceve <- TX del radar (cavo giallo)
#define RADAR_TX_PIN 17           // ESP32 trasmette -> RX del radar (cavo nero)
#define PIR_PIN 23
#define LED_PIN 2

#define sensorSerial Serial2
MyLD2410 sensor(sensorSerial);

unsigned long lastPrint = 0;

void printGateCSV(const byte &value) {  // callback per ValuesArray.forEach
  Serial.print(',');
  Serial.print(value);
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(PIR_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  sensorSerial.begin(LD2410_BAUD_RATE, SERIAL_8N1, RADAR_RX_PIN, RADAR_TX_PIN);
  delay(500);

  if (!sensor.begin()) {
    Serial.println("ERROR: radar not detected");
    while (true) delay(1000);
  }

#if ENGINEERING_MODE
  sensor.enhancedMode(true);
#endif

  // Intestazione CSV — le prime 9 colonne coincidono con il firmware del professore
  Serial.print("timestamp_ms,radar_presence,moving_target,stationary_target,"
               "moving_distance_cm,stationary_distance_cm,moving_energy,"
               "stationary_energy,pir_presence");
#if ENGINEERING_MODE
  for (int i = 0; i <= 8; i++) { Serial.print(",menergy_gate"); Serial.print(i); }
  for (int i = 0; i <= 8; i++) { Serial.print(",senergy_gate"); Serial.print(i); }
#endif
  Serial.println();
}

void loop() {
  sensor.check();  // processa i frame UART del radar

  unsigned long now = millis();
  if (now - lastPrint < samplePeriodMs) return;
  lastPrint = now;

  int pirPresence = digitalRead(PIR_PIN);
  bool moving = sensor.movingTargetDetected();
  bool stationary = sensor.stationaryTargetDetected();

  digitalWrite(LED_PIN, (moving || stationary) ? HIGH : LOW);

  Serial.print(now);
  Serial.print(',');
  Serial.print(sensor.presenceDetected() ? 1 : 0);
  Serial.print(',');
  Serial.print(moving ? 1 : 0);
  Serial.print(',');
  Serial.print(stationary ? 1 : 0);
  Serial.print(',');
  Serial.print(moving ? sensor.movingTargetDistance() : 0);
  Serial.print(',');
  Serial.print(stationary ? sensor.stationaryTargetDistance() : 0);
  Serial.print(',');
  Serial.print(moving ? sensor.movingTargetSignal() : 0);
  Serial.print(',');
  Serial.print(stationary ? sensor.stationaryTargetSignal() : 0);
  Serial.print(',');
  Serial.print(pirPresence);

#if ENGINEERING_MODE
  if (sensor.inEnhancedMode()) {
    sensor.getMovingSignals().forEach(printGateCSV);      // 9 valori: gate 0-8
    sensor.getStationarySignals().forEach(printGateCSV);  // 9 valori: gate 0-8
  }
#endif

  Serial.println();
}
