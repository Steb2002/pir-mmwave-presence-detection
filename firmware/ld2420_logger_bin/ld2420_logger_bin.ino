/*
 * Logger CSV per HLK-LD2420 in MODALITA' BINARIA ("energy mode") — tutto via UART,
 * come per il LD2410B. Sostituisce `ld2420_logger` (modalita' ASCII + pin OT2).
 *
 * PERCHE' (03/09/2026). L'interfaccia ASCII di fabbrica non fornisce una presenza
 * utilizzabile: in 4 minuti il modulo ha emesso 2528 `ON` e zero `OFF`, stanza vuota
 * inclusa. Il ripiego sul pin OT2 ha portato solo errori di cablaggio (D15 e' di
 * strapping, D2 accende il LED) e comunque nella configurazione di fabbrica non
 * rilasciava. Questa modalita' trasmette presenza, distanza e 16 energie per gate
 * dentro un frame binario: esattamente quello che leggiamo dal LD2410B.
 *
 * ⚠️ FONTE: componente ESPHome `ld2420` (sorgenti ld2420.h / ld2420.cpp), NON Hi-Link.
 *   Il Protocol Document ufficiale non documenta ne' il comando 0x0012 ne' il frame di
 *   uscita. Va dichiarato in tesi come scelta implementativa di comunita', non come
 *   specifica ufficiale (CLAUDE.md, regola sulle fonti).
 *
 * Formato del frame (ESPHome):
 *   F4 F3 F2 F1 | len(2) | presenza(1) | distanza cm (uint16 LE) | 16 x energia (uint16 LE) | F8 F7 F6 F5
 *   = 4 + 2 + 1 + 2 + 32 + 4 = 45 byte. Presenza all'offset 6, distanza 7-8, energie 9-40.
 *
 * Commutazione: in modalita' comandi, 0x0012 (CMD_WRITE_SYS_PARAM) con parametro
 * 0x0000 (system mode) e valore 0x0004 = energy, 0x0064 = simple (ASCII di fabbrica).
 *
 * ⚠️ ALIMENTAZIONE 3.3V — NON 5V.
 *   J2 pin 1  3V3 -> 3V3    | J2 pin 3  OT1 -> GPIO16 (RX2)   [il radar parla]
 *   J2 pin 2  GND -> GND    | J2 pin 4  RX  -> GPIO17 (TX2)   [il radar ascolta]
 *   J2 pin 5  OT2 -> GPIO19  facoltativo: solo per la colonna di confronto `ot2_level`
 *   PIR OUT       -> GPIO21  facoltativo
 *
 * ⏱️ Dopo l'accensione il modulo resta muto ~55 s (misurato il 03/09/2026): aspettare
 *    90 s dal collegamento del 3V3 prima di lanciare acquire.py.
 * 🚨 MAI con il LD2410B alimentato (interferenza a 24 GHz).
 *
 * CSV: le 9 colonne standard della tesi + 16 energie grezze + ot2_level. Le energie
 * sono uint16 0-65535, NON la scala 0-100 del LD2410B: per questo la colonna si chiama
 * `energy2420_gateN` e non `menergy_gateN`, cosi' nessuno script le confonde.
 * `moving_energy` e `stationary_energy` restano 0: quelle grandezze in scala 0-100 il
 * LD2420 non le ha. `moving_target` = presenza (canale unico), `stationary_*` = 0.
 */

#define RADAR_RX_PIN 16
#define RADAR_TX_PIN 17
#define RADAR_BAUD   115200
#define OT2_PIN      19
#define PIR_PIN      21
#define sensorSerial Serial2

const unsigned long samplePeriodMs = 200;   // 5 Hz, come il LD2410B

// ---------------------------------------------------------------- comandi

static uint8_t risp[64];
static int nRisp = 0;

void inviaFrame(uint16_t cmd, const uint8_t *dati, uint16_t nDati) {
  const uint8_t testa[] = {0xFD, 0xFC, 0xFB, 0xFA}, coda[] = {0x04, 0x03, 0x02, 0x01};
  uint16_t len = 2 + nDati;
  sensorSerial.write(testa, 4);
  sensorSerial.write((uint8_t)(len & 0xFF)); sensorSerial.write((uint8_t)(len >> 8));
  sensorSerial.write((uint8_t)(cmd & 0xFF)); sensorSerial.write((uint8_t)(cmd >> 8));
  if (nDati) sensorSerial.write(dati, nDati);
  sensorSerial.write(coda, 4);
  sensorSerial.flush();
}

