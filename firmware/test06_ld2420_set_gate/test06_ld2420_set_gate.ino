/*
 * Configurazione del LD2420 via UART — l'equivalente di `test04_set_gate` per l'altro
 * radar. Legge versione e parametri, imposta il gate massimo, e sa riportare il modulo
 * alla configurazione di fabbrica del NOSTRO esemplare.
 *
 * Perche' via UART e non col tool PC: la regola del progetto e' che dei valori numerici
 * ci si fida solo dalla rilettura via seriale. Sul LD2410B il tool PC diede una lettura
 * sbagliata delle sensibilita' e la verita' venne dall'UART (vedi CLAUDE.md). Questo
 * sketch rilegge SEMPRE dopo aver scritto.
 *
 * ⚠️ ALIMENTAZIONE 3.3V — NON 5V.
 *   J2 pin 1  3V3 -> 3V3     | J2 pin 3  OT1 -> GPIO16 (RX2)
 *   J2 pin 2  GND -> GND     | J2 pin 4  RX  -> GPIO17 (TX2)
 * OT2 non serve a questo sketch.
 *
 * 🚨 MAI con il LD2410B alimentato (interferenza a 24 GHz).
 *
 * Protocollo: HLK-LD2420 Protocol Document, Tabelle 1 e 2.
 *   intestazione FD FC FB FA | lunghezza dati (2 byte, little endian)
 *   comando (2 byte LE) + parametri | chiusura 04 03 02 01
 *   0x00FF apri modalita' comandi (valore 0x0001) · 0x00FE chiudi
 *   0x0000 versione · 0x0068 riavvio · 0x0008 leggi parametri · 0x0007 scrivi parametri
 *   nomi parametro: 0x0000 gate minimo · 0x0001 gate massimo · 0x0004 ritardo
 *                   0x0010-0x001F soglie trigger · 0x0020-0x002F soglie maintain
 *
 * Serial Monitor a 115200 baud, invio riga per riga.
 */

#define RADAR_RX_PIN 16
#define RADAR_TX_PIN 17
#define RADAR_BAUD   115200
#define sensorSerial Serial2

// Configurazione di fabbrica del NOSTRO esemplare, da `HLK-LD2420/Backup config/
// ld2420_config_fabbrica.xml`. I valori in dB del tool sono convertiti in grezzo con
// grezzo = 10^(dB/10): relazione verificata sui gate 0-5, dove coincide byte per byte
// con gli esempi del Protocol Document (60000, 30000, 3000, 2000, 500, 400).
const uint16_t FAB_GATE_MAX = 12;
const uint16_t FAB_RITARDO  = 30;
const uint32_t FAB_TRIGGER[16] = {60000, 30000, 3000, 2000, 500, 400, 400, 300,
                                    300,   300,  300,  250, 250, 200, 200, 200};
const uint32_t FAB_MAINTAIN[16] = {40000, 20000, 400, 300, 300, 200, 200, 150,
                                     150,   100, 100, 100, 100, 100, 100, 100};

static uint8_t risp[128];
static int nRisp = 0;

// ---------------------------------------------------------------- invio e ricezione

void inviaFrame(uint16_t cmd, const uint8_t *dati, uint16_t nDati) {
  uint16_t len = 2 + nDati;
  uint8_t testa[] = {0xFD, 0xFC, 0xFB, 0xFA};
  uint8_t coda[]  = {0x04, 0x03, 0x02, 0x01};
  sensorSerial.write(testa, 4);
  sensorSerial.write((uint8_t)(len & 0xFF));
  sensorSerial.write((uint8_t)(len >> 8));
  sensorSerial.write((uint8_t)(cmd & 0xFF));
  sensorSerial.write((uint8_t)(cmd >> 8));
  if (nDati) sensorSerial.write(dati, nDati);
  sensorSerial.write(coda, 4);
  sensorSerial.flush();
}

