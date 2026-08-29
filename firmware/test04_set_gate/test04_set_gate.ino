/*
  Test 2.4 — Configurazione del gate massimo del LD2410B (selettivita' spaziale).

  SCOPO
  Il Test 2.4 del PIANO_TEST simula lo scenario UPRISE dei banchi affiancati: il radar
  vede attraverso il legno, quindi il sensore del banco A rischia di rilevare la persona
  sotto il banco B. La mitigazione e' limitare la portata al volume del proprio banco
  riducendo il gate massimo. Questo sketch serve a impostare quel parametro via UART,
  a RILEGGERLO per conferma, e soprattutto a RIPRISTINARE lo stato di partenza a fine
  test.

  PERCHE' NON L'APP BLUETOOTH
  Il PIANO_TEST prevedeva la configurazione via app; si fa via UART per due motivi:
  1. il LD2410 Tool PC ha gia' dato una lettura sbagliata delle soglie (vedi CLAUDE.md,
     "sensibilita' = 100"): dei valori numerici ci si fida solo via comando 0x0061
  2. qui la rilettura di conferma e' automatica e stampata, quindi finisce nel registro

  ATTENZIONE — IL RIPRISTINO NON E' OPZIONALE
  Le soglie e i gate di fabbrica sono il riferimento fisso di tutta la campagna
  (decisione documentata in CLAUDE.md: non ricalibrare a meta' campagna, altrimenti i
  trial non sono confrontabili). Se finisci il Test 2.4 e ti dimentichi di rimettere
  8/8/5, ogni acquisizione successiva e' fatta con una configurazione diversa da quella
  delle fasi 1-3 — e te ne accorgi solo rileggendo i parametri. Comando 'd' a fine test,
  sempre.

  Cablaggio (nostro, verificato 09/08/2026 — vedi CLAUDE.md):
    rosso  (Pin 5 VCC)     -> VIN ESP32 (5V)
    nero   (Pin 4 GND)     -> GND ESP32
    giallo (Pin 3 UART_Rx) -> D26 ESP32 (TX2)
    verde  (Pin 2 UART_Tx) -> D25 ESP32 (RX2)
    blu    (Pin 1 OUT)     -> non collegato

  NOTA: il radar ha un solo UART. Chiudere il LD2410 Tool PC prima di usare questo
  sketch, altrimenti la porta del radar e' occupata.

  Monitor seriale a 115200 baud, invio riga per riga ("Nuova riga" o "NL & CR").
*/
#include <MyLD2410.h>

#define RADAR_RX_PIN 25  // D25 = RX2, riceve il TX del radar (verde)
#define RADAR_TX_PIN 26  // D26 = TX2, va al RX del radar (giallo)
#define SERIAL_BAUD_RATE 115200

// Configurazione di fabbrica del NOSTRO esemplare (firmware 2.44.25070917), letta col
// comando 0x0061 il 18/08/2026 e registrata in HLK-LD2410x/data/REGISTRO_SESSIONI.md.
// E' lo stato a cui riporta il comando 'd': non sono valori copiati dal datasheet, sono
// quelli misurati su questo pezzo.
const byte SOGLIE_MOV_FABBRICA[9]  = {50, 50, 40, 30, 20, 15, 15, 15, 15};
const byte SOGLIE_STAZ_FABBRICA[9] = { 0,  0, 40, 40, 30, 30, 20, 20, 20};
const byte MAX_GATE_FABBRICA = 8;
const byte NOONE_FABBRICA = 5;

MyLD2410 sensor(Serial2);

// stampa un numero allineato a destra su 'larghezza' caratteri
void printPad(int val, byte larghezza) {
  for (byte i = String(val).length(); i < larghezza; i++) Serial.print(' ');
  Serial.print(val);
}

