# Traccia di quello che dico al professore (per obiettivo)

Materiali da avere aperti: `RIEPILOGO_INCONTRO.pdf` (10 pagine, tutte le figure con
didascalia), `analisi/dati_tesi.xlsx` (una riga per trial), il repo GitHub.

---

## Obiettivi 1 + 2 — Studio dei sensori e dati prodotti (li tratto insieme)

**Perché insieme**: lo studio di "come funzionano" e quello di "che dati danno" vengono
dalla stessa fonte — la documentazione ufficiale del produttore — e si spiegano meglio
di seguito. Prima il principio fisico, poi cosa esce dal filo.

### Da dove vengono le informazioni
Manuali e protocolli ufficiali Hi-Link scaricati e tenuti in locale nel repo:
- LD2410B: manuale V1.04 + protocollo seriale V1.07 + nota firmware V2.44
- LD2420: manuale V1.2 + Protocol Document
- PIR HC-SR501: datasheet + datasheet del chip BISS0001

Regola che mi sono dato: **ogni dato tecnico ha la sua fonte**, con gerarchia
datasheet > manuale ufficiale > guide riconosciute (ESPHome/Adafruit) > blog. Dove i
documenti ufficiali si contraddicono lo dichiaro invece di scegliere (es. il LD2420
dice ±60° in §1.1 e ±45° in §5.2; il LD2410B dà gate "1-8" nel manuale e "2-8" nel
protocollo).

### PIR HC-SR501 — che dato produce
Sensore **piroelettrico differenziale** + lente di Fresnel: risponde al *transito* del
flusso IR fra le zone della lente, non al movimento in sé. Uscita: **1 bit**, e per
giunta un **monostabile a durata fissa** — non misura presenza né durata, **conta
eventi**. Due regolazioni analogiche (sensibilità, ritenuta) e un jumper H/L
(ritrigger sì/no). Dato misurato a supporto: 183 impulsi su tre sessioni, **tutti fra
3,4 e 3,8 s**, nessuno oltre 5, nemmeno con movimento continuo.

### LD2410B — che dato produce (frame UART, engineering mode)
Frame base (header `F4 F3 F2 F1`): presenza, stato target moving/still, **distanza
moving**, **distanza stazionaria**, energia moving, energia stazionaria.
Attivando l'**engineering mode** (comando `0x62`) il frame si allunga e aggiunge:

| Campo aggiunto | Byte | Nel CSV? |
|---|---|---|
| Maximum moving gate N | 1 | no |
| Maximum static gate N | 1 | no |
| Energia moving per gate 0…8 | 9 | `menergy_gate0..8` |
| Energia stationary per gate 0…8 | 9 | `senergy_gate0..8` |
| Photosensitive (0–255) | 1 | `light_level` |
| Stato del pin OUT (0 = nessuno, 1 = occupato) | 1 | `out_level` |

Tre note che mi porto dietro nei capitoli:
- l'energia è un **intero 0-100 normalizzato**: sul bersaglio vicino **satura** a
  fondoscala e un segnale clippato non porta informazione. Non lo risolvono né le
  soglie né l'auto-calibrazione: la soglia agisce sulla *decisione*, non sulla scala
- `senergy_gate0/1` sono **sempre 0**, coerentemente con la Tabella 7 del protocollo
  V1.07 dove la sensibilità *Rest* dei gate 0-1 è marcata "cannot be set"
- il `light_level` funziona davvero (21-29 di giorno, 0-1 di notte su 6,5 h) e
  `out_level` coincide con la presenza in **1699/1699** campioni → il cavo blu è
  ridondante, chi vuole solo il bit può leggere il pin senza UART

### LD2420 — che dato produce
Con l'interfaccia **documentata** (ASCII di fabbrica, 115200 baud): righe `ON` / `OFF`
/ `Range NN`. Cioè **presenza + una distanza, e nulla più** — niente energia per-gate,
niente separazione moving/still, e per esplicita ammissione del manuale (§8) **niente
distanza sui bersagli fermi**.

