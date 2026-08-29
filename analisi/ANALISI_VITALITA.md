# Analisi — Indice di vitalità (Obiettivo 6)

> Obiettivo 6 dalle parole del professore: *"oltre a presenza sì/no, creare un indice
> di vitalità: un algoritmo che valuta quanto una persona si muove — questa persona
> si muove 50 su 100 → vivo o moderatamente vivo"*.
>
> Questo documento è la specifica di riferimento dell'algoritmo. È indipendente dalla
> web UI: l'indice si sviluppa e si valida sui CSV dei test (Fase 6 di PIANO_TEST.md);
> la visualizzazione nella dashboard (gauge) è solo uno dei suoi utilizzi.

---

## 1. Il problema in termini UPRISE

Nel contesto del progetto, la differenza tra "presenza" e "vitalità" è la differenza
tra due domande dei soccorritori:

1. *C'è qualcuno sotto il banco?* → presenza (obiettivi 1-3)
2. *In che condizioni è?* → vitalità: si muove attivamente (cosciente), fa solo
   micro-movimenti (ferito/intrappolato ma vivo), o non dà segni?

Il PIR non può nemmeno porsi la seconda domanda. Il mmWave sì, perché espone
l'**energia riflessa per gate di distanza** — una misura continua di *quanto* si
muove ciò che riflette, non solo *se* si muove. L'indice di vitalità è la sintesi
di questa informazione in un numero 0-100 leggibile da un non tecnico.

## 2. Dati di ingresso (dal firmware, 5 Hz)

| Segnale | Colonna CSV | Cosa misura | Utilizzabile? |
|---|---|---|---|
| Energia moving del target | `moving_energy` | intensità del movimento rilevato (0-100) | ✔ satura solo a movimento pieno |
| Energia per-gate moving | `menergy_gate0..8` | *dove* e *quanto* si muove il bersaglio | ✔ **è il canale portante dell'indice** |
| Energia per-gate stationary | `senergy_gate0..8` | riflessione del corpo fermo | ✘ **saturo a 100 in ogni scenario occupato** (§3.0) |
| Energia stationary del target | `stationary_energy` | idem | ✘ saturo al 100 % dei campioni |
| Stato presenza | `radar_presence` | gate di guardia: se 0, vitalità forzata a 0 | ✔ |

⚠️ **Correzione rispetto alla prima stesura di questo documento.** L'ipotesi di
partenza era: *"una persona viva ma immobile ha energia moving ≈ 0 mentre l'energia
stationary del suo gate oscilla col respiro"*. La prima metà è falsa e la seconda è
inutilizzabile:

- l'energia **moving** di una persona immobile **non** è ≈ 0: vale in media **30,9**
  a 1 m (`fermo_1m_H`, 5 trial) contro **11,9** a stanza vuota. Il canale moving
  raccoglie i micro-movimenti involontari, ed è proprio lì che si vede la vita;
- l'energia **stationary** è satura e quindi costante: non oscilla con niente.

L'indice si costruisce quindi **interamente sui canali moving**. È la stessa
conclusione a cui erano già arrivati, per due strade indipendenti, il pilota del
respiro (18/08) e il Test 1.3 (i canali stazionari danno un artefatto a ~7 atti/min).

## 3. Algoritmo — specifica v2 (26/08/2026)

### 3.0 Perché la v1 non era applicabile

La v1 (conservata in §3.3) costruiva la componente di micro-vitalità sulla variazione
tick-a-tick dell'energia **stazionaria** del gate attivo. Misurata sui CSV già
acquisiti, scartando i transitori secondo le convenzioni del registro (20 s ordinari,
40 s sotto il banco), quel canale risulta inchiodato al fondoscala:

| scenario | trial | saturazione `senergy_gate2` | **dev.std** di `senergy_gate2` |
|---|---|---|---|
| `fermo_1m_H` | 5 | 98 % | **1,0** |
| `micromovimenti_1m_H` | 5 | 100 % | **0,0** |
| `movimento_1m_H` | 5 | 100 % | **0,0** |
| `sotto_banco_immobile_H` | 5 | 100 % | **0,2** |
| `sotto_banco_movimenti_H` | 5 | 100 % | **0,0** |
| `stanza_vuota` (riferimento) | 1 | 0 % | 1,0 |

