#!/usr/bin/env python3
"""
Costruisce il catalogo delle figure della tesi, ciascuna con la spiegazione di cosa mostra.

    python analisi/genera_pagina.py

Legge i PNG prodotti da analisi/grafici_tesi.py e grafici_tesi_2.py, li incorpora nella pagina come
data URI in formato WebP - nessun file esterno, quindi la pagina si apre offline
e si puo' mandare per mail cosi' com'e' - e scrive CATALOGO_FIGURE.html nella
radice del progetto.

Va lanciato DOPO i due script delle figure, altrimenti incorpora le figure vecchie.
Di norma non si lancia a mano: ci pensa analisi/rigenera_tutto.py.
"""
import base64
import io
from pathlib import Path

from PIL import Image

RADICE = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from uscita_figure import PNG as FIGURE, nome_file  # noqa: E402
OUTFILE = RADICE / "CATALOGO_FIGURE.html"

# Le PNG a 300 dpi servono a LaTeX; per la pagina bastano 1200 px di larghezza,
# che tengono il file incorporato sotto il megabyte.
LARGHEZZA_MAX = 1200


def carica_figure():
    """Ogni .png della tesi diventa un data URI WebP, indicizzato per nome senza estensione."""
    if not FIGURE.is_dir():
        raise SystemExit(f"Cartella figure assente: {FIGURE}\n"
                         "Lancia prima:  python analisi/grafici_tesi.py")
    out = {}
    for f in sorted(FIGURE.glob("*.png")):
        im = Image.open(f).convert("RGB")
        if im.width > LARGHEZZA_MAX:
            im = im.resize((LARGHEZZA_MAX, int(im.height * LARGHEZZA_MAX / im.width)),
                           Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=88, method=5)
        out[f.stem] = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
    if not out:
        raise SystemExit(f"Nessuna figura in {FIGURE}: lancia prima grafici_tesi.py")
    return out


FIGS = carica_figure()


def fig(nome, didascalia, numero):
    nome = nome_file(nome)
    if nome not in FIGS:
        raise SystemExit(f"Figura mancante: {nome}.png. Rilancia grafici_tesi.py.")
    return f'''<figure class="fig">
  <img src="{FIGS[nome]}" alt="{didascalia[:110]}">
  <figcaption><span class="fignum">Fig. {numero}</span>{didascalia}</figcaption>
</figure>'''