// Rilegge i parametri dal modulo e li stampa. E' la funzione di verita' dello sketch:
// tutto quello che si scrive nel registro delle sessioni deve venire da qui, non da
// quello che "abbiamo chiesto" al modulo.
bool stampaParametri(const char *intestazione) {
  Serial.print("\n=== ");
  Serial.print(intestazione);
  Serial.println(" ===");

  if (!sensor.requestParameters()) {
    Serial.println("!! Lettura parametri FALLITA (0x0061): i valori sotto NON sono");
    Serial.println("   affidabili. Riprovare con 'p'; se persiste e' un problema UART.");
    return false;
  }

  const MyLD2410::ValuesArray &mThr = sensor.getMovingThresholds();
  const MyLD2410::ValuesArray &sThr = sensor.getStationaryThresholds();
  byte res = sensor.getResolution();

  Serial.print("Gate massimo movimento:   ");
  Serial.println(mThr.N);
  Serial.print("Gate massimo stazionario: ");
  Serial.println(sThr.N);
  Serial.print("Risoluzione gate:         ");
  Serial.print(res);
  Serial.println(" cm");
  // Portata: si calcola come gate_massimo x risoluzione. E' la regola del manuale
  // V1.04 §5.2 ("if the farthest door is set to 2, only ... within 1.5m"), verificata
  // sul nostro esemplare il 23/08/2026 col monitor 'm'.
  // ⚠️ getRange_cm() di MyLD2410 calcola (gate+1) x risoluzione e sovrastima di un
  // gate: con gate 8 riporta 675 cm invece di 600. Stampato qui solo per confronto.
  Serial.print("Portata (gate x ris.):    ");
  Serial.print((int)mThr.N * (int)res);
  Serial.println(" cm");
  Serial.print("  MyLD2410 getRange_cm(): ");
  Serial.print(sensor.getRange_cm());
  Serial.println(" cm  <- sovrastima di un gate, non usarlo");
  Serial.print("Timeout presenza:         ");
  Serial.print(sensor.getNoOneWindow());
  Serial.println(" s");

  Serial.println("\ngate |   distanza   | soglia mov. | soglia staz.");
  for (byte i = 0; i <= mThr.N; i++) {
    Serial.print("  ");
    Serial.print(i);
    Serial.print("  | ");
    printPad(i * res, 4);
    Serial.print(" - ");
    printPad((i + 1) * res, 4);
    Serial.print(" cm |");
    printPad(mThr.values[i], 8);
    Serial.print("     |");
    printPad((i <= sThr.N) ? sThr.values[i] : 0, 8);
    Serial.println();
  }
  if (mThr.N < MAX_GATE_FABBRICA) {
    Serial.println("(i gate oltre il massimo non vengono riportati dal modulo: normale)");
  }

  // Confronto esplicito con lo stato di fabbrica: e' l'unico modo per accorgersi di
  // avere ancora addosso una configurazione da esperimento.
  bool difforme = (mThr.N != MAX_GATE_FABBRICA) || (sThr.N != MAX_GATE_FABBRICA) ||
                  (sensor.getNoOneWindow() != NOONE_FABBRICA);
  for (byte i = 0; i <= mThr.N && !difforme; i++) {
    if (mThr.values[i] != SOGLIE_MOV_FABBRICA[i]) difforme = true;
    if (i <= sThr.N && sThr.values[i] != SOGLIE_STAZ_FABBRICA[i]) difforme = true;
  }
  if (difforme) {
    Serial.println("\n*** CONFIGURAZIONE DIVERSA DA QUELLA DI FABBRICA ***");
    Serial.println("    Va annotata nel registro insieme ai trial acquisiti adesso,");
    Serial.println("    e ripristinata con 'd' prima di tornare alle altre fasi.");
  } else {
    Serial.println("\nConfigurazione = fabbrica (riferimento della campagna fasi 1-3).");
  }
  return true;
}

// Imposta i gate massimi mantenendo il timeout presenza corrente.
void applicaGate(byte movGate, byte stazGate) {
  byte noOne = sensor.getNoOneWindow();
  if (noOne == 0) noOne = NOONE_FABBRICA;

  Serial.print("\nImposto gate massimo: movimento=");
  Serial.print(movGate);
  Serial.print(", stazionario=");
  Serial.print(stazGate);
  Serial.print(", timeout=");
  Serial.print(noOne);
  Serial.println(" s ...");

  if (!sensor.setMaxGate(movGate, stazGate, noOne)) {
    Serial.println("!! setMaxGate ha restituito errore. NON dare per fatto il cambio:");
    Serial.println("   la rilettura qui sotto dice cosa c'e' davvero nel modulo.");
  }
  // La conferma la da' la rilettura, non il valore di ritorno del comando.
  stampaParametri("Parametri dopo la scrittura");
}

