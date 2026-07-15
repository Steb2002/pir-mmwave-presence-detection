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
- scartare il primo minuto di ogni acquisizione

Confronto informativo con il mmWave (obiettivo 2 in una riga): il PIR produce
**1 bit filtrato da isteresi**; il LD2410B produce **~20 valori** (stato, 2 distanze,
2+18 energie) a ogni frame. La tesi quantifica quanto quel divario informativo
si traduce in capacità di rilevamento.

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

Nel progetto UPRISE: il **DIPME-DEVICE monta un PIR** proprio per questi motivi
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
| Portata | 3–7 m (regolabile col trimmer sensibilità) |
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
