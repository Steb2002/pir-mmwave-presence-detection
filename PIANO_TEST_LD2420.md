# Piano di test del LD2420 — campagna parallela a quella del LD2410B

Documento gemello di [PIANO_TEST.md](PIANO_TEST.md), dedicato al secondo radar.
Stesse convenzioni: `data/<scenario>_T<numero>.csv`, 5 trial per scenario dove non
indicato diversamente, sessioni annotate in `data/REGISTRO_SESSIONI.md`.

Scritto il 26/08/2026 dopo la lettura della documentazione ufficiale
(`HLK-LD2420/Documentazione/`: manuale V1.2 + Protocol Document).

---

## 0. Cosa va rifatto e cosa no

L'impressione che "vada rifatto tutto" è comprensibile ma sbagliata. La campagna del
LD2410B ha prodotto tre categorie di risultati, e solo una dipende dal radar:

| categoria | esempi | va rifatta col LD2420? |
|---|---|---|
| **Proprietà del PIR** | jumper H/L, impulsi da 3,46 s, curva dose-risposta del PIR, cecità alla persona immobile | ❌ **No.** Il PIR non c'entra col radar. E nelle nuove sessioni viene registrato comunque, gratis |
| **Il risultato centrale della tesi** | PIR 98,5% di falsi negativi su persona immobile vs radar 0% | ❌ **No.** È già dimostrato. Il LD2420 semmai aggiunge un secondo punto di conferma |
| **Proprietà del radar** | distanza, latenze, selettività, due persone, falsi positivi | ✔ **Sì**, sono le uniche da ripetere |

Quindi: **10 test radar da rifare**, non 25. E costano meno della prima volta, perché
protocollo, script di acquisizione, script di analisi e convenzioni di scarto del
transitorio sono già scritti e validati — la prima campagna è servita anche a costruire
gli strumenti.

⚠️ **Tre test NON sono replicabili sul LD2420**, e il motivo è esso stesso un risultato
da mettere in tesi, non un buco:

1. **Distanza su bersaglio fermo** — il manuale §8 dice che il modulo *"does not support
   proximity ranging for stationary bodies"*. Tutto ciò che nel Test 1.3 e 1.4 riguarda
   `stationary_distance_cm` non ha equivalente
2. **Separazione moving/still** — il LD2420 ha **un solo canale**. Il Test 2.5, che sul
   LD2410B ha prodotto "un bersaglio per canale", qui misura una cosa diversa: quanto si
   perde avendone uno solo
3. **Respiro e indice di vitalità** — richiedono la serie temporale dell'energia per-gate,
   che l'interfaccia documentata non trasmette (Fase 4-2420, opzionale e non ufficiale)

---

## 0-bis. 🔴 CAMPAGNA RIDOTTA ENTRO 2 m (decisione 05/09/2026)

**Contesto.** L'esemplare in nostro possesso vede una persona **solo fino a ~2 m**
(diagnosi completa in CLAUDE.md e nel registro, sessioni 03-04/09/2026). Il professore,
informato per mail, ha risposto di **riportare in tesi esattamente i test fatti e i
risultati ottenuti**, problemi e limitazioni compresi. Non chiede di sostituire il modulo
prima di scrivere.

**Decisione conseguente**: invece di sospendere la Fase 4, si esegue la campagna
**dentro la zona in cui il modulo funziona**, cioè da 0,5 a 2 m. Non è un ripiego: è il
perimetro sperimentale onesto di questo esemplare, e va dichiarato come tale in tesi
esattamente come i 5 m della stanza sono il perimetro del LD2410B.

### Regole della campagna ridotta
1. **Modalità binaria (energy)** obbligatoria — `firmware/ld2420_logger_bin/`. L'ASCII è
   inutilizzabile (2528 `ON` e 0 `OFF` in 4 min, stanza vuota inclusa) e OT2 a
   configurazione di fabbrica non rilascia mai
2. **Gate massimo 6** e **soglie tarate col tool** (`ld2420_config_tarato_max_6.xml`).
   Con gate 8 il muro a ~5 m tiene la presenza attiva e ogni misura di rilascio salta.
   ⚠️ È una **deroga dichiarata** alla parità di configurazione del §1.3: il LD2410B è
   stato caratterizzato a soglie di fabbrica, il LD2420 no perché **a soglie di fabbrica
   non rilascia**. La deroga è essa stessa un risultato da riportare
3. **Ogni numero va attribuito all'esemplare, non al modello.** Formula da usare in tesi:
   *"sull'esemplare in prova, entro la sua portata utile di ~2 m"*
4. **Verificare `BUILD n` e `frames_ok`** all'avvio di ogni sessione: tre giri di prove
   sono già stati persi su un binario vecchio e su un cavo OT1 sganciato
5. Se arriva un **secondo esemplare**, questa stessa campagna si ripete tal quale in
   metà tempo e diventa un confronto esemplare-vs-esemplare: la variabilità fra unità di
   uno stesso modello è un risultato di tesi, non tempo perso

### Cosa entra e cosa esce

| test LD2410B | distanza originale | nella campagna ridotta | perché |
|---|---|---|---|
| 1.1 stanza vuota | — | ✔ **invariato** | il tempo non c'entra con la portata; con gate 6 il modulo rilascia |
| 1.2 distanza nota | 1-5 m | ⚠️ **0,5 / 1 / 1,5 / 2 m** | 4 punti invece di 5; basta per la retta *dentro* la zona utile |
| 1.3 immobile | 2,3 m | ⚠️ **1 m** (+ 1,5 m come estensione) | 2,3 m è fuori portata. 1 m e non 1,5: è il gate con più margine **e** l'unica distanza con un dataset LD2410B gemello (`fermo_1m_H`) — vedi protocollo esecutivo |
| 1.4 sotto il banco | ~0,6 m | ✔ **fatto 09/09**: immobile 98,4 %, micro-movimenti 100 % | un rilascio di 24 s in 1 trial su 5 da immobile |
| 1.5 attraversamento | 2-5 m | ❌ escluso | è un test del **PIR**, già chiuso, e il radar lì fa solo da testimone |
| 2.1 latenza ingresso | porta ~4-5 m | ⚠️ **doppia versione** (vedi nota) | il confronto col LD2410B non sarebbe appaiato |
| 2.2 rilascio | 1 m | ✔ **invariato**, doppio (ritardo 5 e 30) | chiude anche l'unità del parametro di ritardo |
| 2.3 dose-risposta | 1 m | ✔ **invariato** — 🎯 il più prezioso | tre sensori sulla stessa scala di movimento |
| 2.4 selettività | 1 m asse + 3 m + 90° | ⚠️ **solo 1 m asse e 1 m a 90°** | lo scenario a 3 m darebbe 0 % per portata, non per selettività: non discrimina |
| 2.5 due persone | 2 m + 4 m | ⚠️ **1 m + 2 m** | riscalato; serve la seconda persona |
| 2.6 gate minimo | — | ✔ **1 m escluso vs 2 m visto** | test nuovo, possibile solo su questo modulo |
| misura angolare | arco r = 1 m | ✔ **invariata** — 🎯 molto informativa | il LD2410B copre ±90°; qui il fascio sembra assai più stretto |
| Fase 3 ostacoli | 3 m radar / 1 m PIR | ✔ **1 m** — 🎯 fatta 09/09 | vedi §0-ter: attenuazioni in dB, cartongesso 0,7 dB, stessa graduatoria del LD2410B |
| Fase 5 respiro | 2 m | ✔ **tentativo a 1 m fatto 09/09**: 1/3 col criterio a 2 gate, fermata al primo blocco | vedi §FASE 5-2420: non satura, ma la persona sta in 2 gate soli e l'SNR max è 6× |
| Fase 6 vitalità | deriva da 2.3 | ✔ ricalcolabile dagli stessi CSV | nessuna acquisizione in più |
| Fase 8 portata massima | 8 m | ❌ **già fatta, l'esito è ~2 m** | è il risultato, non un test mancante |

⚠️ **Test 2.1, avvertenza da non dimenticare**: sul LD2410B la latenza d'ingresso è
misurata mentre il soggetto rientra dalla porta, e il radar lo aggancia *in
avvicinamento*, a diversi metri. Qui il LD2420 non può agganciarlo prima dei 2 m, quindi
una latenza più alta sarebbe **un effetto della portata, non della reattività**. Due
letture possibili, e vanno tenute separate:
- **latenza fuori scatola** (stesso protocollo del LD2410B, evento = rientro dalla porta):
  confrontabile *come comportamento di sistema*, non come reattività del rivelatore
