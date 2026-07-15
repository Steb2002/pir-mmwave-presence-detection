# Piano di test della tesi — in ordine di esecuzione

Ogni test indica: obiettivo della tesi a cui serve, setup, procedura, comando pronto
e script di analisi. I comandi usano `acquire.py` del repo del professore
(cartella `HLK-LD2410x/`) e gli script in `analisi/`.

**Convenzione nomi file**: `data/<scenario>_T<numero>.csv` — lo scenario finisce
dentro il CSV e gli script di analisi aggregano automaticamente per scenario.

**Regola generale**: ogni scenario va ripetuto **almeno 5 volte** (T01…T05) per avere
media e deviazione standard — è questo che rende il confronto "numerico" (obiettivo 3).

**Regole di sessione (valgono per TUTTI i test)**:
- 🌡️ **Annotare la temperatura della stanza** a inizio sessione in `data/REGISTRO_SESSIONI.md`
  (data, ora, temperatura, scenario svolti): il PIR degrada quando l'ambiente si avvicina
  ai ~34°C del corpo — testando d'estate è una variabile che va tracciata, e un confronto
  mattina fresca vs pomeriggio caldo sul Test 1.3 è un risultato in più per la tesi
- 🔌 **Alimentazione da alimentatore USB da muro ≥1 A**, non dalla porta del portatile:
  ESP32 con WiFi + LD2410B hanno picchi >400 mA e una porta USB debole causa brownout
  (riavvii casuali che sembrano bug del firmware). Per il solo logging seriale la porta
  del PC va bene, per web UI e sessioni lunghe no
- 👤 I test si svolgono con **1-2 soggetti** (dichiararlo nella tesi come perimetro
  sperimentale); dove possibile ripetere i test chiave (1.3, 1.4) con entrambi

---

## FASE 0 — Preparazione (una tantum, prima di tutti i test)

### Test 0.1 — Verifica cablaggio e primo contatto con il LD2410B
- **Serve per**: sbloccare tutto il resto
- Collegare il LD2410B come da CLAUDE.md (blu→VIN, verde→GND, giallo→D16, nero→D17)
- Caricare `firmware/ld2410b_logger/ld2410b_logger.ino` da Arduino IDE (board: ESP32 Dev Module, COM3)
- Aprire il Serial Monitor a **115200 baud**: devono apparire righe CSV
- ⚠️ Se appare `ERROR: radar not detected`: controllare che giallo/nero non siano invertiti
  (il firmware del professore usa i pin al contrario — il nostro sketch segue il NOSTRO cablaggio)
- **Esito atteso**: righe CSV con `radar_presence=1` quando ti muovi davanti al sensore

### Test 0.2 — Verifica engineering mode
- **Serve per**: obiettivi 2, 6 e test respiro
- Con lo sketch caricato (`ENGINEERING_MODE 1`), controllare che le righe CSV abbiano
  le 18 colonne extra `menergy_gate0..8` e `senergy_gate0..8` con valori 0-100 variabili
- **Esito atteso**: muovendoti a ~1.5 m il gate 2 (risoluzione 0.75 m) deve alzarsi

### Test 0.3 — Configurazione del PIR HC-SR501
- **Serve per**: obiettivi 1, 2, 3, 4
- ✔ Modello già identificato dalle foto: **HC-SR501** (BISS0001 + HT7133, uscita 3.3V
  sicura per ESP32) — specifiche e fonti in `analisi/ANALISI_PIR.md` §6
- Configurare: jumper in modalità **H (repeat trigger)**; trimmer tempo di ritenuta
  al **MINIMO** (~3 s, antiorario a fondo corsa — fondamentale per le latenze reali);
  trimmer sensibilità a **metà corsa** → fotografare la posizione dei trimmer
  (va tenuta identica per tutta la campagna)
