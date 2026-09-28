# PIR e radar mmWave per il rilevamento di persone in scenari post-sisma

Repository della tesi di laurea triennale in Informatica (Classe L-31) *Analisi sperimentale
di sensori radar mmWave e PIR per il rilevamento di persone in scenari post-sisma*,
Università degli Studi di Camerino, A.A. 2025/2026.

- **Laureando:** Stefano De Bernardinis
- **Relatore:** Prof. Massimo Callisto De Donato

La tesi confronta un sensore PIR (HC-SR501) con due moduli radar mmWave a 24 GHz
(HLK-LD2410B e HLK-LD2420) per capire quale rilevi con maggiore affidabilità una persona
rifugiata sotto un arredo dopo un sisma. Lo scenario applicativo è quello del progetto
DIPME, i cui nodi integrati negli arredi scolastici affidano oggi la presenza a un PIR.

Il repository contiene tutto ciò che serve a rifare il lavoro: i sorgenti della tesi, i
firmware per l'ESP32, gli script di acquisizione e di analisi e i dati della campagna
sperimentale, che sono l'unico contenuto non ricostruibile.

## Risultati in breve

- **Persona immobile.** Con la persona ferma, anche sotto il banco, il PIR l'ha rilevata
  in meno del 2 % del tempo, il radar HLK-LD2410B nel 100 % dei casi in tutti gli scenari di
  confronto. A decidere se il PIR vede è il tipo di movimento, non la distanza.
- **Ostacoli e falsi positivi.** L'HLK-LD2410B rileva la persona attraverso legno, vetro,
  cartongesso e plastica, che bloccano il PIR, e a stanza vuota non ha dato falsi positivi in
  oltre 6 ore con le soglie di fabbrica.
- **Secondo radar.** L'HLK-LD2420 conferma il comportamento, con limiti attribuiti
  all'esemplare in prova, che vede una persona solo entro circa 2 m.
- **Indice di vitalità.** Sulle energie per gate del radar è calcolato a bordo dell'ESP32 un
  indice a tre classi che, oltre alla presenza, stima quanto la persona si muove.
- **Consumi.** Il radar consuma circa mille volte più del PIR: la conclusione è che deve
  affiancarlo e non sostituirlo, con il PIR che decide quando accenderlo.

La campagna conta 444 trial validi. I dettagli sono nei capitoli 5-7 della tesi.

## Contenuto

| Cartella / file | Contenuto |
|---|---|
| `overleaf/` | Sorgenti LaTeX della tesi (classe `unicam_thesis`), file `0) Abstract.tex` … `9) Ringraziamenti.tex`, `biblio.bib` |
| `overleaf/Immagini/` | Tutte le immagini della tesi; in `origin/` le versioni PDF vettoriali delle figure generate |
| `firmware/` | Sketch Arduino per l'ESP32: logger dei due radar, web UI, sketch di configurazione e di diagnostica |
| `acquisizione/` | `acquire.py` (acquisizione dalla seriale con i metadati del trial) e `serie.py` (serie di trial consecutivi) |
| `data/` | I CSV della campagna, un file per trial (`<scenario>_Txx.csv`), e `REGISTRO_SESSIONI.md` |
| `analisi/` | Script di analisi e script che generano le figure della tesi, il foglio Excel e il catalogo delle figure |
| `analisi/approfondimenti/` | Documenti di analisi e di progetto scritti durante il lavoro (PIR, consumi, vitalità, web UI) |
| `HLK-LD2410x/` | Il repository di riferimento da cui è partito il lavoro (firmware PlatformIO, README), la documentazione ufficiale del LD2410B e gli script di diagnostica via adattatore USB-seriale |
| `HLK-LD2420/` | Documentazione ufficiale del LD2420, backup delle configurazioni lette e scritte col tool del produttore, script di diagnostica |
| `tools/` | I tool per PC di Hi-Link per i due radar (copie locali, distribuiti dal produttore) |
| `PIANO_TEST.md`, `PIANO_TEST_LD2420.md` | Piani della campagna sperimentale, test per test |
| `CLAUDE.md` | Diario tecnico del progetto: decisioni, verifiche e stato di avanzamento |

## Hardware e collegamenti

ESP32-WROOM-32 (scheda da 30 pin), HLK-LD2410B, HLK-LD2420, HC-SR501.

| Sensore | Piedino | ESP32 |
|---|---|---|
| HLK-LD2410B | VCC / GND | VIN (5 V) / GND |
| | UART_Tx / UART_Rx | GPIO25 (RX2) / GPIO26 (TX2), 256000 baud |
| HLK-LD2420 | 3V3 / GND | 3V3 / GND (**3,3 V, non 5 V**) |
| | OT1 (TX) / RX | GPIO16 / GPIO17, 115200 baud |
| HC-SR501 | VCC / GND / OUT | VIN (5 V) / GND / GPIO34 |

