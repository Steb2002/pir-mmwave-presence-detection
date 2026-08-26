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
- 🔌 **Alimentazione**: l'ESP32 ha UNA sola porta USB per dati e alimentazione, quindi per
  **qualsiasi acquisizione seriale** (comprese le notturne) deve stare attaccato all'USB del
  PC — un caricatore da muro escluderebbe il collegamento dati. Se comparissero brownout
  (riavvii casuali che sembrano bug del firmware: ESP32 + LD2410B hanno picchi >400 mA),
  la soluzione e' un **hub USB alimentato**, non un caricatore. L'alimentatore da muro
  serve solo nella Fase 7, quando il nodo gira autonomo in WiFi senza PC
- 👤 I test si svolgono con **1-2 soggetti** (dichiararlo nella tesi come perimetro
  sperimentale); dove possibile ripetere i test chiave (1.3, 1.4) con entrambi
- 🪟 **Per le acquisizioni lunghe (oltre ~1 h): sospendere gli aggiornamenti di Windows.**
  Il 20/08/2026 un aggiornamento automatico ha riavviato il PC e troncato una notturna di
  7 h a 6.57 h. Impostazioni > Windows Update > "Sospendi aggiornamenti", e verificare che
  sospensione/ibernazione siano su "mai". Il dato troncato resta valido (nessun buco), ma
  se il riavvio arriva a 20 minuti dall'inizio la sessione e' persa
- ✅ **Controllare sempre il conteggio righe** alla fine: `serie.py` lo stampa, e a 5 Hz
  deve valere ~5 x durata_in_secondi. Uno scarto grande significa interruzione

---

## FASE 0 — Preparazione (una tantum, prima di tutti i test)

### Test 0.1 — Verifica cablaggio e primo contatto con il LD2410B
- **Serve per**: sbloccare tutto il resto
- Collegare il LD2410B come da CLAUDE.md: **rosso→VIN, nero→GND, giallo(Rx radar)→D26,
  verde(Tx radar)→D25, blu(OUT) scollegato**
- **Passo A — sketch diagnostico**: caricare `firmware/test01_ld2410_base/test01_ld2410_base.ino`
  (board: ESP32 Dev Module, COM3), Serial Monitor a **115200 baud**. Fa auto-scan del baud
  (256000/115200/57600/9600), stampa i byte grezzi ricevuti per ciascuno, poi la versione
  firmware del radar e righe leggibili `PRESENZA [movimento] dist=... energia=...`
- **Passo B — logger CSV**: solo se il passo A funziona, caricare
  `firmware/ld2410b_logger/ld2410b_logger.ino` e verificare che escano righe CSV a 5 Hz
- ⚠️ Se appare `ERROR: radar not detected` / nessun frame valido: controllare che
  giallo/verde non siano invertiti (è stato l'errore che il 19/07/2026 ha fatto credere il
  modulo guasto). Il firmware del professore usa i pin scambiati rispetto al nostro sketch
  — non mescolare i due
- Diagnostica dai byte grezzi del passo A: **molti byte ma nessun frame valido** → baud
  giusto ma seriale/massa disturbata; **zero byte a tutti i baud** → alimentazione o
  verde/giallo invertiti
- **Esito atteso**: versione firmware letta + righe CSV con `radar_presence=1` quando ti
  muovi davanti al sensore
- **Annotare in `HLK-LD2410x/data/REGISTRO_SESSIONI.md`**: versione firmware del radar
  (serve nella tesi) e baud confermato

### Test 0.2 — Verifica engineering mode
- **Serve per**: obiettivi 2, 6 e test respiro
- Con lo sketch caricato (`ENGINEERING_MODE 1`), controllare che le righe CSV abbiano
  le 18 colonne extra `menergy_gate0..8` e `senergy_gate0..8` con valori 0-100 variabili
- **Esito atteso**: muovendoti a ~1.5 m il gate 2 (risoluzione 0.75 m) deve alzarsi

### Test 0.3 — Configurazione del PIR HC-SR501
- **Serve per**: obiettivi 1, 2, 3, 4
- ✔ Modello già identificato dalle foto: **HC-SR501** (BISS0001 + HT7133, uscita 3.3V
  sicura per ESP32) — specifiche e fonti in `analisi/ANALISI_PIR.md` §6