- **latenza appaiata** (evento = attraversamento di una tacca a 1,5 m, dentro la portata
  di entrambi): è quella da usare per dire "quale dei due reagisce prima"

Acquisire **entrambe** costa 20 minuti in più ed evita una conclusione sbagliata.

### Ordine di esecuzione consigliato

| # | blocco | ore | nota |
|---|---|---|---|
| 1 | 1.3 a **1 m** (immobile) + estensione 1,5 m | 1,0 | 🔴 punto di decisione: se non vede la persona ferma, il resto è accademico |
| 2 | 2.3 dose-risposta a 1 m | 1,0 | il grafico a tre sensori |
| 3 | 1.2 a 0,5/1/1,5/2 m | 1,25 | accuratezza dentro la zona utile |
| 4 | 1.4 sotto il banco | ✔ 1,3 h | scenario DIPME |
| 5 | misura angolare a 1 m | 1,0 | confronto col ±90° del LD2410B |
| 6 | 2.2 rilascio (×2) + 2.6 gate minimo | 1,25 | chiude l'unità del ritardo |
| 7 | 2.4 selettività (2 scenari) + 2.1 (2 varianti) | 1,25 | |
| 8 | 1.1 stanza vuota | notturna | non presidiata |
| 9 | 2.5 due persone | 0,75 | serve 2ª persona |
| 10 | Fase 3-2420 ostacoli a 1 m | ✔ fatta | vedi §0-ter |
| 11 | Fase 5 respiro a 1 m (opzionale) | ✔ 20 min | criterio di abbandono applicato al primo blocco |
| | **totale** | **~9,5 h** | + 1 notturna |

---

## 0-ter. L'unica cosa che il LD2420 misura MEGLIO del LD2410B: l'attenuazione in dB

Richiesta del professore (mail del 05/09/2026): *"capire rispetto al materiale se e
quanto viene attenuato"*. Sul LD2410B questa domanda **non ha risposta pulita**:
`menergy` è un indice normalizzato 0-100 con elaborazione interna, e le nostre
percentuali (−7,5 % plastica … −41,6 % legno) sono in unità dello strumento, non
convertibili in dB (avvertenza già in CLAUDE.md).

Sul LD2420 la situazione è diversa: le energie per-gate sono **uint16 grezzi** e il tool
ufficiale le mostra come **dB = 10·log₁₀(grezzo)** — corrispondenza che abbiamo validato
su tutti e 32 i parametri di soglia. Quindi il grezzo si comporta come una grandezza
**proporzionale alla potenza ricevuta**, e il rapporto fra due misure È esprimibile in dB:

```
attenuazione_dB = 10 · log₁₀( E_senza_ostacolo / E_con_ostacolo )
```

⚠️ **Ipotesi dichiarata, non specifica ufficiale**: Hi-Link non documenta la natura del
campo energia. Il 10·log₁₀ del tool e i moltiplicatori di rumore del manuale (trigger 5×,
hold 3,5×, applicati in lineare) sono indizi concordi, non una definizione. In tesi va
scritto come assunzione, con questo ragionamento a supporto.

⚠️ **Limite di dinamica del nostro esemplare**: a 1 m il gate 2 passa da ~20 (rumore) a
~90 (persona), cioè appena **~6,5 dB** di margine utile. Materiali che attenuano più di
~6 dB porteranno il segnale sotto il rumore e daranno solo *"attenuazione > 6,5 dB"*.
Quindi il metodo quantifica bene gli attenuatori deboli (plastica, cartone, vetroresina)
e satura sui forti (vetro, legno, metallo). **Dirlo prima di acquisire**, non dopo.

**Protocollo**: identico alla Fase 3 (pannello a ~20 cm dal sensore, soggetto in
movimento sul posto), ma soggetto a **1 m** e metrica = energia del **gate 2** grezza,
mediata sui campioni utili; baseline mediata su inizio **e** fine sessione.
Criterio di abbandono: se la baseline oscilla di più di 3 dB fra inizio e fine, la misura
non regge e va chiusa.

### ✅ ESITO (09/09/2026) — 27 file `ost2420_*`, 3 trial × 60 s utili per materiale

Baseline mediata su 6 trial (inizio 41,8, fine 37,3): **39,5 ± 2,7**, deriva **0,49 dB**
→ sessione valida. Fondo del gate 2 a vuoto: 13. Controllo col metallo: gate 2 a **11,0**,
cioè al fondo, nessun residuo → l'aggiramento è sotto soglia e il pavimento della misura è
il fondo stesso. Dinamica disponibile 39,5/13 = **4,8 dB**.

| materiale | spessore | gate 2 media | att. grezza `10·log₁₀(E₀/E)` | att. netta (fondo sottratto) | hold superato | LD2410B (30/08, %) |
|---|---|---|---|---|---|---|
| nessuno | — | 39,5 ± 2,7 | — | — | 25-33 % | — |
| plastica (tanica) | 2×5 mm + aria | 36,3 ± 11,3 ⚠️ | **0,4 dB** (1,3 senza T01) | 0,6 | 15-38 % | −7,5 |
| **cartongesso** | **10 mm** | 33,7 ± 2,7 | **0,7 dB** | 1,1 | 17-24 % | *non provato* |
| cartone (scatola) | 2×5 mm + aria | 31,3 ± 1,0 | **1,0 dB** | 1,6 | 17-22 % | −17,2 |
| vetroresina | 1 mm | 31,5 ± 1,9 | **1,0 dB** | 1,6 | 15-23 % | −19,6 |
| vetro | 5 mm | 22,6 ± 1,3 | **2,4 dB** | 4,4 | 7-10 % | −40,9 |
| legno | 10 mm | 15,4 ± 1,9 | **4,1 dB** (al fondo) | > 9 | **0-1 %** | −41,6 |
| metallo | 1 mm | 11,0 ± 2,1 | **5,5 dB** = limite | > 9 | 0 % | blocca |

- 🔑 **La graduatoria è identica a quella del LD2410B** (plastica < cartone ≈ vetroresina
  < vetro < legno < metallo), misurata con due moduli, due distanze e due unità diverse:
  è la conferma più forte che le percentuali del 30/08 ordinavano davvero i materiali
- 🔑 **Il cartongesso attenua come plastica e cartone**, non come vetro e legno: la
  parete tipica di un'aula non è un ostacolo per il radar. È la risposta alla seconda
  domanda del professore, nell'unità che chiedeva
