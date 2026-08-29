#!/usr/bin/env python3
"""
Costruisce la pagina di riepilogo per l'incontro col professore.

    python analisi/genera_pagina.py

Legge i PNG prodotti da analisi/grafici_tesi.py, li incorpora nella pagina come
data URI in formato WebP - nessun file esterno, quindi la pagina si apre offline
e si puo' mandare per mail cosi' com'e' - e scrive RIEPILOGO_INCONTRO.html nella
radice del progetto.

Va lanciato DOPO grafici_tesi.py, altrimenti incorpora le figure vecchie.
Di norma non si lancia a mano: ci pensa analisi/rigenera_tutto.py.
"""
import base64
import io
from pathlib import Path

from PIL import Image

RADICE = Path(__file__).resolve().parent.parent
FIGURE = RADICE / "tesi-unicam" / "figures"
OUTFILE = RADICE / "RIEPILOGO_INCONTRO.html"

# Le PNG a 300 dpi servono a LaTeX; per la pagina bastano 1200 px di larghezza,
# che tengono il file incorporato sotto il megabyte.
LARGHEZZA_MAX = 1200


def carica_figure():
    """Ogni fig*.png diventa un data URI WebP, indicizzato per nome senza estensione."""
    if not FIGURE.is_dir():
        raise SystemExit(f"Cartella figure assente: {FIGURE}\n"
                         "Lancia prima:  python analisi/grafici_tesi.py")
    out = {}
    for f in sorted(FIGURE.glob("fig*.png")):
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

LEDGER = [
    (1, "Studio dei sensori", "done", "completo",
     "Principio piroelettrico del PIR e FMCW 24 GHz del radar, dati prodotti, limiti fisici. "
     "Documentazione ufficiale Hi-Link acquisita per entrambi i moduli."),
    (2, "Analisi dei dati prodotti", "done", "completo",
     "mmWave: 18 canali di energia per-gate + 2 distanze a 5 Hz. PIR: 1 bit, monostabile "
     "da 3,45 s. Misurati anche i limiti del dato (saturazione, gate stazionari 0-1)."),
    (3, "Comparazione con testing numerico", "done", "fasi 0-2 complete",
     "115 trial, 223 291 campioni, 12,4 h di acquisizione. Accuratezza, distanza, latenze, "
     "falsi positivi, due persone, selettività spaziale."),
    (4, "Consumo energetico (informativo)", "done", "completo",
     "80 mA contro 0,05 mA: tre ordini di grandezza. È l'argomento che regge "
     "l'architettura ibrida PIR + mmWave."),
    (5, "Web UI ed export CSV", "wip", "in sviluppo",
     "Due architetture progettate in dettaglio (ESP32 self-hosted / server esterno con MQTT). "
     "Serve una decisione prima di implementare."),
    (6, "Indice di vitalità", "wip", "in sviluppo",
     "Specifica v2 scritta e prototipo Python pronto. La base misurata esiste già: "
     "due indicatori continui e monotoni col movimento."),
]


def riga(n, cosa, cls, stato, ev):
    return (f'<tr><td class="n">{n}</td><td class="what">{cosa}</td>'
            f'<td><span class="chip {cls}">{stato}</span></td>'
            f'<td class="ev">{ev}</td></tr>')


