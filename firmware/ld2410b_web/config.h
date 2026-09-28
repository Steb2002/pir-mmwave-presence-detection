/*
 * config.h — l'unico file da toccare per configurare ld2410b_web.
 *
 * Rete: SOLO Access Point (decisione 05/09/2026, ANALISI_WEB_UI.md §1). L'ESP32 crea la
 * sua rete e non si collega a nessun WiFi esistente: nello scenario DIPME la rete di
 * casa non c'e'. Nessun segreto qui dentro: la password dell'AP e' pubblica per
 * definizione (sta scritta sul dispositivo), quindi il file resta nel repo.
 */
#pragma once

// ---------------------------------------------------------------- Access Point
#define AP_SSID        "DIPME-Sensor"
#define AP_PASSWORD    "dipme2026"      // WPA2, minimo 8 caratteri
#define AP_CANALE      1
#define AP_MAX_CLIENT  4                // coincide con il massimo di client WebSocket
// IP dell'AP: 192.168.4.1 (default del softAP dell'ESP32). Il DNS catch-all risponde
// con questo indirizzo a qualunque nome, quindi "dipme.local" o qualsiasi cosa
// scritta nel browser porta alla dashboard.

// ---------------------------------------------------------------- Radar e PIR (dallo step 2)
// Stesso cablaggio di firmware/ld2410b_logger (CLAUDE.md, "Collegamento ESP32 <-> LD2410B")
#define RADAR_RX_PIN   25               // D25 = RX2  <- cavo VERDE (UART_Tx del radar)
#define RADAR_TX_PIN   26               // D26 = TX2  -> cavo GIALLO (UART_Rx del radar)
#define RADAR_BAUD     256000
#define PIR_PIN        34               // HC-SR501 OUT, solo-input senza pull-up: va bene
#define PERIODO_CAMPIONE_MS 200         // 5 Hz, come il logger e i CSV della tesi

// ---------------------------------------------------------------- Indice di vitalita' (step 5)
// Algoritmo v3 di analisi/approfondimenti/ANALISI_VITALITA.md (§3.1 + §4.5), parametri tarati il
// 31/08/2026 (§4.6) su vitalita_proto.py. Le stesse costanti del prototipo: se cambiano
// qui devono cambiare anche la' (e viceversa), altrimenti bordo e offline divergono.
#define VIT_ALPHA_M     0.05f           // EWMA del livello di movimento (~4 s a 5 Hz)
#define VIT_ALPHA_V     0.01f           // EWMA della variabilita' (~20 s)
#define VIT_K           0.5f            // peso della componente di variabilita'
#define VIT_SOGLIA_1    45.0f           // < 45  -> vitalita_bassa (la piu' urgente per il soccorso)
                                        // tarata a 1 m; con il sensore sotto il banco (~60 cm) usare 70
                                        // (ritaratura sui trial sotto_banco_*_H, tesi Sezione 6.4)
#define VIT_SOGLIA_2    95.0f           // < 95  -> vitalita_moderata, altrimenti vitalita_alta
// Gate attivo: 1 = dalla distanza riportata dal radar (gate = dist / 75 cm; se non c'e'
// bersaglio si ripiega sull'energia), 0 = argmax dell'energia moving per gate.
// Con 'distanza' il prototipo riproduce meglio la tabella tarata (fermo 1 m 28,4 vs 28,6;
// movimento 99,4 vs 99,2); con 'energia' sotto il banco l'immobile sale a 64.
#define VIT_GATE_DA_DISTANZA 1
// Rumore di fondo per gate (canale moving), media sui campioni con radar_presence = 0 di
// stanza_vuota_notte_T01.csv (6,5 h, 118108 campioni): la stessa regola di
// vitalita_proto.py --fondo-da. Senza questa sottrazione stanza vuota e persona immobile
// danno lo stesso indice (§5.3). Specifico di QUESTA stanza e di QUESTO montaggio.
#define VIT_FONDO_GATE  { 17.58f, 13.20f, 4.35f, 2.88f, 5.29f, 3.06f, 3.87f, 3.33f, 4.41f }

// ---------------------------------------------------------------- Seriale verso il PC
#define SERIALE_BAUD   115200           // come il logger: acquire.py continua a funzionare
// Regola: ogni riga che NON e' CSV inizia con "# " (acquire.py la scarta)