// Raccoglie la risposta fino alla chiusura 04 03 02 01. Ritorna il numero di byte utili
// del corpo (dopo intestazione e lunghezza), oppure -1 in caso di timeout.
// 5 s: il modulo risponde in millisecondi, ma in modalita' ASCII trasmette di continuo
// e la risposta arriva in mezzo al flusso. Un timeout largo costa nulla quando tutto va
// bene e toglie un dubbio quando non va.
int leggiRisposta(unsigned long timeoutMs = 5000) {
  unsigned long t0 = millis();
  nRisp = 0;
  int fase = 0;                       // 0=cerca intestazione, 1=raccoglie
  const uint8_t testa[] = {0xFD, 0xFC, 0xFB, 0xFA};
  int iTesta = 0;
  while (millis() - t0 < timeoutMs) {
    if (!sensorSerial.available()) continue;
    uint8_t b = sensorSerial.read();
    if (fase == 0) {
      iTesta = (b == testa[iTesta]) ? iTesta + 1 : (b == testa[0] ? 1 : 0);
      if (iTesta == 4) fase = 1;
      continue;
    }
    if (nRisp < (int)sizeof(risp)) risp[nRisp++] = b;
    if (nRisp >= 4 && risp[nRisp-4] == 0x04 && risp[nRisp-3] == 0x03 &&
        risp[nRisp-2] == 0x02 && risp[nRisp-1] == 0x01)
      return nRisp - 4;               // esclude la chiusura
  }
  return -1;
}

bool comando(uint16_t cmd, const uint8_t *dati, uint16_t nDati, const char *nome) {
  // Svuota il buffer: in modalita' normale il modulo trasmette ASCII a ~10 Hz, e i byte
  // gia' accodati prima del comando allungano la ricerca dell'intestazione.
  while (sensorSerial.available()) sensorSerial.read();
  inviaFrame(cmd, dati, nDati);
  int n = leggiRisposta();
  if (n < 0) { Serial.print("!! "); Serial.print(nome);
               Serial.println(": nessuna risposta (timeout)"); return false; }
  // corpo: lunghezza(2) + comando di ritorno(2) + stato(2) + eventuali dati
  if (n < 6) { Serial.print("!! "); Serial.print(nome);
               Serial.println(": risposta troppo corta"); return false; }
  uint16_t stato = risp[4] | (risp[5] << 8);
  if (stato != 0x0000) { Serial.print("!! "); Serial.print(nome);
                         Serial.print(": il modulo ha risposto ERRORE 0x");
                         Serial.println(stato, HEX); return false; }
  return true;
}

bool apriConfig()  { uint8_t d[] = {0x01, 0x00};
                     return comando(0x00FF, d, 2, "apri modalita' comandi"); }
bool chiudiConfig(){ return comando(0x00FE, nullptr, 0, "chiudi modalita' comandi"); }

// ---------------------------------------------------------------- lettura parametri

bool leggiParam(uint16_t nome, uint32_t &valore) {
  uint8_t d[] = {(uint8_t)(nome & 0xFF), (uint8_t)(nome >> 8)};
  if (!comando(0x0008, d, 2, "leggi parametro")) return false;
  // corpo: len(2) + cmd(2) + stato(2) + valore(4)
  if (nRisp - 4 < 10) { Serial.println("!! risposta senza valore"); return false; }
  valore = (uint32_t)risp[6] | ((uint32_t)risp[7] << 8) |
           ((uint32_t)risp[8] << 16) | ((uint32_t)risp[9] << 24);
  return true;
}

bool scriviParam(uint16_t nome, uint32_t valore) {
  uint8_t d[6] = {(uint8_t)(nome & 0xFF), (uint8_t)(nome >> 8),
                  (uint8_t)(valore & 0xFF), (uint8_t)((valore >> 8) & 0xFF),
                  (uint8_t)((valore >> 16) & 0xFF), (uint8_t)((valore >> 24) & 0xFF)};
  return comando(0x0007, d, 6, "scrivi parametro");
}

void stampaVersione() {
  if (!comando(0x0000, nullptr, 0, "leggi versione")) return;
  // corpo: len(2) + cmd(2) + stato(2) + lunghezza stringa(2) + ASCII
  int n = nRisp - 4;
  if (n < 8) { Serial.println("(versione: risposta inattesa)"); return; }
  int lung = risp[6] | (risp[7] << 8);
  Serial.print("Versione firmware: ");
  for (int i = 0; i < lung && 8 + i < n; i++) Serial.print((char)risp[8 + i]);
  Serial.println();
}

