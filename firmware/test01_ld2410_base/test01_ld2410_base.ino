/*
 * Test 0.1 — Primo contatto con il LD2410B (con auto-scan del baud rate)
 *
 * Scopo: verificare cablaggio + libreria + radar, e SCOPRIRE il baud rate corretto.
 * Lo sketch prova diversi baud e si ferma su quello con cui il radar risponde.
 *
 * Collegare SOLO il LD2410B (regola: TX di uno -> RX dell'altro).
 * Colori verificati 09/08/2026 sul datasheet Hi-Link (Tabella 1):
 *   Rosso  VCC          -> VIN  (5V)
 *   Nero   GND          -> GND        <-- la massa DEVE esserci, se no esce garbage
 *   Verde  TX del radar -> D25  (RX2 dell'ESP32)
 *   Giallo RX del radar -> D26  (TX2 dell'ESP32)
 *   Blu    OUT          -> non collegare
 *
 * Serial Monitor a 115200 baud.
 */

#include <MyLD2410.h>

#define RADAR_RX_PIN 25   // ESP32 riceve <- TX del radar (cavo verde)
#define RADAR_TX_PIN 26   // ESP32 trasmette -> RX del radar (cavo giallo)

#define sensorSerial Serial2
MyLD2410 sensor(sensorSerial);

// baud da provare, dal più probabile al meno
const uint32_t bauds[] = {256000, 115200, 57600, 9600};
const int nBauds = sizeof(bauds) / sizeof(bauds[0]);

uint32_t baudTrovato = 0;
unsigned long lastPrint = 0;

bool provaBaud(uint32_t baud) {
  sensorSerial.end();
  delay(50);
  sensorSerial.begin(baud, SERIAL_8N1, RADAR_RX_PIN, RADAR_TX_PIN);
  delay(300);

  // conta i byte grezzi in ~600 ms
  unsigned long fine = millis() + 600;
  unsigned long conteggio = 0;
  while (millis() < fine) {
    if (sensorSerial.available()) { sensorSerial.read(); conteggio++; }
  }

  Serial.print("  baud ");
  Serial.print(baud);
  Serial.print(": ");
  Serial.print(conteggio);
  Serial.print(" byte grezzi in 0.6s -> ");

  // tenta la comunicazione vera e propria (begin verifica i frame)
  bool ok = sensor.begin();
  Serial.println(ok ? "RADAR OK (frame validi!)" : "nessun frame valido");
  return ok;
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  Serial.println();
  Serial.println("=== Test 0.1 - Auto-scan baud LD2410B ===");

  for (int i = 0; i < nBauds; i++) {
    if (provaBaud(bauds[i])) {
      baudTrovato = bauds[i];
      break;
    }
  }

  Serial.println("-------------------------------------------");
  if (baudTrovato == 0) {
    Serial.println("Nessun baud ha prodotto frame validi.");
    Serial.println("Guarda i byte grezzi qui sopra:");
    Serial.println(" - se un baud ha MOLTI byte ma nessun frame valido -> quello e' il baud, ma i cavi TX/RX o la massa disturbano");
    Serial.println(" - se TUTTI hanno pochi/zero byte -> problema di collegamento o alimentazione");
    while (true) delay(1000);
  }

  Serial.print(">> Baud corretto: ");
  Serial.println(baudTrovato);
  if (sensor.requestFirmware()) {
    Serial.print("Versione firmware radar: ");
    Serial.println(sensor.getFirmware());
  }
  Serial.println("Muoviti davanti al sensore.");
  Serial.println("-------------------------------------------");
}

void loop() {
  if (baudTrovato == 0) return;
  sensor.check();

  if (millis() - lastPrint < 500) return;
  lastPrint = millis();

  if (sensor.presenceDetected()) {
    Serial.print("PRESENZA  ");
    if (sensor.movingTargetDetected()) {
      Serial.print("[movimento] dist=");
      Serial.print(sensor.movingTargetDistance());
      Serial.print("cm energia=");
      Serial.print(sensor.movingTargetSignal());
      Serial.print("  ");
    }
    if (sensor.stationaryTargetDetected()) {
      Serial.print("[fermo] dist=");
      Serial.print(sensor.stationaryTargetDistance());
      Serial.print("cm energia=");
      Serial.print(sensor.stationaryTargetSignal());
    }
    Serial.println();
  } else {
    Serial.println("--- nessuno ---");
  }
}
