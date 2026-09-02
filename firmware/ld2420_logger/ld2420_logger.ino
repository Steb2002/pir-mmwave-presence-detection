/*
 * Logger CSV per HLK-LD2420 — schema identico al logger del LD2410B.
 *
 * Emette le STESSE 9 colonne di `firmware/ld2410b_logger/`, cosi' acquire.py,
 * serie.py e analizza_test.py funzionano senza modifiche e i due dataset sono
 * confrontabili riga per riga (PIANO_TEST_LD2420.md, §1.2).
 *
 * ⚠️ ALIMENTAZIONE 3.3V — NON 5V. Il VCC del LD2420 va sul pin 3V3 dell'ESP32.
 *
 * Collegamento (regola seriale: TX di uno -> RX dell'altro):
 *   J2 pin 1  3V3   -> 3V3    ESP32
 *   J2 pin 2  GND   -> GND    ESP32
 *   J2 pin 3  OT1   -> GPIO16 (RX2 ESP32)   [il radar parla]
 *   J2 pin 4  RX    -> GPIO17 (TX2 ESP32)   [il radar ascolta]
 *   J2 pin 5  OT2   -> GPIO19  [presenza: alto = occupato, basso = libero]
 *   PIR OUT         -> GPIO21  [non collegato nelle sessioni del 02/09/2026]
 *
 * ⚠️ Due scelte di pin che si discostano dalla campagna LD2410B, entrambe da dichiarare:
 *
 *   OT2 su GPIO19 e non su GPIO15. Il 15 e' un pin di strapping: con OT2 che lo teneva
 *   alto l'ESP32 si avviava in modalita' flash invece che download e rifiutava l'upload
 *   ("Wrong boot mode detected"). GPIO19 non partecipa all'avvio, e i suoi vicini di
 *   fila (D18 e D21) sono altrettanto innocui — un filo spostato di un pin non fa danni.
 *   Sulla fila di sinistra e' l'unica posizione con questa proprieta'.
 *
 *   PIR su GPIO21 e non su GPIO34, perche' sulla breadboard attuale il 34 non e'
 *   raggiungibile. Il 21 ha i pull interni, quindi con INPUT_PULLDOWN la colonna legge
 *   0 pulito anche con il PIR scollegato, invece di fluttuare come farebbe il 34
 *   (solo-input e senza pull).
 *
 * 🚨 MAI con il LD2410B alimentato: entrambi lavorano a 24 GHz e si interferiscono.
 *
 * Serial Monitor / acquire.py a 115200 baud.
 */

#define RADAR_RX_PIN 16          // ESP32 riceve  <- OT1 del sensore
#define RADAR_TX_PIN 17          // ESP32 trasmette -> RX del sensore
#define RADAR_BAUD   115200      // firmware >= 1.5.3 (nostro esemplare, verificato)
#define OT2_PIN      19          // uscita di presenza del modulo (manuale V1.2, Tab. 3-2)
#define PIR_PIN      21          // ha i pull interni (a differenza del 34): vedi sopra
#define sensorSerial Serial2

// Cadenza identica a quella del LD2410B. Il modulo aggiorna a 10 Hz, ma l'ASCII e'
// asincrono e non emette una riga per campione: si campiona lo stato corrente a 5 Hz,
// che e' cio' che rende i due dataset confrontabili (PIANO_TEST_LD2420.md, Test 0.6).
const unsigned long samplePeriodMs = 200;

// 🚨 LA PRESENZA VIENE DAL PIN OT2, NON DALLE RIGHE ASCII (accertato 02/09/2026).
// Il dump grezzo di `firmware/test05_ld2420_raw/` ha mostrato che in modalita' ASCII il
// modulo emette coppie `ON` + `Range N` a ~9,5 Hz e **non emette praticamente mai `OFF`**:
// 2528 `ON` e zero `OFF` in 4 minuti, inclusi i 60 s con la stanza vuota. Su una notturna
// di 7 h a stanza vuota il rilascio e' arrivato solo 110 volte, con il modulo che
// dichiarava "occupato" per l'80 % del tempo. Le righe ASCII non sono quindi un indicatore
// di presenza utilizzabile; OT2 e' l'uscita di presenza documentata dal manuale.
//
// Il campo `Range` resta preso dall'ASCII, ma vale solo quando OT2 dice "occupato": a
// stanza vuota collassa su valori 0-6, mentre con un bersaglio vero riporta valori
// compatibili con i centimetri (105 a ~1 m, 414-425 a ~4,5 m). Il gate di presenza fa da
// filtro, cosi' non serve inventare una soglia arbitraria.