Con deviazione standard 0,0 il termine `delta` della v1 è **identicamente nullo**: la
seconda componente non contribuisce all'indice qualunque valore si dia a `k`. Non è un
difetto del nostro esemplare — è la saturazione già documentata nel Test 0.2 (92 % dei
campioni stazionari a fondoscala) e nel protocollo V1.07, dove l'energia è un valore
normalizzato 0-100 che nessuna soglia e nessuna auto-calibrazione riportano in scala.

### 3.1 Specifica v2

Due componenti, aggiornate a ogni campione (5 Hz), entrambe sul canale **moving**:

```
g = gate_attivo                                              # vedi §3.2

# Componente 1 — livello di movimento (reattiva, ~2 s di memoria)
mov_raw  = max(moving_energy, menergy_gate[g])               # 0-100
mov_ewma = α_m · mov_raw + (1-α_m) · mov_ewma                # α_m = 0.1

# Componente 2 — variabilità del ritorno (lenta, ~10 s di memoria)
var_raw  = |menergy_gate[g](t) - menergy_gate[g](t-1)|
var_ewma = α_v · var_raw + (1-α_v) · var_ewma                # α_v = 0.02

# Fusione
vitality = clamp( mov_ewma + k · var_ewma , 0, 100 )         # k da tarare
if radar_presence == 0: vitality = 0
```

Razionale, con i valori misurati sui trial già acquisiti (medie fra 5 trial, 1 m,
gate 1, transitorio scartato):

| scenario | `menergy_gate1` medio → **componente 1** | dev.std → **componente 2** |
|---|---|---|
| stanza vuota | 11,9 | 2,2 |
| immobile che respira | 30,9 ± 7,2 | 20,7 |
| micro-movimenti | 66,5 ± 4,7 | 31,0 |
| movimento pieno | 98,9 ± 0,7 | 5,8 |

- **la componente 1 da sola separa già i quattro scenari** ed è monotona. È l'asse
  principale dell'indice;
- **la componente 2 non è monotona** (sale fino ai micro-movimenti, poi crolla perché
  a movimento pieno il canale satura a 100 e non può più variare). Non è un difetto se
  entra come **termine additivo**: serve a sollevare la fascia bassa — dove separare
  "vivo immobile" da "niente" è il compito difficile — mentre in alto è la componente 1,
  già a 99, a determinare la classe. `k` va tarato per questo, non per massimizzare
  la separazione in alto;
- **EWMA e non media mobile**: costa O(1) in RAM (2 float), identica in Python e su
  ESP32;
- **due costanti di tempo diverse**: il movimento deve reagire in ~2 s (α=0.1 a 5 Hz),
  la variabilità va integrata su ~10 s (α=0.02) per emergere dal rumore;
- **`max(target, gate)`**: le due energie a volte divergono per i filtri interni del
  radar; il massimo rende l'indice conservativo verso i falsi "nessun segno", che è
  l'errore più grave nel dominio UPRISE.

**Correzione del rumore di fondo (obbligatoria).** Prima di entrare nell'indice,
l'energia del gate va portata al netto del rumore misurato a stanza vuota e riscalata:

```
e_netta = max(0, (menergy_gate[g] - fondo[g]) · 100 / (100 - fondo[g]))
```

dove `fondo[g]` è la media per-gate misurata su un file a stanza vuota (nel nostro
ambiente: g0≈18, g1≈13, g2-g8 = 3-5, stabili su 6,5 h). Senza questa correzione i gate
vicini portano ~19 unità di rumore dentro l'indice e la stanza vuota diventa
indistinguibile da una persona immobile — vedi §5.3 per le due tabelle a confronto.

⚠️ **Il livellamento è indispensabile, non un abbellimento.** Per singolo campione le
distribuzioni si sovrappongono quasi completamente: in `fermo_1m_H` il 5°-95°
percentile di `menergy_gate1` va da **10 a 100**. Sono le EWMA a rendere le classi
separabili: la taratura di α_m e α_v è quindi parte dell'algoritmo, non una rifinitura.

### 3.2 Scelta del gate attivo

La v1 usava `argmax(senergy_gate)`, che su un canale saturo restituisce sempre lo
stesso gate. Il prototipo implementa tre criteri selezionabili, da confrontare in
taratura:

