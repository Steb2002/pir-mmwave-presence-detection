# Registro sessioni di test

Compilare una riga a ogni sessione di acquisizione (vedi PIANO_TEST.md, regole di sessione).
La temperatura serve soprattutto per interpretare i risultati del PIR (degrada con caldo ~30°C+).

## Identità dell'hardware usato (da citare nella tesi per la riproducibilità)

| Componente | Dato | Valore | Rilevato il |
|---|---|---|---|
| HLK-LD2410B | Versione firmware | **2.44.25070917** | 2026-08-18 (Test 0.1, `requestFirmware()`) |
| HLK-LD2410B | Baud UART confermato | **256000** 8N1 | 2026-08-18 (auto-scan Test 0.1) |
| HLK-LD2410B | MAC Bluetooth | **5E:E4:93:22:B9:3F** | 2026-08-18 (`requestMAC()`) |
| HLK-LD2410B | Versione protocollo | 1 | 2026-08-18 |
| HLK-LD2410B | Risoluzione gate / range | 75 cm per gate, range massimo 675 cm (gate 0-8) | 2026-08-18 (cmd 0x0061) |
| HLK-LD2410B | Timeout presenza ("no-one duration") | **5 s** | 2026-08-18 (cmd 0x0061) |
| HLK-LD2410B | Soglie di fabbrica | vedi tabella sotto | 2026-08-18 (cmd 0x0061) |
| HLK-LD2420 | Versione firmware | *(da leggere, Test 0.5)* — baud 115200 ⇒ ≥ 1.5.3 | — |
| PIR HC-SR501 | Ritenuta / jumper | ~3.4 s (trimmer al minimo), **jumper su L** (non-ripetibile; creduto H fino al 22/08/2026 — tutta la fase 1 è in L), sensibilità a metà | 2026-07-19, corretto 2026-08-22 |
| ESP32 | Modello / porta | ESP32-WROOM-32 (dev board 30 pin) / COM3 | — |

> **Nota sul firmware 2.44**: è l'ultima versione rilasciata da Hi-Link ed è quella che
> introduce il **rilevamento automatico del rumore di fondo** (auto-calibrazione delle
> soglie movimento + stazionario). Vedi `HLK-LD2410x/Documentazione/LD2410B V2.44
> (24073110)- introduction of new features.pdf` ed esempio `MyLD2410 > auto_thresholds`.

### Soglie per-gate di fabbrica (lettura via UART, comando 0x0061 — 18/08/2026)

Confronto con il rumore di fondo misurato a stanza vuota nella stessa giornata
(29 s, `20260818_test01B_ld2410b_engineering.csv`). Regola del protocollo V1.07 §1.2.2:
il target è riconosciuto **solo se energia > soglia**.

| Gate | Distanza | Soglia mov. | Rumore mov. (max) | Margine | Soglia staz. | Rumore staz. (max) |
|---|---|---|---|---|---|---|
| 0 | 0-75 cm | 50 | 26 | 24 | **0** | 0 |
| 1 | 75-150 cm | 50 | 21 | 29 | **0** | 0 |
| 2 | 150-225 cm | 40 | 9 | 31 | 40 | 6 |
| 3 | 225-300 cm | 30 | 4 | 26 | 40 | 4 |
| 4 | 300-375 cm | 20 | 9 | 11 | 30 | 4 |
| 5 | 375-450 cm | 15 | 6 | 9 | 30 | 3 |
| 6 | 450-525 cm | 15 | 11 | **4** | 20 | 5 |
| 7 | 525-600 cm | 15 | 8 | 7 | 20 | 7 |
| 8 | 600-675 cm | 15 | 7 | 8 | 20 | 5 |

Osservazioni:
- il **gate 6 in movimento** è l'anello debole (margine 4). È anche il gate dove si è
  presentato il "bersaglio fantasma" a ~5.2 m dopo l'uscita del soggetto
- le soglie **stazionarie dei gate 0 e 1 valgono 0** e le rispettive energie sono sempre 0:
  con la regola "energia > soglia" il canale stazionario è quindi **strutturalmente
  disattivato sotto 1.5 m**. (Resta da spiegare perché il radar riporti comunque
  `stationary_distance` di 70-89 cm: da approfondire)
- ⚠️ questi valori **smentiscono** la lettura "sensibilità = 100" ottenuta dal LD2410 Tool:
  per i valori numerici fare fede alla lettura via UART, non al tool PC

## Sessioni

