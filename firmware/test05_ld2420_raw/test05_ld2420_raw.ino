/*
 * Dump GREZZO di quello che il LD2420 manda sulla seriale.
 *
 * Non interpreta niente: stampa ogni riga cosi' com'e', con il tempo in millisecondi
 * e la lunghezza, ed evidenzia i byte non stampabili in esadecimale. Serve a rispondere
 * a una domanda che due sessioni di misure hanno lasciato aperta: quali righe emette
 * davvero il modulo, e con che cadenza.
 *
 * Perche' esiste (02/09/2026): il logger `ld2420_logger` ha riportato presenza nel
 * 79,4 % dei campioni in 7 h di stanza vuota, senza mai rilasciare — nemmeno quando la
 * stanza si e' svuotata davvero all'inizio della sessione — e con il campo `Range`
 * fermo su valori 0-6 invece dei 105-425 osservati con una persona presente. Il modulo
 * funziona (a 5 m rileva e riporta distanze sensate), quindi il sospetto e' sulla
 * nostra lettura dello stream ASCII: forse `OFF` non viene emesso come pensiamo, o ci
 * sono righe di altro tipo che il parser scambia per dati.
 *
 * ⚠️ ALIMENTAZIONE 3.3V — NON 5V.
 *
 * Collegamento: identico al logger.
 *   J2 pin 1  3V3 -> 3V3    | J2 pin 3  OT1 -> GPIO16
 *   J2 pin 2  GND -> GND    | J2 pin 4  RX  -> GPIO17
 *
 * 🚨 MAI con il LD2410B alimentato (interferenza a 24 GHz).
 *
 * Serial Monitor a 115200 baud.
 */

#define RADAR_RX_PIN 16
#define RADAR_TX_PIN 17
#define RADAR_BAUD   115200
#define sensorSerial Serial2

static char linea[128];
static int  lung = 0;
static unsigned long t0 = 0;
static unsigned long nRighe = 0;
static unsigned long ultimaRiga = 0;

void stampaRiga() {
  unsigned long ora = millis() - t0;
  unsigned long dt = ultimaRiga ? (millis() - ultimaRiga) : 0;
  ultimaRiga = millis();
  nRighe++;

  Serial.print('[');  Serial.print(ora);
  Serial.print(" ms, +"); Serial.print(dt);
  Serial.print(" ms, "); Serial.print(lung);
  Serial.print(" byte]  \"");
  for (int i = 0; i < lung; i++) {
    char c = linea[i];
    if (c >= 32 && c <= 126) Serial.print(c);
    else { Serial.print("<0x"); Serial.print((uint8_t)c, HEX); Serial.print('>'); }
  }
  Serial.println('"');
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  sensorSerial.begin(RADAR_BAUD, SERIAL_8N1, RADAR_RX_PIN, RADAR_TX_PIN);
  t0 = millis();
  ultimaRiga = 0;
  Serial.println();
  Serial.println("=== DUMP GREZZO LD2420 (115200 baud) ===");
  Serial.println("Ogni riga: [tempo, intervallo dalla precedente, lunghezza] contenuto");
  Serial.println("I byte non stampabili sono mostrati come <0xNN>.");
  Serial.println("Stai fermo ~30 s, poi muoviti ~30 s, poi esci dalla stanza ~60 s.");
  Serial.println("--------------------------------------------------------------");
}

void loop() {
  while (sensorSerial.available()) {
    char c = (char)sensorSerial.read();
    if (c == '\n') {
      linea[lung] = 0;
      stampaRiga();
      lung = 0;
    } else if (lung < (int)sizeof(linea) - 1) {
      linea[lung++] = c;      // il '\r' NON viene tolto: va visto anche quello
    }
  }

  // Se il modulo tace a lungo lo si deve sapere: un silenzio prolungato spiegherebbe
  // da solo lo stato "incollato" del logger, perche' l'ultimo valore resta valido.
  static unsigned long ultimoAvviso = 0;
  // Caso "mai arrivato nulla": prima l'avviso partiva solo dopo la PRIMA riga, quindi
  // un modulo completamente muto lasciava lo sketch in silenzio (02/09/2026). Ora si
  // avvisa anche se dall'avvio non e' arrivato un solo byte.
  if (!ultimaRiga && millis() - t0 > 5000 && millis() - ultimoAvviso > 5000) {
    ultimoAvviso = millis();
    Serial.print("!! NESSUN BYTE dal modulo da ");
    Serial.print((millis() - t0) / 1000);
    Serial.println(" s: o il filo OT1->GPIO16 e' staccato, o il modulo non trasmette");
  }
  if (ultimaRiga && millis() - ultimaRiga > 5000 && millis() - ultimoAvviso > 5000) {
    ultimoAvviso = millis();
    Serial.print("... nessuna riga da ");
    Serial.print((millis() - ultimaRiga) / 1000);
    Serial.print(" s (righe totali finora: ");
    Serial.print(nRighe);
    Serial.println(")");
  }
}