| criterio | come | note |
|---|---|---|
| `energia` (default) | `argmax(menergy_gate[i])` | segue il bersaglio; a stanza vuota punta al rumore dei gate 0-1, ma lì interviene il gate di presenza |
| `distanza` | dalla distanza riportata: `gate = dist // 75 cm` | usa la stima del radar; indefinito quando nessun target è riportato |
| `fisso N` | gate imposto | per il confronto controllato fra trial della stessa geometria |

### 3.3 Versione v1 (superata, conservata per storia)

```
gate_attivo = argmax(senergy_gate[i])
mov_raw     = max(moving_energy, menergy_gate[gate_attivo])
delta       = |senergy_gate[gate_attivo] - senergy_prec|      # <-- sempre 0: §3.0
vitality    = clamp(mov_ewma + k · resp_ewma, 0, 100)
```

## 4. Classificazione

📌 **Decisione dell'incontro col professore (29/08/2026): TRE classi, non quattro.**
La presenza/assenza non è una classe di vitalità, è il **gate** che sta a monte:
se `radar_presence == 0` non c'è nessuno da classificare. Le classi descrivono
*quanto si muove chi c'è*.

| vitality | classe | cosa significa | priorità per i soccorritori |
|---|---|---|---|
| — | (nessuna presenza) | il sensore non rileva nessuno | — |
| 0-33 | `vitalita_bassa` | presenza confermata, movimento minimo | 🔴 **la più alta** |
| 34-66 | `vitalita_moderata` | micro-movimenti, persona che si aggiusta | 🟠 media |
| 67-100 | `vitalita_alta` | movimento ampio, persona reattiva | 🟡 la più bassa |

🔑 **L'ordine di priorità è INVERSO rispetto all'indice, ed è il punto più
interessante da scrivere in tesi.** Un segnale debole ma presente significa
"c'è qualcuno che non si muove", cioè **possibilmente incosciente**: è il caso
che va raggiunto per primo. Un segnale forte significa "c'è qualcuno che si
muove attivamente", quindi probabilmente cosciente e in grado di aspettare.
L'indice misura la vitalità; la priorità è il suo complemento.

### 4.1 Come va PRESENTATO l'indice — richiesta esplicita del professore

Non descriverlo come *"misura del movimento toracico"* o *"rilevamento del
respiro"*, ma come **indice generico di vitalità** calcolato dall'energia radar.

⚠️ **Questa non è solo una preferenza di forma: è anche la scelta più difendibile.**
Senza ground truth non possiamo validare una frequenza respiratoria — è
esattamente il motivo per cui il pilota del 18/08/2026 non è citabile — quindi
dichiarare "misuriamo il respiro" sarebbe una **sovradichiarazione**. Definire
l'indice per quello che effettivamente *calcola* (una funzione delle energie
per-gate del canale moving) è al tempo stesso più generico e più rigoroso.

Formulazione consigliata: definire l'indice in modo operativo, e dedicare **una
sola frase** a cosa lo produce fisicamente — i micro-movimenti involontari del
corpo, fra cui quelli respiratori — senza costruirci sopra alcuna misura.

⚠️ **Sui nomi delle classi**: evitare formule come *"poco vivo"*. In un contesto
di triage descrivere una persona come poco viva è impreciso (la classe descrive
il **segnale**, non la persona) e sgradevole per chi legge la mappa. I nomi
proposti sopra qualificano l'indice, non l'individuo. Alternative accettabili se
si vuole staccarsi ancora di più dal lessico clinico: `attività: debole /
moderata / marcata`.

⚠️ Soglie **iniziali e arbitrarie**: la taratura vera si fa sui dati (sotto).
Nella tesi va detto chiaramente: le classi sono un supporto informativo al triage,
NON una diagnosi medica — assenza di segnale significa "il sensore non rileva
variazioni", non "deceduto" (la persona può essere fuori portata, schermata,
svenuta ma viva).

✔ **Effetto collaterale utile**: passando da 4 a 3 classi si elimina un confine,
il che **allevia** (non risolve) il problema di trasferibilità fra geometrie del
§ più avanti — `sotto_banco_immobile_H` dà 65,6 contro i 77,3 dei micro-movimenti
a 1 m, e con soglie a 33/66 le due cadono comunque in classi diverse.

## 5. Sviluppo e taratura — Python prima, C++ poi

Regola: **l'algoritmo si sviluppa su PC, sui CSV, dove si può iterare in secondi.**
Il porting su ESP32 (`vitality.h`) avviene solo a soglie validate.