- ⚠️ Prima di collegare: verificare la serigrafia VCC/OUT/GND sul lato saldature
  (nei cloni l'ordine dei 3 pin può variare)
- Collegare: VCC→VIN(5V), GND→GND, OUT→D23
- **Esito atteso**: colonna `pir_presence` a 1 quando ti muovi
- ⚠️ ~60 s di stabilizzazione all'accensione: ignorare il primo minuto. Ricordare
  anche il **block time di 2.5 s** dopo ogni rilascio (cecità strutturale, cita nel
  Test 2.1)

### Test 0.4 — Setup ambiente Python di acquisizione
```powershell
cd HLK-LD2410x
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install pyserial numpy
mkdir data
```
- Prova rapida (30 s, tu presente in movimento):
```powershell
python acquire.py --port COM3 --duration 30 --output data/prova_T01.csv --scenario prova --trial T01 --ground_truth_presence 1 --ground_truth_state moving
```
- **Esito atteso**: file CSV creato, righe visibili a schermo

### Test 0.5 — Verifica firmware LD2420 (con CH340E, senza ESP32)
- **Serve per**: decidere pinout e baud del LD2420 (Fase 4)
- Collegare il LD2420 al CH340E → PC, aprire il tool HiLink (Google Drive, cartella
  `HLK-LD2420_TOOL - English`), leggere la **versione firmware**
- Annotare qui il risultato: firmware = ______ → pinout OT1/OT2 = ______, baud = ______
- **Esito atteso**: versione letta; se ≥1.5.3 il TX seriale è OT1 (pin 3) a 115200 baud

### Test 0.6 — Configurazione via app Bluetooth (facoltativo ma consigliato)
- App HLKRadarTool (password modulo: `HiLink`), verificare firmware LD2410B,
  lasciare i parametri di default (documentarli con uno screenshot per la tesi)

---

## FASE 1 — Caratterizzazione dei sensori (obiettivo 2)

Setup fisso per tutta la fase: LD2410B e PIR affiancati sul bordo di un tavolo,
altezza ~1 m, puntati verso l'area di test, nessun oggetto in movimento nella stanza
(no ventilatori, no tende, porta chiusa).

### Test 1.1 — Baseline stanza vuota (falsi positivi)
- **Metrica**: falsi positivi/ora di entrambi i sensori
- Avviare l'acquisizione e **uscire dalla stanza**; durata: 30 min (meglio 60)
```powershell
python acquire.py --port COM3 --duration 1800 --output data/stanza_vuota_T01.csv --scenario stanza_vuota --trial T01 --ground_truth_presence 0 --ground_truth_state absent
```
- Ripetere 3 volte (anche in momenti diversi della giornata)
- **Analisi**: `python ..\analisi\analizza_test.py data\stanza_vuota_*.csv`
  → guardare `fp_radar_eventi_h` e `fp_pir_eventi_h`

### Test 1.2 — Persona in movimento a distanze note
- **Metrica**: accuratezza della distanza (solo radar), tasso di rilevamento
- Segnare sul pavimento con nastro: 1, 2, 3, 4, 5, 6 m dal sensore
- Per ogni distanza: camminare sul posto per 60 s
```powershell
python acquire.py --port COM3 --duration 60 --output data/movimento_1m_T01.csv --scenario movimento_1m --trial T01 --ground_truth_presence 1 --ground_truth_state moving
```
  (ripetere per 2m, 3m, 4m, 5m, 6m — 5 trial ciascuna)
- **Analisi**: confrontare `sdist_media_cm`/`mdist` con la distanza reale del nastro
  → grafico Excel: distanza reale vs misurata (retta ideale a 45°)

### Test 1.3 — Persona seduta immobile (il test chiave della tesi)
- **Metrica**: falsi negativi — qui il PIR deve fallire e il mmWave no
- Sedersi su una sedia a 2 m, **stare fermi** (leggere un libro senza gesti ampi), 5 min
```powershell
python acquire.py --port COM3 --duration 300 --output data/fermo_seduto_T01.csv --scenario fermo_seduto --trial T01 --ground_truth_presence 1 --ground_truth_state static
```
- 5 trial; poi ripetere anche a 4 m (`fermo_seduto_4m`)
- **Analisi**: `fn_radar_%` vs `fn_pir_%` — risultato atteso: PIR ~100% FN dopo il
  timeout di ritenuta, radar < 5%. **Questo è il numero centrale del capitolo di confronto**

### Test 1.4 — Persona sotto il banco (scenario UPRISE reale)
- **Metrica**: come 1.3, ma nella postura reale del progetto
- Sensore fissato sotto il piano del banco/tavolo puntato verso il basso o di lato;
  persona rannicchiata sotto, immobile, 5 min × 5 trial
```powershell
python acquire.py --port COM3 --duration 300 --output data/sotto_banco_T01.csv --scenario sotto_banco --trial T01 --ground_truth_presence 1 --ground_truth_state static
```
- **Analisi**: come 1.3. Questo test dà il titolo alla tesi: il sensore vede la persona
  rifugiata sotto l'arredo?

---

## FASE 2 — Confronto dinamico PIR vs mmWave (obiettivo 3)

### Test 2.1 — Latenza di rilevamento all'ingresso
- **Metrica**: secondi tra ingresso nella stanza e prima rilevazione, per sensore
- Procedura: avvia l'acquisizione stando FUORI dal campo visivo; entra
  **esattamente a 10 s** dall'avvio (usa un timer sul telefono); resta in movimento 20 s
```powershell
python acquire.py --port COM3 --duration 40 --output data/ingresso_T01.csv --scenario ingresso --trial T01 --ground_truth_presence 1 --ground_truth_state moving
```
- **10 trial** (la latenza varia molto, servono più ripetizioni)
- **Analisi**: `python ..\analisi\analizza_test.py data\ingresso_*.csv --event-time 10`
  → `latenza_radar_s` vs `latenza_pir_s` (media ± dev.std)

### Test 2.2 — Latenza di rilascio all'uscita
- **Metrica**: dopo quanti secondi il sensore dichiara "stanza vuota"
- Procedura: muoviti davanti al sensore per 10 s, poi esci di scatto a t=10 s e resta fuori
```powershell
python acquire.py --port COM3 --duration 120 --output data/uscita_T01.csv --scenario uscita --trial T01 --ground_truth_presence 0 --ground_truth_state absent
```
- 5 trial. Nota: il ground truth qui è "assente" solo dopo t=10 s — l'analisi della
  latenza di rilascio va fatta guardando l'ultimo campione con presence=1 (in Excel
  o annotando i tempi); il timeout configurato del radar è 5 s, del PIR il potenziometro