// Riporta il modulo allo stato documentato di fabbrica riscrivendo TUTTO: le 9+9 soglie,
// i gate massimi e il timeout. Non si limita a rialzare il gate massimo perche' durante
// il test possono essere state toccate anche le soglie.
void ripristinaFabbrica() {
  Serial.println("\nRipristino la configurazione di fabbrica del nostro esemplare...");
  Serial.println("(9 comandi per-gate + gate massimo: richiede qualche secondo)");

  MyLD2410::ValuesArray mov, staz;
  mov.setN(MAX_GATE_FABBRICA);
  staz.setN(MAX_GATE_FABBRICA);
  for (byte i = 0; i < 9; i++) {
    mov.values[i] = SOGLIE_MOV_FABBRICA[i];
    staz.values[i] = SOGLIE_STAZ_FABBRICA[i];
  }

  if (!sensor.setGateParameters(mov, staz, NOONE_FABBRICA)) {
    Serial.println("!! Ripristino FALLITO a meta'. Il modulo puo' essere in uno stato");
    Serial.println("   misto: NON acquisire dati. Riprovare con 'd', e se non torna");
    Serial.println("   usare 'F' (reset di fabbrica del modulo).");
  }
  stampaParametri("Parametri dopo il ripristino");
}

// Reset di fabbrica vero e proprio (comando del modulo) + riavvio. E' la via di scampo se
// il ripristino selettivo non basta: il protocollo V1.07 dice che il reset ha effetto
// dopo il riavvio, quindi si fanno entrambi.
void resetDiFabbrica() {
  Serial.println("\nRESET DI FABBRICA del modulo + riavvio...");
  if (!sensor.requestReset()) {
    Serial.println("!! Comando di reset non confermato.");
  }
  delay(200);
  if (!sensor.requestReboot()) {
    Serial.println("!! Comando di riavvio non confermato.");
  }
  Serial.println("Attendo il riavvio del radar (3 s)...");
  delay(3000);
  if (!sensor.begin()) {
    Serial.println("!! Il radar non risponde dopo il riavvio. Staccare e riattaccare");
    Serial.println("   l'alimentazione, poi resettare l'ESP32.");
    return;
  }
  stampaParametri("Parametri dopo il reset di fabbrica");
  Serial.println("Confrontare con le soglie di fabbrica registrate: se differiscono,");
  Serial.println("il valore 'di fabbrica' annotato il 18/08/2026 va rivisto.");
}

// Controllo rapido dell'effetto del gate: mostra presenza e distanze in tempo reale.
// Serve a verificare sul campo che oltre il gate massimo il radar davvero non veda,
// PRIMA di bruciare 3 trial da 3 minuti con una seconda persona.
void monitor() {
  Serial.println("\nMonitor: presenza / distanze. Invia un tasto qualsiasi per uscire.");
  Serial.println("Camminando avanti e indietro si trova dove il radar 'perde' il");
  Serial.println("bersaglio: quella e' la portata effettiva del gate impostato.\n");

  while (!Serial.available()) {
    if (sensor.check() == MyLD2410::DATA) {
      bool moving = sensor.movingTargetDetected();
      bool stationary = sensor.stationaryTargetDetected();
      Serial.print("presenza=");
      Serial.print(sensor.presenceDetected() ? 1 : 0);
      Serial.print("  mov=");
      Serial.print(moving ? 1 : 0);
      Serial.print(" d=");
      printPad(moving ? sensor.movingTargetDistance() : 0, 4);
      Serial.print("cm e=");
      printPad(moving ? sensor.movingTargetSignal() : 0, 3);
      Serial.print("  |  staz=");
      Serial.print(stationary ? 1 : 0);
      Serial.print(" d=");
      printPad(stationary ? sensor.stationaryTargetDistance() : 0, 4);
      Serial.print("cm e=");
      printPad(stationary ? sensor.stationaryTargetSignal() : 0, 3);
      Serial.println();
    }
    delay(200);
  }
  while (Serial.available()) Serial.read();
  Serial.println("Monitor chiuso.");
}

void menu() {
  Serial.println("\n--------------------------------------------------------------");
  Serial.println(" p           rileggi e stampa i parametri correnti");
  Serial.println(" g <m> <s>   imposta gate massimo movimento / stazionario (0-8)");
  Serial.println("             portata = gate x 75 cm (manuale V1.04 5.2, misurato");
  Serial.println("             il 23/08/2026): 'g 2 2' = 150 cm, 'g 8 8' = 600 cm");
  Serial.println(" w <sec>     imposta il timeout presenza (no-one window)");
  Serial.println(" m           monitor presenza/distanza in tempo reale");
  Serial.println(" d           RIPRISTINA la configurazione di fabbrica (da fare a");
  Serial.println("             fine Test 2.4, prima di qualsiasi altra acquisizione)");
  Serial.println(" F           reset di fabbrica del modulo + riavvio (via di scampo)");
  Serial.println("--------------------------------------------------------------");
}