📌 **Il porting è ora RICHIESTO, non opzionale** (incontro del 29/08/2026): il
professore vuole che l'indice sia calcolato **a bordo**, dentro il sito
self-hosted, accanto ai grafici di presenza. Vedi `analisi/ANALISI_WEB_UI.md`.

✔ **Buona notizia: costa quasi nulla.** La v2 dell'algoritmo è interamente basata
su **EWMA** (medie mobili esponenziali) e su differenze fra campioni consecutivi:
nessuna FFT, nessun buffer lungo, nessuna libreria. Sono poche moltiplicazioni per
campione a 5 Hz, con uno stato di manciate di byte. Ci sta comodamente accanto al
web server asincrono senza toccare il budget di RAM.
⚠️ È la ragione per cui l'indice **non** deve diventare una misura di frequenza
respiratoria: quella richiederebbe una FFT su finestra lunga (300 campioni per
60 s a 5 Hz), fattibile ma tutt'altro impegno, e comunque non validabile senza
ground truth. La FFT resta uno strumento di **analisi offline** in
`analizza_respiro.py`, non entra nel firmware.

### 5.1 I dati ci sono già (verificato 26/08/2026)

La Fase 6 di PIANO_TEST.md prevedeva quattro acquisizioni dedicate. Non servono: la
serie dose-risposta del Test 2.3 le copre tutte, a geometria costante (1 m, in piedi,
jumper H) e con 5 trial ciascuna.

| scenario previsto | CSV disponibile | trial | durata utile |
|---|---|---|---|
| `vitalita_0` | `stanza_vuota`, `stanza_vuota_notte` | 1 + notturna | 30 min + 6,5 h |
| `vitalita_respiro` | `fermo_1m_H` | 5 | ~200 s |
| `vitalita_micro` | `micromovimenti_1m_H` | 5 | ~200 s |
| `vitalita_attivo` | `movimento_1m_H` | 5 | ~60 s |

In più, **due scenari nella geometria UPRISE reale** che il piano non prevedeva:
`sotto_banco_immobile_H` e `sotto_banco_movimenti_H` (5 trial × ~340 s). Servono come
insieme di validazione **su geometria diversa da quella di taratura**, che è una prova
molto più severa del semplice hold-out sui trial.

### 5.2 Percorso

1. ✔ **Dati**: già acquisiti (§5.1)
2. ✔ **Prototipo**: `analisi/vitalita_proto.py` — implementa la v2 di §3.1, gira su
   tutti i CSV, produce la serie `vitality(t)` per trial, le distribuzioni per scenario
   e la matrice di confusione. Solo libreria standard. Opzioni pensate per la taratura:
   `--alpha-mov --alpha-var --k --soglie` (parametri), `--gate` (criterio del gate
   attivo, §3.2), `--fondo-da` (correzione del rumore, §3.1), `--trials` (separa
   taratura e validazione), `--istogrammi` (distribuzioni per scegliere le soglie),
   `--senza-gate-presenza` (§5.3), `--serie-out` (serie temporale per i grafici)
3. **Taratura**: scegliere α_m, α_v, k e le 3 soglie sui trial **T01-T03** dei quattro
   scenari a 1 m. Metodo: guardare le distribuzioni per scenario (istogrammi prodotti
   dal prototipo) e mettere le soglie nei vuoti fra le distribuzioni
4. **Validazione**, su due livelli:
   - *hold-out*: trial **T04-T05**, mai usati in taratura, stessa geometria
   - *trasferibilità*: scenari **sotto il banco**, geometria diversa. ⚠️ Da verificare:
     lo stesso soggetto immobile dà `menergy_gate1` = 30,9 a 1 m e **54,0** sotto il
     banco — le soglie tarate a 1 m potrebbero non trasferirsi. Se non si trasferiscono,
     è un risultato da riportare, non un fallimento: significa che l'indice va tarato
     per geometria di montaggio, cosa che in UPRISE è nota a priori (il sensore è
     fissato sotto un arredo di dimensioni note)
5. Porting in `vitality.h` (stesse costanti) + verifica live con la web UI (step 5)

Il punto 4 dà il numero finale per la tesi: *"l'indice classifica correttamente l'X %
dei campioni su trial mai visti in taratura"*, con un secondo numero per la geometria
diversa.

### 5.3 Chi decide la classe "nessun segno" — e la correzione del fondo