bool attendiRisposta(unsigned long timeoutMs = 3000) {
  const uint8_t testa[] = {0xFD, 0xFC, 0xFB, 0xFA};
  unsigned long t0 = millis(); int iT = 0; bool dentro = false; nRisp = 0;
  while (millis() - t0 < timeoutMs) {
    if (!sensorSerial.available()) continue;
    uint8_t b = sensorSerial.read();
    if (!dentro) { iT = (b == testa[iT]) ? iT + 1 : (b == testa[0] ? 1 : 0);
                   if (iT == 4) dentro = true; continue; }
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

// Commuta in energy mode. Ritorna true se il modulo ha accettato ogni passo.
bool attivaEnergyMode() {
  const uint8_t apri[] = {0x01, 0x00};
  if (!cmd2420(0x00FF, apri, 2)) return false;
  // 0x0012: parametro 0x0000 (system mode), valore 0x00000004 (energy)
  const uint8_t modo[] = {0x00, 0x00, 0x04, 0x00, 0x00, 0x00};
  bool ok = cmd2420(0x0012, modo, 6);
  cmd2420(0x00FE, nullptr, 0);
  return ok;
}

// ---------------------------------------------------------------- frame dati

static uint8_t fr[64];
static int nFr = 0;
static bool dentroFrame = false;
static int iTesta = 0;

static int   presenza = 0;
static int   distanzaCm = 0;
static uint16_t energia[16];
static unsigned long ultimoFrameMs = 0;
static unsigned long frameRicevuti = 0;

void leggiFrame() {
  const uint8_t testa[] = {0xF4, 0xF3, 0xF2, 0xF1};
  while (sensorSerial.available()) {
    uint8_t b = sensorSerial.read();
    if (!dentroFrame) {
      iTesta = (b == testa[iTesta]) ? iTesta + 1 : (b == testa[0] ? 1 : 0);
      if (iTesta == 4) { dentroFrame = true; nFr = 0; }
      continue;
    }
    if (nFr < (int)sizeof(fr)) fr[nFr++] = b;
    // chiusura F8 F7 F6 F5
    if (nFr >= 4 && fr[nFr-4] == 0xF8 && fr[nFr-3] == 0xF7 &&
        fr[nFr-2] == 0xF6 && fr[nFr-1] == 0xF5) {
      // fr: len(2) presenza(1) dist(2) energie(32) coda(4) = 41 byte attesi
      if (nFr >= 41) {
        presenza   = fr[2] ? 1 : 0;
        distanzaCm = fr[3] | (fr[4] << 8);
        for (int g = 0; g < 16; g++) energia[g] = fr[5 + 2*g] | (fr[6 + 2*g] << 8);
        ultimoFrameMs = millis();
        frameRicevuti++;
      }
      dentroFrame = false; iTesta = 0; nFr = 0;
    }
  }
}

// ---------------------------------------------------------------- setup / loop

void setup() {
  Serial.begin(115200);
  delay(1000);
  pinMode(PIR_PIN, INPUT_PULLDOWN);
  pinMode(OT2_PIN, INPUT_PULLDOWN);
  sensorSerial.begin(RADAR_BAUD, SERIAL_8N1, RADAR_RX_PIN, RADAR_TX_PIN);
  delay(500);

  // Righe di servizio come commenti '#': acquire.py le ignora.
  Serial.println("# ld2420_logger_bin BUILD 1 - energy mode via 0x0012, presenza dal frame");
  bool ok = attivaEnergyMode();
  Serial.print("# energy mode: ");
  Serial.println(ok ? "attivata" : "!! il modulo NON ha accettato (0x0012) - restera' in ASCII");
  delay(300);

  Serial.print("timestamp_ms,radar_presence,moving_target,stationary_target,"
               "moving_distance_cm,stationary_distance_cm,moving_energy,"
               "stationary_energy,pir_presence");
  for (int g = 0; g < 16; g++) { Serial.print(",energy2420_gate"); Serial.print(g); }
  Serial.println(",ot2_level,frames_ok");
}

void loop() {
  leggiFrame();

  static unsigned long lastPrint = 0;
  unsigned long now = millis();
  if (now - lastPrint < samplePeriodMs) return;
  lastPrint = now;

  // Se non arrivano frame da oltre 2 s la presenza non e' affidabile: si scrive 0 e
  // frames_ok lo dichiara. Dopo l'accensione il modulo tace ~55 s: e' normale.
  bool frameFresco = ultimoFrameMs && (now - ultimoFrameMs) < 2000;
  int p = frameFresco ? presenza : 0;
  int d = (frameFresco && p) ? distanzaCm : 0;

  Serial.print(now);  Serial.print(',');
  Serial.print(p);    Serial.print(',');      // radar_presence
  Serial.print(p);    Serial.print(',');      // moving_target = presenza (canale unico)
  Serial.print(0);    Serial.print(',');      // stationary_target: non esiste
  Serial.print(d);    Serial.print(',');      // moving_distance_cm
  Serial.print(0);    Serial.print(',');      // stationary_distance_cm: non esiste
  Serial.print(0);    Serial.print(',');      // moving_energy (scala 0-100): non esiste
  Serial.print(0);    Serial.print(',');      // stationary_energy: non esiste
  Serial.print(digitalRead(PIR_PIN));         // pir_presence
  for (int g = 0; g < 16; g++) { Serial.print(','); Serial.print(frameFresco ? energia[g] : 0); }
  Serial.print(','); Serial.print(digitalRead(OT2_PIN));
  Serial.print(','); Serial.println(frameFresco ? 1 : 0);
}
