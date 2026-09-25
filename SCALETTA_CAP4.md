# Capitolo 4 — proposta di riduzione (20/09/2026)

**Stato: applicata il 20/09/2026.** Il capitolo riscritto è in
`tesi-unicam/capitoli/04-confronto-sperimentale.tex` (22 pagine, 16 figure, 8 tabelle);
il testo precedente è in `tesi-unicam/capitoli/backup/`. Il respiro è nel cap. 7 (§7.4).

Stato attuale: `tesi-unicam/capitoli/04-confronto-sperimentale.tex`, 2640 righe,
**50 pagine su 102 di corpo** (pag. 25-75 del PDF compilato; cap. 2 = 6 pagine,
cap. 3 = 12). 13 sezioni + 28 sottosezioni, 17 tabelle, 19 figure, 129 trattini
lunghi. Obiettivo: **22-25 pagine, 16 figure, 7-8 tabelle**, una sezione = un test
= una figura, tre sensori nella stessa figura ovunque esistano i dati.

Regola di scrittura: si tiene procedura (3-5 righe), figura, numeri con dispersione,
lettura per DIPME (un paragrafo). Si toglie il racconto di processo (errori scoperti,
regole di protocollo nate strada facendo, indicazioni del relatore, note operative),
le interpretazioni fisiche già date nel cap. 2, le proprietà dei moduli già date nel
cap. 3, le citazioni testuali in inglese dei manuali.

## Indice proposto

| § | Titolo | Figure | Tabelle | Pag. |
|---|---|---|---|---|
| 4.1 | Protocollo e metriche | **A nuova** (geometrie di prova) + foto setup | — | 1,5 |
| 4.2 | Stanza vuota: falsi positivi | fig18 | — | 1 |
| 4.3 | La persona ferma | fig02 (+ pannello 2,3 m, opz.), fig07 | fermo seduto (mini) | 2 |
| 4.4 | Il tipo di movimento decide il PIR | fig01, **B nuova** (sul posto vs attraversamento) | dose-risposta | 3 |
| 4.5 | Lo scenario DIPME: sotto il banco | fig19 | — | 2 |
| 4.6 | Distanza ed energia | fig04, fig05 (solo pannello sx) | distanza | 2 |
| 4.7 | Latenze di rilevamento e di rilascio | fig06 | latenze (unica) | 1,5 |
| 4.8 | Copertura angolare e selettività | fig20, fig09 | — | 2 |
| 4.9 | Due persone | fig08 | due persone | 1 |
| 4.10 | Penetrazione degli ostacoli | fig15, fig14 | ostacoli (ridotta) | 2,5 |
| 4.11 | Portata massima in corridoio | fig17 (fig16 opz.) | — | 1,5 |
| 4.12 | Il secondo radar: che cosa cambia | — | sintesi LD2410B vs LD2420 | 2 |
| 4.13 | Sintesi del confronto | — | sintesi campagna | 1,5 |
| | **Totale** | **16 (+2 opz.)** | **7** | **~23,5** |

Il respiro (fig12 + tabella metronomo) **esce dal cap. 4 e va nel cap. 7**: il
cap. 2 già scritto (§2.2.2) rimanda al Capitolo 7 per la stima della frequenza
respiratoria, ed è la base fisica dell'indice di vitalità.

## Sezione per sezione: cosa resta, cosa va via