CSS = """
:root{
  --ground:#EDF1F4; --surface:#FFFFFF; --surface-2:#F5F8FA;
  --ink:#16202A; --ink-2:#3D4C58; --muted:#66757F;
  --rule:#D3DCE3; --rule-strong:#B6C4CE;
  --radar:#1B6CA8; --pir:#D1495B; --ok:#2E7D5B; --wip:#B8791C;
  --shadow:0 1px 2px rgba(22,32,42,.06), 0 8px 24px rgba(22,32,42,.05);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#0D1318; --surface:#151F27; --surface-2:#1B262F;
    --ink:#E3EAEF; --ink-2:#B4C2CC; --muted:#8496A2;
    --rule:#26343E; --rule-strong:#384A56;
    --radar:#5FA8D9; --pir:#E9788A; --ok:#5FBE92; --wip:#DDA84A;
    --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px rgba(0,0,0,.3);
  }
}
:root[data-theme="dark"]{
  --ground:#0D1318; --surface:#151F27; --surface-2:#1B262F;
  --ink:#E3EAEF; --ink-2:#B4C2CC; --muted:#8496A2;
  --rule:#26343E; --rule-strong:#384A56;
  --radar:#5FA8D9; --pir:#E9788A; --ok:#5FBE92; --wip:#DDA84A;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px rgba(0,0,0,.3);
}

*{box-sizing:border-box}
body{
  margin:0; background:var(--ground); color:var(--ink);
  font-family:"IBM Plex Serif",Georgia,"Times New Roman",serif;
  font-size:16.5px; line-height:1.62;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:920px; margin:0 auto; padding:0 24px 96px}
.prose{max-width:66ch}

h1,h2,h3,.eyebrow,.chip,.stat,.ledger,table,figcaption,.fignum,.tag{
  font-family:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
}
.mono,.stat-n,.ledger td.n,.fignum,code{
  font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;
  font-variant-numeric:tabular-nums;
}

/* ---- testata ---- */
header.top{
  border-bottom:2px solid var(--ink); margin-bottom:40px;
  padding:56px 0 26px;
}
.eyebrow{
  font-size:11.5px; font-weight:600; letter-spacing:.13em; text-transform:uppercase;
  color:var(--radar); margin:0 0 14px;
}
h1{
  font-size:clamp(30px,5.2vw,44px); line-height:1.12; font-weight:600;
  letter-spacing:-.02em; margin:0 0 16px; text-wrap:balance;
}
.dek{font-size:19px; color:var(--ink-2); margin:0 0 26px; max-width:60ch}
.meta{
  display:flex; flex-wrap:wrap; gap:8px 26px; font-size:12.5px; color:var(--muted);
  letter-spacing:.02em;
}
.meta b{color:var(--ink-2); font-weight:600}

/* ---- numeri in evidenza ---- */
.stats{
  display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  gap:1px; background:var(--rule); border:1px solid var(--rule);
  margin:36px 0 44px;
}
.stat{background:var(--surface); padding:18px 18px 16px}
.stat-n{display:block; font-size:26px; font-weight:600; letter-spacing:-.02em; line-height:1.1}
.stat-l{display:block; font-size:12px; color:var(--muted); margin-top:6px; line-height:1.4}
.stat.r .stat-n{color:var(--radar)}
.stat.p .stat-n{color:var(--pir)}

/* ---- sezioni ---- */
section{margin:0 0 12px; padding-top:44px}
h2{
  font-size:13px; font-weight:600; letter-spacing:.12em; text-transform:uppercase;
  color:var(--muted); margin:0 0 6px; padding-bottom:10px;
  border-bottom:1px solid var(--rule-strong);
  display:flex; align-items:baseline; gap:12px;
}
h2 .obj{
  color:var(--ink); font-family:"IBM Plex Mono",monospace; font-size:12px;
  border:1px solid var(--rule-strong); padding:2px 7px; letter-spacing:.04em;
}
h3{font-size:21px; font-weight:600; letter-spacing:-.01em; margin:26px 0 10px; text-wrap:balance}
p{margin:0 0 16px}
.lead{font-size:18px; color:var(--ink-2)}

/* ---- ledger obiettivi ---- */
.ledger{width:100%; border-collapse:collapse; font-size:14px; margin:8px 0 8px}
.ledger th{
  text-align:left; font-size:11px; letter-spacing:.1em; text-transform:uppercase;
  color:var(--muted); font-weight:600; padding:0 12px 9px 0;
  border-bottom:1px solid var(--rule-strong);
}
.ledger td{padding:13px 12px 13px 0; border-bottom:1px solid var(--rule); vertical-align:top}
.ledger td.n{width:26px; color:var(--muted); font-size:13px; padding-right:16px}
.ledger td.what{font-weight:500; width:32%}
.ledger td.ev{color:var(--ink-2); font-size:13.5px; line-height:1.5}
.chip{
  display:inline-block; font-size:11px; font-weight:600; letter-spacing:.05em;
  padding:3px 9px; white-space:nowrap; border:1px solid;
}
.chip.done{color:var(--ok); border-color:var(--ok)}
.chip.wip{color:var(--wip); border-color:var(--wip)}

/* ---- figure ---- */
.fig{margin:26px 0 32px}
.fig img{
  display:block; width:100%; height:auto; background:#fff;
  border:1px solid var(--rule); box-shadow:var(--shadow);
}
figcaption{
  font-size:12.5px; color:var(--muted); line-height:1.55; margin-top:11px;
  padding-left:2px;
}
.fignum{
  color:var(--radar); font-weight:600; font-size:11.5px; letter-spacing:.06em;
  margin-right:9px; text-transform:uppercase;
}

/* ---- callout risultato ---- */
.key{
  background:var(--surface); border:1px solid var(--rule);
  border-left:3px solid var(--radar); padding:22px 24px; margin:28px 0;
  box-shadow:var(--shadow);
}
.key h3{margin-top:0}
.key ol{margin:0; padding-left:20px}
.key li{margin-bottom:9px}
.key li:last-child{margin-bottom:0}

.warn{border-left-color:var(--pir)}

/* ---- tabella dati ---- */
.tw{overflow-x:auto; margin:20px 0 26px}
table.data{
  border-collapse:collapse; font-size:13.5px; min-width:100%;
  font-family:"IBM Plex Sans",sans-serif;
}
table.data th{
  text-align:left; font-size:11px; letter-spacing:.08em; text-transform:uppercase;
  color:var(--muted); font-weight:600; padding:0 18px 9px 0;
  border-bottom:1px solid var(--rule-strong); white-space:nowrap;
}
table.data td{
  padding:10px 18px 10px 0; border-bottom:1px solid var(--rule);
  white-space:nowrap; font-variant-numeric:tabular-nums;
}
table.data td.lbl{white-space:normal; font-weight:500}
td.rad{color:var(--radar); font-weight:600}
td.pir{color:var(--pir); font-weight:600}

.tag{
  display:inline-block; font-size:11px; letter-spacing:.06em; text-transform:uppercase;
  color:var(--muted); border:1px solid var(--rule-strong); padding:2px 8px; margin-right:6px;
}
ul.plain{padding-left:20px; margin:0 0 16px}
ul.plain li{margin-bottom:8px}
footer{
  margin-top:64px; padding-top:22px; border-top:2px solid var(--ink);
  font-size:12.5px; color:var(--muted);
}
code{
  font-size:.88em; background:var(--surface-2); padding:1px 5px;
  border:1px solid var(--rule);
}

/* ---- stampa / PDF ---- */
@page{ size:A4; margin:15mm 14mm 16mm; }
@media print{
  /* In stampa si forza sempre la tavolozza chiara: un PDF su fondo scuro
     e' illeggibile fotocopiato e spreca toner. */
  :root, :root[data-theme="dark"], :root:not([data-theme="light"]){
    --ground:#FFFFFF; --surface:#FFFFFF; --surface-2:#F5F8FA;
    --ink:#16202A; --ink-2:#3D4C58; --muted:#5B6B77;
    --rule:#D3DCE3; --rule-strong:#9FB0BC;
    --radar:#1B6CA8; --pir:#C03B4D; --ok:#256B4C; --wip:#96620F;
    --shadow:none;
  }
  body{ background:#fff; font-size:10.2pt; line-height:1.5; }
  .wrap{ max-width:none; padding:0; }
  .prose{ max-width:none; }

  header.top{ padding:0 0 14px; margin-bottom:22px; }
  h1{ font-size:23pt; margin-bottom:10px; }
  .dek{ font-size:11.5pt; margin-bottom:14px; }
  .stats{ margin:20px 0 26px; }
  .stat-n{ font-size:15pt; }
  .stat-l{ font-size:8pt; }

  section{ padding-top:22px; }
  h2{ font-size:9pt; }
  h3{ font-size:13pt; }
  .lead{ font-size:11pt; }
  figcaption{ font-size:8.4pt; }
  table.data, .ledger{ font-size:9pt; }

  /* Niente titoli orfani in fondo alla pagina, niente figure spezzate. */
  h1,h2,h3{ break-after:avoid; page-break-after:avoid; }
  .fig,.key,.stats,tr,figcaption{ break-inside:avoid; page-break-inside:avoid; }
  .fig img{ max-height:96mm; width:auto; max-width:100%; margin:0 auto; }
  .fig{ text-align:center; margin:16px 0 20px; }
  section{ padding-top:16px; }
  p{ margin:0 0 11px; }
  figcaption{ text-align:left; }
  footer{ break-inside:avoid; }
  a{ color:inherit; text-decoration:none; }
}

@media (max-width:640px){
  body{font-size:16px}
  .ledger td.what{width:auto}
  .ledger, .ledger tbody, .ledger tr, .ledger td{display:block; width:auto}
  .ledger thead{display:none}
  .ledger tr{border-bottom:1px solid var(--rule-strong); padding:12px 0}
  .ledger td{border:0; padding:2px 0}
}
"""