- ⚠️ **Legno e metallo sono al fondo**: 4,1 e 5,5 dB grezzi sono **limiti inferiori**
  (la dinamica dell'esemplare si esaurisce lì); l'attenuazione netta dice solo "> 9 dB".
  Con un esemplare sano (accoppiamento ~12000 al gate 0 contro 110) la scala misurabile
  sarebbe di ~20 dB più ampia
- ⚠️ **La presenza non è una metrica qui**: 100 % con ogni materiale, metallo compreso,
  per il ritardo di 30 s e le code dei gate 1-2 (Test 2.2). Ma gli **hold del gate 2**
  dicono cosa farebbe il modulo a regime: attraverso **legno da 10 mm** trigger e hold
  non vengono mai superati a 1 m → questo esemplare **non acquisirebbe** la persona,
  dove il LD2410B a 3 m restava al 100 %. Per DIPME: l'incasso nell'arredo in legno,
  ammesso dal LD2410B, non lo è per questo LD2420
- Col metallo il **gate 4 sale da 8 a 22** (riflessione multipla?) mentre i gate 0-1
  restano a vuoto: un riflettore fermo a 20 cm non compare nel proprio gate, coerente
  con un canale che misura variazione e non ampiezza. `dist_raw` stantia ovunque; col
  legno riporta 8/20/20 cm, cioè il pannello
- Coperture angolari diverse come il 30/08 (cartongesso 80×120 cm in verticale, ±63°
  orizzontali a 20 cm): tutte le attenuazioni restano **limiti inferiori**. Il confronto
  più pulito è cartone vs legno (stessa larghezza, ±54°): 1,0 contro ≥ 4,1 dB
- Formula dell'attenuazione **netta**: `10·log₁₀((E₀−13)/(E−13))`, assume fondo additivo
  non attenuato dal pannello (il metallo lo conferma: 11 ≈ 13). Riportare entrambe

---

## 1. Decisioni di metodo, da prendere prima di acquisire

### 1.1 🔴 Mai i due radar accesi insieme
Lavorano entrambi a 24 GHz e si disturbano. **Un radar alla volta.** Il confronto si fa
ripetendo gli stessi scenari in sessioni separate, non in simultanea. Il PIR è passivo e
può restare collegato sempre.

### 1.2 🔑 Un solo schema CSV per tutta la tesi
Il logger del LD2420 deve emettere **le stesse 9 colonne** del logger del LD2410B, così
`acquire.py`, `serie.py` e `analizza_test.py` funzionano senza modifiche. Mappatura:

| colonna | LD2410B | LD2420 |
|---|---|---|
| `radar_presence` | presenza | presenza (`ON`/`OFF`) |
| `moving_target` | bersaglio in movimento | **= presenza** (canale unico) |
| `stationary_target` | bersaglio fermo | **0 fisso** |
| `moving_distance_cm` | distanza movimento | `Range` convertito (vedi Test 0.5-bis) |
| `stationary_distance_cm` | distanza fermo | **0 fisso** (non esiste) |
| `moving_energy` | energia movimento | **0** in ASCII |
| `stationary_energy` | energia fermo | **0** in ASCII |
| `pir_presence` | PIR | PIR |

⚠️ Le colonne a 0 fisso **non sono dati mancanti per sbaglio**: sono l'assenza documentata
di quella grandezza. Vanno dichiarate come tali in tesi, non presentate come zeri.

### 1.3 ⚖️ Parità di configurazione
Il LD2410B è stato caratterizzato **a soglie di fabbrica**, senza mai ricalibrare. Stessa
regola qui: si acquisisce con la configurazione di fabbrica del nostro esemplare
(`GateMax=12`, `ObjectDisappearDelayTime=30`, soglie del backup XML), che coincide con i
valori d'esempio del Protocol Document.

**Unica eccezione, e va dichiarata**: il ritardo di scomparsa. Il LD2410B ha timeout 5 s,
il LD2420 ne ha 30 di fabbrica. Confrontare le latenze di rilascio così sarebbe scorretto.
Il Test 2.2-2420 si esegue quindi **due volte**: a 5 (appaiato al LD2410B) e a 30
(comportamento fuori scatola).

### 1.4 Portata e geometria
Il LD2420 dichiara 8 m contro i ~6 m del LD2410B, ma la **stanza resta quella**: i test di
distanza arrivano a 5 m come prima. Il limite è logistico, già dichiarato come perimetro
sperimentale nel cap. 4 — non va riaperto qui.

---

## FASE 0-2420 — Preparazione

### Test 0.5 — Lettura di firmware e parametri (già in PIANO_TEST.md, ora eseguibile)
- **Serve per**: sapere cosa stiamo caratterizzando; la versione va in tesi
- Due strade, fare **entrambe** e confrontare (sul LD2410B il tool PC diede valori
  sbagliati e la verità venne dall'UART — vedi CLAUDE.md):
  - **tool PC**: LD2420 → CH340E → PC, `HLK-LD2420_TOOL - English`, baud 115200
  - **via UART**, sketch nuovo `firmware/test05_ld2420_info/`: comando `0x00` per la
    versione, poi `0x08` per rileggere `GateMax` (0x01), ritardo (0x04) e le 32 soglie
    (0x10-0x1F trigger, 0x20-0x2F maintain), come da Protocol Document
- **Esito atteso**: versione ≥ 1.5.3 (dedotta dal baud 115200 già osservato); soglie
  coincidenti col backup XML, cioè con l'esempio ufficiale
- 🔑 **Verifica utile**: il tool mostra le soglie in **dB = 10·log₁₀(grezzo)**. Se via UART
  leggi 60000 e il tool mostra 47,78, la corrispondenza è confermata sull'esemplare
- ✔ **Annotato (02/09/2026)**: firmware = **v1.6.1**, GateMax = **12**, ritardo = **30 s**,
  32 soglie lette via UART e coincidenti con l'XML di fabbrica (conversione dB→grezzo
  validata su tutti i parametri)

### Test 0.5-bis — 🔴 Taratura dell'unità del campo `Range` (BLOCCANTE)
- **Serve per**: qualunque test di distanza. Senza questo il Test 1.2-2420 non è
  interpretabile
- **Il problema**: leggiamo valori 7-37 camminando per la stanza. ESPHome dichiara
  centimetri (incompatibile: sarebbero 7-37 cm), i decimetri tornerebbero (0,7-3,7 m), ma
  **nessuno dei due documenti ufficiali definisce l'unità**
- **Procedura**: nastro a 1, 2, 3, 4, 5 m. Per ogni segno, stare in piedi e camminare sul
  posto 60 s, registrando il `Range` grezzo. Cinque punti bastano
- **Analisi**: regressione `Range_grezzo` vs distanza reale. Il coefficiente angolare dice
  l'unità: ~10 per metro = decimetri, ~100 = centimetri, ~1,43 = gate da 70 cm
- ⚠️ Se la relazione **non è lineare**, il campo non è una distanza e va trattato come
  indicatore ordinale. Sarebbe un risultato negativo pubblicabile, non un fallimento
- **Esito**: fattore di conversione = ______ → da cablare nel logger

### Test 0.6-2420 — Logger CSV
- Scrivere `firmware/ld2420_logger/ld2420_logger.ino`: Serial2 a 115200 su GPIO16/17,
  parsing delle righe ASCII, PIR su GPIO34, emissione CSV a **5 Hz** con le 9 colonne di §1.2
- ⚠️ **Perché 5 Hz e non 10**: il modulo aggiorna a 10 Hz, ma l'ASCII è asincrono (non
  emette una riga per campione). Campionare a 5 Hz lo stato corrente mantiene la cadenza
  identica al LD2410B, che è ciò che rende i due dataset confrontabili. I 10 Hz nativi
  servirebbero solo alla FFT del respiro, che qui non è in gioco
- **Verifica**: `python analisi/verifica_engineering.py` su un CSV di prova → cadenza
  5,00 Hz, jitter ~0, nessuna colonna mancante
- **Esito atteso**: `radar_presence` a 1 quando ti muovi davanti al sensore

### Test 0.7-2420 — Il pin OT2 serve davvero?
- **Serve per**: obiettivo 4 e architettura DIPME. Sul LD2410B abbiamo dimostrato che il
  pin OUT coincide con la presenza in 1699/1699 campioni, cioè un nodo a basso consumo può
  fare a meno dell'UART
- Collegare OT2 a un GPIO libero, loggarlo come colonna extra per una sessione di 10 min
- **Esito atteso**: OT2 == `radar_presence`. Se coincide, stessa conclusione del LD2410B

**Costo Fase 0**: ~2,5 h, di cui buona parte è scrittura di firmware.

---

## FASE 1-2420 — Caratterizzazione

### Test 1.1-2420 — Stanza vuota (falsi positivi)
- **Metrica**: eventi/h di falso positivo, con limite superiore alla regola del tre (3/T)
- Una sessione **notturna** (stanza vuota, porta chiusa, ~7 h) + 30 min diurni
- ⚠️ Sospendere gli aggiornamenti di Windows (il 20/08/2026 un riavvio troncò una notturna)
- **Confronto atteso**: il LD2410B ha dato **0 eventi, limite 95% ≤ 0,43 eventi/h**. Per
  ottenere un limite confrontabile serve un tempo di osservazione simile: una notte
- **Analisi**: `analizza_test.py data\stanza_vuota_2420_*.csv`

### Test 1.2-2420 — Distanze note 1-5 m — 🎯 il test più importante della campagna
- **Metrica**: accuratezza della distanza, tasso di rilevamento
- **Perché conta**: il manuale dichiara **±0,35 m**; sul LD2410B abbiamo misurato una retta
  con R² = 0,99965 e residui ≤ 4,9 cm. È un ordine di grandezza di differenza, ed è **la
  ragione principale per cui il progetto sceglie un modulo invece dell'altro**
- Procedura identica al Test 1.2 originale: 5 distanze × 5 trial, 80 s per trial
  (20 di transitorio + 60 utili), camminata sul posto, soggetto in piedi
- Comando:
  ```powershell
  .venv\Scripts\python.exe serie.py --scenario mov2420_2m --gt-state moving
  ```
- **Analisi**: `python ..\analisi\analizza_test.py data\mov2420_*.csv --salta-inizio 20`
- **Da produrre**: la stessa regressione del LD2410B, sovrapposta nello stesso grafico.
  Due rette sullo stesso piano valgono più di due tabelle

