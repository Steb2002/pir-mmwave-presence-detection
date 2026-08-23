/*
 * Test — Primo contatto con il LD2420 (auto-baud + dump grezzo HEX/ASCII)
 *
 * Il LD2420 NON ha una libreria Arduino matura e pinout/baud dipendono dal
 * firmware. Questo sketch non interpreta i dati: prima RILEVA da solo a quale
 * baud il sensore trasmette (115200 o 256000), poi si aggancia e fa un DUMP
 * continuo dei byte in arrivo, sia in HEX sia come testo ASCII. Serve a capire
 * il FORMATO reale dei dati (frame binario oppure testo) prima di scrivere un
 * parser su misura.
 *
 * ⚠️ ALIMENTAZIONE 3.3V — NON 5V! Il VCC del LD2420 va sul pin 3V3 dell'ESP32.
 *    Collegarlo a VIN (5V) puo' DANNEGGIARE il sensore.
 *
 * Collegamento (regola seriale: TX di uno -> RX dell'altro):
 *   3V3      del sensore  -> 3V3   ESP32 (lato sinistro, primo pin in alto)
 *   GND      del sensore  -> GND   ESP32
 *   TX/OT    del sensore  -> GPIO16 (RX2 dell'ESP32: qui l'ESP32 ascolta)
 *   RX       del sensore  -> GPIO17 (TX2 dell'ESP32: qui l'ESP32 parla)
 *
 * Quale pin sia il "TX seriale" dipende dal firmware (OT1 pin3 se fw >=1.5.3,
 * OT2 pin5 se fw <=1.5.2): leggere le sigle stampate sul PCB. Se non arrivano
 * byte, provare a spostare il filo dati sull'altro pin di uscita.
 *
 * Serial Monitor a 115200 baud.
 */

#define RADAR_RX_PIN 16   // ESP32 riceve  <- TX/OT del sensore
#define RADAR_TX_PIN 17   // ESP32 trasmette -> RX del sensore

// Baud forzato: metti 0 per usare l'auto-detect, oppure fissa il valore.
// L'auto-detect "piu' byte = vince" e' inaffidabile (un baud troppo alto legge
// piu' byte spuri), quindi conviene fissare il baud giusto una volta scoperto.
// Il firmware >=1.5.3 del LD2420 e' 115200; <=1.5.2 e' 256000.
#define FORCE_BAUD 115200

#define sensorSerial Serial2

const uint32_t BAUDS[] = {115200, 256000};   // i due baud possibili del LD2420
const int N_BAUDS = sizeof(BAUDS) / sizeof(BAUDS[0]);

uint32_t baudAttivo = 0;   // baud su cui ci siamo agganciati (0 = non ancora)

// Conta quanti byte arrivano in ~800 ms a un dato baud.
unsigned long provaBaud(uint32_t baud) {
  sensorSerial.end();
  delay(50);
  sensorSerial.begin(baud, SERIAL_8N1, RADAR_RX_PIN, RADAR_TX_PIN);
  delay(150);
  while (sensorSerial.available()) sensorSerial.read();   // svuota buffer

  unsigned long conteggio = 0;
  unsigned long fine = millis() + 800;
  while (millis() < fine) {
    if (sensorSerial.available()) {
      sensorSerial.read();
      conteggio++;
    }
  }
  return conteggio;
}

// Cerca il baud con piu' traffico. Ritorna 0 se non arriva nulla.
uint32_t rilevaBaud() {
  uint32_t migliore = 0;
  unsigned long maxByte = 0;
  for (int i = 0; i < N_BAUDS; i++) {
    unsigned long n = provaBaud(BAUDS[i]);
    Serial.print("  baud ");
    Serial.print(BAUDS[i]);
    Serial.print(" -> ");
    Serial.print(n);
    Serial.println(" byte");
    if (n > maxByte) {
      maxByte = n;
      migliore = BAUDS[i];
    }
  }
  return (maxByte > 0) ? migliore : 0;
}

// Stampa una riga: byte in HEX e, a fianco, la loro versione ASCII.
void stampaRiga(const byte *buf, int n) {
  for (int i = 0; i < n; i++) {
    if (buf[i] < 0x10) Serial.print('0');
    Serial.print(buf[i], HEX);
    Serial.print(' ');
  }
  // allinea la colonna ASCII se la riga e' corta
  for (int i = n; i < 16; i++) Serial.print("   ");
  Serial.print("| ");
  for (int i = 0; i < n; i++) {
    char c = (buf[i] >= 32 && buf[i] < 127) ? (char)buf[i] : '.';
    Serial.print(c);
  }
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  Serial.println();
  Serial.println("=== Test LD2420 - dump grezzo HEX/ASCII ===");
  Serial.println("ALIMENTAZIONE 3.3V! (VCC su 3V3, non su VIN)");
  Serial.println("Pin: sensore TX -> GPIO16, sensore RX -> GPIO17");
  Serial.println("-------------------------------------------");
  if (FORCE_BAUD != 0) {
    baudAttivo = FORCE_BAUD;
    Serial.print("Baud forzato a ");
    Serial.println(baudAttivo);
  } else {
    Serial.println("Rilevo il baud (muoviti davanti al sensore)...");
    baudAttivo = rilevaBaud();
  }

  if (baudAttivo == 0) {
    Serial.println();
    Serial.println("!! Nessun byte a nessun baud.");
    Serial.println("   - il TX del sensore e' davvero su GPIO16? prova l'altro pin di uscita (OT1<->OT2)");
    Serial.println("   - alimentazione 3.3V presente tra 3V3 e GND del sensore?");
    Serial.println("   - alcuni firmware del LD2420 NON trasmettono di default:");
    Serial.println("     in quel caso serve il tool HiLink (Test 0.5) per leggere fw e modalita'.");
    Serial.println("   Riavvio lo scan tra 3 s...");
    delay(3000);
    return;   // il loop ritentera' il rilevamento
  }

  Serial.println();
  Serial.print(">>> Agganciato a ");
  Serial.print(baudAttivo);
  Serial.println(" baud. Dump continuo (HEX | ASCII):");
  Serial.println("-------------------------------------------");
  sensorSerial.begin(baudAttivo, SERIAL_8N1, RADAR_RX_PIN, RADAR_TX_PIN);
}

void loop() {
  // se non ci siamo agganciati, ritenta il rilevamento
  if (baudAttivo == 0) {
    baudAttivo = rilevaBaud();
    if (baudAttivo != 0) {
      Serial.print(">>> Agganciato a ");
      Serial.print(baudAttivo);
      Serial.println(" baud. Dump continuo (HEX | ASCII):");
      sensorSerial.begin(baudAttivo, SERIAL_8N1, RADAR_RX_PIN, RADAR_TX_PIN);
    } else {
      delay(2000);
    }
    return;
  }

  // dump: accumula fino a 16 byte o fino a una pausa nello stream, poi stampa
  static byte buf[16];
  static int n = 0;
  static unsigned long ultimoByte = 0;

  while (sensorSerial.available()) {
    buf[n++] = sensorSerial.read();
    ultimoByte = millis();
    if (n == 16) {
      stampaRiga(buf, n);
      n = 0;
    }
  }

  // pausa > 20 ms nello stream: chiudi la riga parziale (fine di un "frame")
  if (n > 0 && (millis() - ultimoByte) > 20) {
    stampaRiga(buf, n);
    n = 0;
  }
}