void eseguiComando(String riga) {
  riga.trim();
  if (riga.length() == 0) return;
  char cmd = riga.charAt(0);

  switch (cmd) {
    case 'p':
      stampaParametri("Parametri correnti");
      break;

    case 'g': {
      // 'g 2 2' -> due interi attesi. Senza entrambi non si indovina: si rifiuta.
      int m = -1, s = -1;
      if (sscanf(riga.c_str() + 1, "%d %d", &m, &s) != 2) {
        Serial.println("Sintassi: g <gate_movimento> <gate_stazionario>, es. 'g 2 2'");
        break;
      }
      if (m < 0 || m > 8 || s < 0 || s > 8) {
        Serial.println("I gate ammessi sono 0-8. La libreria satura a 8 in silenzio,");
        Serial.println("quindi il controllo lo facciamo qui per non credere di aver");
        Serial.println("impostato un valore che il modulo non ha.");
        break;
      }
      // Il protocollo V1.07 §2.2.3 dichiara il range configurabile 2-8. Sotto il 2 il
      // modulo accetta il comando ma il comportamento non e' documentato, e con gate 0
      // e' risultato ROTTO: distanza congelata a 72 cm e presenza sempre attiva su 650
      // campioni (misurato il 23/08/2026). Gate 1 invece si comporta bene (portata 75 cm),
      // ma resta fuori specifica: usabile solo dichiarandolo.
      if (m < 2 || s < 2) {
        Serial.println("*** ATTENZIONE: gate < 2 e' FUORI SPECIFICA ***");
        Serial.println("    Il protocollo V1.07 dichiara il range configurabile 2-8.");
        Serial.println("    Misurato il 23/08/2026 su questo esemplare:");
        Serial.println("      gate 1 -> portata 75 cm, sembra funzionare (fuori spec)");
        Serial.println("      gate 0 -> ROTTO: distanza fissa 72 cm, presenza sempre 1");
        Serial.println("    Se procedi, dichiaralo nei dati acquisiti.");
      }
      applicaGate((byte)m, (byte)s);
      break;
    }

    case 'w': {
      int sec = -1;
      if (sscanf(riga.c_str() + 1, "%d", &sec) != 1 || sec < 0 || sec > 255) {
        Serial.println("Sintassi: w <secondi>, 0-255. Fabbrica = 5 s.");
        break;
      }
      Serial.print("\nImposto timeout presenza a ");
      Serial.print(sec);
      Serial.println(" s ...");
      if (!sensor.setNoOneWindow((byte)sec)) {
        Serial.println("!! setNoOneWindow ha restituito errore (oppure il valore era");
        Serial.println("   gia' quello richiesto). Vale la rilettura qui sotto.");
      }
      stampaParametri("Parametri dopo la scrittura");
      break;
    }

    case 'm':
      monitor();
      break;

    case 'd':
      ripristinaFabbrica();
      break;

    case 'F':
      Serial.println("\nReset di fabbrica: scrivere SI per confermare, altro per annullare.");
      while (!Serial.available()) delay(50);
      delay(100);
      if (Serial.readStringUntil('\n').indexOf("SI") >= 0) {
        resetDiFabbrica();
      } else {
        Serial.println("Annullato.");
      }
      break;

    default:
      Serial.print("Comando non riconosciuto: ");
      Serial.println(riga);
      menu();
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD_RATE);
  Serial2.begin(LD2410_BAUD_RATE, SERIAL_8N1, RADAR_RX_PIN, RADAR_TX_PIN);
  delay(2000);
  Serial.println("LD2410B — configurazione gate massimo (Test 2.4)");

  if (!sensor.begin()) {
    Serial.println("Comunicazione col sensore FALLITA.");
    Serial.println("Controlla: cablaggio giallo->D26 / verde->D25, alimentazione 5V,");
    Serial.println("e che il tool PC non stia tenendo occupata la UART del radar.");
    while (true) delay(1000);
  }

  // Si parte sempre da una fotografia dello stato reale: se una sessione precedente ha
  // lasciato il modulo configurato, si vede subito.
  stampaParametri("Stato ALL'AVVIO");
  menu();
}

void loop() {
  if (Serial.available()) {
    eseguiComando(Serial.readStringUntil('\n'));
    Serial.println("\nPronto (invia 'p' per rileggere, 'd' per ripristinare).");
  }
}
