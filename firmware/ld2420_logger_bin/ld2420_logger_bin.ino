/*
 * Logger CSV per HLK-LD2420 in MODALITA' BINARIA ("energy mode") — tutto via UART,
 * come per il LD2410B. Sostituisce `ld2420_logger` (modalita' ASCII), ora superato.
 *
 * PERCHE' (03/09/2026). L'interfaccia ASCII di fabbrica non fornisce una presenza
 * utilizzabile: in 4 minuti il modulo ha emesso 2528 `ON` e zero `OFF`, stanza vuota
 * inclusa. Questa modalita' trasmette presenza, distanza e 16 energie per gate
 * dentro un frame binario: esattamente quello che leggiamo dal LD2410B. Il pin OT2
 * (uscita di presenza) NON viene letto: la presenza e' quella del frame, che e' la
 * stessa decisione del modulo (04/09/2026: tolto tutto il codice OT2, non serviva).
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
 *   J2 pin 5  OT2   non collegato
 *   PIR OUT       -> GPIO21  facoltativo
 *
 * ⏱️ Dopo l'accensione il modulo resta muto ~55 s (misurato il 03/09/2026): aspettare
 *    90 s dal collegamento del 3V3 prima di lanciare acquire.py.
 * 🚨 MAI con il LD2410B alimentato (interferenza a 24 GHz).
 *
 * CSV: le 9 colonne standard della tesi + 16 energie grezze + frames_ok + dist_raw_cm.
 * ⚠️ Sono 27 colonne, lo stesso numero del logger LD2410B in engineering mode: se
 * acquire.py perde la riga di intestazione, la ricostruzione per conteggio sceglie i nomi
 * del LD2410B. L'intestazione viene stampata a ogni avvio, quindi succede solo se il reset
 * dell'ESP32 all'apertura della porta non scatta. Le energie
 * sono uint16 0-65535, NON la scala 0-100 del LD2410B: per questo la colonna si chiama
 * `energy2420_gateN` e non `menergy_gateN`, cosi' nessuno script le confonde.
 * `moving_energy` e `stationary_energy` restano 0: quelle grandezze in scala 0-100 il
 * LD2420 non le ha. `moving_target` = presenza (canale unico), `stationary_*` = 0.
 */

// Gate massimo da scrivere a ogni avvio (0 = non toccare quello in flash). Serve alla
// prova di portata del 04/09/2026: 8 → 7 → 6 con le soglie tarate dal tool, senza dover
// ricablare al CH340E a ogni cambio. ⚠️ La scrittura via UART vive in RAM: il modulo
// la perde se gli si toglie il 3V3, ma il reset dell'ESP32 per l'upload non lo spegne.
// Il valore letto dopo la scrittura finisce nel commento '#' in testa al CSV.
#define GATE_MAX_DA_IMPOSTARE 0

// Gate MINIMO da scrivere a ogni avvio (0 = non toccare). Test 2.6 e prova sul rilascio del
// 06/09/2026: il gate 0 e' l'accoppiamento TX->RX, non una distanza (la persona a 50 cm
// accende il gate 1), e ha code lunghissime (media 105, massimi 400-545 contro hold 367 e
// trigger 525) che tengono alta la presenza a stanza vuota. Con 1 il modulo dovrebbe
// ignorarlo nella decisione: parametro 0x0000, manuale Tab. 4-2, range 0-15. Come il gate
// massimo vive in RAM: riscritto a ogni reset dell'ESP32, quindi a ogni trial.
#define GATE_MIN_DA_IMPOSTARE 0

// Ritardo di scomparsa (parametro 0x0004, s) da scrivere a ogni avvio (0 = non toccare).
// Test 2.2-2420 con ritardo 5 s invece dei 30 in flash: chiude anche l'unita' del
// parametro, su cui manuale (0-65535) e Protocol Document (0x00-0x0F) si contraddicono.
// Come gli altri: RAM, si annulla col ciclo di alimentazione del modulo.
#define RITARDO_DA_IMPOSTARE 0