- **Analisi**: tempo di rilascio radar (atteso ~5 s + inerzia) vs PIR (ritenuta impostata)

### Test 2.3 — Micro-movimenti (zona grigia tra i due sensori)
- **Metrica**: tasso di rilevamento con soli micro-movimenti (digitare al telefono,
  girare pagine) a 2 m, 3 min × 5 trial
```powershell
python acquire.py --port COM3 --duration 180 --output data/micromovimenti_T01.csv --scenario micromovimenti --trial T01 --ground_truth_presence 1 --ground_truth_state micro_movement
```
- **Analisi**: `radar_rate_%` vs `pir_rate_%` — atteso: radar ~100%, PIR intermittente

### Test 2.4 — Selettività spaziale (scenario "banchi adiacenti" UPRISE)
- **Perché**: in un'aula reale i banchi sono affiancati e il radar vede attraverso il
  legno → il sensore del banco A rischia di rilevare la persona sotto il banco B,
  falsando la mappa dei sopravvissuti. La mitigazione è limitare la portata al volume
  del proprio banco riducendo il gate massimo
- **Setup**: configurare via app Bluetooth (o comando UART) il gate massimo a 2-3
  (~1.5-2 m); persona A ferma a 1 m, persona B ferma a 2.5-3 m (fuori dal gate massimo)
- **Metrica**: il sensore deve rilevare SOLO la persona A; poi persona A esce → il
  sensore deve dichiarare vuoto nonostante B sia ancora lì
- 3 trial × 3 min con nomi `selettivita_A_presente` (gt=1) e `selettivita_solo_B` (gt=0)
```powershell
python acquire.py --port COM3 --duration 180 --output data/selettivita_solo_B_T01.csv --scenario selettivita_solo_B --trial T01 --ground_truth_presence 0 --ground_truth_state absent
```
- **Analisi**: `radar_rate_%` in `selettivita_solo_B` è il tasso di "falso vicino" —
  numero chiave per l'applicabilità UPRISE multi-banco. Ricordarsi di **ripristinare
  il gate massimo di default** dopo il test (annotare la configurazione usata!)

### Test 2.5 — Due persone (limite dichiarato del sensore)
- **Metrica**: qualitativa — il LD2410B riporta un solo target
- Due persone: una ferma a 2 m, una che cammina a 4 m, 2 min × 3 trial
```powershell
python acquire.py --port COM3 --duration 120 --output data/due_persone_T01.csv --scenario due_persone --trial T01 --ground_truth_presence 1 --ground_truth_state moving
```
- **Analisi**: osservare quale target "vince" nelle distanze riportate → paragrafo
  della tesi sui limiti (no conteggio persone senza array di antenne)

---

## FASE 3 — Penetrazione ostacoli (obiettivo 3)

Setup: persona ferma seduta a 2 m dal sensore; pannello di materiale interposto
a ~20 cm davanti al sensore. Prima una baseline senza ostacolo, stesso giorno.

### Test 3.1 — Baseline senza ostacolo
```powershell
python acquire.py --port COM3 --duration 180 --output data/ostacolo_nessuno_T01.csv --scenario ostacolo_nessuno --trial T01 --ground_truth_presence 1 --ground_truth_state static
```

### Test 3.2 — Cartongesso → 3.3 legno → 3.4 vetro → 3.5 plastica
- 3 min × 3 trial per materiale, stesso scenario con nomi `ostacolo_cartongesso`,
  `ostacolo_legno`, `ostacolo_vetro`, `ostacolo_plastica`
- Fare lo stesso test anche con il PIR attivo: per il PIR ogni ostacolo è bloccante
  (risultato atteso: `pir_rate_% = 0` con qualunque materiale — altro numero chiave)
- **Analisi**: `python ..\analisi\analizza_test.py data\ostacolo_*.csv`
  → confrontare `senergy_media` e `radar_rate_%` per materiale rispetto alla baseline
  → grafico Excel: degradazione % dell'energia per materiale