Esiste anche una **modalità binaria "energy"** (comando `0x0012` valore `0x0004`) con
frame da 45 byte: presenza + distanza + **16 energie per-gate a 16 bit, a 10 Hz**.
⚠️ Da dichiarare onestamente: è ricostruita dal componente **ESPHome**, non è
documentata da Hi-Link. Sulla carta sarebbe **migliore** del LD2410B per il respiro —
16 bit non saturano e 10 Hz contro i nostri 5 — ma non è citabile come specifica
ufficiale e la devo validare io. **Non ancora testata a fondo**: è il prossimo blocco
di lavoro (`PIANO_TEST_LD2420.md`).

### Il logger
È **il firmware del repo del professore**, a cui ho aggiunto:
1. l'**engineering mode**, quindi le 18 colonne di energia per-gate + luce + OUT
2. la cadenza portata da **1 Hz a 5 Hz costanti** (jitter zero misurato: 200 ms su
   672 intervalli su 672)

Il punto 2 non è un dettaglio: serve perché sull'energia per-gate faccio la **FFT**, e
la FFT vuole campionamento **uniforme** e sopra Nyquist. La banda respiratoria è
0,1-0,5 Hz: **a 1 Hz Nyquist cade esattamente a 0,5 Hz**, cioè sul bordo della banda da
misurare. A 5 Hz sto abbondantemente al sicuro. Ed è la stessa serie temporale che
alimenta l'**indice di vitalità** dell'obiettivo 6.