// 🚨 PIR CABLATO SU GPIO21? Metterlo a 0 quando il PIR non e' collegato: la colonna
// `pir_presence` esce a **-1** invece che a 0, e gli script di analisi la trattano come
// dato mancante (metriche del PIR omesse) invece che come una misura. Con lo 0 il pin
// in pull-down darebbe "fn_pir_% = 100,0" con una persona davanti, e quel numero finto
// entrerebbe da solo nel foglio `tutti_i_trial` di esporta_excel.py, che scandisce
// TUTTI i CSV della cartella. Nei test del solo LD2420 il PIR non serve: il suo dato a
// 1 m con persona immobile e' gia' in `fermo_1m_H` (pir_rate 1,52 %) ed e' indipendente
// da quale radar sia montato.
#define PIR_COLLEGATO 0

#define RADAR_RX_PIN 16
#define RADAR_TX_PIN 17
#define RADAR_BAUD   115200
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

bool leggiParam(uint16_t nome, uint32_t &valore) {
  uint8_t d[] = {(uint8_t)(nome & 0xFF), (uint8_t)(nome >> 8)};
  if (!cmd2420(0x0008, d, 2)) return false;
  if (nRisp - 4 < 10) return false;          // len(2) cmd(2) stato(2) valore(4)
  valore = (uint32_t)risp[6] | ((uint32_t)risp[7] << 8) |
           ((uint32_t)risp[8] << 16) | ((uint32_t)risp[9] << 24);
  return true;
}

bool scriviParam(uint16_t nome, uint32_t valore) {
  uint8_t d[6] = {(uint8_t)(nome & 0xFF), (uint8_t)(nome >> 8),
                  (uint8_t)(valore & 0xFF), (uint8_t)((valore >> 8) & 0xFF),
                  (uint8_t)((valore >> 16) & 0xFF), (uint8_t)((valore >> 24) & 0xFF)};
  return cmd2420(0x0007, d, 6);
}

static uint32_t gateMaxLetto = 0;
static bool     gateMaxOk = false;
static uint32_t gateMinLetto = 0;
static bool     gateMinOk = false;
static uint32_t ritardoLetto = 0;
static bool     ritardoOk = false;

// Una sola sessione di comandi: apre, (opzionale) scrive il gate massimo, rilegge il
// gate massimo, commuta in energy mode, chiude. Ritorna true se l'energy mode e' passato.
bool attivaEnergyMode() {
  const uint8_t apri[] = {0x01, 0x00};
  if (!cmd2420(0x00FF, apri, 2)) return false;
  if (GATE_MAX_DA_IMPOSTARE > 0) scriviParam(0x0001, (uint32_t)GATE_MAX_DA_IMPOSTARE);
  gateMaxOk = leggiParam(0x0001, gateMaxLetto);
  if (GATE_MIN_DA_IMPOSTARE > 0) scriviParam(0x0000, (uint32_t)GATE_MIN_DA_IMPOSTARE);
  gateMinOk = leggiParam(0x0000, gateMinLetto);
  if (RITARDO_DA_IMPOSTARE > 0) scriviParam(0x0004, (uint32_t)RITARDO_DA_IMPOSTARE);
  ritardoOk = leggiParam(0x0004, ritardoLetto);
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
  sensorSerial.begin(RADAR_BAUD, SERIAL_8N1, RADAR_RX_PIN, RADAR_TX_PIN);
  delay(500);

  // Righe di servizio come commenti '#': acquire.py le ignora.
  Serial.println("# ld2420_logger_bin BUILD 8 - gate min e ritardo opzionali, energy mode via 0x0012, presenza dal frame, dist_raw_cm, gate max opzionale, senza OT2");
  Serial.print("# PIR: ");
  Serial.println(PIR_COLLEGATO ? "cablato su GPIO21, colonna valida"
                               : "NON collegato, pir_presence = -1 (colonna non valida)");
  bool ok = attivaEnergyMode();
  Serial.print("# energy mode: ");
  Serial.println(ok ? "attivata" : "!! il modulo NON ha accettato (0x0012) - restera' in ASCII");
  Serial.print("# gate max: ");
  if (gateMaxOk) { Serial.print("letto "); Serial.print(gateMaxLetto); }
  else           { Serial.print("!! lettura fallita"); }
  Serial.print(" (GATE_MAX_DA_IMPOSTARE = "); Serial.print(GATE_MAX_DA_IMPOSTARE);
  Serial.println(GATE_MAX_DA_IMPOSTARE > 0 ? ", scritto in RAM a questo avvio)" : ", flash non toccata)");
  Serial.print("# gate min: ");
  if (gateMinOk) { Serial.print("letto "); Serial.print(gateMinLetto); }
  else           { Serial.print("!! lettura fallita"); }
  Serial.print(" (GATE_MIN_DA_IMPOSTARE = "); Serial.print(GATE_MIN_DA_IMPOSTARE);
  Serial.println(GATE_MIN_DA_IMPOSTARE > 0 ? ", scritto in RAM a questo avvio)" : ", flash non toccata)");
  Serial.print("# ritardo scomparsa: ");
  if (ritardoOk) { Serial.print("letto "); Serial.print(ritardoLetto); }
  else           { Serial.print("!! lettura fallita"); }
  Serial.print(" (RITARDO_DA_IMPOSTARE = "); Serial.print(RITARDO_DA_IMPOSTARE);
  Serial.println(RITARDO_DA_IMPOSTARE > 0 ? ", scritto in RAM a questo avvio)" : ", flash non toccata)");
  delay(300);

  Serial.print("timestamp_ms,radar_presence,moving_target,stationary_target,"
               "moving_distance_cm,stationary_distance_cm,moving_energy,"
               "stationary_energy,pir_presence");
  for (int g = 0; g < 16; g++) { Serial.print(",energy2420_gate"); Serial.print(g); }
  Serial.println(",frames_ok,dist_raw_cm");
}

