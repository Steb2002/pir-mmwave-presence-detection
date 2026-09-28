# Analisi teorica — Sensore PIR (Obiettivo 1-2)

> Controparte "teorica" delle specifiche LD2410B/LD2420 già in CLAUDE.md: come
> funziona il PIR, che dati produce e perché ha i limiti che ha. Analisi valida per
> qualsiasi PIR consumer; la sezione 6 va completata quando il modello in dotazione
> sarà identificato (Test 0.3).

---

## 1. Principio fisico: rilevatore di VARIAZIONE, non di presenza

PIR = *Passive InfraRed*. Il cuore è un **sensore piroelettrico**: un cristallo che
genera una piccola carica elettrica quando la radiazione infrarossa che lo colpisce
**cambia**. Il corpo umano (~34°C di temperatura superficiale) emette IR con picco
a ~9.4 µm; il sensore è filtrato proprio su quella banda (finestra 5-14 µm).

Punto fondamentale per la tesi: il cristallo risponde alla **derivata** del flusso
IR, non al suo valore. Costruttivamente il sensore contiene **due elementi
piroelettrici in configurazione differenziale** (collegati in serie con polarità
opposte):

- persona che si muove → gli elementi vengono investiti dall'IR **in tempi diversi**
  → segnale differenziale ≠ 0 → rilevamento
- persona ferma → entrambi gli elementi ricevono lo stesso flusso costante →
  differenza = 0 → **il sensore è fisicamente cieco**
- vantaggio della configurazione: variazioni globali (sole che scalda la stanza)
  colpiscono entrambi gli elementi insieme → si annullano → immunità parziale ai
  falsi positivi ambientali

Quindi il "difetto" del PIR che la tesi misurerà (Test 1.3: falsi negativi ~100% su
persona ferma) **non è un limite del modello economico ma della fisica del principio
di funzionamento**: nessun PIR, a nessun prezzo, può rilevare una persona immobile.
Questa è la frase chiave del confronto con il mmWave.

## 2. La lente di Fresnel: da 2 elementi a decine di zone

Da soli, i due elementi coprono un campo strettissimo. La cupola bianca che si vede
sui moduli è una **lente di Fresnel multi-segmento**: ogni segmento focalizza sul
cristallo una "fetta" diversa della scena, creando decine di **zone di rilevamento**
a ventaglio separate da zone cieche.

Conseguenze misurabili nei test:
- il movimento **trasversale** (che attraversa le zone) genera più transizioni
  IR → rilevato meglio; il movimento **radiale** (dritto verso il sensore) resta
  nella stessa zona più a lungo → rilevato peggio. (Il radar Doppler/FMCW ha la
  sensibilità opposta: meglio il radiale.) Da annotare nel Test 2.1 in base alla
  direzione di ingresso
- la portata dichiarata (~5-7 m) vale per movimento trasversale di tutto il corpo;
  micro-movimenti a distanza cadono facilmente tra le zone (Test 2.3)

### 2.1 La portata dipende dal TIPO di movimento (3-7 m dichiarati vs 0% misurato a 2 m)

Questa sezione risponde alla domanda più naturale — e alla più probabile obiezione della
commissione: *«il datasheet dichiara 3-7 m, come fa il vostro PIR a non vedere niente a
2 m? Era guasto o tarato male?»*

#### Il dato dichiarato non è confrontabile con il nostro

Il datasheet HC-SR501 dichiara **3-7 m** (§6), ma **non dichiara in quale condizione**
quella portata è misurata. Per convenzione industriale un PIR si collauda con una persona
che **attraversa** il campo, cioè lo stimolo per cui la lente di Fresnel è progettata.
I nostri Test 1.2/2.3 usano invece **cammino sul posto**: le due cifre misurano grandezze
diverse, e il nostro 0% a 2 m non è una violazione della specifica.
⚠️ Il fatto che la condizione di prova non sia dichiarata è una **debolezza del datasheet**
e va detto in tesi: è il motivo per cui il numero da solo non è utilizzabile.