---

## FASE 4 — LD2420 (obiettivo di contorno: altri sensori)

Prerequisito: Test 0.5 completato (firmware noto).

⚠️ **Mai tenere accesi LD2410B e LD2420 puntati sulla stessa scena**: lavorano
entrambi a 24 GHz e possono interferire tra loro falsando i dati. Un radar alla
volta — il confronto tra i due si fa ripetendo gli stessi scenari, non in simultanea
(il PIR invece è passivo e può restare sempre collegato).

### Test 4.1 — Collegamento e lettura dati
- Cablare secondo la versione firmware (vedi CLAUDE.md); alimentazione **3.3V!**
- Sketch dedicato da scrivere in base al firmware trovato (Serial2 raw)

### Test 4.2 — Ripetere i test chiave in versione ridotta
- `stanza_vuota` (30 min ×1), `fermo_seduto` (5 min ×3), `movimento_[2,4,6,8,10]m` (×3)
- **Analisi**: tabella comparativa LD2410B vs LD2420: portata reale, FP/FN, granularità dati

---

## FASE 5 — Respiro (test avanzato, obiettivi 2-3)

Prerequisito: engineering mode funzionante (Test 0.2), campionamento a 5 Hz.

### Test 5.1 — Respiro a 1 m
- Persona seduta immobile a 1 m, respiro normale, **120 s**; contare manualmente
  gli atti respiratori durante la prova (o respirare a ritmo con un metronomo: 15/min)
```powershell
python acquire.py --port COM3 --duration 120 --output data/respiro_1m_T01.csv --scenario respiro_1m --trial T01 --ground_truth_presence 1 --ground_truth_state static
```
- **Analisi**: `python ..\analisi\analizza_respiro.py data\respiro_1m_T01.csv --colonna senergy_gate1`
  (gate = distanza/0.75 arrotondata: 1 m → gate 1; a 2 m usare gate 3 (~2.25m) o 2)
- **Esito atteso**: picco FFT vicino agli atti/min contati; annotare il confronto
- 5 trial; poi ripetere a 2 m (`respiro_2m`)

### Test 5.2 — Controllo negativo
- Stessa acquisizione con stanza vuota (`respiro_vuoto`, 120 s × 3)
- **Analisi**: la FFT NON deve mostrare picchi con rapporto picco/fondo > 3
  → dimostra che il picco del test 5.1 è respiro vero, non rumore

---

## FASE 6 — Indice di vitalità (obiettivo 6)

I dati servono a tarare l'algoritmo: si riusano le acquisizioni delle fasi precedenti
più tre scenari dedicati (3 min × 5 trial ciascuno):

### Test 6.1 — Scala di movimento
- `vitalita_0`: stanza vuota → indice atteso ~0
- `vitalita_respiro`: persona immobile che respira → indice atteso basso (10-30)
- `vitalita_micro`: micro-movimenti (mani, testa) → indice atteso medio (30-60)
- `vitalita_attivo`: movimento continuo sul posto → indice atteso alto (60-100)
- **Analisi**: da questi 4 gruppi di CSV si costruisce l'algoritmo (media mobile
  esponenziale dell'energia di movimento del gate attivo, normalizzata 0-100) e si
  verificano le soglie di classificazione "nessun segno vitale / vitalità bassa /
  moderata / attiva". L'algoritmo si sviluppa prima in Python sui CSV, poi si porta
  sull'ESP32 per la web UI

---

## FASE 7 — Web UI (obiettivo 5) — sviluppo, non test

Da sviluppare in parallelo alle fasi 1-6 (indipendente):
1. ESP32 in WiFi (station mode) + web server asincrono + WebSocket
2. Pagina con: stato presenza live, distanza, grafico energia (Chart.js), indice di vitalità
3. Buffer dati + bottone "Export CSV" lato browser
4. Test funzionale finale: 10 min di uso con confronto CSV web vs CSV seriale

---

## Riepilogo tempi stimati

| Fase | Test | Tempo effettivo di misura |
|---|---|---|
| 0 | Preparazione | mezza giornata |
| 1 | Caratterizzazione | ~4 h di acquisizioni |
| 2 | Confronto dinamico | ~2 h |
| 3 | Ostacoli | ~1.5 h |
| 4 | LD2420 | mezza giornata (incluso sketch) |
| 5 | Respiro | ~1 h |
| 6 | Vitalità | ~1.5 h |
| 7 | Web UI | 2-4 giorni di sviluppo |

Ordine consigliato: 0 → 1 → 2 → 3 → 5 → 6 → 4 → 7 (la fase 4 può slittare senza
bloccare nulla; la 7 si sviluppa nei tempi morti tra le acquisizioni).