### 4.1 Protocollo e metriche (1,5 pag.)
Resta: 5 ripetizioni per scenario, acquisizione sincrona, ground truth dichiarata,
setup fisso (tavolo a 1 m, sensori affiancati), convenzioni di scarto del transitorio
(20/40/60/120 s) in tre righe, le 5 metriche in elenco. **Figura A nuova**: pianta
delle quattro geometrie (stanza con tacche 1-5 m, sotto il banco a 50-60 cm, arco a
1 m per l'angolare, corridoio con i due vani a 4 e 5 m). Foto del setup (da fare).
Via: la tabella `tab:sessioni` (→ appendice o registro), la nota sull'aggiornamento
di Windows, i cinque principi in forma di elenco lungo, la nota sulla temperatura.

### 4.2 Falsi positivi (1 pag.)
Resta: fig18; regola del tre, LD2410B e PIR zero eventi in 7,05 h (≤ 0,43/h);
LD2420 26,2/h tarato → 5,4/h con il gate 0 alzato, con rimando a 4.12.
Via: equazione display, nota sulla temperatura, letteratura (<0,05/h).

### 4.3 La persona ferma (2 pag.)
Resta: fermo seduto 2,3 m, 99,78 ± 0,49 % vs 0,00 % (tabellina 3 righe o solo
testo); fig02 timeline sotto il banco (proposta: aggiungere un pannello con la
timeline di un trial a 2,3 m, così la figura mostra entrambe le geometrie);
**che cosa misura il bit del PIR**: fig07, 195 impulsi da 3,46 ± 0,09 s in L, in H si
concatenano fino a 61 s, quindi la percentuale conta eventi; un paragrafo di 5 righe
che dichiara la fase 1 in L e la ripetizione in H delle due serie sensibili, con
rimando alla fig. 2.3 del cap. 2 per il significato di L/H.
Via: tutta la §"ponticello di ritrigger" (110 righe: scoperta, due errori, tab:jumper,
nota operativa), §"come va interpretato il valore percentuale" (fusa in 5 righe), il
pilota da 93 s.

### 4.4 Il tipo di movimento decide il PIR (3 pag.)
Resta: dose-risposta a 1 m (fig01 + tabella: 1,52 / 51,60 ± 21,72 / 85,20 %, radar
100 %); imprevedibilità della zona intermedia (un paragrafo); **figura B nuova**:
PIR sul posto vs attraversamento a 1-5 m (barre affiancate, radar come riga al
100 %), costruita da `movimento_Nm_*` e `attraversamento_*`; la prova del 30/08 a
stimolo radar costante (braccia 2 % vs busto laterale 100 %) in 4 righe; gli
indicatori graduati del radar (energia 78 → 86 → 98, dispersione 20 → 18 → 11 cm) in
un paragrafo con rimando al cap. 7.
Via: §"PIR in movimento" come sezione autonoma (fusa qui), controllo di
comparabilità L/H col radar testimone, robustezza al transitorio (una frase),
artefatto del canale stazionario durante il moto (→ cap. 3 `sec:coda`), il
paragrafo "perché le distanze di questa serie non sono utilizzabili" (una frase in
4.6), tab:attraversamento (diventa la figura B).

### 4.5 Lo scenario DIPME: sotto il banco (2 pag.)
Resta: fig19 a tre sensori (sostituisce fig03, tab:sotto-banco e tab:tre-sensori):
immobile PIR 1,32 / LD2410B 100 / LD2420 98,4; micro 96,52 / 100 / 100; seconda
coppia appaiata con 4.4; localizzazione grossolana (dispersione 14-24 cm contro
1,5 cm a 2,3 m) in un paragrafo; presenza retta dai gate 2-3 su entrambi i radar in
due frasi, con rimando al cap. 3 per i gate stazionari 0-1 nulli.
Via: fig03, tab:gate-sotto-banco e la sua lettura in tre punti, la versione in L,
la lamiera (→ cap. 8), il respiro sotto il banco (→ cap. 7).

### 4.6 Distanza ed energia (2 pag.)
Resta: fig04 + tab:distanza; retta 1,0381·d − 1,32 cm, R² 0,99965, residui < 5 cm,
errore di scala correggibile con un coefficiente; dispersione entro trial (10-26 cm
in cammino, 1,5 cm da fermo); fig05 rigenerata a pannello singolo (energia 99 → 28,
non è una potenza, in una frase); causa del +3,81 % non attribuibile (una frase);
perimetro 1-5 m (una frase).
Via: paragrafo sull'errore relativo non monotono, congettura sul 5 m, "perimetro
sperimentale" esteso.

### 4.7 Latenze (1,5 pag.)
Resta: fig06; una sola tabella con ingresso (5,36 / 5,96 / −0,60 ± 0,35 s, 10/10) e
rilascio (18,36 / 12,96 s, 0 riaccensioni); latenza operativa vs differenza appaiata
(un paragrafo); coda propria ≈ 9 s contro 5 s configurati (un paragrafo).
Via: previsione smentita, punto metodologico sul numero di ripetizioni, limite di
risoluzione a 5 Hz (una frase), confronto con la sessione di validazione.

### 4.8 Copertura angolare e selettività (2 pag.)
Resta: fig20 a tre sensori (radar ≥ ±90°, PIR collassa a 90° e non è ripetibile fra
45 e 75°, LD2420 al fondo a 90°); fig09: con gate massimo 2 la persona a 3 m è a 0 %
e il vicino fermo a 90° è a 0 % a regime, ma il vicino **in movimento** a 90° è al
100 % → la selettività fra banchi non si ottiene dai parametri ma dal montaggio.
Via: il paragrafo sul gate 1 con le citazioni del manuale (→ cap. 3, `sec:soglie`),
tab:selettivita, tab:vicino (una frase: nessuna differenza sopra 2σ), tab:angolare
(è la figura), l'osservazione metodologica sul transitorio a 120 s (in 4.1), la
distanza fuori asse sottostimata (una frase).

### 4.9 Due persone (1 pag.)
Resta: fig08 + tab:due-persone; un bersaglio per canale; B riportata 73,8 / 19,5 /
0,3 %; presenza sempre 100 %; conseguenza: un sensore per banco sì, contatore d'aula no.
Via: sottosezioni "i due canali sono lo strumento" e "che cosa si perde" (fuse in
due paragrafi), controllo preliminare (una frase).

### 4.10 Ostacoli (2,5 pag.)
Resta: fig15 (attenuazione per materiale sui due radar, % e dB) + fig14 (portata
residua con cartongesso, legno, vetro, porta); tab:ostacoli ridotta a materiale /
spessore / attenuazione / PIR a 1 m; il caso del vetro; cartongesso 0,7 dB, la
parete d'aula non è un ostacolo; porta trasparente a 3 m e canale moving al 3 % a
5 m; metallo blocca; energia non convertibile in dB (una frase); LD2420 non
acquisirebbe dietro 10 mm di legno.
Via: baseline poco riproducibile, cartone flessibile, PIR attraverso la porta (una
frase: dato non usato), confondente del movimento laterale, regola di protocollo,
"la domanda del relatore" come titolo, tab:ld2420-attenuazione (è fig15B).

### 4.11 Portata massima in corridoio (1,5 pag.)
Resta: fig17; LD2410B 100 % a 5-6 m e 0 % a 7 m, tetto 8 × 75 = 600 cm misurato
(distanza satura a 600 in 5/5); PIR 5-6 m a metà corsa, 7-8 m al massimo, la velocità
del transito decide (0-6 % vs 30 % a 6 m); LD2420 1-2 m anche con gate 12.
Via: tab:corridoio, fig16 (opzionale o appendice), nota sul trimmer, geometria
dettagliata (va nella didascalia della figura A).

### 4.12 Il secondo radar: che cosa cambia (2 pag.)
I risultati del LD2420 test per test sono **già nelle figure 15, 17, 18, 19, 20**
delle sezioni precedenti. Qui resta solo ciò che non ha un gemello sul LD2410B:
le 4 deroghe in 4 righe; a fabbrica non rilascia (muro a 5 m nel gate 7) e lo
strumento di taratura sottostima il rumore; dose-risposta piatta (41 / 35 / 31 contro
68 → 84 → 99); distanza stantia oltre 1 m (§8 del manuale misurato); rilascio 7,7 s
con ritardo 5 s, quindi era il parametro; gate minimo che non tocca la decisione;
respiro 1/3; fondo corrotto da un corpo vicino all'avvio (due frasi);
tab:ld2420-sintesi; riscontro Dell'Aquila in un paragrafo.
Via: le 400 righe attuali (ridotte a ~100), le sottosezioni per test, "il relatore
ha indicato", il modello del rilascio spiegato in dettaglio.

### 4.13 Sintesi (1,5 pag.)
Resta: tab:sintesi (è la tabella migliore del capitolo); 4 punti dove il mmWave
vince, 4 dove non vince; limiti del setup in mezza pagina (un soggetto, una stanza,
25-29 °C, un esemplare per modello, ripetizioni disomogenee).
Via: "la lettura per il progetto" (è il cap. 8, doppione), i limiti in forma di
elenco a 11 voci.

## Figure

Nuove da produrre:
- **A `fig27_geometrie`** (in `analisi/grafici_schemi.py`): pianta schematica delle
  quattro geometrie di prova. Più le foto del setup (tavolo, sotto il banco,
  corridoio) da scattare.
- **B `fig28_tipo_movimento`** (in `analisi/grafici_tesi_2.py`, funzioni di
  `analizza_test.py`): PIR sul posto vs attraversamento a 1-5 m, radar al 100 %.
  Assorbe tab:attraversamento e il pannello destro di fig05.
- Opzionali: fig02 a due pannelli (2,3 m seduto + sotto il banco); fig05 a pannello
  singolo.

Escono dal cap. 4: fig03 (contenuta in fig19), fig12 (→ cap. 7), fig16 (opzionale
o appendice).

Tabelle che escono: sessioni (→ appendice), jumper, attraversamento (→ fig. B),
gate-sotto-banco, sotto-banco, tre-sensori (→ fig19), selettività, vicino, angolare
(→ fig20), corridoio, ld2420-attenuazione (→ fig15B), respiro-metronomo (→ cap. 7);
le due tabelle delle latenze diventano una.

## Cosa si sposta altrove
- Respiro (metodo, pilota, metronomo, ambiguità di ottava, criterio) → **cap. 7**
- Registro delle sessioni → **appendice** (o resta nel repository)
- Lettura per il progetto, architettura ibrida, lamiera → **cap. 8**
- Gate 1 e contraddizione del protocollo, artefatto stazionario in moto → **cap. 3**
- Riscontro Dell'Aquila → un paragrafo in 4.12 (o cap. 3, §LD2420)

## Da sistemare comunque nella riscrittura
- 129 trattini lunghi e molti due punti introduttivi: vietati dallo stile della tesi.
- Citazioni testuali in inglese dei manuali (§1.2.2, §2.2.3 del protocollo, §5.2 del
  manuale): parafrasare e citare.
- Il cap. 4 rimanda a questi label che il cap. 2 e il cap. 3 devono conservare:
  cap. 2 `sec:pir-principio`, `sec:fresnel`, `sec:pir-temperatura`,
  `sec:respiro-teoria`; cap. 3 `sec:hcsr501`, `sec:protocollo-seriale`,
  `sec:saturazione`, `sec:senergy-zero`, `sec:coda`, `sec:soglie`, `tab:soglie`,
  `tab:identita`, `sec:ld2420-stato`. Da allineare con la chat del cap. 3.