### Test 1.3-2420 — Persona seduta immobile a 2,3 m — 🎯 il test che decide tutto
- **Metrica**: tasso di rilevamento su soggetto **immobile** (non la distanza: non esiste)
- **La domanda**: il LD2420 vede la persona ferma? La soglia *maintain* è definita dal
  manuale come "sensitivity for detecting human micro-movements and maintaining the
  presence of a person", quindi **dovrebbe**. Ma è una lettura del manuale, non una misura
- 5 trial × 302 s, stessa postura e stessa distanza del Test 1.3 originale
- **Confronto atteso**: LD2410B `fn_radar = 0,00 ± 0,00 %`
- ⚠️ **Se il LD2420 fallisce qui, la campagna può fermarsi**: un sensore che non vede la
  persona immobile è inutile per DIPME, e i test successivi diventano accademici. È il
  punto di decisione naturale del piano
- 📌 Attenzione a **non** riportare `stationary_distance_cm`: sarà 0 per costruzione

### 🔴 Test 1.3-2420 — PROTOCOLLO ESECUTIVO (scritto 05/09/2026, da eseguire)

> **La domanda**: il LD2420 mantiene la presenza su una persona **immobile**? È il punto
> di decisione della campagna ridotta: se la risposta è no, il modulo è inutile per
> DIPME e i test successivi diventano accademici.

#### ⚠️ Perché si esegue a **1 m** e non a 1,5 m come scritto nel §0-bis

Due ragioni, entrambe emerse incrociando le soglie tarate con le energie misurate:

1. **A 1,5 m il bersaglio cade nel gate 3, dove l'esemplare è già marginale sul
   *movimento*.** Convertendo le soglie di `ld2420_config_tarato_max_6.xml` in grezzi
   (`grezzo = 10^(dB/10)`):

   | gate | copre | trigger | hold | energia misurata (persona che cammina sul posto) |
   |---|---|---|---|---|
   | 2 | 70-140 cm | **44,3** | 31,0 | **90** a 100 cm (fondo ~20) |
   | 3 | 140-210 cm | **55,3** | 38,7 | **32** a 200 cm (fondo ~20) — *sotto persino l'hold* |

   A 2 m nemmeno una persona **che cammina** raggiunge la soglia di mantenimento. A 1,5 m
   si sta nello stesso gate 3. Partire da lì significa rischiare un "no" ambiguo, che non
   distingue *"non vede le persone ferme"* da *"1,5 m è già fuori portata per questa
   unità"*. A 1 m il margine è ~2× sul trigger e ~2,9× sull'hold: è la condizione
   migliore che l'esemplare può offrire.
2. **A 1 m esiste già il dataset gemello del LD2410B**: `fermo_1m_H` — 5 trial, persona
   **in piedi immobile a 1 m**, 202 s utili ciascuno, `radar_rate_% = 100,00 ± 0,00`,
   `pir_rate_% = 1,52 ± 1,03`. A 1,5 m non c'è nulla con cui confrontarsi. Acquisire a
   1 m completa una **riga a tre sensori a geometria identica**, che è il formato in cui
   la tesi presenta tutto il resto.

Quindi: **1 m come blocco decisivo, 1,5 m come estensione** subito dopo, solo se il
blocco a 1 m dà esito positivo.

#### ⚠️ Che cosa si sta misurando davvero (da scrivere così in tesi)

Sul LD2410B "vedere la persona ferma" significa che il **canale stazionario**, che ha
soglie proprie, riporta un bersaglio. Sul LD2420 il canale è **uno solo** con
un'**isteresi**: `Trigger` porta da libero a occupato, `Maintain` (hold) *mantiene* la
presenza sui micro-movimenti. Su una persona che entra, si posiziona e poi si immobilizza,
la grandezza misurata è quindi il **mantenimento della presenza**, non l'acquisizione da
zero. È esattamente lo scenario DIPME (la vittima è entrata sotto l'arredo e poi non si
muove più) ed è l'uso per cui il manuale definisce la soglia *Maintain* — ma non è la
stessa identica grandezza del LD2410B, e i due numeri vanno confrontati dichiarandolo.

#### 🚨 Il confondente da neutralizzare: il ritardo di scomparsa

`ObjectDisappearDelayTime = 30` significa che, quando l'energia scende sotto l'hold, la
presenza resta alta ancora **30 s**. Una presenza che dura meno di 30 s dopo che il
soggetto si è fermato **non è mantenimento**: è la coda. È lo stesso errore che nella
prima campagna produsse il falso "24,83 %" sul LD2410B.

➡️ **Convenzione di scarto per questo test: 60 s**, non 20 (20 per raggiungere la
posizione + 30 di ritardo + margine). Con `--duration 262 --transitorio 60` restano
**202 s utili**, cioè esattamente la finestra di `fermo_1m_H`.

#### Preparazione (una volta, ~20 min)

1. 🔴 **Scollegare l'alimentazione del LD2410B.** Due radar a 24 GHz sulla stessa scena
   si disturbano — e qui si misura un segnale a 2-3× il fondo, quindi non è un dettaglio
2. **Caricare `HLK-LD2420/Backup config/ld2420_config_tarato_max_6.xml`** con il tool PC
   via CH340E. Serve la coppia completa *gate max 6 + soglie tarate*: la configurazione
   `_max_8` ha il gate 2 con trigger 18,21 dB (66 grezzi) invece di 16,46 (44), cioè un
   margine molto più stretto proprio nel gate che decide questo test.
   *Ripiego se il tool non si collega*: mettere `#define GATE_MAX_DA_IMPOSTARE 6` nello
   sketch (scrive in RAM a ogni avvio) e **dichiarare** che le soglie erano quelle in
   flash, annotando quali
3. Cablare il LD2420: `3V3→3V3`, `GND→GND`, `OT1→D16`, `RX→D17`. OT2 non serve
4. **Il PIR NON serve**: lasciarlo scollegato e mettere `#define PIR_COLLEGATO 0` nello
   sketch (è già il default dal BUILD 6). Il dato del PIR a 1 m con persona immobile è
   già in `fermo_1m_H` (`pir_rate_% = 1,52 ± 1,03`) ed è indipendente da quale radar sia
   montato, perché il PIR non emette nulla che il radar possa disturbare.
   🚨 **Il flag non è una formalità**: con `PIR_COLLEGATO 0` la colonna esce a **-1** e
   `analizza_test.py` omette tutte le metriche del PIR, marcando la riga
   `pir_stato = NON COLLEGATO`. Se invece uscisse a 0 (pin in pull-down) il file
   direbbe `fn_pir_% = 100,0` con una persona davanti, e quel numero **entrerebbe da
   solo** nel foglio `tutti_i_trial` di `esporta_excel.py`, che scandisce tutti i CSV
   della cartella con una glob. Se il PIR lo si vuole cablare lo stesso, va su **D21**
   (non D34) e il flag va messo a 1
5. Caricare `firmware/ld2420_logger_bin/` e verificare a monitor seriale:
   `BUILD 5` · `energy mode: attivata` · `gate max: letto 6`. **Se una delle tre manca,
   fermarsi**: tre giri di prove sono già stati persi così
6. **Aspettare 90 s** dall'accensione del 3V3 prima della prima acquisizione (il modulo
   resta muto ~55 s)

#### Sequenza di acquisizione (~35 min)

```powershell
cd HLK-LD2410x
# 1. CONTROLLO NEGATIVO — stanza vuota, si esce e si chiude la porta
.venv\Scripts\python.exe serie.py --scenario vuoto2420_1m --trials 1 --duration 150 --transitorio 30 --gt-presence 0 --gt-state empty

# 2. CONTROLLO POSITIVO — cammino sul posto a 1 m
.venv\Scripts\python.exe serie.py --scenario mov2420_1m --trials 1 --duration 80 --gt-state moving

# 3. IL TEST — in piedi, IMMOBILE a 1 m, 5 trial da 262 s
.venv\Scripts\python.exe serie.py --scenario fermo2420_1m --trials 5 --duration 262 --transitorio 60 --gt-state static

# 4. CONTROLLO POSITIVO DI CHIUSURA — identico al 2, prova che nulla è derivato
.venv\Scripts\python.exe serie.py --scenario mov2420_1m_fine --trials 1 --duration 80 --gt-state moving
```

