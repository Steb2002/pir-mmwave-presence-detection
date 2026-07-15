# Analisi del consumo energetico (Obiettivo 4)

> Analisi a titolo informativo, basata su dati di datasheet (come concordato con il professore —
> non si dispone di strumentazione di misura). Valori medi dichiarati dai produttori.

## Consumi dei componenti

### Sensori

| Componente | Tensione | Corrente media | Potenza media | Fonte |
|---|---|---|---|---|
| **HLK-LD2410B** | 5 V (alimentatore >200 mA richiesto) | **80 mA** | ~400 mW | Manuale ufficiale Hi-Link V1.03, tabella parametri elettrici |
| **HLK-LD2420** | 3.3 V (3.0–3.6 V) | **~50 mA** | ~165 mW | Datasheet Hi-Link / OpenELAB |
| **PIR HC-SR501** (modello in dotazione ✔) | 4.5–20 V | **< 0.05 mA** (50 µA quiescente) | ~0.3 mW | Datasheet HC-SR501 (mirror electronicoscaldas.com) |

Modello identificato dalle foto il 15/07/2026 (chip BISS0001 + regolatore HT7133,
vedi `analisi/ANALISI_PIR.md` §6): uscita a 3.3 V, compatibile ESP32.

### Microcontrollore ESP32-WROOM-32 (datasheet Espressif)

| Modalità | Corrente | Note |
|---|---|---|
| Attivo, WiFi TX | 160–260 mA (picco) | invio dati alla web UI |
| Attivo, WiFi ricezione/idle | ~95–100 mA | connesso, in ascolto |
| Modem-sleep (CPU attiva, WiFi off) | 20–68 mA | dipende da freq. CPU (80–240 MHz) |
| Light-sleep | ~0.8 mA | |
| Deep-sleep | ~0.01 mA (10 µA) | solo RTC attivo |

## Confronto dei nodi di sensing completi

Stima del consumo del nodo completo (ESP32 + sensore) nelle configurazioni della tesi:

| Configurazione | Corrente totale stimata | Potenza (5V) |
|---|---|---|
| ESP32 attivo + LD2410B + WiFi | ~180–260 mA | ~0.9–1.3 W |
| ESP32 attivo + LD2410B (solo logging seriale) | ~110–150 mA | ~0.55–0.75 W |
| ESP32 attivo + LD2420 | ~80–120 mA | ~0.4–0.6 W |
| ESP32 attivo + PIR | ~30–70 mA | ~0.15–0.35 W |
| ESP32 deep-sleep + PIR (veglia su interrupt) | **~0.06 mA** | ~0.3 mW |

Il punto chiave per la tesi: il PIR può funzionare da "sveglia" a costo quasi nullo
(l'uscita digitale può risvegliare l'ESP32 dal deep-sleep via interrupt GPIO),
mentre il radar mmWave costa 3 ordini di grandezza di più ed è pensato per alimentazione fissa.

## Stime di autonomia a batteria (Li-ion 18650 da 3000 mAh, efficienza regolatore ~85%)

| Scenario | Corrente media | Autonomia stimata |
|---|---|---|
| Nodo mmWave sempre attivo (LD2410B + ESP32 + WiFi) | ~200 mA | **~13 ore** |
| Nodo mmWave attivo senza WiFi continuo | ~130 mA | ~20 ore |
| Nodo PIR sempre attivo (ESP32 modem-sleep) | ~25 mA | ~4 giorni |
| Nodo dormiente (deep-sleep + PIR watchdog) | ~0.06 mA | **~4-5 anni** (limite: autoscarica batteria) |

## Implicazione per il progetto UPRISE — architettura ibrida consigliata

Il sistema negli arredi sta in "tempo di pace" per anni e deve funzionare a batteria durante
il blackout post-sisma. I numeri sopra suggeriscono l'architettura ibrida:

1. **Tempo di pace**: tutto in deep-sleep, PIR spento o usato come watchdog (~µA)
2. **Trigger "modalità terremoto"** (accelerometro sul gateway / blackout): l'ESP32 si sveglia
3. **Emergenza**: si accende il radar mmWave per il rilevamento fine (persona ferma sotto il
   banco, respiro, indice di vitalità) — l'autonomia di ~13-20 ore copre la finestra critica
   delle operazioni di ricerca e soccorso (le prime 72 ore sarebbero coperte con batteria maggiorata
   o duty-cycling del radar, es. 1 min ON / 4 min OFF → ~5× autonomia)

Questa argomentazione collega l'obiettivo 4 al contesto UPRISE e giustifica la coesistenza
PIR + mmWave invece della sostituzione secca: il PIR non è un concorrente ma il
"guardiano a basso costo" che decide quando accendere il radar.

## Fonti

- Manuale HLK-LD2410 V1.03 (Shenzhen Hi-Link): "Power Requirements DC 5V, Power supply capability >200mA, Average operating current 80 mA" — https://seengreat.com/upload/file/86/HLK+LD2410+Life+Presence+Sensor+Module+Manual+V1.03(220629).pdf
- HLK-LD2420 (OpenELAB/datasheet): 3.0–3.6 V, ~50 mA medi — https://openelab.io/blogs/learn/what-is-hlk-ld2420-and-how-to-use-it
- ESP32-WROOM-32 Datasheet (Espressif), sezione "Current Consumption" — https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32_datasheet_en.pdf
- Datasheet HC-SR501 — https://www.electronicoscaldas.com/datasheet/HC-SR501.pdf (mirror; altra copia: https://www.mpja.com/download/31227sc.pdf)