// 🔴 Fattore di conversione del campo `Range` in centimetri.
// NON e' documentato in nessuno dei due documenti ufficiali Hi-Link. Finche' vale 0
// la colonna `moving_distance_cm` riporta il valore GREZZO, ed e' la condizione in cui
// si esegue il Test 0.5-bis (taratura). Dopo la taratura si mette qui il coefficiente
// misurato e da quel momento la colonna e' in centimetri.
const float RANGE_IN_CM = 0.0f;  // 0 = grezzo, non convertito

// 🔑 GATE MASSIMO IMPOSTATO A OGNI AVVIO (02/09/2026).
// Sul nostro esemplare la scrittura dei parametri via UART **non sopravvive al riavvio**:
// verificato due volte con `test06_ld2420_set_gate` BUILD 4, dove il gate viene accettato
// e riletto come 8 e dopo il riavvio torna a 12. Invece di dipendere dalla flash, il
// logger riconfigura il modulo ogni volta che parte: cosi' ogni acquisizione ha una
// configurazione nota e dichiarata, che e' anche metodologicamente preferibile.
// 0 = non toccare la configurazione del modulo.
// ⚠️ TEMPORANEAMENTE 0 (02/09/2026, passo 1 della diagnosi): si vuole vedere se il
// modulo riprende a tracciare quando il logger NON gli manda alcun comando. L'ipotesi
// e' che qualunque sessione di comandi (anche solo apri+chiudi) fermi il rilevamento
// fino al riavvio — e il riavvio scarta la configurazione. Rimettere 8 se smentita.
#define GATE_MAX_DA_IMPOSTARE 0

static uint8_t risp[64];
static int nRisp = 0;

void inviaFrame(uint16_t cmd, const uint8_t *dati, uint16_t nDati) {
  uint8_t testa[] = {0xFD, 0xFC, 0xFB, 0xFA}, coda[] = {0x04, 0x03, 0x02, 0x01};
  uint16_t len = 2 + nDati;
  sensorSerial.write(testa, 4);
  sensorSerial.write((uint8_t)(len & 0xFF));  sensorSerial.write((uint8_t)(len >> 8));
  sensorSerial.write((uint8_t)(cmd & 0xFF));  sensorSerial.write((uint8_t)(cmd >> 8));
  if (nDati) sensorSerial.write(dati, nDati);
  sensorSerial.write(coda, 4);
  sensorSerial.flush();
}

bool attendiRisposta(unsigned long timeoutMs = 3000) {
  unsigned long t0 = millis();
  const uint8_t testa[] = {0xFD, 0xFC, 0xFB, 0xFA};
  int iTesta = 0; nRisp = 0; bool dentro = false;
  while (millis() - t0 < timeoutMs) {
    if (!sensorSerial.available()) continue;
    uint8_t b = sensorSerial.read();
    if (!dentro) {
      iTesta = (b == testa[iTesta]) ? iTesta + 1 : (b == testa[0] ? 1 : 0);
      if (iTesta == 4) dentro = true;
      continue;
    }
    if (nRisp < (int)sizeof(risp)) risp[nRisp++] = b;
    if (nRisp >= 4 && risp[nRisp-4] == 0x04 && risp[nRisp-3] == 0x03 &&
        risp[nRisp-2] == 0x02 && risp[nRisp-1] == 0x01) return true;
  }
  return false;
}

bool cmd2420(uint16_t cmd, const uint8_t *dati, uint16_t nDati) {
  while (sensorSerial.available()) sensorSerial.read();
  inviaFrame(cmd, dati, nDati);
  if (!attendiRisposta()) return false;
  return nRisp >= 6 && (risp[4] | (risp[5] << 8)) == 0x0000;
}

// Imposta il gate massimo e lascia il modulo in modalita' normale. NON riavvia: il
// riavvio scarterebbe la scrittura. Ritorna il valore riletto, oppure -1 se fallisce.
int impostaGateAllAvvio(uint8_t g) {
  uint8_t apri[] = {0x01, 0x00};
  if (!cmd2420(0x00FF, apri, 2)) return -1;
  uint8_t w[6] = {0x01, 0x00, g, 0x00, 0x00, 0x00};
  cmd2420(0x0007, w, 6);
  uint8_t rd[] = {0x01, 0x00};
  int letto = -1;
  if (cmd2420(0x0008, rd, 2) && nRisp >= 10) letto = risp[6] | (risp[7] << 8);
  cmd2420(0x00FE, nullptr, 0);          // chiude: il modulo torna a trasmettere ASCII
  return letto;
}