HTML = f"""<title>Sensori di presenza per DIPME</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&display=swap">
<style>{CSS}</style>

<div class="wrap">

<header class="top">
  <p class="eyebrow">Tesi triennale · Progetto DIPME · Catalogo delle figure</p>
  <h1>PIR e mmWave a confronto per il rilevamento di persone sotto gli arredi</h1>
  <p class="dek">Il sensore piroelettrico fa bene un lavoro che non è questo. Trentadue ore di
  acquisizioni su tre sensori dicono perché, e quanto.</p>
  <p class="meta">
    <span><b>Relatore</b> Massimo Callisto</span>
    <span><b>Hardware</b> ESP32 · HLK-LD2410B · HLK-LD2420 · HC-SR501</span>
  </p>
</header>

<div class="stats">
  <div class="stat r"><span class="stat-n">444</span><span class="stat-l">trial validi in 32,1 h, tre sensori</span></div>
  <div class="stat r"><span class="stat-n">577 437</span><span class="stat-l">campioni a 5 e 10 Hz, jitter zero</span></div>
  <div class="stat r"><span class="stat-n">0,00 %</span><span class="stat-l">falsi negativi del radar, in ogni scenario</span></div>
  <div class="stat p"><span class="stat-n">98,7 %</span><span class="stat-l">falsi negativi del PIR sulla persona immobile</span></div>
</div>

<section id="risultato">
  <h2><span class="obj">Obiettivo 3</span> Il risultato centrale</h2>

  <div class="key">
    <h3>La tesi in tre frasi, come esce dai dati</h3>
    <ol class="prose">
      <li>Il PIR, configurato correttamente ed entro un metro, è un ottimo rilevatore di
      <b>movimento</b>.</li>
      <li>È praticamente cieco alla persona <b>immobile</b>, a qualunque distanza e in
      qualunque configurazione.</li>
      <li>Il radar mmWave rileva entrambe le condizioni al 100 % in tutti i test svolti.</li>
    </ol>
    <p style="margin:14px 0 0; font-size:14.5px; color:var(--muted)">Per DIPME, dove la
    persona intrappolata può essere incosciente o esausta e quindi immobile, il PIR non è
    adeguato e il mmWave è necessario.</p>
  </div>

  <p class="prose">L'esperimento che lo dimostra tiene fissa ogni variabile — distanza,
  postura, configurazione del sensore, setup — e ne cambia una sola: quanto il soggetto si
  muove. Il PIR segue il movimento in modo monotono; il radar resta al 100 % ovunque.</p>

  {fig("fig01_dose_risposta",
       "Curva dose-risposta a 1 m con jumper H, cioè nella configurazione più favorevole al PIR. "
       "Fra le colonne cambia solo la quantità di movimento. Da notare la dispersione nella zona "
       "intermedia: ±21,7 su 51,6. Vicino alla soglia il PIR non è solo meno sensibile, è "
       "imprevedibile — e per un'applicazione salvavita l'imprevedibilità è peggio di un limite noto.",
       1)}

  <p class="prose">La stessa dimostrazione, ripetuta nella geometria reale del progetto — sensore
  fissato sotto il piano del banco, soggetto rannicchiato a circa 60 cm — dà un contrasto ancora
  più netto. A quella distanza il PIR è un rilevatore di movimento quasi perfetto, e resta
  completamente cieco alla persona ferma.</p>

  {fig("fig03_dipme_sotto_banco",
       "Scenario DIPME, 5 trial per condizione, entrambe le serie in modalità H: il confronto è "
       "perfettamente appaiato, senza asterischi da mettere in tesi.", 3)}

  {fig("fig02_timeline_sotto_banco",
       "Un singolo trial da 5 minuti, per vedere la cosa nel tempo invece che in media. Il radar "
       "tiene la presenza senza un buco; il PIR non emette un solo impulso in tutta l'acquisizione.",
       2)}
</section>

<section id="perche">
  <h2><span class="obj">Obiettivo 3</span> Perché il PIR fallisce</h2>
  <p class="prose">Non è una questione di taratura o di qualità del componente. L'uscita
  dell'HC-SR501 non è una misura di presenza: è un <b>monostabile</b> che ogni evento di
  movimento alza per un tempo fisso. Il sensore non misura quanto a lungo qualcuno è
  presente — <b>conta eventi</b>.</p>

  {fig("fig07_impulsi_pir",
       "181 impulsi in modalità L, tutti fra 3,4 e 3,8 s, nessuno oltre i 5: la durata non si "
       "allunga nemmeno con movimento continuo. In modalità H il ritrigger li concatena, e i più "
       "lunghi arrivano a coprire l'intero trial. Il tasso di rilevamento apparente del PIR è quindi "
       "il prodotto fra numero di eventi e tempo di ritenuta impostato col trimmer, non una misura "
       "di presenza.", 7)}

  <div class="key warn">
    <h3>Una correzione che ci siamo fatti da soli</h3>
    <p style="margin:0" class="prose">Tutta la fase 1 era stata acquisita con il jumper in
    posizione L. In quella configurazione il PIR sembrava sbagliare anche sulla persona
    <i>in movimento</i> (80,5 % di falsi negativi). Ripetendo la serie in H lo stesso
    scenario dà 14,8 %: l'affermazione era un artefatto della configurazione. I due
    risultati portanti — persona immobile a 2,3 m e sotto il banco — sono invece intatti,
    perché lì il PIR non genera alcun trigger e il jumper agisce solo <i>dopo</i> un
    trigger. Le coppie mostrate sopra sono state comunque tutte rifatte in H.</p>
  </div>
</section>

<section id="caratterizzazione">
  <h2><span class="obj">Obiettivo 3</span> Caratterizzazione quantitativa del radar</h2>
  <p class="prose">Oltre al confronto, il radar è stato caratterizzato come strumento di
  misura: accuratezza della distanza, portata, tempi di reazione, comportamento con più
  persone e selettività spaziale.</p>

  {fig("fig04_distanza_regressione",
       "Il radar è estremamente lineare (R² = 0,99965) ma ha un errore di scala del +3,81 % con "
       "offset praticamente nullo. È quindi correggibile con un solo coefficiente: dividendo per "
       "1,0381 l'errore residuo scende sotto i 5 cm a tutte le distanze. La causa del +3,81 % non è "
       "attribuibile con questi dati — servirebbe un riferimento indipendente, tipo un metro laser.",
       4)}

  {fig("fig05_energia_distanza",
       "A sinistra il decadimento dell'energia con la distanza; a destra la portata utile del PIR "
       "con movimento sul posto. Non è un degrado graduale: fra 1 e 2 metri il PIR passa da "
       "«funziona bene» a «non vede niente».", 5)}

  {fig("fig06_latenze",
       "A sinistra le latenze appaiate all'ingresso: il radar rileva per primo in 10 trial su 10. "
       "Le latenze assolute (~5-6 s) contengono il tragitto e il tempo di reazione all'annuncio, "
       "quindi sono una latenza operativa; la grandezza pulita è la differenza appaiata, dove quei "
       "termini si cancellano. A destra il rovescio della medaglia: il radar impiega 18 s a "
       "dichiarare la stanza vuota, contro un timeout dichiarato di 5.", 6)}

  {fig("fig08_due_persone",
       "Il limite del modulo va formulato con precisione: non «riporta un solo bersaglio», ma "
       "«riporta un bersaglio per canale». Separa bene due persone in stati diversi; in fila, chi "
       "sta dietro è invisibile. In tutti i casi la presenza resta al 100 %: si perde il conteggio, "
       "mai il rilevamento. Questo rafforza l'architettura distribuita del progetto — un sensore "
       "per banco — invece di indebolirla.", 8)}

  {fig("fig09_selettivita",
       "Riducendo il gate massimo a 2 la portata si taglia a 150 cm e la selettività funziona: a "
       "3 m zero rilevamenti, e il vicino a 90° non viene rilevato da fermo. Il 24,8 % nella "
       "finestra standard non è un rilevamento, è la coda di presenza residua dal posizionamento, "
       "che negli scenari di selettività dura fino a 101 s.", 9)}
</section>

<section id="dati">
  <h2><span class="obj">Obiettivo 2</span> Che dati producono davvero i due sensori</h2>
  <p class="prose">È la differenza che rende possibile tutto il resto. Nello stesso istante il
  PIR produce un bit, il radar produce diciotto canali di energia più due distanze, cinque
  volte al secondo.</p>

  {fig("fig10_gate_engineering",
       "Engineering mode del LD2410B. In alto i 9 gate del canale moving, con sovrapposto il gate "
       "atteso calcolato dalla distanza riportata: la mappa gate↔distanza si verifica al 98,3 %. "
       "In mezzo i 9 gate stazionari — si vede che i gate 0 e 1 sono sempre nulli, coerentemente "
       "con la Tabella 7 del protocollo. In basso, quello che i due sensori dichiarano: il radar "
       "una presenza continua, il PIR una sequenza di impulsi isolati.", 10)}

  {fig("fig11_saturazione",
       "Il limite del dato, da dichiarare in tesi: l'energia è un intero 0-100 e sul bersaglio "
       "vicino il canale stazionario satura al fondoscala nel 100 % dei campioni. Un segnale "
       "clippato non porta informazione, e non lo risolvono né le soglie né l'auto-calibrazione: "
       "sono rimedi geometrici. È il motivo per cui respiro e vitalità vanno cercati sul canale "
       "moving.", 11)}

  {fig("fig12_respiro",
       "Il micro-movimento respiratorio su un soggetto immobile a 2,3 m, estratto per FFT "
       "dall'energia per-gate. Il picco cade in piena banda respiratoria e il valore è "
       "fisiologicamente plausibile per un adulto seduto. Manca ancora la ground truth: la prova "
       "vera è il test a metronomo, dove si confronta la stima con un ritmo imposto noto.", 12)}
</section>

<section id="consumi">
  <h2><span class="obj">Obiettivo 4</span> Consumo energetico</h2>
  <p class="prose">Trattato a titolo informativo su dati di datasheet, come concordato: non
  disponiamo di strumentazione di misura. Il rapporto fra i due sensori è però così ampio —
  tre ordini di grandezza — che nessuna incertezza di misura cambierebbe la conclusione.</p>

  {fig("fig13_consumi",
       "Il PIR può funzionare da sveglia a costo quasi nullo, risvegliando l'ESP32 dal deep-sleep "
       "via interrupt; il radar costa tre ordini di grandezza in più ed è pensato per alimentazione "
       "fissa. Le 13-20 ore di autonomia del nodo radar coprono la finestra critica dei soccorsi; "
       "per le 72 ore servirebbe duty-cycling o batteria maggiorata.", 13)}

  <div class="key">
    <h3>La conseguenza per l'architettura</h3>
    <p style="margin:0" class="prose">Il PIR non è un concorrente del radar ma il guardiano a
    basso costo che decide quando accenderlo. In tempo di pace tutto dorme; al trigger di
    «modalità terremoto» si sveglia l'ESP32 e si accende il mmWave per il rilevamento fine.
    Questo lega l'obiettivo 4 al contesto DIPME e giustifica la <b>coesistenza</b> dei due
    sensori nel DIPME-DEVICE, invece della sostituzione secca.</p>
  </div>
</section>

<section id="settembre">
  <h2><span class="obj">Obiettivi 3 · 5 · 6</span> La campagna di settembre</h2>
  <p class="prose">Le due richieste del professore dell'incontro del 29 agosto — quantificare
  l'attenuazione degli ostacoli e misurare la portata massima dei tre sensori — più la
  caratterizzazione del secondo radar e il porting dell'indice di vitalità sull'ESP32.
  L'esemplare di LD2420 in dotazione vede una persona solo fino a ~2 m (trasmettitore
  ~20-25 dB sotto progetto): ogni suo numero è attribuito all'esemplare, non al modello, come
  indicato dal professore.</p>

  {fig("fig14_portata_ostacoli",
       "Test 3.6, LD2410B: nessun dielettrico accorcia la portata entro i 5 m della stanza, nemmeno "
       "la porta interna chiusa. A: energia moving con cartongesso a 1-5 m e legno, vetro e porta a "
       "3-5 m — presenza 100 % e distanza corretta in tutti i 39 trial con ostacolo. B: ciò che "
       "degrada è il canale moving (a 5 m: senza 78 %, cartongesso 44 %, vetro 26 %, legno 19 %, "
       "porta 3 %); la presenza la tiene il canale stazionario. La porta tamburata è trasparente a "
       "3 m e quasi opaca a 5: non spiegato, dichiarato.", 14)}

  {fig("fig15_attenuazione_materiali",
       "Attenuazione per materiale sui due radar, pannello a 20 cm dal sensore. A: LD2410B a 3 m, "
       "riduzione dell'energia moving rispetto alla baseline mediata su 6 trial — l'energia è un "
       "indice 0-100, non una potenza, quindi vale la graduatoria e non la conversione in dB. B: "
       "LD2420 a 1 m, energie a 16 bit grezze, attenuazione in dB: il cartongesso (0,7 dB) attenua "
       "come plastica e cartone, ben sotto vetro e legno; legno e metallo sono limiti inferiori "
       "perché la dinamica dell'esemplare è di 5 dB. Stessa graduatoria su due moduli, due distanze "
       "e due unità di misura.", 15)}

  {fig("fig16_energia_distanza_radar",
       "Fase 8 in corridoio (120 cm di larghezza, muro a 9 m). A: il LD2410B segue la curva della "
       "stanza fino a 6 m, dove la distanza riportata è satura a 600 cm, e a 7 m non riporta "
       "nulla: il limite è il tetto configurato di 8 gate × 75 cm, non la sensibilità. B: "
       "l'esemplare LD2420 con gate massimo 12 (840 cm) sta sopra il fondo del corridoio vuoto "
       "solo a 1-2 m (4,2× e 1,7×, trigger superato nel 14 % e 4 % dei campioni) e da 3 m in su "
       "le sue energie sono indistinguibili dal corridoio vuoto.", 16)}

  {fig("fig17_portata_tre_sensori",
       "Portata dei tre sensori sulla stessa scala, stanza (agosto) e corridoio (settembre). "
       "LD2410B: 100 % fino a 6 m, 0 % a 7 (tetto configurato). PIR a metà corsa: attraversamento "
       "a ~1 m/s rilevato al 99-100 % fino a 5 m e al 2 % a 6 m; con la sensibilità al massimo "
       "100 % a 5-6 m, 57 % a 7 m e 15 % a 8 m. Decide la velocità di transito, non solo la "
       "distanza: un attraversamento veloce a 6 m dà il 30 % anche a metà corsa. LD2420 "
       "(esemplare): si accende entro 1 m (triangoli pieni, campioni sopra il trigger) e mantiene la "
       "presenza fino a 2 m (triangoli vuoti).", 17)}

  {fig("fig18_falsi_positivi",
       "Falsi positivi a stanza vuota di notte, scala logaritmica. LD2410B a soglie di fabbrica: "
       "zero eventi in 6,6 h, quindi si riporta il limite superiore 3/T ≈ 0,5 eventi/h (regola del "
       "tre). LD2420 con le soglie tarate dal tool: 26 riaccensioni/h per 7 h, presenza al 26 % del "
       "tempo con nessuno nella stanza. Portando il solo gate 0 sopra la coda del rumore si scende a "
       "6/h: un pavimento strutturale, perché nei gate 1-2 rumore e persona si sovrappongono. "
       "Conteggi dello script con scarto di 60 s; il registro conta 181 e 5 eventi (26,2 e 5,4/h) "
       "con la sua finestra.", 18)}

  {fig("fig19_dipme_tre_sensori",
       "Lo scenario DIPME a tre sensori: persona immobile e con micro-movimenti, a 1 m in piedi e "
       "sotto il banco. I due radar sono al 100 % in tutte le condizioni (il LD2420 al 98,4 % da "
       "immobile sotto il banco, per un rilascio di 24 s in un trial su cinque); il PIR passa da "
       "1-2 % da fermo a 52-97 % con i micro-movimenti. Il LD2420 è stato provato a settembre nella "
       "stessa geometria, con soglie tarate e scarto del transitorio di 90 s.", 19)}

  {fig("fig20_angolare",
       "Copertura angolare a 1 m, busto laterale da seduto. A: il LD2410B rileva al 100 % fino a "
       "90° e crolla a 120°, ben oltre i ±60° dichiarati; il PIR non è ripetibile fra 45 e 75° "
       "(barre d'errore dell'ordine dell'effetto). B: l'esemplare LD2420 è al fondo a 90°, fascio "
       "utile fino a ~75°: più stretto del LD2410B e più largo dei ±45°/±60° del manuale. È l'unico "
       "punto della campagna in cui il LD2420 fa meglio per DIPME — il vicino in movimento a 90° "
       "non è visto — ma il confine è coerente anche con il margine di 4-6 dB del suo trasmettitore, "
       "quindi va attribuito all'esemplare.", 20)}

  {fig("fig21_vitalita_scenari",
       "Distribuzione dell'indice di vitalità v3 con la configurazione del firmware (gate dalla "
       "distanza riportata, fondo notturno). Le tre classi a 1 m si separano (mediane 23, 77, 100). "
       "Sotto il banco la persona immobile dà 45, a cavallo della soglia bassa/moderata: il 25,7 "
       "della taratura del 31/08 (sesta scatola) nasceva dal gate fisso 2, che a 60 cm vede solo "
       "un'eco indiretta della persona. Le soglie tarate a 1 m non si trasferiscono sotto il banco; "
       "la discriminazione immobile / in movimento (96 %) sì. Per DIPME la via è la taratura per "
       "installazione.", 21)}

  {fig("fig22_vitalita_bordo",
       "Verifica del porting sull'ESP32: indice calcolato a bordo (vitality.h) contro il ricalcolo "
       "offline (vitalita_proto.py) sullo stesso CSV esportato dalla web UI. Nei primi 60 s le EWMA "
       "offline devono ancora convergere, quelle del firmware sono già a regime dall'accensione; "
       "dopo, le due curve coincidono entro ±1 nel 100 % dei campioni. L'indice mostrato nella "
       "dashboard è lo stesso della validazione.", 22)}
</section>

<footer>
  <p style="margin:0 0 6px"><span class="tag">Riproducibilità</span> Tutte le cifre di questa
  pagina sono ricalcolate dai CSV grezzi da <code>analisi/grafici_tesi.py</code>,
  <code>analisi/grafici_tesi_2.py</code> e <code>analisi/esporta_excel.py</code>, che riusano le
  stesse funzioni di <code>analizza_test.py</code> del capitolo 4.</p>
  <p style="margin:0">Convenzioni di scarto del transitorio: 20 s negli scenari ordinari,
  40 s sotto il banco, 120 s negli scenari di selettività, 60 s a stanza vuota, 90 s nei trial
  da fermo del LD2420 (rilascio ~55 s).</p>
</footer>

</div>
"""

OUTFILE.write_text(HTML, encoding="utf-8")
print(f"  ok  {OUTFILE.name}  ({len(FIGS)} figure incorporate, "
      f"{len(HTML)/1024/1024:.2f} MB)")