void stampaParametri(const char *intestazione) {
  Serial.print("\n=== "); Serial.print(intestazione); Serial.println(" ===");
  uint32_t v;
  if (leggiParam(0x0000, v)) { Serial.print("Gate minimo:  "); Serial.println(v); }
  uint32_t gmax = 0;
  if (leggiParam(0x0001, gmax)) {
    Serial.print("Gate massimo: "); Serial.print(gmax);
    Serial.print("   -> portata "); Serial.print(gmax * 70); Serial.println(" cm");
    if (gmax != FAB_GATE_MAX) {
      Serial.print("   ⚠️  DIVERSO dalla fabbrica ("); Serial.print(FAB_GATE_MAX);
      Serial.println("): annotarlo nel registro insieme ai trial acquisiti adesso");
    }
  }
  if (leggiParam(0x0004, v)) { Serial.print("Ritardo scomparsa: "); Serial.print(v);
                               Serial.println(" s"); }
  // Le 32 soglie restano memorizzate per tutti e 16 i gate anche quando il gate
  // massimo e' piu' basso: i gate oltre il massimo vengono marcati inattivi,
  // altrimenti la tabella lunga fa sembrare che l'impostazione non sia stata applicata.
  Serial.print("\nGate ATTIVI: da 0 a "); Serial.print(gmax);
  Serial.print("   (i gate da "); Serial.print(gmax + 1);
  Serial.println(" a 15 conservano le soglie ma non rilevano)");
  Serial.println("\ngate | distanza      | trigger | maintain");
  for (int i = 0; i < 16; i++) {
    uint32_t t = 0, m = 0;
    // Se il modulo non risponde si esce subito: con 32 letture e un timeout di 5 s
    // proseguire bloccherebbe il monitor per oltre due minuti.
    if (!leggiParam(0x0010 + i, t) || !leggiParam(0x0020 + i, m)) {
      Serial.println("   !! lettura fallita: interrompo la tabella");
      return;
    }
    Serial.print("  "); if (i < 10) Serial.print(' '); Serial.print(i);
    Serial.print(" | "); Serial.print(i * 70); Serial.print('-');
    Serial.print((i + 1) * 70); Serial.print(" cm");
    if (i < 10) Serial.print(' ');
    Serial.print(" | "); Serial.print(t);
    Serial.print("\t| "); Serial.print(m);
    if (t != FAB_TRIGGER[i] || m != FAB_MAINTAIN[i]) Serial.print("   <-- non di fabbrica");
    if ((uint32_t)i > gmax) Serial.print("   (inattivo)");
    Serial.println();
  }
}

// ---------------------------------------------------------------- comandi utente

void riavvia();

void impostaGateMax(long g) {
  if (g < 0 || g > 15) {
    Serial.println("!! il Protocol Document dichiara il range 0x00-0x0F, cioe' 0-15.");
    return;
  }
  Serial.print("\n-> imposto gate massimo = "); Serial.println(g);
  if (!apriConfig()) return;
  bool ok = scriviParam(0x0001, (uint32_t)g);
  Serial.println(ok ? "   comando accettato" : "   comando RIFIUTATO");
  uint32_t letto = 0;
  if (leggiParam(0x0001, letto)) {
    Serial.print("   rilettura: gate massimo = "); Serial.print(letto);
    Serial.print("  -> portata "); Serial.print(letto * 70); Serial.println(" cm");
  }
  chiudiConfig();                     // come il LD2410B: si applica alla chiusura

  // NON si riavvia. Il 02/09/2026 e' stato verificato due volte (BUILD 4) che il
  // riavvio 0x68 ricarica la configurazione dalla flash e SCARTA la scrittura: il gate
  // veniva riletto come 8 prima del riavvio e come 12 dopo. La scrittura vale finche'
  // il modulo resta alimentato, e per una sessione di misure e' tutto cio' che serve.
  // Verifica utile invece: riaprire la modalita' comandi e rileggere, per accertare che
  // il valore tenga in RAM anche fuori dalla sessione di comandi in cui e' stato scritto.
  delay(300);
  Serial.println("   verifica: riapro la modalita' comandi e rileggo...");
  if (!apriConfig()) { Serial.println("   !! il modulo non risponde"); return; }
  uint32_t dopo = 0;
  if (leggiParam(0x0001, dopo)) {
    Serial.print("   gate massimo = "); Serial.print(dopo);
    if ((long)dopo == g) {
      Serial.println("   OK: il valore tiene (in RAM, fino allo spegnimento)");
      Serial.println("   NON riavviare il modulo e NON staccare il 3V3, o torna a 12.");
    } else {
      Serial.print("   !! tornato a "); Serial.println(dopo);
    }
  }
  chiudiConfig();
}

