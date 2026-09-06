/*
 * config.h — l'unico file da toccare per configurare ld2410b_web.
 *
 * Rete: SOLO Access Point (decisione 05/09/2026, ANALISI_WEB_UI.md §1). L'ESP32 crea la
 * sua rete e non si collega a nessun WiFi esistente: nello scenario UPRISE la rete di
 * casa non c'e'. Nessun segreto qui dentro: la password dell'AP e' pubblica per
 * definizione (sta scritta sul dispositivo), quindi il file resta nel repo.
 */
#pragma once

// ---------------------------------------------------------------- Access Point
#define AP_SSID        "UPRISE-Sensor"
#define AP_PASSWORD    "uprise2026"     // WPA2, minimo 8 caratteri
#define AP_CANALE      1
#define AP_MAX_CLIENT  4                // coincide con il massimo di client WebSocket
// IP dell'AP: 192.168.4.1 (default del softAP dell'ESP32). Il DNS catch-all risponde
// con questo indirizzo a qualunque nome, quindi "uprise.local" o qualsiasi cosa
// scritta nel browser porta alla dashboard.

// ---------------------------------------------------------------- Radar e PIR (dallo step 2)
// Stesso cablaggio di firmware/ld2410b_logger (CLAUDE.md, "Collegamento ESP32 <-> LD2410B")
#define RADAR_RX_PIN   25               // D25 = RX2  <- cavo VERDE (UART_Tx del radar)
#define RADAR_TX_PIN   26               // D26 = TX2  -> cavo GIALLO (UART_Rx del radar)
#define RADAR_BAUD     256000
#define PIR_PIN        34               // HC-SR501 OUT, solo-input senza pull-up: va bene
#define PERIODO_CAMPIONE_MS 200         // 5 Hz, come il logger e i CSV della tesi

// ---------------------------------------------------------------- Seriale verso il PC
#define SERIALE_BAUD   115200           // come il logger: acquire.py continua a funzionare
// Regola: ogni riga che NON e' CSV inizia con "# " (acquire.py la scarta)
