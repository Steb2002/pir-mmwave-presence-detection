/*
  Test 0.x — Lettura versione firmware, MAC Bluetooth e parametri del LD2410B.

  Serve a documentare l'esemplare usato nella tesi (riproducibilita'):
  versione firmware, versione protocollo, MAC BT, risoluzione gate,
  range massimo, soglie per-gate, timeout presenza.

  Cablaggio (nostro, verificato 09/08/2026 — vedi CLAUDE.md):
    rosso  (Pin 5 VCC)     -> VIN ESP32 (5V)
    nero   (Pin 4 GND)     -> GND ESP32
    giallo (Pin 3 UART_Rx) -> D26 ESP32 (TX2)
    verde  (Pin 2 UART_Tx) -> D25 ESP32 (RX2)
    blu    (Pin 1 OUT)     -> non collegato

  ATTENZIONE: il radar ha un solo UART. Chiudere/disconnettere il tool PC
  (LD2410 Tool) prima di leggere via ESP32.

  Monitor seriale a 115200 baud.
*/
#include <MyLD2410.h>

#define RADAR_RX_PIN 25  // D25 = RX2, riceve il TX del radar (verde)
#define RADAR_TX_PIN 26  // D26 = TX2, va al RX del radar (giallo)
#define SERIAL_BAUD_RATE 115200

MyLD2410 sensor(Serial2);

// stampa un numero allineato a destra su 'larghezza' caratteri
void printPad(int val, byte larghezza) {
  for (byte i = String(val).length(); i < larghezza; i++) Serial.print(' ');
  Serial.print(val);
}

void printInfo() {
  sensor.configMode();
  sensor.requestFirmware();
  sensor.requestMAC();
  bool paramOk = sensor.requestParameters();

  String fw(sensor.getFirmware());
  Serial.println("=== Identificazione modulo ===");
  Serial.print("Firmware:          ");
  Serial.println(fw);
  Serial.print("Versione protocollo: ");
  Serial.println(sensor.getVersion());
  Serial.print("MAC Bluetooth:     ");
  Serial.println(sensor.getMACstr());
  if (!fw.startsWith(LD2410_LATEST_FIRMWARE)) {
    Serial.print("(la libreria considera '");
    Serial.print(LD2410_LATEST_FIRMWARE);
    Serial.println("' l'ultima nota — annotare, NON aggiornare)");
  }

  Serial.println("\n=== Parametri correnti ===");
  if (!paramOk) {
    Serial.println("!! Lettura parametri FALLITA (comando 0x0061): i valori sotto non");
    Serial.println("   sono affidabili. Riprovare; se persiste, e' un problema di UART.");
  }
  Serial.print("Risoluzione gate:  ");
  Serial.print(sensor.getResolution());
  Serial.println(" cm");
  // Portata = gate massimo x risoluzione (manuale V1.04 §5.2, verificato il
  // 23/08/2026 col monitor di test04_set_gate: gate 2 -> 150 cm, gate 1 -> 75 cm).
  // ⚠️ getRange_cm() di MyLD2410 fa (gate+1) x risoluzione e sovrastima di un gate:
  // con gate 8 riporta 675 cm invece di 600. Nel registro va il primo valore.
  Serial.print("Portata (gate x ris.): ");
  Serial.print((int)sensor.getMovingThresholds().N * (int)sensor.getResolution());
  Serial.println(" cm");
  Serial.print("  MyLD2410 getRange_cm(): ");
  Serial.print(sensor.getRange_cm());
  Serial.println(" cm  <- sovrastima di un gate, non usarlo");

  // Soglie per-gate in tabella: vanno confrontate riga per riga col rumore di fondo
  // misurato a stanza vuota (analisi/verifica_engineering.py). Regola del protocollo
  // V1.07 §1.2.2: il target e' riconosciuto solo se energia > soglia, quindi
  //   soglia <= rumore massimo di quel gate -> falsi positivi
  //   soglia = 100                          -> quel gate non rileva mai
  const MyLD2410::ValuesArray &mThr = sensor.getMovingThresholds();
  const MyLD2410::ValuesArray &sThr = sensor.getStationaryThresholds();
  byte res = sensor.getResolution();

  Serial.println("\n=== Soglie per-gate ===");
  Serial.println("gate |   distanza   | soglia mov. | soglia staz.");
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

  Serial.print("\nTimeout presenza:  ");
  Serial.print(sensor.getNoOneWindow());
  Serial.println(" s");

  // Configurazione ausiliaria (controllo luce / livello OUT), comando 0x01AE.
  if (sensor.requestAuxConfig()) {
    Serial.print("Config ausiliaria: controllo luce = ");
    Serial.print((int)sensor.getLightControl());
    Serial.print(", soglia = ");
    Serial.print(sensor.getLightThreshold());
    Serial.print(", livello OUT di default = ");
    Serial.println((int)sensor.getOutputControl());
  } else {
    // NON dedurre la versione firmware da questo esito: il nostro esemplare E' 2.44
    // e la richiesta non risponde comunque. Causa non accertata -> riportare il fatto,
    // non una spiegazione inventata.
    Serial.println("Config ausiliaria: richiesta 0x01AE senza risposta (causa non accertata)");
  }

  sensor.configMode(false);
}

void setup() {
  Serial.begin(SERIAL_BAUD_RATE);
  Serial2.begin(LD2410_BAUD_RATE, SERIAL_8N1, RADAR_RX_PIN, RADAR_TX_PIN);
  delay(2000);
  Serial.println("LD2410B — lettura firmware e parametri");

  if (!sensor.begin()) {
    Serial.println("Comunicazione col sensore FALLITA.");
    Serial.println("Controlla: cablaggio giallo->D26 / verde->D25, alimentazione 5V,");
    Serial.println("e che il tool PC non stia tenendo occupata la UART del radar.");
    while (true) delay(1000);
  }

  printInfo();
  Serial.println("\nFatto. Annotare questi valori in HLK-LD2410x/data/REGISTRO_SESSIONI.md");
}

void loop() {
}