HTML = f"""<title>Sensori di presenza per UPRISE</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&display=swap">
<style>{CSS}</style>

<div class="wrap">

<header class="top">
  <p class="eyebrow">Tesi triennale · Progetto UPRISE · Stato di avanzamento</p>
  <h1>PIR e mmWave a confronto per il rilevamento di persone sotto gli arredi</h1>
  <p class="dek">Il sensore piroelettrico fa bene un lavoro che non è questo. Dodici ore di
  acquisizioni dicono perché, e quanto.</p>
  <p class="meta">
    <span><b>Relatore</b> Massimo Callisto</span>
    <span><b>Hardware</b> ESP32 · HLK-LD2410B · HC-SR501</span>
    <span><b>Aggiornato</b> 26 agosto 2026</span>
  </p>
</header>

<div class="stats">
  <div class="stat r"><span class="stat-n">115</span><span class="stat-l">trial acquisiti in 12,4 h</span></div>
  <div class="stat r"><span class="stat-n">223 291</span><span class="stat-l">campioni a 5 Hz, jitter zero</span></div>
  <div class="stat r"><span class="stat-n">0,00 %</span><span class="stat-l">falsi negativi del radar, in ogni scenario</span></div>
  <div class="stat p"><span class="stat-n">98,7 %</span><span class="stat-l">falsi negativi del PIR sulla persona immobile</span></div>
</div>

<section id="stato">
  <h2>Dove siamo</h2>
  <p class="lead prose">I primi quattro obiettivi concordati sono raggiunti e documentati con
  dati misurati. Il quinto e il sesto sono progettati e specificati, con la parte
  sperimentale già in mano. In parallelo è iniziata la caratterizzazione del secondo
  radar, l'HLK-LD2420.</p>
  <div class="tw">
  <table class="ledger">
    <thead><tr><th></th><th>Obiettivo</th><th>Stato</th><th>Evidenza</th></tr></thead>
    <tbody>
    {"".join(riga(*r) for r in LEDGER)}
    </tbody>
  </table>
  </div>
</section>

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
    <p style="margin:14px 0 0; font-size:14.5px; color:var(--muted)">Per UPRISE, dove la
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

  {fig("fig03_uprise_sotto_banco",
       "Scenario UPRISE, 5 trial per condizione, entrambe le serie in modalità H: il confronto è "
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

  {fig("fig05_energia_e_portata",
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
    Questo lega l'obiettivo 4 al contesto UPRISE e giustifica la <b>coesistenza</b> dei due
    sensori nel DIPME-DEVICE, invece della sostituzione secca.</p>
  </div>
</section>

<section id="avanti">
  <h2>Cosa resta</h2>

  <h3>Obiettivi 5 e 6 — in sviluppo</h3>
  <p class="prose">La web UI è progettata in due varianti alternative, entrambe documentate
  fino al dettaglio implementativo: ESP32 self-hosted (tutto offline, coerente con lo scenario
  post-sisma) oppure un sito su server esterno con MQTT. Il frontend è condiviso all'85 %, quindi
  cambiare rotta costa pochi giorni — ma la decisione va presa prima di iniziare.</p>
  <p class="prose">L'indice di vitalità ha specifica v2 e prototipo Python pronti, e la base
  sperimentale <b>esiste già</b>: gli stessi trial della curva dose-risposta mostrano che il radar
  fornisce due indicatori <i>continui</i> e monotoni col movimento — l'energia media
  (68,6 → 84,4 → 99,3) e la dispersione della distanza (21,3 → 16,4 → 10,4 cm). Restano la
  taratura dei parametri e la validazione su trial separati.</p>

  <h3>Secondo radar — HLK-LD2420</h3>
  <p class="prose">Documentazione ufficiale acquisita e piano di test dedicato scritto. Il modulo
  costa meno corrente (50 mA) e arriva più lontano (8 m), ma il manuale dichiara che
  <b>non riporta la distanza dei corpi fermi</b> — esattamente lo scenario del progetto. Il piano
  distingue i test da ripetere da quelli non replicabili su questo modulo.</p>

  <h3>Domande da portare all'incontro</h3>
  <ul class="plain prose">
    <li>Web UI: ESP32 self-hosted o piattaforma su server? È la decisione che sblocca l'obiettivo 5.</li>
    <li>Il montaggio sotto il banco prevede la lamiera antisfondamento: il metallo blocca il radar.
    Dove va fissato il sensore?</li>
    <li>Scadenza per la consegna, per costruire il cronoprogramma.</li>
    <li>UPRISE e SAFE: quale nome usare in tesi?</li>
    <li>Che ruolo dare all'UWB già presente nel DIPME-DEVICE nel confronto?</li>
  </ul>
</section>

<footer>
  <p style="margin:0 0 6px"><span class="tag">Riproducibilità</span> Tutte le cifre di questa
  pagina sono ricalcolate dai CSV grezzi da <code>analisi/grafici_tesi.py</code> e
  <code>analisi/esporta_excel.py</code>, che riusano le stesse funzioni di
  <code>analizza_test.py</code> del capitolo 4.</p>
  <p style="margin:0">Convenzioni di scarto del transitorio: 20 s negli scenari ordinari,
  40 s sotto il banco, 120 s negli scenari di selettività, 60 s a stanza vuota.</p>
</footer>

</div>
"""

OUTFILE.write_text(HTML, encoding="utf-8")
print(f"  ok  {OUTFILE.name}  ({len(FIGS)} figure incorporate, "
      f"{len(HTML)/1024/1024:.2f} MB)")