#### Il controllo sperimentale: stessa distanza, movimento diverso

Il confronto è già nei dati acquisiti (`pir_jumper_attraversamento_T01.csv`, 22/08/2026,
nato come test del jumper). Stesso sensore, stesso trimmer di sensibilità, **stessa
modalità L** nelle prime due righe:

| condizione | distanza (radar) | fronti di salita | PIR alto |
|---|---|---|---|
| **attraversamento del campo**, jumper L | 219 cm (171-313) | **9 in 92 s** | **32.8 %** |
| cammino **sul posto** a 2 m, jumper L (5 trial) | 210 cm | **2 in 410 s** | 1.7 % |
| cammino **sul posto** a 2 m, jumper H (5 trial) | 216 cm | **1 in 410 s** | 4.6 % |

Il 32.8% in L è il **57% del tetto strutturale** di quella modalità (~58%, cfr. §3.1): in
H sarebbe stato vicino al 100%. **Il sensore non è guasto e il trimmer non è troppo
basso**: a 2.2 m rileva benissimo, purché gli si passi davanti.

#### La prova interna ai trial: *quando* cadono i pochi impulsi

Cercando gli impulsi PIR nel tempo dentro i 10 trial a 2 m:

```
movimento_2m_H_T01     0.0 – 15.0 s
movimento_2m_H_T03     1.4 –  4.8 s
movimento_2m_T01       3.0 –  6.2 s ; 13.2 – 16.4 s
gli altri 6 trial      nessuno
```

**Tutti gli impulsi, in tutti i trial, cadono entro i primi 16.4 s** — cioè durante il
posizionamento, mentre il soggetto raggiungeva il segno *camminando trasversalmente*.
Dopo t = 16.4 s, su ~650 s complessivi di cammino sul posto continuo a 2 m, il PIR ha
emesso **zero** eventi. Stesso file, stesso minuto, stessa distanza: si avvicina →
rilevato; si ferma sul segno e continua a muoversi → niente.
📌 È anche il motivo per cui la finestra standard `--salta-inizio 20` restituisce
`fn_PIR = 100.00 ± 0.00 %`: lo scarto del transitorio elimina esattamente e solo gli
eventi da attraversamento.

#### Perché è il comportamento atteso (meccanismo)

Le zone della lente hanno **apertura angolare fissa**, quindi la loro impronta lineare a
distanza D vale D·θ e **cresce proporzionalmente a D**. Il piroelettrico si attiva solo
quando il corpo **attraversa il confine** fra due zone, cioè quando l'ampiezza
*trasversale* del movimento supera D·θ:

- **attraversare il campo**: ampiezza dell'ordine dei metri → supera l'impronta a
  qualunque D nel range → funziona a tutte le distanze dichiarate
- **muoversi sul posto**: ampiezza di alcune decine di cm e **costante con la distanza**
  → esiste una distanza critica oltre la quale l'oscillazione resta *dentro una singola
  zona* e il sensore è cieco

Il salto **85.2% → ~0% fra 1 e 2 m** ha la firma di una **soglia geometrica**, non di un
degrado di sensibilità: un calo di SNR (∝1/D²) darebbe una curva morbida, non un crollo
di un fattore ~18 su un raddoppio di distanza.

Controllo di coerenza sugli ordini di grandezza (⚠️ *plausibilità, non misura*): se
l'ampiezza dell'oscillazione è ~10-15 cm — la `mdist_dev` del radar a 1 m è 10.4 cm, che
è un proxy **radiale** e non trasversale — allora perché la soglia cada fra 1 e 2 m
occorre θ fra ~3° e ~9°, compatibile con una cupola da 110° divisa in una ventina di zone.

#### Conseguenze

1. **In tesi la portata del PIR va sempre qualificata dal tipo di movimento.** La frase
   corretta non è "il PIR non arriva a 2 m", ma **"per movimento sul posto il PIR è cieco
   già a 2 m, pur rilevando un attraversamento alla stessa distanza"**