⚠️ **Fermarsi dopo il primo trial del punto 3 e guardare il CSV** prima di lanciare gli
altri quattro: ogni trial resetta l'ESP32 e quindi riapre una sessione di comandi verso il
modulo (0x0012). Su file lunghi singoli ha sempre funzionato, ma una serie di 5 reset è uno
schema nuovo. Controllare `frames_ok = 1` e che le energie non siano tutte uguali al fondo.

#### Analisi

```powershell
python ..\analisi\analizza_test.py data\fermo2420_1m_*.csv --salta-inizio 60
python ..\analisi\portata2420.py data\fermo2420_1m_T01.csv --finestre 0-60:transitorio 60-262:fermo_100 --gate-max 6
```
⚠️ Di `analizza_test.py` qui hanno senso **solo** `radar_rate_%`, `fn_radar_%` e le
colonne del PIR. `senergy_*`, `sdist_*` e `menergy_*` sono 0 per costruzione: il LD2420
non ha né il canale stazionario né la scala 0-100. Le energie vere sono le
`energy2420_gate*`, che solo `portata2420.py` legge.

#### Criteri di lettura dell'esito

| esito | come si riconosce | conclusione |
|---|---|---|
| ✅ **mantiene** | `radar_rate_%` ≈ 100 sui 202 s utili, energia del gate 2 stabilmente sopra **31** | il modulo regge la persona ferma a 1 m → si estende a 1,5 e 2 m |
| ⚠️ **intermittente** | presenza che va e viene, gate 2 che oscilla intorno a 31 | risultato interessante: siamo sul ginocchio dell'isteresi. Riportare la **serie temporale**, non solo la media |
| ❌ **non mantiene** | presenza che cade entro ~30-40 s dal fermo e **non risale**, gate 2 al fondo (~20) | il LD2420 non è utilizzabile per DIPME. La campagna ridotta si ferma qui e il resto diventa documentazione del limite |

🚨 **In tutti e tre i casi il controllo negativo e i due positivi sono obbligatori**: senza
il negativo, un `radar_rate_% = 100` potrebbe essere di nuovo il muro; senza i positivi,
uno 0 % non distingue "non vede le persone ferme" da "quella sera non funzionava niente".

📌 **Attesa onesta prima di acquisire** (da scrivere ora, non dopo): l'esito ❌ è
plausibile. Una persona immobile restituisce un'eco molto più debole di una che cammina, e
a 1 m il margine della persona *in movimento* è solo 2,9× sull'hold. Un esito negativo qui
**non è un fallimento della campagna**: è la misura che, insieme alla portata di ~2 m,
descrive l'esemplare.

---

#### ✅ ESITO (06/09/2026): **mantiene** — 5 trial su 5, `radar_rate_%` = 100,00 ± 0,00

Ma con una premessa che va nel testo: la configurazione `tarato_max_6` del 04/09 **non
rilasciava** a stanza vuota (presenza 100 % per 120 s, `vuoto2420_1m_norilascio_T01`), e
**nemmeno due nuove scansioni del tool** lo facevano — l'hold del gate 5 esce 13,82-13,84 dB
in tre scansioni indipendenti, cioè rumore stimato ~7 contro una media misurata di 15 su
120 s. La configurazione usata è `ld2420_config_fondo120s_max_6.xml`: **stessa formula del
manuale** (trigger 5×, hold 3,5× il rumore) ma rumore = media su 120 s del nostro file a
stanza vuota. Con quella, negativo e positivi passano e i cinque trial da fermo danno:

| | LD2410B `fermo_1m_H` | **LD2420 `fermo2420_1m`** | PIR `fermo_1m_H` |
|---|---|---|---|
| presenza, 202 s × 5 | 100,00 ± 0,00 % | **100,00 ± 0,00 %** | 1,52 ± 1,03 % |
| fronti di presenza | — | **0** in ogni trial | — |
| gate 2: hold superato | — | 17-44 % dei campioni, gap max 5,8-16 s | — |

- non è coda: l'hold è alimentato dai micro-movimenti (gate 2 media 30-51, p95 80-121,
  contro fondo 13 / max 34), con intervalli fra superamenti sempre sotto i 30 s di ritardo
- **§8 del manuale misurato**: `dist_raw` a riposo in 4/5 trial con presenza al 100 %;
  T04 riporta 133 cm costanti per 202 s. Dice *se*, non *dove*
- ⚠️ **il gate 2 non distingue immobile da cammino sul posto** (chiusura a 105 cm: media
  29, p95 68 — meno della persona ferma). Ipotesi: dinamica dell'esemplare esaurita a 1 m.
  La dose-risposta a 1 m (Test 2.3-2420) va fatta comunque, ma può uscire piatta
- rilascio a stanza vuota ~55 s (30 s di ritardo + coda dell'ultimo superamento);
  per questo lo scarto dei trial da fermo è **90 s**, non 60

#### 📉 Dose-risposta a 1 m (06/09/2026): presenza piatta al 100 %, energia NON graduata

`micromovimenti2420_1m_T01..T05`, stessa sessione e posizione dei trial da fermo:

| condizione | LD2410B `menergy` | **LD2420 gate 2** | presenza LD2420 |
|---|---|---|---|
| immobile | 68,6 | **41,0 ± 9,3** | 100 % |
| micro-movimenti | 84,4 | **34,8 ± 1,0** | 100 % |
| cammino sul posto | 99,3 | **31,0** | 100 % |

Sul LD2410B la scala è monotona; qui è rovesciata e le tre condizioni si sovrappongono
entro la dispersione dell'immobile. Il canale d'energia dell'esemplare separa vuoto (13) da
occupato (30-50) e basta: **è un bit, non una scala**. Conseguenza: su questo LD2420 non
esiste la grandezza continua su cui il LD2410B costruisce l'indice di vitalità (obiettivo 6)
— va scritto come limite dell'esemplare, con l'ipotesi (non dimostrata) della dinamica
esaurita. La frazione di `dist_raw` valida cresce con il movimento (0-9 → 25-86 → 100 %)
ma i valori sono spesso stantii (133 cm ricorrente): non è un indicatore usabile.

#### 📏 Test 1.2-2420 (06/09/2026): presenza 100 % a 0,5-2 m, distanza solo fino a 1 m

| distanza | presenza | trigger superato /min | distanza riportata | errore | valori distinti /60 s |
|---|---|---|---|---|---|
| 0,5 m | 100 % | 33-64 | **59 ± 5** | +9 cm | 22-38 |
| 1 m | 100 % | 24-34 | **121 ± 9** | +21 cm | 4-11 |
| 1,5 m | 100 % | **0-8** | stantia (47/61/71 o riposo) | — | **0-1** |
| 2 m | 100 % | **1-13** | stantia (60/212/258/134 o riposo) | — | **0-1** |

- **acquisisce fino a ~1 m, mantiene fino a 2 m**: oltre il metro la persona sta appena
  sopra il fondo (p95 26-41 vs max 25 a vuoto) e supera l'hold ogni 5-12 s, ma quasi mai il
  trigger. La presenza a 1,5-2 m era già accesa dal passaggio a 1 m
- **la distanza a 1,5-2 m non è una misura**: un solo valore per trial, agganciato e mai
  aggiornato. Retta non costruibile. Dove riporta (≤ 1 m) sbaglia del ~20 %; LD2410B alle
  stesse distanze: −0,5 / +11 cm, con inseguimento continuo fino a 5 m
- ⚠️ zero del metro e montaggio da annotare: la tacca da 1 m ha dato 105 / 118 / 105 / 121
  in quattro momenti diversi. Gli errori assoluti valgono solo con lo zero dichiarato

#### 🎯 Test 1.1-2420 e configurazione v2 (07/09/2026)

| configurazione | durata a vuoto | riaccensioni | tasso | presenza a vuoto |
|---|---|---|---|---|
| LD2410B, fabbrica (20-21/08) | 6,55 h | **0** | ≤ 0,43/h | 0 % |
| LD2420 `fondo120s_max_6` (notte) | 7,00 h | **181** | **26,2/h** | 26,0 % |
| LD2420 `fondo120s_max_6_g0alto` (1 h) | 1,02 h | **5** | **5,4/h** | 5,3 % |

- episodi di 31,8 s mediani = un trigger isolato + 30 s di ritardo; **il gate 0** (accoppiamento,
  non una distanza) sopra il trigger in 80/181 casi di notte, mai con trigger 1600
- il residuo (gate 1: 208/221 > 196; gate 2: 74 > 73) **non è eliminabile senza perdere la
  persona**: 5,4/h è il pavimento dell'esemplare
- ⚠️ **avvio**: il modulo stima il fondo all'accensione; un corpo a 20 cm in quei secondi
  lo lascia con tutti i gate ×10-20 finché non si riavvia a stanza libera. Regola: accendi,
  allontanati, 90 s, check del fondo (60 s). Cinque trial persi così (`ingresso2420_rumore_*`)
- 📌 **da qui in avanti la configurazione è `g0alto`** (v2). Tutto ciò che è stato acquisito
  con `fondo120s_max_6` resta valido: il gate 0 non decideva nessuno di quei test

#### ⏱️ Test 2.1-2420 (07/09/2026): latenza d'ingresso dalla porta **7,28 ± 1,40 s** (n = 5)

| | LD2410B (23/08) | **LD2420** |
|---|---|---|
| protocollo | dalla porta, evento a 30 s, 10 trial | dalla porta, evento a 30 s, **pausa 270 s fuori**, 5 validi |
| latenza | **5,36 ± 0,30 s** | **7,28 ± 1,40 s** |
| trial validi | 10/10 | 5/5 (+1 scartato: lanciato da dentro) |

- l'acquisizione **coincide col primo superamento del trigger sul gate 2** in 4/5 trial: il
  trigger e' spiegato dal frame, il mantenimento no
- +1,9 s e dispersione 4-5×: il LD2410B aggancia in avvicinamento a 4-5 m, il LD2420 entro
  ~1 m su un margine minimo (trigger 73 vs p95 68-85 della persona che cammina)
- ⚠️ **tre tentativi falliti prima di questo**, tutti per la stessa ragione: il modulo non
  torna spento finche' c'e' una persona nella stanza (anche a 4 m, invisibile nelle
  energie) o finche' la stanza non e' vuota da ≥ 2 min. **La pausa fra trial va passata
  fuori dalla stanza** — e' parte del protocollo, non tempo morto