void loop() {
  leggiFrame();

  // Se il modulo non ha ancora mandato un frame, ritenta l'energy mode ogni 5 s.
  // Serve quando il modulo e' stato appena alimentato: per ~55 s dopo l'accensione non
  // risponde ai comandi (misurato il 03/09/2026), quindi il comando dato in setup() va
  // perso e il modulo resta in ASCII per tutta l'acquisizione (successo il 04/09/2026,
  // `altezza2420_h180_T01`: 230 s con frames_ok = 0). Il ritentativo e' silenzioso sul
  // CSV; `frames_ok` dice da che momento i frame sono arrivati.
  static unsigned long ultimoTentativoMs = 0;
  if (!ultimoFrameMs && millis() - ultimoTentativoMs > 5000) {
    ultimoTentativoMs = millis();
    if (attivaEnergyMode()) Serial.println("# energy mode attivata al ritentativo");
  }
  // Oltre i 90 s (mutezza dopo l'accensione gia' passata) l'assenza di frame e' un
  // guasto di cablaggio: il 04/09/2026 un OT1->D16 sganciato ha prodotto 230 s di righe
  // a frames_ok = 0 senza nessun avviso. acquire.py mostra le righe '#' in console.
  static unsigned long ultimoAvvisoMs = 0;
  if (!ultimoFrameMs && millis() > 90000 && millis() - ultimoAvvisoMs > 30000) {
    ultimoAvvisoMs = millis();
    Serial.println("# ATTENZIONE: nessun frame dal modulo - controllare OT1->D16, RX->D17, 3V3, GND");
  }

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
  // -1 quando il PIR non e' cablato: e' il marcatore di "dato assente" che impedisce
  // agli script di scambiare il pull-down per una misura. Vedi PIR_COLLEGATO in testa.
  Serial.print(PIR_COLLEGATO ? digitalRead(PIR_PIN) : -1);   // pir_presence
  for (int g = 0; g < 16; g++) { Serial.print(','); Serial.print(frameFresco ? energia[g] : 0); }
  Serial.print(','); Serial.print(frameFresco ? 1 : 0);
  // Distanza grezza dal frame ANCHE con presenza 0: serve alla diagnosi, perche' dice
  // se il modulo sta agganciando qualcosa pur non dichiarando presenza.
  Serial.print(','); Serial.println(frameFresco ? distanzaCm : 0);
}