2. È la versione misurata di *«non "il PIR è scarso", ma "il PIR fa bene un lavoro che non
   è questo"»*, e rende la frase un dato invece di un'interpretazione
3. **Rilevanza DIPME**: una persona intrappolata si muove *sul posto*, non attraversa la
   stanza. Lo scenario del progetto cade esattamente nella condizione in cui la portata
   utile del PIR collassa — e la portata da datasheet, presa alla lettera, la
   sovrastimerebbe di metri
4. ⚠️ **Limite del controllo attuale**: `pir_jumper_attraversamento` è **1 solo trial, in
   L, con distanza non controllata** (nato per altro scopo). Convince come riscontro
   incidentale, è fragile come dato di tesi → **Test 1.5** del piano di test lo converte
   in una serie vera (2/3/5 m, jumper H, 3 trial)

## 3. Dati prodotti: 1 bit, e come interpretarlo

L'uscita è **un solo bit digitale** (OUT alto/basso). Tutta l'"intelligenza" è
nell'elettronica di condizionamento (tipicamente il chip BISS0001):

| Meccanismo | Effetto sul dato |
|---|---|
| Soglia sul segnale amplificato | sensibilità (potenziometro) |
| **Tempo di ritenuta** (hold) | OUT resta alto N secondi dopo l'ultimo trigger (potenziometro) |
| Modalità trigger L (single) | OUT va basso a fine ritenuta anche se il movimento continua |
| Modalità trigger H (repeat) | ogni nuovo movimento riarma la ritenuta (da usare nei test!) |
| Tempo di stabilizzazione | ~30-60 s all'accensione: uscita instabile, da scartare |

Implicazioni per il protocollo di test (già recepite in PIANO_TEST.md, Test 0.3):
- il tempo di ritenuta al MINIMO, altrimenti la "latenza di rilascio" misurata è
  il potenziometro, non il sensore