Le linee seriali sono incrociate (il TX del radar va sul RX dell'ESP32). I dettagli sono
nelle Tabelle 3.2, 3.8 e 3.13 della tesi.

## Come si usa

### Ambiente Python

Dalla radice del repository:

```
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install pyserial numpy matplotlib openpyxl pillow
```

Per la sola acquisizione basta `pyserial`.

### Firmware

Arduino IDE 2.x con il supporto *esp32 by Espressif Systems*, scheda **ESP32 Dev Module**.

| Sketch | Uso | Note |
|---|---|---|
| `firmware/ld2410b_logger` | CSV a 5 Hz del LD2410B in engineering mode + PIR | libreria MyLD2410 |
| `firmware/ld2420_logger_bin` | CSV a 5 Hz del LD2420 in energy mode (16 energie per gate) | `PIR_COLLEGATO` a 1 solo se il PIR è cablato (GPIO21), altrimenti la colonna vale -1 |
| `firmware/ld2410b_web` | Web UI: Access Point, dashboard in tempo reale, export CSV, indice di vitalità a bordo | librerie MyLD2410, ArduinoJson, *ESP Async WebServer* e *Async TCP* di ESP32Async; *Partition Scheme* = *Huge APP (3MB No OTA/1MB SPIFFS)* |
| `firmware/test*`, `ld2420_monitor` | Configurazione dei parametri via UART e diagnostica | |

Dopo ogni modifica ai file in `firmware/ld2410b_web/web/` va rigenerata la pagina compressa
prima di compilare:

```
python firmware/ld2410b_web/embed_web.py
```

**Web UI.** Il nodo crea la rete Wi-Fi `DIPME-Sensor` (password `dipme2026`, in
`config.h`) e serve la dashboard su `http://192.168.4.1/`. Per registrare e scaricare il CSV
va aperta nel browser: la finestra del portale captive che si apre da sola non scarica file.

### Acquisizione

Con l'ESP32 collegato via USB (nell'esempio sulla COM3), dalla radice del repository:

```
# un trial
python acquisizione\acquire.py --port COM3 --duration 80 --output data\prova_T01.csv --scenario prova --trial T01 --ground_truth_presence 1 --ground_truth_state moving

# cinque trial di fila, con i nomi dei file assegnati da serie.py
python acquisizione\serie.py --scenario movimento_2m --gt-state moving
```

`acquire.py` resetta l'ESP32 all'apertura della porta: va lanciato **prima** di collegarsi
alla web UI, e nessun altro programma (monitor seriale compreso) deve tenere aperta la porta.
`serie.py` non sovrascrive file esistenti senza `--force`. Ogni sessione va annotata in
`data/REGISTRO_SESSIONI.md`.

### Analisi

```
python analisi\verifica_engineering.py data\prova_T01.csv          # qualità del CSV
python analisi\analizza_test.py data\movimento_2m_*.csv --salta-inizio 20
python analisi\analizza_respiro.py data\respiro_2m_10_T01.csv --scan --salta-inizio 40
python analisi\rigenera_tutto.py
```

`rigenera_tutto.py` rifà dai CSV i grafici della tesi (in `overleaf/Immagini/`), il foglio
Excel `analisi/dati_tesi.xlsx` e il catalogo delle figure `CATALOGO_FIGURE.html`, stampato
anche in PDF se trova Chrome o Edge. Gli schemi che non derivano dai dati (PIR a due
elementi, lente di Fresnel, modalità del PIR, FMCW, geometrie di prova, collegamenti,
piattaforma, percorsi dei dati) si rigenerano con `analisi/grafici_schemi.py` e `analisi/grafici_schemi_cap3.py`. A dati
invariati le figure escono identiche byte per byte. Il nome con cui ogni figura finisce nella
tesi è in `analisi/uscita_figure.py`.

### Tesi

I sorgenti in `overleaf/` sono gli stessi del progetto Overleaf e si compilano con pdfLaTeX
e BibTeX (`pdflatex`, `bibtex`, `pdflatex`, `pdflatex` su `tesi.tex`). Nei tex le immagini
sono richiamate col solo nome: le trova `\graphicspath{{Immagini/}}`.

## Dati

Ogni CSV ha le 9 colonne comuni ai firmware, le colonne proprie del radar (20 per il
LD2410B, 18 per il LD2420) e le 6 colonne di metadati aggiunte da `acquire.py`; il CSV
esportato dalla web UI ha in più le 2 colonne dell'indice di vitalità (Tabella 3.16 della
tesi). In `data/` ci sono anche controlli del fondo, prove tecniche e file marcati come non
validi: l'elenco di quelli esclusi dalle statistiche, con il motivo, è in
`analisi/esporta_excel.py` (`ESCLUSIONI`) e nel foglio `file_esclusi` dell'Excel.

## Crediti

- Il firmware e lo script di acquisizione di partenza vengono dal repository
  [massimocallisto/HLK-LD2410x](https://github.com/massimocallisto/HLK-LD2410x).
- La web UI usa [Chart.js](https://www.chartjs.org/), incluso in `firmware/ld2410b_web/web/`.
- Manuali, protocolli e tool per PC dei moduli radar sono del produttore, Shenzhen Hi-Link
  Electronic Co., Ltd.; le copie locali servono solo come riferimento.