| Data | Ora | Temp. stanza (°C) | Soggetto | Alimentazione | Test svolti | Note |
|------|-----|-------------------|----------|---------------|-------------|------|
| es. 2026-07-10 | 09:30 | 26 | S1 | alim. muro 2A | 1.1 T01-T03 | finestre chiuse, no ventilatore |
| 2026-08-18 | | | | USB PC (COM3) | 0.1 | Primo contatto OK dopo la correzione del cablaggio. Firmware 2.44.25070917, baud 256000. A ~40 cm energia moving e still **saturate a 100** e moving/still attivi insieme → distanza troppo ravvicinata per misure quantitative |
| 2026-08-18 | | | S1 | USB PC (COM3) | pilota respiro | `20260818_respiro_40cm_prova.csv` — soggetto fermo a ~40 cm, 91 s, respiro spontaneo (**nessuna ground truth**). 7 gate moving indipendenti concordano su 0.264 Hz = **15.8 atti/min**, SNR fino a 12.8x su `menergy_gate2`. Canali stazionari saturi o discordanti (6.6-9.2 atti/min) → inutilizzabili a questa distanza. Prova di fattibilità, NON una misura: da rifare in fase 6 a ≥1.5 m con respiro a metronomo |
| 2026-08-18 | | | | USB PC (COM3) | 0.1 passo B + 0.2 | Logger validato. 673 campioni / 134 s → `20260818_test01B_ld2410b_engineering.csv`. 5.00 Hz esatti, engineering mode OK, mappa gate↔distanza 97.1% entro ±1 gate, zero falsi positivi in 29 s di stanza vuota. PIR non collegato (colonna a 0) |
| 2026-08-18 | | | S1 | USB PC (COM3) | pilota 1.1 + 1.3 | `pir_vs_radar_T01.csv` — 1699 camp / 339.6 s, PIR su D34. **PIR: 80.4% di falsi negativi** (rileva 254/1298 campioni di presenza reale); nel tratto immobile di **93.2 s continuativi a ~2.9 m il PIR è attivo nell'0.2% dei campioni, il radar nel 100%**. Zero falsi positivi per entrambi in 80.2 s di stanza vuota. PIR: 14 impulsi di durata costante 3.4-3.6 s. `out_level` == `radar_presence` in 1699/1699. `light_level` 21-29 (funziona) |
| 2026-08-18 | | **29** | — | alim. muro | **1.1 T01** | `stanza_vuota_T01.csv` — 1742 s utili (8711 camp) dopo `--salta-inizio 60`. **Zero falsi positivi radar e PIR** (`fp_*_eventi_h` = 0.0, `*_rate_%` = 0.0). ⚠️ 29 °C: temperatura alta, condizione **sfavorevole al PIR** in rilevamento ma favorevole sui falsi positivi |
| 2026-08-18 | | **27** | S1 | alim. muro | **1.3 T01-T05 (serie completa)** | `fermo_seduto_T0*.csv` — 5 trial × 302 s puliti (`--salta-inizio 30`), soggetto immobile a 2.30 m. **fn_PIR = 99.78 ± 0.49 %, fn_radar = 0.00 ± 0.00 %**. Distanza 229.78 ± 2.38 cm (tra trial), stabilità entro trial 1.48 ± 0.77 cm. `senergy` satura (99.96). Respiro dai gate moving: 18.2 / 18.9 / 18.8 / 20.0 / 20.2 atti/min (7-8 canali concordi per trial) |
| 2026-08-20 | | | S1 | alim. muro | **1.2 completo 1-5 m (25 trial)** | Cammino sul posto a 1/2/3/4/5 m, 5 trial × 62 s utili ciascuna. **Regressione: misurata = 1.0381 × reale − 1.32 cm, R² = 0.99965** → errore di **scala +3.81%**, offset nullo. Radar 100% di rilevamento a tutte le distanze. **PIR: 0.0% di rilevamento a 2, 3, 4 e 5 m** (20 trial, tutti 100% FN) con soggetto in movimento continuo; solo a 1 m rileva il 19.5%. Energia media 99 → 85 → 54 → 35 → 28. ⚠️ 6 m non acquisiti |
| 2026-08-20 | notte | **29** | — | alim. muro | **1.1 notturna** | `stanza_vuota_notte_T01.csv` — **118.204 campioni / 23640.6 s = 6.57 h** (attese 7 h: **interrotta da un aggiornamento automatico di Windows** che ha riavviato il PC. I dati sono integri fino all'interruzione: dt = 200 ms esatti su tutti i 118.203 intervalli, nessun buco né campione perso — l'acquisizione è semplicemente troncata, quindi resta pienamente valida). **Zero falsi positivi radar e PIR dopo i primi 60 s**: gli unici 96 campioni di presenza stanno fra t=0 e t=19 s e sono l'operatore che esce. Limite 95% sui FP portato da ≤6.20 a **≤0.43 eventi/h**. Rumore di fondo stabile su 6.5 h (gate0 media 17.4→17.8, gate1 13.3→13.1; max 34 contro soglia 50). `light_level` 0-1 di notte contro 21-29 di giorno → **il sensore di luce funziona e segue l'illuminazione** |
| 2026-08-22 | | | S1 | USB PC | **1.4 immobile T01-T05 (serie completa)** | `sotto_banco_immobile_T0*.csv` — sensore sotto il piano, soggetto rannicchiato a ~50 cm misurati, 5 trial x 302 s puliti. **fn_PIR = 99.90 ± 0.22 %, fn_radar = 0.00 ± 0.00 %**. Distanza 62.70 ± 4.21 cm (moving) e 62.90 ± 4.18 (stazionaria): i due canali concordano. Dispersione entro trial 13.3-14.4 cm, ~9x quella da seduto a 2.3 m (1.5 cm). `senergy` satura al 100% in tutti i trial; `senergy_gate0/1` = 0, presenza portata dai gate 2-3. **Respiro estraibile in 4 trial su 5: 21.0 ± 2.5 atti/min** dai soli canali moving (T04 senza gruppo moving >= 3 canali) |
| 2026-08-22 | | | S1 | USB PC | **1.4 movimenti T01-T05** | `sotto_banco_movimenti_T0*.csv` — come lo scenario immobile ma con micro-aggiustamenti. **fn_PIR = 64.14 ± 1.06 %** (la sua prestazione MIGLIORE dell'intera campagna, e sbaglia comunque due volte su tre), **fn_radar = 0.00 ± 0.00 %**. Distanza 58.2 ± 2.3 cm. `menergy` satura (99.86) → respiro non estraibile con movimento. **153 impulsi PIR misurati, TUTTI fra 3.6 e 3.8 s (dev.std 0.09 s), zero impulsi > 5 s**: prova definitiva che l'uscita e' un monostabile a durata fissa e non si allunga col movimento continuo |
| 2026-08-22 | | | S1 | USB PC | **caratterizzazione jumper PIR** | Quattro prove. Con jumper su **L** (posizione usata in tutta la fase 1): attraversamento del campo 7 impulsi, mano a 20-30 cm 3 impulsi, altra posizione 3 impulsi — tutti 3.40-3.60 s. Spostato su **H**: **un unico impulso >= 9.2 s**, ancora alto a fine acquisizione. **Il ritrigger funziona e la fase 1 e' stata acquisita in L.** Da rifare in H solo `movimento_1m` e `sotto_banco_movimenti`. NB: dopo il ciclo di alimentazione il PIR e' cieco ~60 s (primo impulso a t=33 s) |
| 2026-08-22 | | | S1 | USB PC | **1.2 movimento_1m rifatto in H** | `movimento_1m_H_T0*.csv` — stesso movimento e stessa posizione della serie in L. **fn_PIR: 80.46 ± 6.22 % (L) → 14.80 ± 11.52 % (H)**. Il ritrigger cambia radicalmente il comportamento con movimento continuo. Radar invariato a 0.00% in entrambe. Comparabilita' verificata col radar: `menergy` 98.96 vs 99.30, `mdist_dev` 10.38 vs 10.40; distanza media 99.5 → 103.6 cm per il rimontaggio del setup |
| 2026-08-22 | | | S1 | USB PC | **1.2 movimento_2m in H (controllo)** | `movimento_2m_H_T0*.csv` — **fn_PIR = 100.00 ± 0.00 %**, identico alla serie in L: a 2 m il jumper non cambia nulla perche' non ci sono trigger da prolungare. Deduzione per 3-5 m confermata. ⚠️ errore di distanza +18.68 cm contro +11.22 della serie originale: il setup rimontato ha spostato il sensore di ~7 cm, non mescolare le due serie nella regressione |
| 2026-08-22 | | | S1 | USB PC | 🎯 **fermo_1m_H — esperimento centrale** | `fermo_1m_H_T0*.csv` — in piedi immobile a 1 m, jumper H, stesso setup di `movimento_1m_H`. **fn_PIR = 98.48 ± 1.03 %** contro 14.80 % con cammino sul posto: **a parita' di distanza, configurazione e postura, cambia solo il movimento**. Impulsi: 2 in 1000 s da fermo, contro 6 impulsi da 14.1 s medi (max 29.8 s) in movimento. Radar 0.00% di FN in entrambe. Sul radar: `menergy` 99.3 → 68.6 e dispersione distanza 10.4 → 21.3 cm col soggetto fermo |
| 2026-08-22 | | | S1 | USB PC | 🎯 **sotto_banco_movimenti_H** | `sotto_banco_movimenti_H_T0*.csv` — **fn_PIR = 3.48 ± 3.60 %** (era 64.14 % in L). Coppia UPRISE completa a ~60 cm: con micro-movimenti il PIR rileva il **96.52%**, immobile lo **0.10%**. Radar 0.00% di FN in entrambe. Distanza 65.8 ± 0.7 cm |
| 2026-08-22 | | | S1 | USB PC | **sotto_banco_immobile_H** | `sotto_banco_immobile_H_T0*.csv` — **fn_PIR = 98.68 ± 0.86 %** (in L era 99.90 %). Chiude la coppia UPRISE con entrambe le condizioni in modalita' H: movimenti 96.52 % di rilevamento, immobile 1.32 %. Radar 0.00 % di FN in entrambe. Distanza 68.6 ± 1.1 cm |
|      |     |                   |          |               |             |      |
