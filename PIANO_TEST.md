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
pip install pyserial numpy pypdf
mkdir data
```
- A cosa serve ciascuna: **pyserial** ad `acquire.py`/`serie.py` (acquisizione),
  **numpy** ad `analizza_respiro.py` (FFT), **pypdf** a leggere i PDF ufficiali Hi-Link.
  ⚠️ Quest'ultimo non e' un vezzo: i frontespizi dei manuali Hi-Link **riportano versioni
  e date sbagliate** (vedi CLAUDE.md, sezione fonti), la verita' sta nella tabella di
  *revision records* in fondo, e quei PDF hanno i metadati compressi e il testo in font
  CID — quindi `strings` e i parser artigianali non funzionano, `pypdf` si
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
- ⚠️ **Questo movimento è il caso peggiore per il PIR** ed è la ragione dello 0% di
  rilevamento a 2-5 m. NON è la condizione con cui si misurano i 3-7 m del datasheet →
  il **Test 1.5** aggiunge il controllo per attraversamento; meccanismo in
  `analisi/ANALISI_PIR.md` §2.1
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

### Test 1.4 - Persona sotto il banco (scenario DIPME reale)
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
- ⚠️ **Il banco reale DIPME ha un piano rinforzato con lamiera forata antisfondamento**,
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

### Test 1.5 — Attraversamento del campo (controllo di validità del PIR) — ✅ FATTO 29/08/2026

> **ESITO: superato a tutte le distanze.** `pir_rate_%` = 100,00 / 100,00 / 98,83 / 98,73
> a 2 / 3 / 4 / 5 m (3 trial ciascuna, jumper H, trimmer a metà corsa), contro **0,0 %**
> ✔ **Esteso a 1 m il 25/09/2026**: `attraversamento_1m_T01..T03` = **100,00 ± 0,00 %** (a 1 m il
> cammino sul posto era già rilevato all'85 %: la prova completa la figura, non cambia la conclusione).
> del cammino sul posto alle stesse distanze. Radar `fn_radar_%` = 0,00 ovunque.
> Il PIR non è né guasto né mal tarato: la variabile che decide è il **tipo di movimento**,
> non la distanza. Dettagli e conseguenze in CLAUDE.md; riga nel registro sessioni.
> ✔ Il trial facoltativo a **sensibilità massima è annullato**: superfluo, perché un
> sensore che rileva a 5 m nel 98,7 % dei campioni non è poco sensibile — e non toccare
> il trimmer protegge la comparabilità della campagna.
> ⚠️ `errore_cm` di questi file **non** entra nella regressione del Test 1.2 (a 3 m è
> passato da +9,5 a +19,2 cm fra due sessioni; la spazzata trasversale ne spiega solo 1-8).
- **Perché esiste questo test**: nei Test 1.2/2.3 il PIR rileva lo **0%** a 2, 3, 4 e 5 m
  con soggetto in movimento continuo, mentre il datasheet dichiara **3-7 m**. Senza un
  controllo, quel dato è indistinguibile da "il sensore era guasto o tarato male" — che è
  l'obiezione più probabile della commissione. Questo test dimostra che il PIR **alle
  stesse distanze rileva benissimo un attraversamento**, e che il fallimento dipende dal
  **tipo di movimento**, non dalla distanza né dalla taratura (meccanismo in
  `analisi/ANALISI_PIR.md` §2.1)
- **Metrica**: fronti di salita del PIR e `pir_rate_%`, confrontati con il cammino sul
  posto alla stessa distanza (Test 1.2)
- ⚠️ **NON toccare il trimmer di sensibilità**: deve restare nella posizione usata in
  tutta la campagna, altrimenti il confronto con il Test 1.2 non vale più
- **Jumper su H**, ritenuta al minimo, come tutta la fase 2
- **Movimento**: camminare **trasversalmente** all'asse del sensore, avanti e indietro in
  modo continuo, restando a **distanza costante** dal sensore (segnare a terra una linea
  parallela alla parete del sensore, non un punto). È l'opposto del Test 1.2, dove il
  soggetto sta su un punto e cammina sul posto
- **Distanze**: 2, 3, 5 m — le stesse del Test 1.2, così il confronto è appaiato
- **3 trial per distanza**, 80 s (20 di transitorio + 60 utili)
- Comando:
```powershell
.venv\Scripts\python.exe serie.py --scenario attraversamento_2m --gt-state moving --trials 3
```
  (ripetere con `attraversamento_3m` e `attraversamento_5m`)
- **Analisi**:
```powershell
python ..\analisi\analizza_test.py data\attraversamento_*.csv --salta-inizio 20
```
  Confrontare `pir_rate_%` e i fronti con `data\movimento_{2,3,5}m*.csv` alla stessa
  distanza. ⚠️ Il transitorio da scartare qui **non** è il posizionamento: il soggetto è
  già in movimento trasversale dall'inizio. I 20 s servono solo a uniformare la finestra
  con le altre serie
- **Esito atteso**: `pir_rate_%` alto (in H, plausibilmente > 80%) a tutte e tre le
  distanze. Il riscontro incidentale già disponibile — `pir_jumper_attraversamento_T01`,
  1 trial in **L** a ~2.2 m — dà 9 fronti in 92 s e 32.8% di tempo alto, che in L è il
  **57% del tetto strutturale** della modalità (~58%)
- ⚠️ **Se invece il PIR NON rilevasse l'attraversamento a 3 m**: allora il problema è il
  sensore o la taratura, e va rivista tutta la caratterizzazione del PIR prima di
  scrivere il capitolo 4. È l'esito che questo test serve a escludere
- **Facoltativo, per chiudere del tutto il confondente sensibilità** (~5 min): 1 trial di
  cammino **sul posto** a 2 m con il **trimmer di sensibilità al massimo**. Se resta 0%,
  il trimmer è escluso per via sperimentale invece che per deduzione.
  🚨 Rimetterlo subito a metà corsa e annotarlo nel registro: lasciarlo spostato
  invaliderebbe la comparabilità di tutto il resto della campagna
- **Tempo stimato**: ~30-40 min (+5 min con la prova facoltativa)
- **Dove finisce in tesi**: cap. 4, subito accanto alla tabella delle distanze del
  Test 1.2, come riga di controllo

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
- **Rilevanza per DIPME**: e' la condizione realistica di una persona **cosciente ma
  ferita**, che non cammina sul posto e non sta immobile come una statua

### Test 2.4 — Selettività spaziale (scenario "banchi adiacenti" DIPME)
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

#### Gate 1 (portata 75 cm) — da misurare, ma NON raccomandabile come scelta di progetto

- **Perche' interessa**: gate 2 (1.50 m) comprende gia' il banco accanto, quindi non
  isola nulla. La persona sotto il banco e' stata misurata a **62-69 cm** nel Test 1.4:
  gate 1 la coprirebbe escludendo un vicino a 1 m di lato. E' l'**unica** configurazione
  che potrebbe davvero isolare un banco — margine stretto, ma e' quella o niente
- 🔑 **La contraddizione e' INTERNA al protocollo, non fra due documenti**
  (accertato 29/08/2026 estraendo il testo dei PDF con `pypdf`):
  | fonte | range dichiarato |
  |---|---|
  | Protocollo p.5, §1.2.2 *The role of configuration parameters* | *"the range can be set **from 1 to 8**"* |
  | Protocollo p.8, §2.2.3 *Maximum distance gate…command* | *"(configuration range **2~8**)"* |
  | Manuale V1.04 p.8, §5.2 (stesso titolo di sezione) | *"the setting range is **1 to 8**"* |
  Il paragrafo del manuale §5.2 e' lo **stesso testo copiaincollato** di §1.2.2 del
  protocollo (il protocollo aggiunge solo l'inciso sulla risoluzione 0.2/0.75 m).
  Quindi non ci sono "due documenti che divergono": c'e' **un paragrafo descrittivo
  duplicato in due file** contro **una parentesi nella specifica del comando 0x0060**
- 🚫 **L'argomento della recenza non ha oggetto**: le due frasi stanno nello stesso
  documento e nella stessa versione, a tre pagine di distanza. Non sono ordinabili per
  data. (Le date ci sono comunque, vedi sotto, ma non servono a questa domanda.)
  Gate 0 e' fuori range in **tutte e tre** le formulazioni
- ⚖️ **Come pesare le due letture.** A favore di 1-8: due sezioni descrittive su due
  documenti, l'esempio numerico *"if the farthest door is set to 2, only… within 1.5m"*
  presente in entrambe che **coincide con la nostra misura** (gate 2 -> 150 cm), e gate 1
  che sul nostro esemplare da' esattamente i 75 cm previsti dalla regola. A favore di
  2~8: la parentesi di §2.2.3 — che pero' e' la sezione **normativa** per "quale valore
  posso scrivere via UART", perche' definisce il comando 0x0060 e la codifica del suo
  parametro. §1.2.2 e manuale §5.2 sono prosa esplicativa
- ⚠️ **Attenzione all'argomento "il modulo lo ha accettato": non prova nulla da solo.**
  Il firmware **non valida l'input** — gate 0 e' stato accettato senza errore e ha
  prodotto comportamento rotto. Quello che prova qualcosa e' la *differenza*: gate 0
  accettato e **sbagliato**, gate 1 accettato e **conforme alla regola documentata**
- 📌 **Formula corretta**: non "la documentazione dice di no", ma *"la documentazione e'
  internamente incoerente, e la misura sta dalla parte della sezione descrittiva"*.
  Resta il motivo per non raccomandarlo in un progetto: la sezione normativa lo esclude
- ✔ **Portata gia' misurata**: gate 1 -> **75 cm** (registro 23/08/2026, comando `m`).
  Sullo stesso banco di prova **gate 0 e' risultato rotto** (distanza fissa 72 cm,
  presenza sempre 1): e' la prova sperimentale che i valori fuori specifica possono
  davvero non funzionare, ed e' la ragione per cui gate 1 **non va raccomandato** come
  configurazione di montaggio per il DIPME-DEVICE pur funzionando sul nostro esemplare
- **Cosa manca davvero**: non la portata, ma la **selettivita'** con gate 1. Ripetere due
  scenari `sel_*` con `g 1 1`, 3 trial ciascuno, soggetti **fermi**:
```powershell
.venv\Scripts\python.exe serie.py --scenario sel_g1_dentro_60cm --duration 260 --transitorio 120 --trials 3 --gt-state static
.venv\Scripts\python.exe serie.py --scenario sel_g1_laterale_1m --duration 260 --transitorio 120 --trials 3 --gt-presence 0 --gt-state absent
```
  (`sel_g1_dentro_60cm`: occupante rannicchiato sotto il banco. `sel_g1_laterale_1m`:
  **solo** il vicino a 1 m di lato, nessuno sotto il banco -> `radar_rate_%` e' il tasso
  di falso vicino). ⚠️ Transitorio **120 s**, come tutti gli scenari di selettivita':
  con 20 s si misura la coda di posizionamento e non il regime (vedi CLAUDE.md)
- **Analisi**: `..\analisi\analizza_test.py "data/sel_g1_*.csv" --salta-inizio 120`,
  da confrontare con `sel_dentro_1m` / `sel_laterale_1m` acquisiti a gate 2
- **Come citarlo in tesi** — versione aggiornata al 29/08/2026:
  > Il protocollo seriale ufficiale si contraddice al proprio interno sul range
  > configurabile del gate massimo: il \S1.2.2 (p.5) dichiara che *"the range can be set
  > from 1 to 8"*, mentre il \S2.2.3 (p.8), che definisce il comando 0x0060, dichiara
  > *"(configuration range 2~8)"*. Il manuale \S5.2 (p.8) riporta la prima formulazione,
  > in un paragrafo pressoche' identico a quello del \S1.2.2. Sul nostro esemplare gate 1
  > risponde correttamente, con portata misurata di 75 cm, coerente con la regola
  > *portata = gate x 75 cm* e con l'esempio numerico presente in entrambi i documenti;
  > gate 0, escluso da ogni formulazione, produce invece un comportamento anomalo
  > (distanza fissa a 72 cm, presenza sempre attiva). Poiche' il firmware non convalida
  > il parametro ricevuto, l'accettazione del comando non costituisce di per se' prova di
  > conformita': il dato e' riportato come misura su un singolo esemplare e la
  > configurazione non e' proposta come scelta progettuale, essendo esclusa dalla sezione
  > normativa del protocollo.
- 📌 **Se gate 1 resta fuori, la conclusione del Test 2.4 cambia** e va scritta cosi': la
  selettivita' spaziale **non e' ottenibile per via di configurazione**, perche' l'unica
  portata entro specifica (gate 2 = 150 cm) comprende gia' il banco accanto. Ne segue che
  a fare il lavoro deve essere il **diagramma di irradiazione**, il che rende bloccanti i
  due punti ancora aperti: la **misura angolare dedicata** e il **vicino a 90° in
  movimento** (finora provato solo da fermo)
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
  numero chiave per l'applicabilità DIPME multi-banco. Annotare nel registro che questi
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

## FASE 3 — Penetrazione ostacoli (obiettivo 3) — ✅ FATTA 30/08/2026, ➕ Test 3.6 aperto

> **ESITO**: il radar attraversa **tutti** i dielettrici provati (plastica -7,5 %,
> cartone -17,2 %, vetroresina 1 mm -19,6 %, vetro 5 mm -40,9 %, legno 10 mm -41,6 %)
> restando al 100 % di rilevamento; il **metallo blocca del tutto**; il **PIR e' azzerato
> da tutti e sei**, contro il 79,6 % senza ostacolo. Tabella completa e avvertenze in
> CLAUDE.md; sezione del cap. 4 scritta. Cartongesso non disponibile: lacuna dichiarata.

🚨 **Il protocollo qui sotto e' quello ORIGINALE ed e' SBAGLIATO in due punti.** Se la
fase va ripetuta (per esempio col LD2420), usare le correzioni seguenti:
1. **Soggetto in MOVIMENTO sul posto, non fermo.** Su bersaglio immobile `senergy`
   satura a 100 anche a 4 m: l'attenuazione non sarebbe osservabile
2. **Due distanze, non una**: **3 m** per il radar (energia a meta' scala) e **1 m** per
   il PIR (a 3 m non rileva il movimento sul posto, quindi partirebbe gia' da zero)

Altre tre cose imparate sul campo:
- **il controllo col metallo va fatto per secondo**, subito dopo la baseline: se non
  bloccasse, la geometria andrebbe corretta prima di acquisire tutto il resto
- **il pannello deve essere rigido**: un foglio sottile e ampio flette e diventa un
  bersaglio in movimento (successo con una lastra di cartone 105x71x0,4 mm)
- **la baseline va mediata su inizio E fine sessione**: e' la misura piu' rumorosa della
  serie (6 trial da 47,8 a 57,3), e prenderla una volta sola falsa tutte le percentuali

Setup originale: persona ferma seduta a 2 m dal sensore; pannello di materiale interposto
a ~20 cm davanti al sensore. Prima una baseline senza ostacolo, stesso giorno.

### Test 3.1 — Baseline senza ostacolo — ✅ FATTO 30/08/2026
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

### Test 3.6 — 🆕 **Portata residua per materiale** (richiesto dal professore, 05/09/2026)

> ✅ **ESITO (09-10/09/2026, 42 file `ost36_*`)**: **nessun dielettrico provato accorcia la
> portata entro i 5 m della stanza** — presenza 100 % e distanza corretta in tutti i 39
> trial con ostacolo (cartongesso 1-5 m, legno e vetro 4-5 m, porta chiusa 3-5 m; negativi
> puliti in entrambe le geometrie). Quello che si degrada è il **canale moving**:
>
> | frazione di campioni con `moving_target` = 1 | 1 m | 2 m | 3 m | 4 m | 5 m |
> |---|---|---|---|---|---|
> | senza ostacolo (Test 1.2) | 100 % | 98 % | 91 % | 87 % | 78 % |
> | cartongesso 10 mm | 99 % | 89 % | 77 % | 63 % | 45 % |
> | legno 10 mm | — | — | (Fase 3) | 52 % | 19 % |
> | vetro 5 mm | — | — | (Fase 3) | 41 % | 26 % |
> | **porta interna chiusa** | — | — | **96 %** | **20 %** | **3 %** |
>
> Energia moving del cartongesso 97 / 68 / 36 / 25 / 22 contro 99 / 85 / 54 / 35 / 28
> senza (a 3 m **−26 %** rispetto alla baseline della stessa sera, 48,6); PIR 0 % a 1 m.
> La **porta** a 3 m è trasparente (49,6 = baseline) ma a 4-5 m spegne il canale moving
> più del legno pieno: la presenza resta al 100 % grazie al canale **stazionario**, saturo
> e con la distanza giusta (433-441 a 4 m, 525-543 a 5 m; corridoio vuoto → 0 %).
> **Frase per il professore**: *senza ostacolo il LD2410B vede fino a 5 m (limite della
> stanza); con cartongesso, legno, vetro o una porta chiusa vede ancora fino a 5 m; il
> segnale in movimento si riduce, e con la porta a 5 m sopravvive solo il canale
> stazionario.* Plastica, cartone, vetroresina non ripetuti (−7…−20 % a 3 m: dedotti sopra
> soglia a 5 m, da dichiarare); metallo 0 m già misurato. ⚠️ Baseline di sessione ~10 %
> sotto quella di agosto (48,6 vs 53,5-54,4): riferire i materiali alla baseline della
> stessa sera. Scarti: `ost36_nessuno_3m_nonvalido` (stanza vuota per istruzione ambigua,
> tenuto come negativo), `ost36_porta_5m_congelato_T01` (radar muto, 392 frame identici).
> Porta **tamburata senza vetro**, chiusa; a 5 m il muro di fondo (negativo a 0 %). Il
> soggetto stasera **oscillava lateralmente di ~50 cm** invece di camminare sul posto: per il
> radar cambia poco (baseline −10 %, riferimento della stessa sera), per il **PIR cambia
> tutto** — a 3 m senza ostacolo 13-100 % contro 0 % in 14 trial di agosto, stesso meccanismo
> del 30/08 (transito attraverso le zone di Fresnel) confermato a 3 m. Con cartongesso 0 %.
> ⚠️ Il 78-100 % del PIR **attraverso la porta chiusa** non è spiegato (fessura sotto o luce
> del battente, non verificato): non usarlo in nessuna direzione.


> *"Altro aspetto è capire rispetto al materiale se e quanto viene attenuato. Ad esempio
> se prima arrivava a 5 mt, con una porta di mezzo quanto si attenua il segnale?"*

**Perché è un test nuovo e non una rilettura dei dati esistenti.** La Fase 3 ha misurato
l'attenuazione **a distanza fissa**, in punti percentuali di `menergy`. Ma `menergy` è un
indice normalizzato 0-100 con elaborazione interna: le percentuali sono in unità dello
strumento e **non** si convertono in dB né si confrontano con i coefficienti di
trasmissione teorici. La domanda del professore invece ha una risposta esprimibile in
**metri**, che non richiede alcuna ipotesi su cosa sia `menergy`:

> *senza ostacolo il sensore vede una persona fino a X m; con il materiale interposto
> fino a Y m.*

È il numero più utile per il progetto (dice se il sensore incassato nell'arredo copre
ancora il volume sotto il banco) ed è quello più difendibile in discussione.

**Setup.** Identico alla Fase 3 — pannello a ~20 cm davanti al sensore, soggetto **in
movimento sul posto** — ma invece di una distanza sola si percorrono **1, 2, 3, 4, 5 m**.
Tacche a terra già presenti dal Test 1.2. 3 trial per coppia (materiale × distanza),
80 s per trial (20 di transitorio + 60 utili).

**Metrica**: la distanza massima a cui `radar_rate_%` ≥ 95 % *e* `menergy_media` resta
sopra il rumore di fondo del gate corrispondente. In più la curva `menergy` vs distanza
per ciascun materiale, sovrapposta a quella senza ostacolo (che abbiamo già dal Test 1.2:
99,0 / 85,1 / 54,4 / 35,1 / 27,6 da 1 a 5 m).

**Materiali, in ordine di priorità** — non serve rifarli tutti e sei:
1. 🚪 **Porta interna chiusa** — è l'esempio letterale del professore ed è il caso più
   realistico per un'aula. 🔑 **Ha anche un vantaggio metodologico**: la porta copre
   l'intero campo del sensore, quindi cade l'avvertenza della Fase 3 per cui *"le
   attenuazioni sono limiti inferiori perché i pannelli coprivano solo ±42-70°"*. Qui
   non c'è aggiramento possibile → il numero è pulito
2. **Legno 10 mm** e **vetro 5 mm** — i due dielettrici più attenuanti già misurati
   (−41,6 % e −40,9 %): sono quelli in cui la portata dovrebbe accorciarsi in modo
   visibile
3. **Cartongesso 12,5 mm** — la lacuna dichiarata della Fase 3, e il professore l'ha
   chiesto di nuovo. ⚠️ Uno sfrido da 60×60 cm costa pochi euro in ferramenta: vale la
   pena procurarlo prima di questa sessione invece di dichiarare di nuovo il buco
4. **Metallo** — non serve la curva: blocca già a 1 m (portata residua 0 m). Un solo
   trial di conferma

**Costo**: ~25 min per materiale (5 distanze × 3 trial) + allestimento. Con porta, legno,
vetro e cartongesso ≈ **2 h**.

⚠️ **Le tre avvertenze della Fase 3 restano tutte valide**: pannello rigido, controllo
col metallo per secondo, **baseline mediata su inizio e fine sessione** (è la misura più
rumorosa della serie). E prima di leggere `menergy_media` guardare sempre
`mdist_media_cm`: se sta a ~30 cm con dispersione 0, il radar sta inseguendo il pannello
e l'energia non significa nulla.

📌 **Attenuazione in dB**: se serve il numero in decibel e non in metri, l'unico modulo
che può darlo è il **LD2420**, le cui energie per-gate sono `uint16` grezzi e non un
indice normalizzato — vedi `PIANO_TEST_LD2420.md` §0-ter, con l'ipotesi da dichiarare e
il limite di dinamica del nostro esemplare.

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

## FASE 5 — Respiro (test avanzato, obiettivi 2-3) — ✅ FATTA 31/08/2026

> **ESITO**: 10 -> 10,00 ± 0,00 · 15 -> 14,95 ± 0,30 · 20 -> 19,64 ± 0,09 atti/min,
> errore assoluto medio **0,22**; controllo negativo **senza stime in 3 trial su 3**.
> Dettagli e revisione del criterio di analisi in CLAUDE.md; sezione del cap. 4 scritta.

🚨 **Correzioni al protocollo qui sotto**, se la fase va ripetuta:
1. **2 m, non 1 m**: a 1 m i canali moving saturano e il respiro sparisce nel fondoscala
2. **Rivolto verso il sensore**, cosi' l'escursione toracica e' lungo la linea di vista
3. **Metronomo al doppio del ritmo**: inspira su un battito, espira sul seguente
4. In analisi serve **`--salta-inizio`** pari al transitorio: i secondi del posizionamento
   dominano la FFT e coprono il respiro

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

## FASE 8 — Portata massima dei tre sensori (richiesta dal professore, 29/08/2026)

⏱️ **Va fatta PER ULTIMA**, dopo tutte le fasi in stanza: richiede di spostare PC e
sensori in **corridoio**, e una volta smontato il setup della stanza le serie
precedenti non sono piu' riproducibili a parita' di geometria.

### 8.0 — Baseline di rumore in corridoio (BLOCCANTE, ~20 min)
🔑 **Il rumore misurato in stanza NON vale in corridoio, e serve proprio ai gate
lontani** — cioe' quelli su cui verte tutta questa fase. Un corridoio ha pareti
parallele ravvicinate (multipath) e bersagli fissi reali (porte, fondo) proprio a 6-8 m,
dove in stanza non c'era nulla. Senza baseline non si distingue "rilevamento a 7 m" da
"eco della parete di fondo".
- ⚠️ **Non servono altre 7 ore.** La notturna ha mostrato che il fondo e' **stabile**
  (gate0 17,4 → 17,8 fra prima e seconda meta' della notte): non e' una grandezza che
  deriva lentamente, quindi una finestra breve la caratterizza. **20 minuti bastano**
- ⚠️ Quello che 20 minuti **non** danno e' un limite sui falsi positivi confrontabile con
  lo 0,43 eventi/h (regola del tre: 20 min → ≤ 9 eventi/h, inutile). Non e' un problema:
  la dichiarazione sui falsi positivi riguarda lo **scenario d'impiego** (aula/stanza),
  non il banco di prova della portata. Non rifarla in corridoio
```powershell
python acquire.py --port COM3 --duration 1200 --output data/corridoio_vuoto_T01.csv --scenario corridoio_vuoto --trial T01 --ground_truth_presence 0 --ground_truth_state absent
python ..\analisi\verifica_engineering.py data\corridoio_vuoto_T01.csv
```

### 8.1 — LD2410B: 6 m e' il tetto, non "oltre i 5 m"
🚨 **Da dire al professore.** Il LD2410B **non puo'** andare oltre i 6 m: gate massimo 8
x 75 cm = **600 cm**, ed e' la regola documentata al §5.2 del manuale, gia' verificata da
noi. L'altra risoluzione disponibile (0,2 m/gate) **peggiora** il tetto, portandolo a
1,6 m. Quindi la richiesta si traduce in **un solo punto nuovo: 6 m**.
- Le 5 distanze 1-5 m sono gia' fatte. L'estrapolazione dell'energia dava ~27 a 6 m
  contro soglia 15, quindi il rilevamento e' atteso funzionante fino al tetto
- 5 trial, stesso protocollo del Test 1.2 (cammino sul posto, 80 s, 20 di transitorio)
```powershell
.venv\Scripts\python.exe serie.py --scenario movimento_6m_corridoio --gt-state moving
```
- ⚠️ **NON mescolare con la regressione dei 25 trial in stanza**: geometria diversa,
  setup rimontato. Stessa lezione delle serie `_H` (scarto di ~4 cm dal rimontaggio).
  Serie separata, dichiarata

### 8.2 — PIR a sensibilita' massima
🚨 **Il movimento deve essere di ATTRAVERSAMENTO, non sul posto.** Con il cammino sul
posto abbiamo gia' misurato **0 % a 2 m**: rifarlo a sensibilita' massima misurerebbe di
nuovo zero e non direbbe nulla. I 3-7 m del datasheet sono dichiarati per un bersaglio
che **attraversa** il campo — vedi Test 1.5 e `analisi/ANALISI_PIR.md` §2.1
- Distanze: 2, 4, 6, 8 m finche' il corridoio lo consente, 3 trial ciascuna
- ⚠️ **Serie dichiaratamente separata**: sensibilita' al massimo rompe la comparabilita'
  con tutta la campagna, fatta a meta' corsa. Nome scenario con suffisso `_smax`
- 🚨 **A fine fase rimettere il trimmer a meta' e annotarlo nel registro.** Se resta
  spostato, qualunque acquisizione futura non e' confrontabile con le fasi 1-3
- 📌 Il Test 1.5 resta **a sensibilita' di campagna**: serve a confrontarsi con il Test
  1.2, quindi non va accorpato a questa serie ne' fatto a sensibilita' massima

### 8.3 — LD2420 fino a 8 m
*(Il blocco sull'unità del `Range` è SUPERATO: centimetri, verificato il 02/09; il logger
binario dà anche le 16 energie.)* L'esemplare vede fino a ~2 m (accertato 04/09): la prova
in corridoio serve a **misurarlo formalmente nella stessa geometria degli altri due**, non
a cercare gli 8 m. Distanze 1-2-3-4 m con 3 trial, 6 e 8 m con 1 trial di documentazione.
- ⚠️ **Mai LD2410B e LD2420 accesi insieme**: entrambi a 24 GHz, interferiscono. Un radar
  alla volta, gli stessi scenari ripetuti (il PIR e' passivo e puo' restare collegato)

### 8.5 — 🔴 PROTOCOLLO ESECUTIVO (scritto 10/09/2026)

Due parti, prima il LD2410B col PIR, poi il LD2420. Tacche a terra dal sensore: 2, 4, 5,
6, 7, 8 m e oltre finché il corridoio lo consente; annotare la lunghezza massima, la
larghezza del corridoio, l'altezza del sensore e cosa c'è in fondo.

**Parte A — LD2410B + PIR** (`ld2410b_logger`, PIR su D34, jumper H, trimmer a metà)
1. Baseline di rumore, 20 min a corridoio vuoto (bloccante: i gate 6-8 qui hanno pareti
   e fondo veri) — `corridoio_vuoto`, 1 × 1200 s
2. LD2410B: cammino sul posto a **5 m** (3 trial, aggancio con la stanza), **6 m** (5 trial,
   il tetto documentato 8 × 75 cm), **7 m** (3 trial, atteso 0 %: oltre il gate 8) —
   `movimento_{5,6,7}m_corridoio`
3. PIR attraversamento a **sensibilità di campagna**, 6 e 8 m (3 trial ciascuno) —
   `attrav_{6,8}m_corridoio`: il Test 1.5 arrivava a 5 m al 98,7 %, il limite non è
   ancora stato trovato
4. **Trimmer di sensibilità al massimo** (annotare), stesse distanze più 10 m se c'è —
   `attrav_smax_{6,8,10}m`. Movimento trasversale, larghezza ~1 m, avanti e indietro
   continuo come nel Test 1.5
5. 🚨 **Trimmer di nuovo a metà corsa** e riga nel registro

**Parte B — LD2420** (staccare il VIN del LD2410B, cablare 3V3/GND/OT1→D16/RX→D17,
caricare `ld2420_logger_bin` BUILD 8, PIR non letto)
6. Accendere e **allontanarsi subito**, nessuno entro 2 m per 90 s; `check2420_fondo_corr`
   60 s a vuoto (g0 ~100, g2 ~13, altrimenti fermarsi)
7. Negativo `vuoto2420_corr` 240 s con 120 di scarto
8. Cammino sul posto a **1, 2, 3, 4 m** (3 trial) e **6, 8 m** (1 trial) — `corr2420_{d}m`.
   Attesi: 100 % a 1-2 m, fondo da 3 m in su
9. Positivo di chiusura a 1 m (`corr2420_1m_fine`, 1 trial)

Analisi: `analizza_test.py --salta-inizio 20` per presenza e PIR; per il LD2410B a 6-7 m
guardare `mdist` (segue la persona o il fondo del corridoio?) ed energia del gate 8 contro
la baseline; per il LD2420 le 16 energie con `portata2420.py`. Tempo: ~1 h 45.
⚠️ Serie **separate** da quelle in stanza: geometria diversa, dichiarata come tale.

### 8.4 — Cosa NON va rifatto in corridoio
I risultati portanti della tesi (persona immobile, sotto il banco, curva dose-risposta
del PIR) sono stati acquisiti in stanza e **restano validi**: spostare il setup dopo non
disfa una misura gia' presa. La stanza va dichiarata come perimetro sperimentale di
quelle serie, il corridoio come perimetro di questa fase.

---

## Riepilogo tempi stimati

| Fase | Test | Tempo effettivo di misura |
|---|---|---|
| 0 | Preparazione | mezza giornata |
| 1 | Caratterizzazione | ~4.5 h di acquisizioni (incl. Test 1.5, ~40 min) |
| 2 | Confronto dinamico | ~2 h |
| 3 | Ostacoli | ~1.5 h |
| 4 | LD2420 | mezza giornata (incluso sketch) |
| 5 | Respiro | ~1 h |
| 6 | Vitalità | ~1.5 h |
| 7 | Web UI | 2-4 giorni di sviluppo |
| 8 | **Portata massima (corridoio)** | **~2.5 h** (0.3 baseline + 0.5 LD2410B + 1 PIR + 0.7 LD2420) |

⚠️ **La Fase 8 va per ultima fra le acquisizioni** (dopo la 4, prima o in parallelo alla
7): smontare il setup della stanza rende non riproducibili tutte le serie precedenti.

Ordine consigliato: 0 → 1 → 2 → 3 → 5 → 6 → 4 → 8 → 7 (la fase 4 può slittare senza
bloccare nulla; la 7 si sviluppa nei tempi morti tra le acquisizioni).