- Configurare: **jumper su H (repeat trigger)**, trimmer del tempo di ritenuta al
  **MINIMO** (~3 s, antiorario a fondo corsa), trimmer di sensibilita' a **meta' corsa**
  -> fotografare la posizione di jumper e trimmer, va tenuta identica per tutta la campagna
- ⚠️ **Verificare il jumper guardando la serigrafia L/H accanto al pettine**, non darlo per
  scontato: in tutta la fase 1 il ponticello era in realta' su **L** (non ripetibile) e
  l'errore e' rimasto negli appunti dal 19/07 al 22/08/2026. Effetto: l'uscita si comporta
  da monostabile a durata fissa, ogni evento produce un impulso di ~3.5 s che il movimento
  successivo NON prolunga
- ⚠️ Prima di collegare: verificare la serigrafia VCC/OUT/GND sul lato saldature
  (nei cloni l'ordine dei 3 pin può variare)
- Collegare: VCC→VIN(5V), GND→GND, **OUT→D34** (pin solo-input senza pull-up: ok perché
  l'HC-SR501 pilota attivamente l'uscita; sta sullo stesso lato dei cavi del radar)
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
- ➡️ Procedura completa in [PIANO_TEST_LD2420.md](PIANO_TEST_LD2420.md), Fase 0-2420:
  va fatta **sia** col tool PC **sia** via UART (comandi 0x00 e 0x08), e i due risultati
  vanno confrontati — sul LD2410B il tool PC diede valori sbagliati e la verità venne
  dall'UART
- Collegare il LD2420 al CH340E → PC, aprire il tool HiLink (Google Drive, cartella
  `HLK-LD2420_TOOL - English`), leggere la **versione firmware**
- Annotare qui il risultato: firmware = ______ → pinout OT1/OT2 = ______, baud = ______
- **Esito atteso**: versione letta; se ≥1.5.3 il TX seriale è OT1 (pin 3) a 115200 baud.
  Il manuale ufficiale V1.2 documenta **solo** questa mappatura (OT1 = UART_TX,
  OT2 = presenza); la variante invertita per firmware ≤ 1.5.2 è informazione di comunità

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
- Segnare sul pavimento con nastro: 1, 2, 3, 4, 5, 6 m dal sensore (fin dove arriva la
  stanza: il range massimo del modulo e' 675 cm). Misurare **in orizzontale dal sensore**
- ✔ **Svolto 1-5 m (20/08/2026)**. I 6 m non sono acquisibili nella stanza disponibile:
  limite logistico, da dichiarare in tesi come perimetro sperimentale. Se servisse
  estendere il range, l'unica via e' mettere il sensore in un angolo puntando lungo la
  **diagonale** della stanza — ma cambia la geometria, quindi va trattata come serie
  separata e non mescolata con questi 25 trial
- Per ogni distanza: stare in piedi sul segno e **camminare sul posto**, senza spostarsi
- ⚠️ **Riferimento**: qui il soggetto e' **in piedi**, quindi il torace sta sulla verticale
  dei piedi e il segno a terra va bene. (L'offset di ~30 cm visto nel Test 1.3 riguardava
  il soggetto **seduto**, con il busto arretrato rispetto al segno.) Non sporgersi avanti
  o indietro durante il cammino sul posto
- ✔ **Effetto geometrico: previsto ma NON osservato.** Si era ipotizzato un eccesso di
  ~8 cm a 1 m (il radar misurerebbe l'ipotenusa verso un torace piu' alto del sensore).
  La misura reale a 1 m e' **-0.52 ± 2.61 cm**, cioe' nessun offset: verosimilmente la
  riflessione dominante viene da una parte del corpo all'altezza del sensore. Ipotesi
  scartata dai dati — non c'e' alcun offset da spiegare
- ⚠️ **Durata 80 s, non 60**: devi lanciare il comando dal PC e poi raggiungere il segno.
  Quei secondi contengono te che cammini verso la posizione, con la distanza che spazza
  tutto il range: falserebbero media e deviazione. 80 s − 20 scartati = 60 s utili
- Comando (una serie di 5 trial per volta, `serie.py` li lancia in sequenza):
```powershell
.venv\Scripts\python.exe serie.py --scenario movimento_2m --gt-state moving
```
  (ripetere cambiando `--scenario` in movimento_1m, movimento_3m … movimento_6m)
- **Analisi**: `python ..nalisinalizza_test.py data\movimento_*.csv --salta-inizio 20`
  → colonne `mdist_media_cm`, `mdist_dev_cm`, `dist_nominale_cm`, `errore_cm`
  (la distanza nominale viene letta dal nome dello scenario)
  → grafico Excel: distanza reale vs misurata, con la retta ideale a 45°

### Test 1.3 — Persona seduta immobile (il test chiave della tesi)
- **Metrica**: falsi negativi — qui il PIR deve fallire e il mmWave no
- Sedersi su una sedia a 2 m, **stare fermi** (leggere un libro senza gesti ampi)
- ⚠️ **Durata 330 s, non 300**: per lanciare il comando devi essere al PC, quindi i primi
  secondi del file contengono te che cammini verso la sedia — e sono i secondi in cui il
  PIR ti rileva *correttamente*, perché ti muovi. Se non li scarti, il tasso di falsi
  negativi del PIR risulta più basso del vero. 330 s acquisiti − 30 s scartati = **300 s
  di immobilità pulita**
```powershell
python acquire.py --port COM3 --duration 330 --output data/fermo_seduto_T01.csv --scenario fermo_seduto --trial T01 --ground_truth_presence 1 --ground_truth_state static
```
- Procedura per ogni trial: lancia il comando → raggiungi la sedia e siediti **entro 20 s**
  → immobile fino alla fine → tra un trial e l'altro alzati e muoviti qualche secondo
- 5 trial; poi ripetere anche a 4 m (`fermo_seduto_4m`)
- **Analisi**: `python ..nalisinalizza_test.py dataermo_seduto_*.csv --salta-inizio 30`
  → `fn_radar_%` vs `fn_pir_%`. Risultato atteso: PIR ~100% FN dopo il timeout di
  ritenuta, radar < 5%. **Questo è il numero centrale del capitolo di confronto**
- Annotare la **temperatura**: sopra ~28 °C il contrasto termico corpo/ambiente cala e il
  PIR è penalizzato. Dichiararlo, o ripetere una serie in condizioni più fresche

### Test 1.4 - Persona sotto il banco (scenario UPRISE reale)
- **Metrica**: come 1.3, ma nella postura e alla distanza reali del progetto. E' il test
  che da' il senso alla tesi: il sensore vede la persona rifugiata sotto l'arredo?
- **Perche' e' diverso dal 1.3**: qui la distanza e' di **30-80 cm**, cioe' la regione in
  cui sappiamo gia' (Test 0.2 + piloti) che:
  1. `senergy_gate0` e `senergy_gate1` sono **sempre 0** -> il dettaglio per-gate
     stazionario non e' disponibile. La presenza aggregata viene comunque riportata
  2. le energie **saturano** a fondoscala -> per il respiro serve il canale **moving**
  3. il PIR e' nel suo caso peggiore: persona che si muove **sul posto**, non attraverso
     il campo (misurato: 80% di falsi negativi anche in movimento, a 1 m)

#### Montaggio del sensore
- Fissare il LD2410B **sotto il piano** del tavolo, sul bordo anteriore, puntato verso
  l'interno/basso (verso il torace di chi sta sotto). Nastro di carta, niente viti
- Il PIR affiancato, stessa direzione, cosi' il confronto resta a parita' di vista
- Annotare altezza da terra e orientamento: e' parte del setup da fotografare
- ⚠️ **Il banco reale UPRISE ha un piano rinforzato con lamiera forata antisfondamento**,
  ma dai render del progetto il sensore sta **sotto** il piano: la lamiera e' dietro
  all'antenna, non tra sensore e persona. Quindi non e' un ostacolo da attraversare, ma un
  **riflettore ravvicinato** che puo' alterare il diagramma di irradiazione a 24 GHz — vedi
  l'extra in fondo. Nel nostro setup si usa un tavolo normale, quindi lo scenario base va
  dichiarato come **valido senza lamiera**

#### Scenari (5 trial ciascuno)
- **A - immobile**: persona rannicchiata sotto, ferma, respira e basta
- **B - piccoli movimenti**: come A ma con micro-aggiustamenti ogni tanto (e' il caso
  realistico di una persona intrappolata: si agita, non sta perfettamente ferma)
```powershell
.venv\Scripts\python.exe serie.py --scenario sotto_banco_immobile --duration 340 --transitorio 40 --gt-state static
.venv\Scripts\python.exe serie.py --scenario sotto_banco_movimenti --duration 340 --transitorio 40 --gt-state static
```
- 340 s con 40 scartati = **300 s utili**: infilarsi sotto il banco e sistemarsi richiede
  piu' tempo che sedersi su una sedia, meglio abbondare
- 🔊 **`serie.py` emette segnali acustici** (disattivabili con `--muto`): sotto il banco non
  si vede lo schermo. Grave lungo = trial iniziato, vai in posizione. Doppio acuto = i 40 s
  sono scaduti, da qui i dati contano: stai fermo. Doppio medio = trial finito, muoviti.
  Scala di tre note = serie completata
- ⚠️ Se in qualche trial ci metti di piu', non e' un problema in acquisizione ma in analisi:
  rilancia con `--salta-inizio` piu' alto. Meglio scartare qualche secondo in piu' che
  lasciare dentro i movimenti dell'ingresso, che gonfiano il rilevamento del PIR
- **Analisi**:
```powershell
.venv\Scripts\python.exe ..\analisi\analizza_test.py data\sotto_banco_*.csv --salta-inizio 40
.venv\Scripts\python.exe ..\analisi\analizza_respiro.py data\sotto_banco_immobile_T01.csv --scan
```
- **Esito atteso**: radar ~0% di falsi negativi, PIR vicino al 100%. Sul respiro: canali
  moving utilizzabili, stazionari saturi o piatti
- **Da verificare esplicitamente** (sono le ipotesi aperte di questa tesi):
  - la presenza viene riportata anche con `senergy_gate0/1` a zero?
  - a che distanza legge il radar, e con quale stabilita' rispetto ai 2.7 cm da seduto?
  - il respiro e' estraibile a 30-80 cm nonostante la saturazione?

#### Il metallo DIETRO il sensore — RINVIATO ALLA FASE 3 (decisione 21/08/2026)
- ⚠️ **Chiarimento sulla geometria reale** (dai render del progetto, 21/08/2026): il sensore
  e' montato **sotto il piano** del banco, con l'antenna verso la persona. La lamiera di
  rinforzo sta **nel piano, cioe' dietro al sensore**. Tra sensore e persona non c'e' nulla.
  Un test "foglio metallico interposto" misurerebbe quindi una geometria che nel progetto
  non esiste, e va scartato.
- Il test che ha senso e' l'opposto: **piano metallico immediatamente dietro l'antenna**.
  A 24 GHz un riflettore a pochi millimetri altera il diagramma di irradiazione, e questa
  e' la condizione di montaggio reale.
- Procedura: ripetere lo scenario A con una teglia (o cartone alluminato) **a contatto col
  retro del modulo**, poi con ~2 cm di distanziale, e confrontare con lo scenario A libero.
  Ground truth invariata (`presence=1`): se il rilevamento peggiora, `fn_radar_%` lo misura.
```powershell
.venv\Scripts\python.exe serie.py --scenario sotto_banco_metallo_0mm --duration 340 --transitorio 40 --gt-state static
.venv\Scripts\python.exe serie.py --scenario sotto_banco_metallo_20mm --duration 340 --transitorio 40 --gt-state static
```
- Cosa guardare: non solo `fn_radar_%` (che potrebbe restare 0) ma **`menergy_media`,
  `mdist_media_cm` e la stabilita' della distanza** rispetto allo scenario A. Un'antenna
  disturbata puo' continuare a rilevare la presenza sbagliando distanza o perdendo energia
- Risposta che si ottiene: **serve un distanziale tra modulo e lamiera?** E' una specifica
  di montaggio concreta per il DIPME-DEVICE, ricavata da una misura
- La penetrazione attraverso i materiali (legno, plastica, cartongesso, vetro) resta in
  **Fase 3** dove appartiene: lo scenario e' il sensore chiuso in un contenitore, non la
  lamiera del piano
- ✔ **Decisione: questi due scenari col metallo si fanno in Fase 3**, insieme agli altri
  materiali. Il Test 1.4 si limita agli scenari A e B, che sono quelli che rispondono alla
  domanda centrale della tesi. Accorpare il metallo agli ostacoli evita anche di rimontare
  due volte lo stesso setup

---

## FASE 2 — Confronto dinamico PIR vs mmWave (obiettivo 3)

> 🔊 **Segnali vocali**: `acquire.py --beep-at` pronuncia le parole **"entra"** e
> **"esci"** invece di due bip. Con i bip bisogna ricordare quale significhi cosa, e nei
> due test il senso e' invertito: il 22/08/2026 un trial e' stato perso proprio cosi'.
> L'opzione **`--evento entra|esci`** dice cosa fare all'istante dell'evento; il primo
> annuncio e' automaticamente l'azione opposta, quindi non si possono scambiare.
> Se SAPI non parte lo script lo dichiara e ripiega sui bip (grave = primo, acuto = evento).
> Lo scarto residuo dell'annuncio e' comune ai due sensori e si cancella in `latenza_delta_s`.

### Test 2.1 — Latenza di rilevamento all'ingresso
- **Metrica**: secondi tra ingresso nel campo e prima rilevazione, per sensore
- ⚠️ **NON usare un timer sul telefono.** Tra l'apertura della porta seriale e la prima
  riga del CSV passano 2-3 s (reset dell'ESP32 + setup del logger + i 2 s di attesa in
  `acquire.py`): un timer avviato quando premi Invio sbaglia l'origine dei tempi di
  quella quantità, cioè **più della latenza che stai misurando**. Il riferimento lo dà
  `acquire.py --beep-at`, che emette i beep contando dalla prima riga di dati — la stessa origine che usa
  poi `analizza_test.py`
- ⚠️ **L'evento va a 30 s, non a 10.** Dopo che esci dalla stanza il radar tiene la
  presenza per ~10 s (coda misurata nel Test 0.2). Con l'evento a 10 s il radar sarebbe
  ancora attivo all'ingresso e la latenza risulterebbe zero per costruzione. 30 s danno
  il tempo di uscire, chiudere la porta e far scadere la coda
- Procedura per ogni trial: lancia → senti **"esci"** = esci dal campo e spostati di
  lato → senti **"entra"** (a 30 s) = rientra subito e resta in movimento fino alla fine
- ⚠️ Chiudere la porta NON ti nasconde al radar: il 24 GHz attraversa il legno. Quello
  che conta e' uscire dal cono del sensore e allontanarsi di qualche metro. Lascia
  pure la porta aperta, cosi' senti gli annunci
```powershell
.venv\Scripts\python.exe serie.py --scenario ingresso --duration 60 --trials 10 --pausa 25 --beep-at 30 --evento entra --gt-state moving
```
- **10 trial** (la latenza varia molto, servono più ripetizioni). ~14 min in tutto
- **Analisi**:
```powershell
.venv\Scripts\python.exe ..\analisi\analizza_test.py data\ingresso_*.csv --event-time 30
```
  → `latenza_radar_s` vs `latenza_pir_s`, e soprattutto **`latenza_delta_s`** (differenza
  appaiata radar−PIR sullo stesso trial: negativa = radar prima)
- ⚠️ **Cosa misura davvero questo test**: la latenza assoluta include il tempo di reazione
  al beep e il tragitto per rientrare nel campo, che non sono separabili senza un bersaglio
  meccanico. Va dichiarata come **latenza operativa**, limite superiore di quella del
  sensore. La grandezza pulita è `latenza_delta_s`: reazione e tragitto sono identici per i
  due sensori e si cancellano nella differenza
- Lo script segnala i trial **da scartare** (`pre_radar_%` o `pre_pir_%` > 0: un sensore era
  ancora attivo nei 3 s prima del beep). Se ne scarta più di uno o due, allungare il
  pre-evento a 40 s
- **Aspettativa**: qui il PIR gioca in casa — entrare in una stanza significa
  *attraversare* le zone della lente di Fresnel, esattamente lo stimolo per cui è
  progettato. Latenze comparabili o migliori del radar sono il risultato atteso, e non
  indeboliscono la tesi: mostrano che il PIR misura **transiti**, non presenza, che è
  proprio la conclusione dei test 1.2/1.3/1.4

### Test 2.2 — Latenza di rilascio all'uscita
- **Metrica**: dopo quanti secondi il sensore dichiara "stanza vuota"
- Procedura per ogni trial: lancia → senti **"entra"** = entra nel campo a ~2 m e
  muoviti → senti **"esci"** (a 30 s) = esci di scatto e resta fuori fino alla fine
```powershell
.venv\Scripts\python.exe serie.py --scenario uscita --duration 100 --trials 5 --pausa 15 --beep-at 30 --evento esci --gt-presence 0 --gt-state absent
```
- 70 s dopo l'uscita: la coda del radar è ~10 s, il margine serve perché un trial che
  finisce con il sensore ancora attivo esce come `MAI` e va rifatto
- 5 trial. Nota: il ground truth qui è "assente" solo dopo t=10 s — il file contiene due
  regimi diversi, quindi accuratezza e falsi positivi su questi file **non hanno senso**
  (lo script li salta da sé quando gli passi `--release-time`)
- **Analisi**:
```powershell
.venv\Scripts\python.exe ..\analisi\analizza_test.py data\uscita_*.csv --release-time 30
```
  → `rilascio_radar_s` vs `rilascio_pir_s`, più `riaccensioni_*` (quante volte il sensore
  è tornato a 1 dopo essere andato a 0: nel Test 0.2 il radar ha tenuto un target
  fantasma in decadimento, un solo numero non lo descrive)
- Casi non numerici, da leggere come informazione e non come errore:
  - `MAI` = il sensore era ancora attivo alla fine del file → **allungare la durata**,
    120 s non bastavano
  - `PRIMA` = il sensore era già a 0 al momento dell'uscita. Per il PIR è **atteso**: la
    ritenuta (3.4-3.8 s misurati) può scadere mentre il soggetto è ancora lì e in
    movimento. Non è un rilascio, è il monostabile che si esaurisce prima
- **Cosa aspettarsi**: radar ~10 s (misurato nel Test 0.2, cioè **il doppio** del timeout
  configurato di 5 s — è un risultato da riportare: il parametro dichiarato non descrive
  il comportamento osservato); PIR 3.4-3.8 s, che è solo il suo timer RC e non una misura
  di presenza

### Test 2.3 — Micro-movimenti (la zona grigia del PIR)
- **Metrica**: tasso di rilevamento con soli micro-movimenti, **a 1 m** e in piedi
- ⚠️ **Correzione del 23/08/2026: questo test va fatto a 1 m, non a 2 m.** La stesura
  originale diceva 2 m, ma a quella distanza il PIR ha dato **0.0% anche con movimento
  continuo** (Test 1.2 in L e in H): con micro-movimenti darebbe zero per definizione e
  non si misurerebbe una zona grigia, solo di nuovo il limite di portata. La zona grigia
  esiste **solo dove il PIR funziona**, cioe' a 1 m
- **Serve a completare la curva dose-risposta** a geometria costante — stessa distanza,
  stessa postura, stessa configurazione, cambia solo la quantita' di movimento:
  | condizione | rilevamento PIR |
  | immobile (`fermo_1m_H`) | 1.52 % |
  | micro-movimenti | **da misurare** |
  | cammino sul posto (`movimento_1m_H`) | 85.20 % |
- **Setup**: identico a `fermo_1m_H` e `movimento_1m_H` — in piedi sul segno dell'1 m,
  jumper su H. Micro-movimenti: scrivere al telefono, girare pagine, grattarsi. Niente
  gesti ampi, ma nemmeno immobilita'
```powershell
.venv\Scripts\python.exe serie.py --scenario micromovimenti_1m_H --duration 220 --transitorio 20 --gt-state micro_movement
```
- Durata allineata a `fermo_1m_H` (220 s con 20 scartati = 200 s utili x 5 trial)
- **Analisi**:
```powershell
.venv\Scripts\python.exe ..\analisi\analizza_test.py "data/*_1m_H_*.csv" --salta-inizio 20
```
  mette in fila le tre condizioni. Atteso: radar ~100% in tutte e tre, PIR in mezzo fra
  1.5% e 85%
- **Rilevanza per UPRISE**: e' la condizione realistica di una persona **cosciente ma
  ferita**, che non cammina sul posto e non sta immobile come una statua

### Test 2.4 — Selettività spaziale (scenario "banchi adiacenti" UPRISE)
- **Perché**: in un'aula reale i banchi sono affiancati e il radar vede attraverso il
  legno → il sensore del banco A rischia di rilevare la persona sotto il banco B,
  falsando la mappa dei sopravvissuti. La mitigazione è limitare la portata al volume
  del proprio banco riducendo il gate massimo
- **Setup**: gate massimo **2** con lo sketch `firmware/test04_set_gate/` (comando
  `g 2 2`); persona A ferma a 1 m, persona B ferma a **3.5 m**
- ✔ **MISURATO il 23/08/2026 col comando `m`: gate massimo 2 = portata 1.50 m**, non 2.25 m.
  Il monitor riporta distanze fino a 150 cm esatti e poi perde il bersaglio. La regola vera
  e' `portata = gate_massimo x 75 cm`. (Le due stesure precedenti di questa nota dicevano
  prima 1.5-2 m e poi 2.25 m: entrambe erano calcoli, questo e' una misura.)
- ⚠️ Ne segue che anche il "range massimo 675 cm" della configurazione di fabbrica e'
  sovrastimato: con gate 8 la portata e' **600 cm**. Il 675 viene da `getRange_cm()` di
  MyLD2410, che calcola `(gate+1) x risoluzione`
- 💡 **Provare anche `g 1 1` (portata 75 cm)**: la persona sotto il banco e' stata misurata
  a 62-69 cm nel Test 1.4, quindi gate 1 la coprirebbe escludendo un vicino a 1 m di lato.
  Margine stretto ma e' l'unica configurazione che puo' davvero isolare un banco: gate 2
  (1.50 m) comprende gia' il banco accanto
- Prima dei trial usare il comando `m` dello sketch per verificare dove il
  radar perde davvero il bersaglio: è la portata effettiva, e trovarla costa 1 minuto
  invece di tre trial da 3 minuti con una seconda persona
- ⚠️ **Configurazione via UART, non via app**: il LD2410 Tool PC ha già dato una lettura
  sbagliata delle soglie (vedi CLAUDE.md). Lo sketch rilegge sempre i parametri dopo la
  scrittura e stampa la tabella da incollare nel registro
- ⚠️ **A fine test, comando `d`**: ripristina gate 8/8, timeout 5 s e le 9+9 soglie di
  fabbrica. Se lo salti, tutte le acquisizioni successive sono fatte con una
  configurazione diversa da quella delle fasi 1-3 e non sono confrontabili
- **Metrica**: il sensore deve rilevare SOLO la persona A; poi persona A esce → il
  sensore deve dichiarare vuoto nonostante B sia ancora lì
- 3 trial × 3 min con nomi `selettivita_A_presente` (gt=1) e `selettivita_solo_B` (gt=0)
```powershell
python acquire.py --port COM3 --duration 180 --output data/selettivita_solo_B_T01.csv --scenario selettivita_solo_B --trial T01 --ground_truth_presence 0 --ground_truth_state absent
```
- **Analisi**: `radar_rate_%` in `selettivita_solo_B` è il tasso di "falso vicino" —
  numero chiave per l'applicabilità UPRISE multi-banco. Annotare nel registro che questi
  trial usano una configurazione **non di fabbrica**: senza quella nota, a distanza di
  settimane sembreranno confrontabili con gli altri e non lo sono

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

➡️ **Piano dedicato: [PIANO_TEST_LD2420.md](PIANO_TEST_LD2420.md)** (scritto il
26/08/2026 dopo l'acquisizione della documentazione ufficiale del modulo). Contiene i
10 test radar da ripetere, i 3 che **non sono replicabili** sul LD2420 e perché, il
test nuovo sul gate minimo, e la stima oraria.

⚠️ **Mai tenere accesi LD2410B e LD2420 puntati sulla stessa scena**: lavorano
entrambi a 24 GHz e possono interferire tra loro falsando i dati. Un radar alla
volta — il confronto tra i due si fa ripetendo gli stessi scenari, non in simultanea
(il PIR invece è passivo e può restare sempre collegato).

Tre punti del piano dedicato che conviene conoscere anche da qui:
- il **Test 1.3-2420** (persona immobile) va eseguito **per primo**: è il punto di
  decisione, se fallisce il resto della campagna non serve;
- il campo `Range` va **tarato** prima di qualunque test di distanza (Test 0.5-bis):
  l'unità non è documentata in nessuno dei due documenti ufficiali;
- il LD2420 **non misura la distanza dei bersagli fermi** (manuale §8), quindi le
  colonne `stationary_*` del CSV saranno 0 per costruzione, non per errore.

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