- modalità H, altrimenti una persona in movimento continuo appare intermittente
  (→ §3.1: è esattamente l'errore in cui è incorsa la fase 1, corretto il 22/08/2026)
- scartare il primo minuto di ogni acquisizione

Confronto informativo con il mmWave (obiettivo 2 in una riga): il PIR produce
**1 bit filtrato da isteresi**; il LD2410B produce **~20 valori** (stato, 2 distanze,
2+18 energie) a ogni frame. La tesi quantifica quanto quel divario informativo
si traduce in capacità di rilevamento.

### 3.1 Il jumper L/H: cosa cambia davvero, nel circuito e nei dati

Il jumper agisce su **una sola cosa** — cosa succede *dopo* un trigger — e non tocca
minimamente la capacità del sensore di *vedere*. Da qui discende tutto il resto,
compresa la correzione del 22/08/2026 su `movimento_1m`.

#### Cosa fa fisicamente

L'elemento piroelettrico genera un impulso ogni volta che il flusso IR **cambia**.
Quell'impulso entra nel **BISS0001**, che lo trasforma nel bit su OUT. Il jumper
seleziona il modo del timer interno del chip (pin di *retrigger*):

| | **L** — *single / non-retriggerable* | **H** — *repeat / retriggerable* |
|---|---|---|
| primo trigger | OUT sale, parte il timer di ritenuta Tx | OUT sale, parte il timer Tx |
| trigger successivo **mentre OUT è alto** | **ignorato** | **riazzera Tx** → OUT resta alto |
| fine di Tx | OUT scende, poi *block time* ~2.5 s in cui i trigger sono inibiti | OUT scende solo dopo Tx secondi **senza** movimento |

Tx è il trimmer di ritenuta, che nei nostri test è al minimo: **~3.5 s misurati**.

Cronogramma con movimento continuo (ogni `x` è un trigger del piroelettrico):

```
trigger   x  x x   x  x x  x   x x  x  x x   x  x x  x
L        ▔▔▔▔▔▔▔___▁▁▁▔▔▔▔▔▔▔___▁▁▁▔▔▔▔▔▔▔___▁▁▁▔▔▔▔▔
          3.5 s   blocco  3.5 s  blocco  3.5 s
H        ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
          un solo impulso, lungo quanto il movimento
```

In **L** l'uscita è dunque un **monostabile a durata fissa**: qualunque cosa accada,
l'impulso dura Tx. È esattamente ciò che si misura — **195 impulsi in modalità L,
media 3.46 ± 0.09 s, nessuno oltre 5 s** (su tre sessioni indipendenti).

#### Cosa cambia nei dati

Il punto chiave: **in L `pir_rate_%` non misura la presenza, misura il numero di
eventi**. In prima approssimazione

```
pir_rate(L)  ≈  N_eventi × Tx / T_trial
```

e ha un **tetto strutturale**: con Tx = 3.5 s e block time 2.5 s, anche con movimento
infinitamente denso l'uscita non può stare alta più di 3.5/(3.5+2.5) ≈ **58%** del
tempo. Un PIR in L **non può mai** dare 100%, per costruzione. Quindi l'80.5% di falsi
negativi misurato a 1 m in L non era una misura di cecità del sensore: era in buona
parte il formato dell'uscita.

In **H** gli impulsi si concatenano e la grandezza torna a significare "frazione di
tempo in cui c'è movimento rilevato":

| scenario | L | H |
|---|---|---|
| 1 m, cammino sul posto | `pir_rate` **19.5%** — 1-4 impulsi da 3.6 s | `pir_rate` **85.2%** — 6 impulsi completi da 14.1 s in media, più 5 troncati, il più lungo **≥ 61.6 s** (l'intero trial) |
| sotto il banco, micro-movimenti | 35.9% | **96.5%** |
| immobile a 2.3 m | 0.22% | *(equivalente)* |
| stanza vuota | 0% | 0% |

#### La regola che salva i dati della fase 1

> **Il jumper agisce solo *dopo* un trigger. Dove i trigger sono zero, L e H sono
> indistinguibili.**

Da qui la partizione della campagna:

- **Intatti, senza asterischi** — tutti gli scenari in cui il PIR ha prodotto zero o
  pochissimi impulsi *isolati*: immobile a 2.3 m (99.78% FN), sotto il banco immobile
  (99.90%), movimento a 2-5 m (100%), stanza vuota. Non c'è nulla da riazzerare se il
  timer non parte mai. La verifica diretta lo conferma: `sotto_banco_immobile` rifatto
  in H dà **1.32%** contro **0.10%** in L — cambia il terzo decimale, non la conclusione
- **Da rifare, e rifatti** — gli unici due scenari con eventi *ripetuti durante
  movimento continuo*: `movimento_1m` e `sotto_banco_movimenti`

#### Come va interpretato in tesi

L'inquadramento corretto non è "in L il PIR va male", ma: **in L la grandezza
`pir_rate` non è la grandezza che si crede di misurare**. Confonde due cose diverse —
quanto spesso il sensore si accorge di qualcosa, e per quanto tempo il chip tiene alta
l'uscita dopo essersene accorto. Tre conseguenze pratiche:

1. **Il confronto va fatto in H**, perché è la configurazione *migliore* del PIR. Così
   l'argomento diventa inattaccabile: il PIR perde nella sua condizione ottimale, non
   perché mal configurato. È la struttura dell'esperimento centrale (1 m, H, stessa
   postura, cambia solo il movimento): **85.20% → 1.52%**
2. **La metrica invariante rispetto al jumper è il numero di fronti di salita**, non la
   percentuale di tempo alto: gli eventi/ora non dipendono né dal jumper né dal trimmer,
   la percentuale dipende da entrambi. Per confrontare serie acquisite in configurazioni
   diverse, usare i fronti
3. **Ribaltamento utile per DIPME**: H + ritenuta al massimo farebbe *sembrare* il PIR
   ottimo — l'uscita resterebbe alta per minuti dopo l'ultimo movimento. Ma sarebbe
   **persistenza, non rilevamento**: il sensore racconterebbe il passato. Per un sistema
   salvavita che deve dire "questa persona è ancora lì *adesso*", un latch lungo è peggio
   di un limite dichiarato. È anche la risposta all'obiezione prevedibile della
   commissione ("bastava alzare la ritenuta")

#### Cosa il jumper *non* cambia mai

La cecità alla persona immobile. Quella è la fisica del §1: l'elemento risponde alla
**derivata** del flusso IR, e un corpo fermo dà derivata nulla. Nessuna impostazione del
BISS0001 può inventare un impulso che il sensore non ha generato — il jumper
ridistribuisce nel tempo i trigger esistenti, e se sono zero resta zero.

È il motivo per cui i due risultati portanti della tesi — **98.48%** di falsi negativi
da fermo a 1 m e **98.68%** sotto il banco, **entrambi in H** — non sono un artefatto di
configurazione ma una proprietà del principio di misura.

## 4. Sensibilità alla temperatura ambiente

Il segnale utile è il **contrasto termico** tra corpo e sfondo. A 20°C di ambiente
il contrasto è ~14°C; a 30-32°C (estate, aula assolata) scende a 2-4°C → segnale
più debole, portata ridotta, più falsi negativi. Sopra ~35°C il contrasto può
addirittura invertirsi.

→ per questo ogni sessione di test registra la temperatura (REGISTRO_SESSIONI.md)
e il confronto mattina/pomeriggio sul Test 1.3 è un risultato extra a costo quasi zero.

Altre fonti note di falsi positivi PIR da tenere fuori dal setup: correnti d'aria
calda/fredda (condizionatori, termosifoni), animali, sole diretto attraverso vetri
(il vetro blocca l'IR del corpo ma il riscaldamento solare degli oggetti no).

## 5. Chi lo usa e perché domina (obiettivo 1)

Il PIR è il sensore di presenza più diffuso al mondo: luci automatiche, antifurti,
citofoni video, termostati. Le ragioni sono i suoi tre numeri imbattibili:
**~50 µA, ~1-3 €, zero elaborazione richiesta** — più l'assenza totale di emissioni
(passivo) che semplifica certificazioni e privacy.

Nel progetto DIPME: il **DIPME-DEVICE monta un PIR** proprio per questi motivi
(veglia a batteria per anni). Il limite emerge esattamente nello scenario d'emergenza:
la persona rifugiata sotto il banco è tipicamente **ferma** — il caso cieco del PIR.
Da qui la domanda di tesi: il mmWave può coprire questo buco, e a che costo (energia,
complessità)?

## 6. Modello in dotazione: HC-SR501 ✔ (identificato dalle foto, 15/07/2026)

Foto in `PIR HC-SR501/`. Elementi verificati visivamente sul modulo:
- chip di condizionamento **BISS0001** (serigrafia leggibile) — conferma l'analisi §3
- regolatore lineare **7133** (HT7133, LDO 3.3V): il modulo accetta tensioni alte in
  ingresso ma internamente lavora a 3.3V → **uscita OUT a 3.3V, sicura per i GPIO ESP32**
- **2 trimmer arancioni** (sensibilità/portata e tempo di ritenuta)
- **jumper giallo** per la modalità trigger presente (variante completa: L/H selezionabile)
- header 3 pin (VCC / OUT / GND — verificare la serigrafia sul lato saldature
  prima di collegare: nei cloni l'ordine può variare)
- lente di Fresnel a cupola multi-segmento (~23 mm)

### Specifiche da datasheet

| Campo | Valore |
|---|---|
| Modello | HC-SR501 (base BISS0001 + LHI778) |
| Tensione di alimentazione | DC 4.5–20 V → **collegare a VIN 5V dell'ESP32** |
| Livello logico uscita | alto 3.3 V / basso 0 V (regolatore HT7133 a bordo) ✔ compatibile ESP32 |
| Corrente di riposo | **< 50 µA** → aggiornata ANALISI_CONSUMI.md |
| Portata | 3–7 m (regolabile col trimmer sensibilità) — ⚠️ **condizione di prova non dichiarata dal datasheet**: vale per l'attraversamento del campo, non per il movimento sul posto (→ §2.1) |
| Angolo | cono < 110° (vs ±60° del LD2410B: il PIR copre PIÙ largo) |
| Ritenuta (time delay) | regolabile ~3 s → ~5 min (trimmer tempo) |
| Tempo di blocco (block time) | 2.5 s default (dopo il rilascio l'uscita è inibita) |
| Trigger | jumper: L = singolo, **H = ripetibile (da usare nei test)** |
| Temperatura operativa | -15…+70 °C |
| Dimensioni PCB | 32 × 24 mm |

### Configurazione per i test (da fare al Test 0.3)
1. Jumper in posizione **H** (repeat trigger)
2. Trimmer tempo di ritenuta al **minimo** (~3 s) — antiorario a fondo corsa
3. Trimmer sensibilità a **metà corsa** (annotare la posizione con una foto,
   va tenuta identica per tutta la campagna)
4. Ricordare: ~60 s di stabilizzazione all'accensione + **block time di 2.5 s**
   dopo ogni rilascio — il block time è un dettaglio in più da citare nell'analisi
   della latenza (Test 2.1: se il PIR ha appena rilasciato, per 2.5 s è cieco per
   costruzione)

### Nota per il confronto (obiettivo 3)
L'angolo più ampio del PIR (110° vs 120° del datasheet a seconda della fonte, contro
i ±60°=120° nominali ma direttivi del radar) va tenuto presente nel setup affiancato:
i due sensori vanno orientati sullo stesso volume di test, con la zona di prova
dentro il campo di ENTRAMBI.

## 7. Cosa entra nella tesi da questo documento

- Cap. studio sensori (ob. 1): §1-2-3 (principio, Fresnel, dati) + §5 (applicazioni)
- Cap. confronto (ob. 3), **portata**: §2.1 — perché 3-7 m dichiarati e 0% misurato a 2 m
  non sono in contraddizione, con il controllo per attraversamento. Da citare vicino alla
  tabella del Test 1.2, è la risposta all'obiezione "il vostro PIR era guasto"
- Cap. confronto (ob. 3), **metodo**: §3.1 (jumper L/H) — giustifica perché il confronto
  è condotto in modalità H e perché i risultati sulla persona immobile acquisiti in L
  restano validi. Da citare nella sezione sui limiti di validità del protocollo
- Cap. confronto (ob. 3): §1 come spiegazione *a priori* del risultato del Test 1.3
  ("il PIR non ha fallito: ha funzionato esattamente come la sua fisica prevede")
- Cap. consumi (ob. 4): §6 con i numeri del modello reale
- Limiti/validità: §4 (temperatura) collegato al registro sessioni

## Fonti

- **Datasheet HC-SR501** (specifiche elettriche, trigger, block time):
  https://www.electronicoscaldas.com/datasheet/HC-SR501.pdf (mirror del datasheet
  del produttore; altra copia: https://www.mpja.com/download/31227sc.pdf)
- **Datasheet BISS0001** (chip di condizionamento, principio differenziale):
  mirror Adafruit: https://cdn-shop.adafruit.com/datasheets/BISS0001.pdf
- **Components101 — HC-SR501 PIR Sensor** (pinout, trimmer, modalità H/L):
  https://components101.com/sensors/hc-sr501-pir-sensor
  ⚠ riporta "65 mA" di corrente di riposo: refuso per µA — fa fede il datasheet (<50 µA)
- **Adafruit — PIR Motion Sensor guide** (principio piroelettrico e lente di Fresnel,
  riferimento autorevole per §1-2): https://learn.adafruit.com/pir-passive-infrared-proximity-motion-sensor
- Identificazione del modulo: foto del modulo fisico in `PIR HC-SR501/` (15/07/2026)