### Gli script (a cosa servono, in una riga ciascuno)
| Script | Cosa legge | Cosa fa e perché |
|---|---|---|
| `acquire.py` (adattato dal prof) | seriale ESP32 | salva il CSV e ci aggiunge i metadati del trial; ho aggiunto la ricostruzione dell'intestazione (altrimenti usciva un file vuoto senza avvisi) e `--beep-at` per marcare l'istante dell'evento nelle misure di latenza |
| `verifica_engineering.py` | un CSV appena acquisito | controllo di qualità **prima** di analizzare: cadenza reale, colonne per-gate presenti, % di saturazione, coerenza gate↔distanza, rumore di fondo, transizioni |
| `analizza_test.py` | i CSV di un gruppo di trial | è il motore delle metriche: accuratezza, falsi positivi/negativi, latenza di rilevamento e di rilascio, statistiche distanza/energia, aggregazione per scenario con media ± dev.std |
| `analizza_respiro.py` | la serie di energia per-gate | FFT, picco in banda 0,1-0,5 Hz, stima in atti/min; la modalità `--scan` prova tutti i 20 canali e scarta i saturi e i piatti (serve perché il canale di default era saturo mentre il respiro si leggeva benissimo su `menergy_gate2`) |
| `vitalita_proto.py` | gli stessi CSV | prototipo dell'indice di vitalità (obiettivo 6): calcola `vitality(t)`, classifica in 4 classi, produce le distribuzioni per la taratura |
| `grafici_tesi.py` | tutti i CSV | genera le 13 figure; **importa le funzioni di `analizza_test.py`** invece di ricalcolare, così i numeri dei grafici coincidono per costruzione con quelli del capitolo |
| `esporta_excel.py` | tutti i CSV | `dati_tesi.xlsx`, 11 fogli, una riga per trial + grafici Excel nativi (è il pezzo "→ Excel" dell'obiettivo 5) |
| `rigenera_tutto.py` | — | un comando solo: rifà figure, Excel, pagina HTML e PDF in ~13 s |

---

## Obiettivo 3 — Comparazione con testing numerico

Qui mostro le figure, nell'ordine del PDF. Una riga per ciascuna.

1. **fig01 — Dose-risposta PIR vs radar.** A 1 m, jumper H, cambia **solo** la quantità
   di movimento: PIR 1,5 % (immobile) → 51,6 % (micro) → 85,2 % (cammino), radar 100 %
   sempre. *È l'esperimento centrale: una sola variabile.*
2. **fig03 — Lo stesso confronto nello scenario DIPME**, sotto il banco a 60 cm:
   96,5 % con micro-movimenti contro **1,3 % da immobile**; radar 100 % in entrambe.
3. **fig02 — Timeline di un singolo trial da 5 minuti**: il radar tiene la presenza
   senza un buco, il PIR non emette un solo impulso in tutta l'acquisizione.
4. **fig07 — Struttura degli impulsi PIR**: 181 impulsi in modalità L, tutti fra 3,4 e
   3,8 s. Il "tasso di rilevamento" del PIR è il prodotto fra numero di eventi e
   ritenuta, non una misura di presenza.
5. **fig04 — Accuratezza della distanza**: regressione su 1-5 m, R² = 0,99965, errore
   di **scala** del +3,81 % con offset nullo → correggibile con un solo coefficiente.
6. **fig05 — Energia e portata**: a sinistra il decadimento dell'energia con la
   distanza; a destra la portata utile del PIR, che fra 1 e 2 m passa da 85 % a 0 %.
7. **fig06 — Latenze**: il radar rileva per primo in **10 trial su 10** (differenza
   appaiata −0,60 ± 0,35 s); al rilascio è invece **5,4 s più lento** del PIR.
8. **fig08 — Due persone**: il limite va formulato con precisione — non "un solo
   bersaglio", ma **"un bersaglio per canale"**; in fila chi sta dietro è invisibile,
   ma la presenza resta al 100 %: si perde il conteggio, mai la presenza.
9. **fig09 — Selettività spaziale**: con gate massimo 2 la portata si taglia a 150 cm,
   a 3 m zero rilevamenti e il vicino a 90° non viene rilevato da fermo.
10. **fig10 — Dati per-gate in engineering mode**: mappa gate↔distanza verificata al
    98,3 %, e si vedono i gate stazionari 0-1 sempre nulli.
11. **fig11 — Saturazione**: il limite del dato, da dichiarare — sul bersaglio vicino
    il canale stazionario è a fondoscala nel 100 % dei campioni.
12. **fig12 — Respiro**: micro-movimento respiratorio su soggetto immobile a 2,3 m
    estratto per FFT; picco in piena banda, valore fisiologicamente plausibile.
13. **fig13 — Consumi** (vedi obiettivo 4).

**La tesi in tre frasi, come emerge dai dati**: (1) il PIR configurato bene ed entro
~1 m è un ottimo rilevatore di *movimento*; (2) è praticamente cieco alla persona
*immobile*, a qualunque distanza e in qualunque configurazione; (3) il radar rileva
entrambe le condizioni al 100 % in tutti i test svolti. Non "il PIR è scarso", ma **"il
PIR fa bene un lavoro che non è questo"** — e in DIPME la persona intrappolata può
essere incosciente o esausta, quindi immobile.

**Cosa manca ancora nella fase 3**: penetrazione degli ostacoli (cartongesso, legno,
vetro, plastica), respiro con ground truth a metronomo, misura angolare vera, e tutta
la campagna sul LD2420.

---

## Obiettivo 4 — Consumo energetico

Come concordato, **a titolo informativo e da datasheet** (non ho strumentazione di
misura; ogni dato ha la sua fonte citata riga per riga in `analisi/ANALISI_CONSUMI.md`).

| | corrente media | fonte |
|---|---|---|
| PIR HC-SR501 | **< 0,05 mA** | datasheet |
| LD2420 | **50 mA** | manuale V1.2 Tab. 2-1 |
| LD2410B | **80 mA** | manuale V1.03 |

Mostro **fig13**: i tre ordini di grandezza fra PIR e radar, e le autonomie stimate su
una 18650 da 3000 mAh (nodo radar ~13-20 h, nodo dormiente con PIR watchdog anni).
La conclusione utile al progetto è **architetturale**: il PIR costa quasi nulla e può
fare da **sveglia**, risvegliando l'ESP32 dal deep-sleep via interrupt; il radar è da
alimentazione fissa e va acceso in emergenza. Le 13-20 ore coprono la finestra critica
dei soccorsi — che è esattamente il modello "tempo di pace / tempo di guerra" delle
slide del progetto.

---

## Obiettivo 5 — Web UI: due strade, gli chiedo di decidere

**Opzione A — sito ospitato sull'ESP32** (`ESPAsyncWebServer` + WebSocket + LittleFS)
- ✅ funziona **completamente offline**, senza rete né server: l'ESP32 fa da access
  point e ci si collega col telefono. È lo scenario DIPME (terremoto, blackout,
  infrastruttura giù)
- ✅ zero dipendenze da mantenere, tutto in un firmware; dimostrabile in aula
  staccando il WiFi
- ❌ risorse limitate: niente storico lungo, la memoria è quella che è
- ❌ un browser per volta, e i dati vivono finché la pagina è aperta

**Opzione B — server esterno** (ESP32 → MQTT/Mosquitto → FastAPI + SQLite → browser)
- ✅ **storico persistente** e statistiche vere su database; più dispositivi insieme
- ✅ è l'architettura realistica del progetto vero (più banchi → un gateway)
- ❌ serve infrastruttura accesa: proprio quello che in emergenza non c'è
- ❌ più pezzi da installare e documentare per una tesi triennale

Il frontend è **condiviso all'~85 %**, quindi cambiare idea costa 2-3 giorni, non
settimane. **Il mio default è A**, perché la coerenza con lo scenario di emergenza mi
sembra il criterio giusto: un sito che ha bisogno della rete non serve durante un
terremoto. Ma se per il progetto conta di più la piattaforma, passo a B.

In entrambi i casi **il CSV esportato dal browser usa le stesse colonne di
`acquire.py`** → un solo formato dati in tutta la tesi, e il pezzo "→ Excel" è già
dimostrato con `dati_tesi.xlsx`.

*Stato: progettato in dettaglio (3 documenti), non ancora implementato.*

---

## Obiettivo 6 — Indice di vitalità

Sì, dico che ci sto lavorando, ma **con i risultati in mano**, non come promessa:

- specifica scritta (`ANALISI_VITALITA.md`) e **prototipo Python funzionante**
- **la v1 non era applicabile** e l'ho scoperto sui dati: costruiva la micro-vitalità
  sull'energia *stazionaria*, che è satura a 100 con dev.std **0,0** in ogni scenario
  occupato → quel termine sarebbe identicamente nullo. La v2 usa i canali **moving**
- scoperta che regge tutto: **il fondo va sottratto**, altrimenti stanza vuota 19,1 e
  persona immobile 21,2 (indistinguibili). Sottraendo il rumore per-gate: **2,4 contro
  11,4**. Con i parametri di default la scala a 1 m diventa **2,4 / 30,9 / 77,3 / 99,7**
  sui quattro livelli di movimento — cioè l'indice è **monotono**
- **i dati per tararlo esistono già**: la serie dose-risposta del Test 2.3 copre i
  quattro scenari a geometria costante, più `sotto_banco_*` come insieme di validazione

**Cosa resta e dove voglio il suo parere**: `sotto_banco_immobile` dà **65,6**, vicino
ai micro-movimenti a 1 m (77,3). Una sola terna di soglie non copre entrambe le
geometrie → o si tara per geometria (un sensore per banco, quindi sarebbe accettabile),
o serve una normalizzazione. **È la domanda che gli faccio.**

---

## Cosa mi stavo dimenticando (da dire comunque)

1. **Far validare `PIANO_TEST.md`** — è il motivo principale dell'incontro: sono ~10 h
   di acquisizioni, se il protocollo non va bene si rifà tutto
2. **Il capitolo 4 è già scritto** (~1450 righe, 13 tabelle, in Overleaf con la classe
   ufficiale UNICAM): posso mostrarglielo
3. **I dati sono al sicuro**: repo GitHub, 116 CSV su 116 verificati nel remoto
4. **Domande aperte da porre**: la **scadenza** (senza non posso fare il
   cronoprogramma); DIPME o SAFE, come lo chiamo in tesi; il montaggio del sensore
   sotto la lamiera forata del banco (il metallo è opaco al radar — è un problema
   reale); che ruolo dà all'**UWB**, visto che il DIPME-DEVICE ce l'ha già
5. **Due limiti che dichiaro io per primo**, prima che me li chieda: il range provato è
   **1-5 m** e non 6 (limite della stanza, non del sensore — e per DIPME la distanza
   d'interesse è sotto il metro); e la **coda di presenza** del radar è di ~9 s misurati
   contro i 5 s configurati, fino a ~100 s per un bersaglio laterale
