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
 * Cablaggio (TX di uno -> RX dell'altro) — colori verificati 09/08/2026:
 *   LD2410B TX (verde)  -> GPIO25 (RX2)      PIR OUT -> GPIO34
 *   LD2410B RX (giallo) -> GPIO26 (TX2)      LED interno -> GPIO2
 *   LD2410B VCC (rosso) -> VIN 5V            LD2410B GND (nero) -> GND
 *   LD2410B OUT (blu)   -> non collegato
 *
 * NOTA: il firmware del professore usa GPIO16/17. Qui usiamo GPIO25/26 (scelta
 * nostra). Se non arrivano dati, il primo sospetto e' verde/giallo invertiti.
 */

#include <MyLD2410.h>

// ---- Configurazione ----
#define ENGINEERING_MODE 1        // 1 = energia per-gate nel CSV (serve per respiro/vitalità)
const unsigned long samplePeriodMs = 200;  // 5 Hz (professore: 1000 ms)

#define RADAR_RX_PIN 25           // ESP32 riceve <- TX del radar (cavo verde)
#define RADAR_TX_PIN 26           // ESP32 trasmette -> RX del radar (cavo giallo)
// GPIO34: pin di SOLO INPUT e senza pull-up interni (come 35/36/39). Va bene per
// l'HC-SR501, che pilota attivamente la sua uscita a 3.3V/0V; NON andrebbe bene per
// un contatto passivo o un sensore a collettore aperto. Scelto perche' sta sullo
// stesso lato della scheda dei cavi del radar (D23 e' sul lato opposto).
#define PIR_PIN 34
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
  // light_level (0-255) e out_level (0/1) arrivano dentro il frame di engineering mode
  // (protocollo V1.07, Tabella 15): out_level e' lo stato del pin OUT del radar, quindi
  // NON serve collegare il cavo blu per registrarlo.
  Serial.print(",light_level,out_level");
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
    Serial.print(',');
    Serial.print(sensor.getLightLevel());                // 0-255
    Serial.print(',');
    Serial.print(sensor.getOutLevel());                  // stato del pin OUT: 0/1
  }
#endif

  Serial.println();
}