static bool presenza = false;
static long rangeGrezzo = -1;    // -1 = mai ricevuto
static unsigned long lastPrint = 0;
static String buf;

// Interpreta una riga della modalita' ASCII di fabbrica: "ON", "OFF", "Range NN".
void interpreta(String r) {
  r.trim();
  if (r.length() == 0) return;
  if (r.equalsIgnoreCase("ON"))       presenza = true;
  else if (r.equalsIgnoreCase("OFF")) presenza = false;
  else if (r.startsWith("Range")) {
    String n = r.substring(5); n.trim();
    // Accetta solo se c'e' davvero una cifra: toInt() restituisce 0 anche sulle
    // righe malformate, e uno zero spurio nel CSV sarebbe indistinguibile da un
    // bersaglio a distanza zero.
    bool haCifra = false;
    for (unsigned i = 0; i < n.length(); i++) if (isDigit(n[i])) { haCifra = true; break; }
    if (haCifra) rangeGrezzo = n.toInt();
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  // PULLDOWN: con il PIR scollegato la colonna resta 0 invece di fluttuare, e
  // quando il PIR c'e' lo pilota attivamente vincendo il pull (~45 kOhm).
  pinMode(PIR_PIN, INPUT_PULLDOWN);
  // OT2 e' pilotato attivamente dal modulo; il pulldown serve solo a dare uno 0 pulito
  // se il filo si stacca o il modulo non e' alimentato.
  pinMode(OT2_PIN, INPUT_PULLDOWN);
  sensorSerial.begin(RADAR_BAUD, SERIAL_8N1, RADAR_RX_PIN, RADAR_TX_PIN);
  delay(500);

#if GATE_MAX_DA_IMPOSTARE > 0
  // Le righe di configurazione escono come commenti '#': acquire.py cerca
  // l'intestazione CSV e le ignora, quindi non sporcano il file.
  int g = impostaGateAllAvvio(GATE_MAX_DA_IMPOSTARE);
  Serial.print("# gate massimo richiesto: "); Serial.print(GATE_MAX_DA_IMPOSTARE);
  Serial.print("  riletto: "); Serial.print(g);
  Serial.print(g == GATE_MAX_DA_IMPOSTARE ? "  OK -> portata " : "  !! NON APPLICATO ");
  if (g == GATE_MAX_DA_IMPOSTARE) { Serial.print(g * 70); Serial.print(" cm"); }
  Serial.println();
  delay(500);
#endif

  // Stesse 9 colonne del logger LD2410B. Le colonne a zero fisso non sono dati
  // mancanti: sono l'assenza documentata di quella grandezza sul LD2420 (canale
  // unico, nessuna distanza sul bersaglio fermo, nessuna energia in modalita' ASCII).
  Serial.println("timestamp_ms,radar_presence,moving_target,stationary_target,"
                 "moving_distance_cm,stationary_distance_cm,moving_energy,"
                 "stationary_energy,pir_presence");
}

void loop() {
  while (sensorSerial.available()) {
    char c = (char)sensorSerial.read();
    if (c == '\n') { interpreta(buf); buf = ""; }
    else if (c != '\r' && buf.length() < 64) buf += c;
  }

  unsigned long now = millis();
  if (now - lastPrint < samplePeriodMs) return;
  lastPrint = now;

  // Presenza da OT2. La variabile `presenza` ricavata dalle righe ASCII resta
  // calcolata ma NON viene usata: e' inaffidabile (vedi nota in testa al file).
  int p = digitalRead(OT2_PIN) ? 1 : 0;
  // Distanza: solo quando c'e' presenza, come fa il logger del LD2410B (0 = nessun
  // bersaglio). Se RANGE_IN_CM e' 0 il valore resta grezzo e va dichiarato come tale.
  long dist = 0;
  if (p && rangeGrezzo >= 0)
    dist = (RANGE_IN_CM > 0.0f) ? (long)(rangeGrezzo * RANGE_IN_CM) : rangeGrezzo;

  Serial.print(now);            Serial.print(',');
  Serial.print(p);              Serial.print(',');   // radar_presence
  Serial.print(p);              Serial.print(',');   // moving_target = presenza
  Serial.print(0);              Serial.print(',');   // stationary_target: non esiste
  Serial.print(dist);           Serial.print(',');   // moving_distance_cm
  Serial.print(0);              Serial.print(',');   // stationary_distance_cm: non esiste
  Serial.print(0);              Serial.print(',');   // moving_energy: non in ASCII
  Serial.print(0);              Serial.print(',');   // stationary_energy: non in ASCII
  Serial.println(digitalRead(PIR_PIN));              // pir_presence
}