#### ↔️ Test 2.4-2420 laterale (07/09/2026): vicino fermo a 1 m a 90° → **0 % a regime**, 3/3

Energie al fondo della stanza vuota (gate 2 ~12-13, gate 1 ~38): la persona di lato non
compare in nessun gate, zero superamenti del trigger. Stesso esito del LD2410B a regime
(0 %). Non discrimina: la differenza fra i moduli e' sulla persona **in movimento** a 90°
(LD2410B 100 %), da misurare con la prova angolare.

#### 📐 Misura angolare LD2420 (08/09/2026): fascio utile fino a 75°, al fondo a 90°

| azimut | gate 2 LD2420 (fondo 12-13) | trigger superato | LD2410B presenza | LD2410B energia |
|---|---|---|---|---|
| 0° | 22,8 ± 1,5 | 0,7-3 % | 100 % | 96,5 |
| 45° | 31,5 ± 4,8 | 3-9 % | 100 % | 95,3 |
| 60° | 34,4 ± 3,4 | 5-10 % | 100 % | 95,7 |
| 75° | 29,4 ± 3,7 | 3-9 % | 100 % | 94,1 |
| **90°** | **15,8 ± 1,4** | **0 %** | **100 %** | 94,3 |
| 120° | non eseguito | — | 6,6 % | 59,6 |