// Riavvio: indispensabile dopo una scrittura di parametri. Senza, il modulo resta in
// modalita' comandi e NON fa rilevamento — accertato il 02/09/2026, quando dopo un
// `g 8` il logger ha registrato presenza 0 e distanza 0 su tutti i 903 campioni, con
// il soggetto a 1-2 m in movimento. Il Protocol Document elenca il comando 0x68
// accanto a quelli di scrittura proprio per questo.
void riavvia() {
  Serial.println("   riavvio il modulo per applicare la configurazione...");
  // Si invia il frame SENZA attendere risposta: il riavvio e' l'unico comando per cui
  // il Protocol Document non mostra alcuna riga "Response". Il modulo riparte e basta,
  // quindi aspettare una risposta produrrebbe sempre un timeout — che non e' un errore.
  inviaFrame(0x0068, nullptr, 0);
  delay(3000);                        // il riavvio completo richiede un paio di secondi
  while (sensorSerial.available()) sensorSerial.read();   // scarta il rumore di boot
  Serial.println("   inviato. Nessuna risposta attesa: il modulo riparte e basta.");
  Serial.println("   ⚠️ Verifica con 'p' che risponda, poi col logger che rilevi.");
}

void ripristinaFabbrica() {
  Serial.println("\n-> ripristino la configurazione di fabbrica del nostro esemplare");
  if (!apriConfig()) return;
  bool ok = scriviParam(0x0001, FAB_GATE_MAX) && scriviParam(0x0004, FAB_RITARDO);
  for (int i = 0; i < 16; i++) {
    ok &= scriviParam(0x0010 + i, FAB_TRIGGER[i]);
    ok &= scriviParam(0x0020 + i, FAB_MAINTAIN[i]);
  }
  Serial.println(ok ? "   scritture completate" : "   !! almeno una scrittura e' fallita");
  stampaParametri("rilettura dopo il ripristino");
  chiudiConfig();
  riavvia();
}

void menu() {
  Serial.println("\n--------------------------------------------------------------");
  Serial.println(" v          leggi la versione firmware");
  Serial.println(" p          rileggi e stampa tutti i parametri");
  Serial.println(" g <n>      imposta il gate massimo (portata = n x 70 cm)");
  Serial.println("            es. 'g 8' = 560 cm, vicino ai 600 cm di fabbrica del LD2410B");
  Serial.println(" d          RIPRISTINA la configurazione di fabbrica (gate 12,");
  Serial.println("            ritardo 30 s, le 32 soglie del nostro backup XML)");
  Serial.println(" r          riavvia il modulo (ATTENZIONE: riporta il gate a 12)");
  Serial.println("--------------------------------------------------------------");
}

void eseguiComando(String riga) {
  riga.trim();
  if (riga.length() == 0) return;
  char c = riga.charAt(0);
  switch (c) {
    case 'v': if (apriConfig()) { stampaVersione(); chiudiConfig(); } break;
    case 'p': if (apriConfig()) { stampaParametri("parametri correnti"); chiudiConfig(); } break;
    case 'g': impostaGateMax(riga.substring(1).toInt()); break;
    case 'd': ripristinaFabbrica(); break;
    case 'r': if (apriConfig()) riavvia(); break;
    default:  Serial.println("comando non riconosciuto"); break;
  }
  menu();
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  sensorSerial.begin(RADAR_BAUD, SERIAL_8N1, RADAR_RX_PIN, RADAR_TX_PIN);
  delay(500);
  Serial.println("\n=== Configurazione LD2420 via UART ===");
  // Marcatore di build: distingue a colpo d'occhio quale versione sta girando
  // davvero sull'ESP32. Il 02/09/2026 tre giri di prove sono stati attribuiti al
  // modulo mentre la causa era un binario vecchio, rimasto perche' lo sketch non
  // compilava e l'IDE non caricava nulla di nuovo.
  Serial.println("BUILD 5 - g <n> scrive e chiude SENZA riavviare, poi rilegge;");
  Serial.println("          il riavvio (r) ricarica la flash e scarta la scrittura");
  Serial.println("Alimentazione 3.3V | OT1->GPIO16, RX->GPIO17 | 115200 baud");
  if (apriConfig()) {
    stampaVersione();
    stampaParametri("parametri correnti");
    chiudiConfig();
  } else {
    Serial.println("!! il modulo non risponde: controllare alimentazione e OT1/RX");
  }
  menu();
}

void loop() {
  static String riga;
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') { if (riga.length()) { eseguiComando(riga); riga = ""; } }
    else riga += c;
  }
}
