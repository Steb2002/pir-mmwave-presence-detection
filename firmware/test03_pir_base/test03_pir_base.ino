/*
 * Test 0.3 — Primo contatto con il PIR HC-SR501
 *
 * Il PIR non ha seriale: espone una sola uscita digitale (OUT) che va ALTA
 * quando rileva movimento e torna BASSA dopo il tempo di ritenuta impostato
 * dal trimmer. Questo sketch legge OUT e stampa i cambi di stato con timestamp,
 * piu' un riepilogo periodico. L'uscita del HC-SR501 e' 3.3V (regolatore
 * HT7133 a bordo) quindi e' sicura per il GPIO dell'ESP32.
 *
 * Collegamento (ordine pin verificato sul nostro modulo, visto dal lato
 * trimmer: GND | OUT | +Power):
 *   VCC PIR (+Power) -> VIN ESP32 (5V)
 *   GND PIR          -> GND ESP32
 *   OUT PIR          -> D25 ESP32
 *
 * Configurazione hardware prevista dal PIANO_TEST (Test 0.3):
 *   - jumper in modalita' H (repeat trigger)
 *   - trimmer TEMPO DI RITENUTA al minimo (~3 s, antiorario a fondo corsa)
 *   - trimmer SENSIBILITA' a meta' corsa
 *   -> fotografare i trimmer: la posizione va tenuta identica per tutta la campagna
 *
 * ⚠️ Il HC-SR501 richiede ~60 s di stabilizzazione all'accensione: lo sketch
 *    mostra un conto alla rovescia e ignora quel primo minuto.
 *
 * Serial Monitor a 115200 baud.
 */

#define PIR_PIN 34   // allineato al logger (era D25, ora occupato da RX2 del radar)
#define WARMUP_S 60          // stabilizzazione HC-SR501 (~60 s, da datasheet)

bool statoPrec = false;
unsigned long ultimoRiepilogo = 0;
unsigned long nEventi = 0;   // conteggio fronti di salita (rilevamenti)

void setup() {
  Serial.begin(115200);
  pinMode(PIR_PIN, INPUT);
  delay(1000);
  Serial.println();
  Serial.println("=== Test PIR HC-SR501 (OUT su D25) ===");
  Serial.println("Jumper H, ritenuta al minimo, sensibilita' a meta'.");
  Serial.print("Stabilizzazione: attendo ");
  Serial.print(WARMUP_S);
  Serial.println(" s (non muoverti nella stanza)...");

  for (int s = WARMUP_S; s > 0; s--) {
    if (s % 10 == 0 || s <= 5) {
      Serial.print("  -");
      Serial.print(s);
      Serial.println(" s");
    }
    delay(1000);
  }
  Serial.println("Pronto! Muoviti per testare il rilevamento.");
  Serial.println("---------------------------------------------");
  statoPrec = digitalRead(PIR_PIN);
}

void loop() {
  bool stato = digitalRead(PIR_PIN);
  unsigned long t = millis();

  // stampa i cambi di stato con timestamp (secondi dall'avvio)
  if (stato != statoPrec) {
    Serial.print("[");
    Serial.print(t / 1000.0, 1);
    Serial.print(" s] ");
    if (stato) {
      nEventi++;
      Serial.println("MOVIMENTO rilevato (OUT alto)");
    } else {
      Serial.println("rilascio (OUT basso)  <- ora ~2.5 s di block time, il PIR e' cieco");
    }
    statoPrec = stato;
  }

  // riepilogo ogni 10 s
  if (t - ultimoRiepilogo > 10000) {
    Serial.print("    stato: ");
    Serial.print(stato ? "ALTO" : "basso");
    Serial.print(" | rilevamenti totali: ");
    Serial.println(nEventi);
    ultimoRiepilogo = t;
  }
}