- metrica primaria: energia (la presenza si trascina per isteresi fra un azimut e l'altro)
- **piu' stretto del LD2410B (≥ ±90°), piu' largo del dichiarato (±60° / ±45°)**
- per DIPME: il vicino **in movimento** a 90° non e' visto → selettivita' fra banchi
  adiacenti. E' l'unico punto della campagna in cui il LD2420 fa meglio del LD2410B, e va
  scritto con lo stesso rilievo dei suoi limiti — **ma attribuito all'esemplare**: con un
  margine di 4-6 dB il confine segue il diagramma d'antenna; il LD2410B a 1 m e' saturo
  ovunque e vede nei lobi secondari. I manuali dichiarano settori alla portata massima
  (LD2410B ±60°, LD2420 ±60° §1.1 / ±45° §5.2): nessuno contraddetto, nessuno descrive
  un confine a 1 m

#### 👥 Test 2.5-2420 due persone (08/09/2026): un bit di presenza, nessun conteggio

| scenario (A ferma 1 m, B 2 m) | gate 2 (A) | gate 3 (B) | `dist_raw` | LD2410B: B riportata |
|---|---|---|---|---|
| sfalsate di lato, B cammina | 22,7 ± 2,1 | 20,5 ± 0,7 | **211-214** (B) in 2/3 | 73,8 % |
| in fila, B dietro A | 42,4 ± 4,0 | **16,7 ± 2,3** (= A sola) | 20 / 20 / 123 | 0,4 % |
| entrambe ferme, sfalsate | 20,1 ± 0,8 | 21,5 ± 4,5 | 268 costante | 19,6 % |
| controllo: A sola | 41,0 ± 8,3 | 15,9 ± 2,2 | riposo | — |
| controllo: B sola a 2 m | 15,4 ± 1,9 | 17,0 ± 2,6 | stantia | — |

- presenza 100 % in tutti gli scenari: e' un bit, il conteggio non esiste per costruzione
- in fila B e' invisibile (come sul LD2410B); sfalsate la separazione nelle energie non e'
  dimostrabile (B a 2 m e' gia' al bordo del fondo da sola), ma la distanza si aggancia su
  B — la persona in moto, §8 — in 2/3. Ordine qualitativo identico al LD2410B, senza numeri

#### 🔧 Test 2.6-2420 gate minimo (08/09/2026): non tocca la presenza, blocca la distanza

| gate min 3 (gate 0-2 esclusi) | persona a 1 m — gate 2 **escluso** | persona a 2 m — gate 3 ammesso |
|---|---|---|
| presenza | **100 %**, 240 s × 3, zero fronti | 100 % |
| gate della persona | g2 39-44, hold 26-33 % | g3 18-20, hold 14-17 % |
| `dist_raw` | **202-204** costante | **200-207** costante |

- la decisione di presenza **ignora il gate minimo**: mantiene la persona nel gate escluso
  come in quello ammesso (coerente con le riaccensioni non ridotte a gate min 1)
- la distanza e' **confinata alla finestra ammessa e si pianta sul bordo**: stesso valore a
  1 e a 2 m; con gate min 1 dava 136 a 105 cm. Sotto gate minimo `dist_raw` non e' una misura
- il manuale (Tab. 4-2) da' solo il range 0-15: nessuna delle due proprieta' e' documentata.
  Per DIPME il parametro non serve a escludere riflettori vicini e rompe la distanza

#### ⏱️ Test 2.2-2420 con ritardo 5 s (08/09/2026): rilascio **7,7 ± 0,5 s** (era 87-120 s a 30 s)

| | ritardo | rilascio dopo l'uscita | riaccensioni |
|---|---|---|---|
| LD2420 `fondo120s` (06/09) | 30 s | 87-120 s, MAI in 5/5 a 120 s | 2-3 per finestra |
| LD2420 `g0alto` 1 h (07/09) | 30 s | 119 s | 5,4/h |
| **LD2420 `g0alto`** | **5 s** | **7,2 / 8,0 / 8,0 s** | 2 episodi da ~5 s in 330 s |
| LD2410B (23/08) | 5 s | 18,36 ± 0,54 s | 0 |

- **meccanismo chiuso**: rilascio = intervallo ≥ ritardo senza superamenti dell'hold. Le
  code dei gate 1-2 superano l'hold ogni 10-25 s → con 30 s non arriva quasi mai, con 5 s
  subito. Il rilascio lento era il **parametro di fabbrica**, non l'esemplare
- il confronto col LD2410B e' ora appaiato sul parametro; la differenza (7,7 vs 18,4) e'
  dominata dal tempo di uscita dal campo (1-2 m vs 5-6 m di portata). Coda propria ≈ il
  parametro su entrambi (~5-6 s vs ~9 s)
- i falsi positivi residui durano `trigger + 5 s` invece di 30

---

### Test 1.4-2420 — Persona sotto il banco (~60 cm)
- **Metrica**: tasso di rilevamento nello scenario reale del progetto
- 5 trial × 302 s, sensore fissato sotto il piano, soggetto rannicchiato
- ⚠️ **Scartare 40 s di transitorio**, non 20: il soggetto deve anche posizionarsi
  (convenzione già fissata nella prima campagna)
- **Confronto atteso**: LD2410B `fn_radar = 0,00 %`, distanza 62,7 ± 4,2 cm
- 🔎 **Domanda specifica del LD2420**: il manuale dichiara rilevamento da **0,2 m** senza
  zona cieca. A 60 cm siamo nel primo gate (0-70 cm). Il gate 0 del LD2410B, forzato, si
  era rotto — qui il gate 0 è di serie e va provato

#### ✅ ESITO (09/09/2026) — `banco2420_immobile_T01-05`, `banco2420_movimenti_T01-05`

Sensore sotto il piano come il 22/08, acceso da spento con allontanamento; fondo nella
nuova geometria identico a quello a 85 cm (g0 110 / g1 39 / g2 12); negativo a vuoto 0 %
su 120 s; positivo 100 % con gate 1 a 344 (+9,6 dB). 5 × 392 s con **90 s di scarto**
(ritardo 30 s) = 302 s utili, stessa finestra dei gemelli `sotto_banco_*_H`.

| condizione | PIR | LD2410B | **LD2420** | note LD2420 |
|---|---|---|---|---|
| immobile | 1,32 % | 100 % | **98,4 ± 3,6 %** | 4/5 al 100 %; T05 92 %: un rilascio di 24 s (164-189 s) |
| micro-movimenti | 96,5 % | 100 % | **100,0 ± 0,0 %** | zero fronti |

- 🔑 **Da immobile la presenza la regge il gate 2, non il gate 1 dove sta la persona**:
  gate 1 media 46 contro fondo 38 (hold superato 1-4 %), gate 2 22-41 contro 11 (hold
  6-32 %). Gap massimo senza superamenti su alcun gate: 7 / 22 / 14 / 30 s nei trial
  mantenuti, **65 s in T05** → rilascio. Stesso fenomeno visto sul LD2410B il 22/08
  (presenza portata dai gate 2-3 a 60 cm), verosimilmente cammini multipli sotto il piano
- **Il rilascio di T05 è il primo falso negativo su persona presente dell'intera campagna
  LD2420** (LD2410B: 0 in 20 trial sotto il banco). Margine da immobile a 50 cm sottile
  come a 1 m: +0,8 dB sul gate 1, +3-6 dB sul gate 2. Con micro-movimenti gate 1 141 ± 13,
  hold 30-44 %, gap ≤ 19 s
- **Distanza**: da immobile **un solo valore stantio per trial** (35/49/35/39/51), §8 del
  manuale confermato anche a 50 cm; con micro-movimenti mediana 46-56 con 38-49 valori
  distinti (LD2410B: 68,6 / 65,8 cm)
- **Zona cieca**: il manuale dichiara rilevamento da 0,2 m. A 50 cm il modulo rileva,
  ma il gate che dovrebbe contenere la persona quasi non la vede da ferma (46 vs 38) e
  la vede benissimo in movimento (141-344): la risposta dipende dal movimento, non dalla
  distanza minima
- Positivo di chiusura `mov2420_banco_fine_T01`: 100 %, gate 1 254 (hold 63 %) contro
  344 (70 %) dell'apertura — nulla è derivato nella sessione

**Costo Fase 1**: ~3 h presidiate + 1 notturna non presidiata.

---

## FASE 2-2420 — Confronto dinamico

### Test 2.1-2420 — Latenza di rilevamento all'ingresso
- 10 trial, evento a 30 s annunciato da `serie.py --beep-at 30 --evento entra`
- **Grandezza pulita**: la differenza appaiata radar−PIR (tragitto e reazione si cancellano)
- **Confronto atteso**: LD2410B 5,36 ± 0,30 s, PIR 5,96 ± 0,31 s, differenza −0,60 ± 0,35 s
- ⚠️ Validare ogni trial con `pre_radar_%` = `pre_pir_%` = 0: se un sensore era già attivo
  prima dell'evento il trial va scartato

### Test 2.2-2420 — Latenza di rilascio — 🔑 doppia esecuzione
- 5 trial con ritardo impostato a **5** (appaiato al LD2410B) + 5 trial a **30** (fabbrica)
- Comando: `serie.py --scenario rilascio2420_d5 --beep-at 30 --evento esci`
- **Confronto atteso**: LD2410B 18,36 ± 0,54 s con timeout dichiarato di 5 s — cioè il
  parametro dichiarato **non descriveva** il comportamento, con una coda propria stimata
  in ~8,9 s
- 🔑 **Questo test determina anche l'unità del parametro di ritardo**, che nessuno dei due
  documenti ufficiali dichiara: se passando da 5 a 30 il rilascio si allunga di ~25 s,
  l'unità è il secondo. Due misure che chiudono una domanda aperta di documentazione
- Riportare anche le **riaccensioni** nella coda (sul LD2410B: zero)

### Test 2.3-2420 — Curva dose-risposta
- 3 condizioni × 5 trial a 1 m, in piedi: **immobile / micro-movimenti / cammino sul posto**
- **Confronto atteso** (LD2410B sempre 100% in tutte e tre; PIR 1,52% → 51,60% → 85,20%):
  la domanda è se il LD2420 resta piatto al 100% come il LD2410B o se degrada verso il basso
- 📌 Se degrada, si colloca **fra** PIR e LD2410B: sarebbe il grafico più efficace di tutta
  la tesi, tre sensori sulla stessa scala di movimento

### Test 2.4-2420 — Selettività spaziale (banchi adiacenti)
- Gate massimo ridotto a **2** → portata 140 cm (70 cm/gate, contro i 150 cm del LD2410B:
  non identici, va dichiarato)
- 4 scenari × 3 trial: occupante a 1 m sull'asse / persona a 3 m sull'asse / persona a 1 m
  a 90° / occupante + vicino a 90°
- ⚠️ 🔴 **Scartare 120 s di transitorio**, non 20. Negli scenari di selettività la coda del
  radar dopo il posizionamento è durata 29, 66 e 101 s: con `--salta-inizio 20` si misura
  il transitorio e lo si scambia per rilevamento. È l'errore che nella prima campagna ha
  prodotto un falso "24,83 ± 19,55 %"
- **Confronto atteso**: LD2410B a regime → 100% / 0% / 0% / 100%

### Test 2.5-2420 — Due persone
- 3 scenari × 3 trial: A ferma a 2 m + B che cammina a 4 m **sfalsate di 50 cm**; entrambe
  ferme sfalsate; B **in fila** dietro A
- ⚠️ Sfalsare lateralmente è obbligatorio nei primi due: in fila il corpo davanti fa da
  schermo e non si distingue "non separa" da "era in ombra"
- **Previsione, da verificare**: avendo un canale solo, il LD2420 non dovrebbe riprodurre
  il risultato del LD2410B (79,2% di campioni con due bersagli riportati insieme). Ma
  `radar_presence` dovrebbe restare al 100% in tutti gli scenari, come lì
- 📌 Serve una **seconda persona**: da programmare quando è disponibile, non all'ultimo

### Test 2.6-2420 — 🆕 Gate MINIMO: una funzione che il LD2410B non ha
- **Non è una replica**: è un test nuovo, possibile solo su questo modulo
- Il LD2420 permette di impostare un gate **minimo** (comando `0x00`), cioè di **escludere
  il campo vicino**. Il LD2410B non lo prevede
- Impostare gate minimo 2 e verificare che una persona a 1 m **non** venga rilevata mentre
  una a 3 m sì
- 📌 **Perché è rilevante per DIPME**: un sensore sotto un banco potrebbe ignorare la
  gamba del proprio occupante e sorvegliare una fascia più lontana. È un argomento
  architetturale a favore del LD2420 che vale la pena avere in tesi accanto ai suoi limiti
- 2 scenari × 3 trial

**Costo Fase 2**: ~4 h, di cui ~45 min richiedono una seconda persona.

---

## FASE 3-2420 — Penetrazione ostacoli (da fare in coppia col LD2410B)

Non ancora svolta per **nessuno** dei due moduli. Conviene farla nella stessa giornata,
alternando i radar sullo stesso allestimento: cartongesso, legno, vetro, plastica.

- Baseline senza ostacolo + un blocco per materiale, 3 trial ciascuno, soggetto immobile
  a distanza fissa
- **Metrica**: tasso di rilevamento e (solo LD2410B) attenuazione dell'energia
- ⚠️ Un radar alla volta (§1.1). Segnare a terra le posizioni e **non spostare nulla** fra
  i due giri, altrimenti il confronto salta
- 📌 È l'unico punto in cui il LD2420 può risultare **superiore** in modo netto: più
  potenza utile e portata maggiore significano più margine attraverso un ostacolo

**Costo**: ~3 h per entrambi i moduli.

---

## FASE 4-2420 — Modalità binaria non ufficiale (OPZIONALE)

⚠️ Fonte di comunità (ESPHome), **non** Hi-Link. Da trattare come esperimento dichiarato,
mai come specifica citabile.

- Comando `0x0012` con valore `0x0004` (energy) / `0x0064` (simple). Frame da 45 byte,
  header `F4 F3 F2 F1`, footer `F8 F7 F6 F5`; presenza a offset 6, distanza a offset 7,
  **16 energie per-gate a 16 bit** da offset 9
- 🔑 **Perché tentarlo**: le energie sono `uint16`, non `uint8` 0-100. Il limite più serio
  del LD2410B è la **saturazione a 100** (92% dei campioni stazionari clippati), che
  nessuna soglia risolve. Un canale a 16 bit non satura, e la cadenza nativa è 10 Hz
  contro i nostri 5. Per la FFT del respiro sarebbe **migliore**, non peggiore
- **Criterio di abbandono, da fissare prima di iniziare**: se dopo **una sessione da 3 h**
  non si ricevono frame validi, si chiude. Il reverse engineering è un pozzo senza fondo e
  non è l'oggetto della tesi
- Se funziona: ripetere il pilota respiro (soggetto fermo, ≥1,5 m, **respiro a metronomo a
  ritmo noto**) e confrontare la stima con quella del LD2410B. Il confronto
  saturato-vs-non-saturato sarebbe un ottimo paragrafo

**Costo**: 3 h a tetto fisso, o zero se si decide di lasciarlo fuori.

---

## FASE 5-2420 — Respiro a metronomo a 1 m — ✅ ESEGUITA 09/09/2026, fermata al primo blocco

Protocollo identico al 31/08 sul LD2410B tranne la distanza: seduto a **1 m** rivolto al
sensore (85 cm, altezza del torace), immobile, metronomo al doppio del ritmo, 202 s con
40 di scarto (162 utili), `analizza_respiro.py --scan --salta-inizio 40 --min-canali 2`
(i 16 canali `energy2420_gate*` sono nello scan dal 09/09; regressione sul LD2410B
verificata trial per trial). **Criterio dichiarato prima di acquisire**: trial concorde se
≥ 2 gate con SNR > 3 danno la stessa frequenza entro il 10 %; si passa a 10 e 20 atti/min
solo con ≥ 2 trial su 3 concordi.

| file | esito col criterio a 2 gate | gate 2 da solo (canale a priori) |
|---|---|---|
| `respiro2420_1m_15_T01` | nessun gruppo (un solo canale utilizzabile) | **14,8/min**, SNR 5,8 |
| `respiro2420_1m_15_T02` | **14,6/min** ✔ (gate 2 + gate 3; ottava 28,9 scartata) | **14,8/min**, SNR 4,3 |
| `respiro2420_1m_15_T03` | gruppo spurio 23,7 (gate 0 + 4); ottava 29,6 sul gate 3 | 22,2, SNR 2,8: debole |
| `respiro2420_vuoto_T01-02` | **nessun gruppo** ✔ | picchi singoli a SNR 3-4, uno a 14,8 sul gate 1 |

- **1/3 col criterio dichiarato → fermata**, niente 10 e 20. Con il canale scelto a priori
  (gate della persona a 1 m) sono 2/3 con la frequenza esatta: la stima *c'è*, ma non
  regge un criterio di concordanza, perché la persona occupa **2 gate soli** contro i
  7-14 canali concordi del LD2410B
- **L'ottava (2 × 14,8) compare anche qui**, in 2 trial su 3: conferma indipendente, su
  un modulo diverso, del meccanismo fisico descritto per il LD2410B (energia sensibile
  all'entità dello spostamento, non al verso)
- **Il controllo negativo mostra perché il criterio a 2 gate è necessario**: a stanza
  vuota il gate 1 produce un picco a 14,8/min con SNR 3,1 — la frequenza imposta — che
  un criterio a canale singolo avrebbe accettato
- Saturazione 0 % ovunque: il vantaggio del canale a 16 bit è reale, ma su questo
  esemplare è annullato dal segnale debole (varianza del gate 2: 6-7 a vuoto, 17-22 con
  la persona; SNR max 6,1 contro 12,8 del LD2410B)
- 📌 **Da scrivere**: frequenza respiratoria *recuperabile ma non affidabile* a 1 m su
  questo LD2420, attribuito all'esemplare. Respiro e indice di vitalità restano sul
  LD2410B, come già deciso. 20 minuti spesi, entro il tetto

## 5. Ordine di esecuzione e stima complessiva

| # | blocco | ore | note |
|---|---|---|---|
| 1 | Fase 0 (0.5, 0.5-bis, 0.6, 0.7) | 2,5 | 0.5-bis è **bloccante** |
| 2 | Test 1.3-2420 | 0,75 | 🔴 **anticipato**: è il punto di decisione |
| 3 | Test 1.2-2420 | 1,5 | il confronto ±0,35 m vs cm |
| 4 | Test 1.4-2420 | 0,75 | scenario DIPME |
| 5 | Test 1.1-2420 | notturna | non presidiata |
| 6 | Fase 2 (2.1-2.4, 2.6) | 3,25 | |
| 7 | Test 2.5-2420 | 0,75 | serve 2ª persona |
| 8 | Fase 3 (entrambi i moduli) | 3 | |
| 9 | Fase 4 (opzionale) | 0-3 | tetto fisso |
| | **totale essenziale (1-7)** | **~9,5 h** | + 1 notturna |
| | **con ostacoli e binario** | ~15,5 h | |

⚠️ **Il Test 1.3-2420 va spostato in testa**, prima di 1.2 e 1.4. È l'unico che può
rendere inutile il resto: se il modulo non vede la persona immobile, spendere 8 h a
caratterizzarne la distanza è tempo buttato. Nella prima campagna l'ordine numerico
andava bene perché il LD2410B era già stato validato dal pilota.

---

## 6. La tabella che deve uscire da questa campagna

È l'obiettivo finale: una riga per grandezza, tre colonne di sensori. Materiale diretto
per il cap. 4 e per le conclusioni.

| grandezza | PIR HC-SR501 | LD2410B | LD2420 |
|---|---|---|---|
| persona immobile, 1 m (2,3 m fuori portata dell'esemplare) | 1,52 % | 100 % | **100 %** (5/5) |
| persona immobile, sotto banco | 1,32 % | 100 % | **98,4 ± 3,6 %** (un rilascio di 24 s in 1/5) |
| errore di distanza | — | ≤ 4,9 cm dalla retta | +9 cm a 0,5 m, +21 cm a 1 m, **stantia oltre** |
| latenza ingresso | 5,96 s | 5,36 s | **7,28 ± 1,40 s** |
| coda di rilascio | 3,46 s fissi | ~18,4 s (timeout 5 s) | **87-120 s** a 30 s di fabbrica, **7,7 s** a 5 s |
| falsi positivi | ≤ 0,43 ev/h | ≤ 0,43 ev/h | **26,2 ev/h** a soglie tarate, **5,4 ev/h** con gate 0 alzato |
| due persone separate | ✗ | parziale, per canale (74 / 20 / 0,4 %) | **✗** un bit, nessun conteggio |
| esclusione campo vicino (gate min) | ✗ | ✗ | **non agisce sulla presenza**, blocca la distanza |
| ostacoli | bloccato da tutti | −7,5 … −41,6 %, metallo blocca | **0,4 … ≥ 4,1 dB**, cartongesso 0,7, stessa graduatoria |

---

## 7. Fonti

- `HLK-LD2420/Documentazione/HLK-LD2420-Product-Manual V1.2.pdf` — Tab. 2-1 (specifiche),
  Tab. 3-2 (piedinatura J2), §4.2.1 (parametri), §5 (portate), §8 (*Cautions*: assenza di
  telemetria sui bersagli fermi)
- `HLK-LD2420/Documentazione/HLK-LD2420 Protocol Document.pdf` — Tab. 1 (comandi),
  Tab. 2 (parametri), esempi pagg. 3-5
- `HLK-LD2420/Backup config/ld2420_config_fabbrica.xml` — configurazione dell'esemplare
- ESPHome, componente `ld2420` (fonte di comunità, non ufficiale) —
  https://github.com/esphome/esphome/tree/dev/esphome/components/ld2420
