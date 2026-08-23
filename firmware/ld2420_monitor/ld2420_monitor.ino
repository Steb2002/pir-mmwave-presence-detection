/*
 * Monitor LD2420 (modalita' ASCII di fabbrica) — presenza + range leggibili.
 *
 * Il LD2420 di fabbrica trasmette a 115200 baud un semplice testo a righe:
 *     ON            -> presenza rilevata
 *     OFF           -> nessuna presenza
 *     Range NN      -> distanza del target (valore grezzo del sensore)
 * Questo sketch interpreta quelle righe e stampa uno stato pulito, evitando lo
 * spam: aggiorna solo quando lo stato cambia + un "battito" periodico.
 *
 * ⚠️ ALIMENTAZIONE 3.3V — NON 5V! Il VCC del LD2420 va sul pin 3V3 dell'ESP32.
 *
 * Collegamento (regola seriale: TX di uno -> RX dell'altro):
 *   3V3   sensore -> 3V3   ESP32
 *   GND   sensore -> GND   ESP32
 *   TX/OT sensore -> GPIO16 (RX2 ESP32)
 *   RX    sensore -> GPIO17 (TX2 ESP32)
 *
 * NOTA: l'unita' del "Range" in questa modalita' di fabbrica non e' documentata
 * nel datasheet; va verificata col tool HiLink (Test 0.5) prima di usarla come
 * distanza in metri nella tesi. Qui e' riportata come valore grezzo.
 *
 * Serial Monitor a 115200 baud.
 */

#define RADAR_RX_PIN 16   // ESP32 riceve  <- TX/OT del sensore
#define RADAR_TX_PIN 17   // ESP32 trasmette -> RX del sensore
#define RADAR_BAUD   115200

#define sensorSerial Serial2

// stato corrente
bool presenza = false;
int  range = -1;          // -1 = non ancora ricevuto
bool statoValido = false;

// buffer di riga
char linea[32];
int  lung = 0;

unsigned long ultimaStampa = 0;
bool cambiato = false;

// Interpreta una riga di testo completa dal sensore.
void gestisciLinea(const char *s) {
  if (strcmp(s, "ON") == 0) {
    if (!presenza) cambiato = true;
    presenza = true;
    statoValido = true;
  } else if (strcmp(s, "OFF") == 0) {
    if (presenza) cambiato = true;
    presenza = false;
    statoValido = true;
  } else if (strncmp(s, "Range ", 6) == 0) {
    int r = atoi(s + 6);
    if (r != range) cambiato = true;
    range = r;
    statoValido = true;
  }
  // altre righe (es. versione firmware) vengono ignorate
}

void stampaStato() {
  Serial.print("presenza: ");
  Serial.print(presenza ? "SI " : "NO ");
  if (presenza && range >= 0) {
    Serial.print(" | range (grezzo): ");
    Serial.print(range);
  }
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println();
  Serial.println("=== Monitor LD2420 (presenza + range) ===");
  Serial.println("Alimentazione 3.3V | TX sensore->GPIO16, RX sensore->GPIO17");
  Serial.println("-------------------------------------------");
  sensorSerial.begin(RADAR_BAUD, SERIAL_8N1, RADAR_RX_PIN, RADAR_TX_PIN);
}

void loop() {
  // leggi carattere per carattere e ricomponi le righe (terminate da \n)
  while (sensorSerial.available()) {
    char c = sensorSerial.read();
    if (c == '\n' || c == '\r') {
      if (lung > 0) {
        linea[lung] = '\0';
        gestisciLinea(linea);
        lung = 0;
      }
    } else if (lung < (int)sizeof(linea) - 1) {
      linea[lung++] = c;
    }
  }

  // stampa quando lo stato cambia, oppure ogni 1 s come "battito"
  unsigned long ora = millis();
  if (statoValido && (cambiato || (ora - ultimaStampa) > 1000)) {
    stampaStato();
    ultimaStampa = ora;
    cambiato = false;
  }
}