Con il gate di presenza attivo (`radar_presence == 0 → vitality = 0`), la classe
`nessun_segno` a stanza vuota sarebbe decisa dal **bit di presenza del radar**, non
dall'indice. Per verificare se l'indice sappia cavarsela da solo, il prototipo calcola
anche la versione **senza gate** (`--senza-gate-presenza`). Il primo esito è stato
negativo, e istruttivo:

| scenario | indice senza gate, **senza** correzione del fondo |
|---|---|
| stanza vuota (6,5 h notturne) | **19,1** |
| persona immobile a 2,3 m (`fermo_seduto`) | **21,2** |

Indistinguibili. La causa non è l'algoritmo ma il **rumore di fondo per-gate**: i gate
0-1 stanno a 13-18 unità anche a stanza vuota (già misurato nel Test 0.2 e stabile su
6,5 h), e quel valore entra tale e quale nella componente 1.

La correzione è sottrarre il fondo misurato e riscalare su 0-100
(`--fondo-da <file_stanza_vuota.csv>`, ANALISI_VITALITA.md §3.1). Con il fondo
sottratto (g0=18, g1=13, g2-g8 = 3-5):

| scenario | senza gate, **con** correzione del fondo |
|---|---|
| stanza vuota (6,5 h) | **2,4** |
| immobile a 2,3 m | **11,4** |
| immobile a 1 m | **30,9** |
| micro-movimenti a 1 m | **77,3** |
| movimento pieno a 1 m | **99,7** |

Ora l'indice separa la stanza vuota da una persona immobile **senza** appoggiarsi al
bit di presenza del radar. Il gate di presenza resta come rete di sicurezza, ma non è
più lui a produrre il risultato. In tesi vanno riportate entrambe le tabelle: la prima
mostra perché la correzione serve.

⚠️ **Problema aperto per la taratura — trasferibilità fra geometrie.** Con gli stessi
parametri, `sotto_banco_immobile_H` dà **65,6**, cioè quasi quanto i micro-movimenti a
1 m (77,3). Una sola terna di soglie non può quindi classificare correttamente
entrambe le geometrie. Le strade possibili, da valutare in taratura:
1. tarare per geometria di montaggio (in UPRISE il sensore è fissato sotto un arredo
   di dimensioni note, quindi la geometria è nota a priori);
2. normalizzare rispetto all'energia del bersaglio a riposo di quel sensore, cioè una
   calibrazione una tantum all'installazione;
3. accettare l'errore e dichiararlo — ma significa che sotto il banco una persona
   immobile viene letta come "moderato" anziché "vitalità bassa", il che nel triage
   è un errore **conservativo** (sovrastima la vitalità), quindi non innocuo.

## 6. Casi limite e comportamenti attesi

| Situazione | Comportamento atteso | Note |
|---|---|---|
| Persona esce dal campo | vitality → 0 entro il timeout radar (~5 s) | forzatura su presence=0 |
| Persona si addormenta | attivo → vitalita_bassa in ~30-60 s | le EWMA decadono con le loro costanti |
| Ventilatore/tenda in movimento | falso "moderato" possibile | limite da dichiarare; mitigazione: soglie per-gate del radar |
| Due persone | indice riferito al gate dominante | coerente col limite mono-target del LD2410B |
| Persona oltre 4-5 m | respiro non più rilevabile → sottostima | documentare la distanza massima utile per la classe "vitalita_bassa" (esce dal Test 5.1 a 1 m vs 2 m) |

## 7. Collocazione nella tesi

- Capitolo proprio (o sezione maggiore), DOPO il confronto PIR/mmWave: l'indice è
  la dimostrazione costruttiva che i dati mmWave abilitano ciò che il PIR non può fare
- Contenuto: motivazione triage (§1) → segnali disponibili (§2) → algoritmo e
  razionale (§3-4) → metodo di taratura e risultati (§5) → limiti (§6)
- La web UI compare solo come "consumatore" dell'indice (un paragrafo + screenshot
  della gauge)

## 8. Estensioni possibili (solo se avanza tempo)

- Sostituire il termine respiro EWMA con la **potenza in banda 0.1-0.5 Hz** su una
  finestra scorrevole di 30 s (mini-FFT a bordo): più robusta ma più costosa — v2
- Isteresi sulle classi (una classe cambia solo dopo N secondi stabili) per evitare
  sfarfallio nella UI
- Confidenza affiancata all'indice (funzione della stabilità del gate attivo)
