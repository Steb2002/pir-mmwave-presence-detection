/* app.js — logica client della dashboard. Solo JavaScript puro + Chart.js locale.
   Step 2: WebSocket con riconnessione, watchdog dati, area A, diagnostica via /info.
   Step 3: buffer degli ultimi 60 s (riempito dallo storico dell'ESP32 alla connessione),
           grafici C1/C2/C3, gauge B.
   Step 4: sessione con metadati, statistiche incrementali, export CSV compatibile acquire.py.
   (PROGETTO_SITO_DETTAGLIO.md §3) */
"use strict";

const $ = (id) => document.getElementById(id);

// ---------------------------------------------------------------- costanti
const FINESTRA_S   = 60;           // larghezza dei grafici C1/C3
const RING_MAX     = 320;          // 60 s a 5 Hz + margine
const GATE_CM      = 75;           // risoluzione di gate del LD2410B (manuale V1.04 §5.2)
const GATE_LABELS  = Array.from({ length: 9 }, (_, i) => String(i));   // numero di gate; i metri stanno nel titolo dell'asse
// Ordine dei campi di una riga compatta dello storico (HIST_CAMPI in web_server.h)
const HIST_CAMPI = ["t", "presence", "moving", "still", "mdist", "sdist", "menergy", "senergy", "pir", "light", "out", "gates_m", "gates_s"];

const css = (nome) => getComputedStyle(document.documentElement).getPropertyValue(nome).trim();
const COL = { mov: css("--mov"), still: css("--still"), ok: css("--ok"), warn: css("--warn"),
              alert: css("--alert"), off: css("--off"), muto: css("--testo-muto"), bordo: css("--bordo") };

// ---------------------------------------------------------------- stato
const state = {
  live: null,          // ultimo messaggio ricevuto
  ring: [],            // ultimi ~60 s di campioni (oggetti come il messaggio live)
  soglie: null,        // {mov:[9], still:[9], gate_max, timeout_s} da /info
  wsAperto: false,
  ultimoMsgMs: 0,      // Date.now() dell'ultimo messaggio (watchdog)
  contatore: 0,
  contatoreHz: 0,      // messaggi nell'ultimo secondo, per la stima dei Hz
  frame: 0,            // per aggiornare i grafici a meta' frequenza
};

// ---------------------------------------------------------------- utilita'
function formattaDurata(s) {
  s = Math.floor(s);
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
  const dd = (n) => String(n).padStart(2, "0");
  return h > 0 ? `${h}:${dd(m)}:${dd(sec)}` : `${m}:${dd(sec)}`;
}
function formattaByte(n) {
  return n >= 1024 ? `${(n / 1024).toFixed(1)} KB` : `${n} B`;
}
function metri(cm) {
  return (cm / 100).toFixed(2) + " m";
}
function setBanner(classe, testo) {
  const b = $("banner");
  if (!testo) { b.hidden = true; return; }
  b.className = "banner " + classe;
  b.textContent = testo;
  b.hidden = false;
}
function setStato(classe, testo) {
  $("pallino").className = "pallino " + classe;
  $("stato-testo").textContent = testo;
}
function setPillola(id, classe, testo) {
  const p = $(id);
  p.className = "pillola " + classe;
  p.querySelector(".valore").textContent = testo;
}
function ringPush(m) {
  state.ring.push(m);
  if (state.ring.length > RING_MAX) state.ring.splice(0, state.ring.length - RING_MAX);
}

// ---------------------------------------------------------------- WebSocket
let ws = null;

function connetti() {
  ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onopen = () => {
    state.wsAperto = true;
    setBanner("", "");
    setStato("off", "connesso, in attesa dati");
  };
  ws.onmessage = (e) => {
    let m;
    try { m = JSON.parse(e.data); } catch (_) { return; }
    if (m.errore) { setBanner("alert", "ESP32: " + m.errore); return; }
    if (m.hist)   { onStorico(m); return; }
    onSample(m);
  };
  ws.onclose = () => {
    state.wsAperto = false;
    setStato("alert", "disconnesso");
    setBanner("alert", "Connessione all'ESP32 persa: riprovo ogni 2 s");
    setTimeout(connetti, 2000);         // retry infinito
  };
  ws.onerror = () => { try { ws.close(); } catch (_) {} };
}

// Storico dell'ESP32 alla connessione: righe compatte -> oggetti, inseriti nel ring
// solo se piu' recenti dell'ultimo campione gia' presente (riconnessione).
function onStorico(m) {
  const ultimoT = state.ring.length ? state.ring[state.ring.length - 1].t : -1;
  for (const r of m.hist) {
    const o = {};
    HIST_CAMPI.forEach((k, i) => { o[k] = r[i]; });
    o.radar_ok = 1; o.vitality = 0; o.vitality_class = "";
    if (o.t > ultimoT) ringPush(o);
  }
  if (m.fine) renderCharts();
}

// Watchdog: WS vivo ma nessun campione da > 3 s = radar muto o loop bloccato
setInterval(() => {
  if (state.wsAperto && state.ultimoMsgMs && Date.now() - state.ultimoMsgMs > 3000) {
    setBanner("warn", "WebSocket aperto ma nessun dato da piu' di 3 s: sensore non risponde");
    setStato("warn", "sensore muto");
  }
  $("hz").textContent = state.contatoreHz;
  state.contatoreHz = 0;
}, 1000);

// ---------------------------------------------------------------- pipeline campione
function onSample(m) {
  state.live = m;
  state.ultimoMsgMs = Date.now();
  state.contatore++;
  state.contatoreHz++;
  if (!$("banner").hidden && $("banner").classList.contains("warn")) setBanner("", "");
  ringPush(m);
  renderLive(m);
  renderGauge(m);
  if (++state.frame % 2 === 0) renderCharts();   // 2,5 Hz: fluido anche su tablet
  sessioneCampione(m);                            // area D: registrazione e statistiche
}

// ---------------------------------------------------------------- render area A + testata
function renderLive(m) {
  if (!m.radar_ok) {
    setStato("alert", "radar non rilevato");
    $("dist-testata").textContent = "—";
  } else if (m.moving) {
    setStato("on", "PRESENZA · in movimento");
    $("dist-testata").textContent = metri(m.mdist);
  } else if (m.still) {
    setStato("warn", "PRESENZA · fermo");
    $("dist-testata").textContent = metri(m.sdist);
  } else {
    setStato("off", "nessuno");
    $("dist-testata").textContent = "—";
  }

  if (!m.radar_ok)      setPillola("p-radar", "off", "assente");
  else if (m.presence)  setPillola("p-radar", m.moving ? "on" : "warn", m.moving ? "MOVING" : "STILL");
  else                  setPillola("p-radar", "off", "vuoto");
  setPillola("p-pir", m.pir ? "on" : "off", m.pir ? "ATTIVO" : "inattivo");

  $("mov").textContent   = m.moving ? `${m.mdist} cm` : "—";
  $("still").textContent = m.still  ? `${m.sdist} cm` : "—";
  $("barra-m").style.width = m.menergy + "%";
  $("barra-s").style.width = m.senergy + "%";
  $("menergy").textContent = m.menergy;
  $("senergy").textContent = m.senergy;
  $("light").textContent = m.light;
  $("out").textContent   = m.out ? "alto" : "basso";
  $("contatore").firstChild.textContent = state.contatore + " ";
}

// ---------------------------------------------------------------- area B: gauge
const GAUGE_C = 2 * Math.PI * 52;
function renderGauge(m) {
  const arco = $("gauge-arco"), num = $("gauge-num"), cls = $("gauge-classe");
  if (!m.radar_ok || !m.presence) {
    arco.style.strokeDasharray = `0 ${GAUGE_C}`;
    arco.style.stroke = COL.off;
    num.textContent = "—";
    cls.className = "gauge-classe muto";
    cls.textContent = m.radar_ok ? "nessuna presenza" : "radar assente";
    return;
  }
  if (!m.vitality_class) {                     // firmware senza vitalita' (prima dello step 5)
    arco.style.strokeDasharray = `0 ${GAUGE_C}`;
    arco.style.stroke = COL.off;
    num.textContent = "—";
    cls.className = "gauge-classe muto";
    cls.textContent = "presenza · indice non ancora calcolato a bordo";
    return;
  }
  const v = Math.max(0, Math.min(100, m.vitality));
  arco.style.strokeDasharray = `${v / 100 * GAUGE_C} ${GAUGE_C}`;
  const breve = m.vitality_class.replace("vitalita_", "");      // bassa | moderata | alta
  // semaforo: bassa = rosso (la piu' urgente per il soccorso), moderata = giallo, alta = verde
  arco.style.stroke = breve === "bassa" ? COL.alert : breve === "moderata" ? COL.warn : COL.ok;
  num.textContent = v;
  cls.className = "gauge-classe " + breve;
  cls.textContent = "vitalità " + breve + (breve === "bassa" ? " · priorità alta" : "");
}

// ---------------------------------------------------------------- area C: grafici
Chart.defaults.color = COL.muto;
Chart.defaults.borderColor = COL.bordo;
Chart.defaults.font.family = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif";
Chart.defaults.font.size = 11;
Chart.defaults.animation = false;
Chart.defaults.plugins.legend.labels.boxWidth = 12;

const asseTempo = {
  type: "linear", min: -FINESTRA_S, max: 0,
  ticks: { stepSize: 10, callback: (v) => (v === 0 ? "ora" : `${v} s`) },
  grid: { color: COL.bordo },
};

const c1 = new Chart($("c1"), {
  type: "line",
  data: { datasets: [
    { label: "moving",     data: [], borderColor: COL.mov,   borderWidth: 1.5, pointRadius: 0, tension: 0 },
    { label: "stationary", data: [], borderColor: COL.still, borderWidth: 1.5, pointRadius: 0, tension: 0 },
    { label: "vitalità (a bordo)", data: [], borderColor: COL.warn, borderWidth: 2, borderDash: [6, 3], pointRadius: 0, tension: 0 },
  ]},
  options: {
    responsive: true, maintainAspectRatio: false, parsing: false, normalized: true,
    scales: { x: asseTempo, y: { min: 0, max: 100, grid: { color: COL.bordo } } },
    plugins: { legend: { position: "bottom" }, tooltip: { enabled: false } },
  },
});

const c2 = new Chart($("c2"), {
  data: { labels: GATE_LABELS, datasets: [
    { type: "bar",  label: "moving",       data: new Array(9).fill(0), backgroundColor: COL.mov,   order: 2 },
    { type: "bar",  label: "stationary",   data: new Array(9).fill(0), backgroundColor: COL.still, order: 2 },
    { type: "line", label: "soglia mov.",  data: new Array(9).fill(null), borderColor: COL.mov,   borderDash: [4, 3], borderWidth: 1.5, pointRadius: 2, stepped: "middle", order: 1 },
    { type: "line", label: "soglia stat.", data: new Array(9).fill(null), borderColor: COL.still, borderDash: [4, 3], borderWidth: 1.5, pointRadius: 2, stepped: "middle", order: 1 },
  ]},
  options: {
    responsive: true, maintainAspectRatio: false,
    scales: { x: { grid: { display: false }, ticks: { maxRotation: 0, autoSkip: false },
                   title: { display: true, text: `gate (1 gate = ${GATE_CM} cm)` } },
              y: { min: 0, max: 100, grid: { color: COL.bordo } } },
    plugins: { legend: { position: "bottom" }, tooltip: { enabled: false } },
  },
});

const c3 = new Chart($("c3"), {
  type: "line",
  data: { datasets: [
    { label: "radar", data: [], borderColor: COL.ok,   borderWidth: 2, pointRadius: 0, stepped: "before", fill: { target: { value: 0 }, above: COL.ok + "33" } },
    { label: "PIR",   data: [], borderColor: COL.warn, borderWidth: 2, pointRadius: 0, stepped: "before", fill: { target: { value: 1.5 }, above: COL.warn + "33" } },
  ]},
  options: {
    responsive: true, maintainAspectRatio: false, parsing: false, normalized: true,
    scales: {
      x: asseTempo,
      y: { min: -0.15, max: 2.65, grid: { color: COL.bordo },
           afterBuildTicks: (asse) => { asse.ticks = [0, 1, 1.5, 2.5].map((v) => ({ value: v })); },
           ticks: { callback: (v) => ({ 0: "radar off", 1: "radar ON", 1.5: "PIR off", 2.5: "PIR ON" }[v] ?? "") } },
    },
    plugins: { legend: { display: false }, tooltip: { enabled: false } },
  },
});

function renderCharts() {
  const ring = state.ring;
  if (!ring.length) return;
  const tNow = ring[ring.length - 1].t;
  const rel = (m) => (m.t - tNow) / 1000;

  c1.data.datasets[0].data = ring.map((m) => ({ x: rel(m), y: m.menergy }));
  c1.data.datasets[1].data = ring.map((m) => ({ x: rel(m), y: m.senergy }));
  c1.data.datasets[2].data = ring.map((m) => ({ x: rel(m), y: m.vitality_class ? m.vitality : null }));  // null = nessuna presenza
  c1.update("none");

  const ultimo = ring[ring.length - 1];
  c2.data.datasets[0].data = ultimo.gates_m;
  c2.data.datasets[1].data = ultimo.gates_s;
  c2.update("none");
  // riga sotto C2: dove sta la persona
  let dist = ultimo.moving ? ultimo.mdist : ultimo.still ? ultimo.sdist : 0;
  $("c2-sotto").textContent = dist ? `· persona nel gate ${Math.min(8, Math.floor(dist / GATE_CM))} (~${(dist / 100).toFixed(1)} m)` : "";

  c3.data.datasets[0].data = ring.map((m) => ({ x: rel(m), y: m.presence ? 1 : 0 }));
  c3.data.datasets[1].data = ring.map((m) => ({ x: rel(m), y: m.pir ? 2.5 : 1.5 }));
  c3.update("none");
}

// Soglie del modulo (da /info): linee tratteggiate su C2. Gate 0-1 stazionari non
// impostabili sul LD2410B (protocollo V1.07 Tab. 7): il valore 0 viene mostrato come assente.
function applicaSoglie(info) {
  if (!info.soglie_mov) return;
  state.soglie = { mov: info.soglie_mov, still: info.soglie_still, gate_max: info.gate_max, timeout_s: info.timeout_s };
  c2.data.datasets[2].data = info.soglie_mov.map((v) => v > 0 ? v : null);
  c2.data.datasets[3].data = info.soglie_still.map((v) => v > 0 ? v : null);
  c2.update("none");
}

// ---------------------------------------------------------------- diagnostica /info
async function aggiornaInfo() {
  try {
    const r = await fetch("/info", { cache: "no-store" });
    if (!r.ok) throw new Error("HTTP " + r.status);
    const info = await r.json();
    $("build").textContent  = info.build;
    $("ip").textContent     = info.ip;
    $("uptime").textContent = formattaDurata(info.uptime_s);
    $("client").textContent = `${info.client_ap} sull'AP, ${info.client_ws} WebSocket`;
    $("heap").textContent   = `${formattaByte(info.heap_libero)} (min ${formattaByte(info.heap_minimo)})`;
    $("hash").textContent   = `${info.assets_hash} · ${info.assets_n} file`;
    $("radar-param").textContent = !info.radar_ok ? "non rilevato"
      : info.soglie_mov ? `gate max ${info.gate_max} (${info.gate_max * GATE_CM} cm), timeout ${info.timeout_s} s, soglie mov ${info.soglie_mov.join(" ")}`
      : "parametri non letti";
    if (!state.soglie) applicaSoglie(info);
  } catch (e) {
    $("uptime").textContent = "ESP32 non raggiungibile";
  }
  $("ora").textContent = new Date().toLocaleTimeString("it-IT");
}


// ================================================================ area D: sessione, statistiche, CSV (step 4)
// Il CSV esportato ha le STESSE colonne di acquire.py: 29 del firmware + 6 metadati.
// Cosi' analizza_test.py, analizza_respiro.py ed esporta_excel.py lo leggono senza modifiche
// (ANALISI_WEB_UI.md §3, "un solo formato dati in tutta la tesi").
const CSV_COLONNE_FW = ["timestamp_ms", "radar_presence", "moving_target", "stationary_target",
  "moving_distance_cm", "stationary_distance_cm", "moving_energy", "stationary_energy", "pir_presence",
  ...Array.from({ length: 9 }, (_, i) => `menergy_gate${i}`),
  ...Array.from({ length: 9 }, (_, i) => `senergy_gate${i}`),
  "light_level", "out_level"];
const CSV_COLONNE_META = ["pc_time_s", "group_id", "trial_id", "scenario", "ground_truth_presence", "ground_truth_state"];
// Due colonne IN CODA, oltre le 35 di acquire.py: l'indice calcolato a bordo. Gli script
// leggono per nome e le ignorano; servono a confrontare bordo e vitalita_proto.py (step 5).
const CSV_COLONNE_EXTRA = ["vitality_onboard", "vitality_class_onboard"];
const STAT_IDS = ["s-durata", "s-n", "s-radar", "s-pir", "s-eventi", "s-ultima", "s-dist", "s-menergy", "s-vit"];

const sessione = {
  attiva: false,
  meta: null,          // {scenario, trial, gruppo, gt, gts, durata}
  rows: [],            // TUTTI i campioni della sessione (cresce libero: ~2-3 MB per 30 min)
  t0Pc: null,          // Date.now() alla prima riga -> pc_time_s
  tPrimo: null,        // t (millis ESP32) della prima riga
  timer: null,
  stats: null,
};

function statsVuote() {
  return { n: 0, radarOn: 0, pirOn: 0, radarEventi: 0, pirEventi: 0, ultimoRadar: 0, ultimoPir: 0,
           ultimaRilevazioneT: null, distSum: 0, distN: 0, distMin: Infinity, distMax: 0,
           menergySum: 0, menergyN: 0, vitMin: 100, vitMax: 0, vitN: 0 };
}

// Accumulatori O(1) per campione: niente ricalcoli sull'array
function updateStats(m) {
  const s = sessione.stats;
  s.n++;
  if (m.presence) { s.radarOn++; s.ultimaRilevazioneT = m.t; }
  if (m.pir) s.pirOn++;
  if (m.presence && !s.ultimoRadar) s.radarEventi++;   // fronti 0 -> 1
  if (m.pir && !s.ultimoPir) s.pirEventi++;
  s.ultimoRadar = m.presence; s.ultimoPir = m.pir;
  const d = m.moving ? m.mdist : m.still ? m.sdist : 0;   // bersaglio prioritario
  if (d > 0) { s.distSum += d; s.distN++; s.distMin = Math.min(s.distMin, d); s.distMax = Math.max(s.distMax, d); }
  if (m.moving) { s.menergySum += m.menergy; s.menergyN++; }
  if (m.presence && m.vitality_class) { s.vitMin = Math.min(s.vitMin, m.vitality); s.vitMax = Math.max(s.vitMax, m.vitality); s.vitN++; }
}

function renderStats() {
  const s = sessione.stats;
  if (!s || !s.n) return;
  const pct = (a) => (100 * a / s.n).toFixed(1) + " %";
  const ultimo = sessione.rows[sessione.rows.length - 1];
  const durata = (ultimo.t - sessione.tPrimo) / 1000;
  $("s-durata").textContent  = formattaDurata(durata) + (sessione.attiva ? "" : " (ferma)");
  $("s-n").textContent       = `${s.n} (${(s.n / Math.max(durata, 0.2)).toFixed(1)} Hz)`;
  $("s-radar").textContent   = pct(s.radarOn);
  $("s-pir").textContent     = pct(s.pirOn);
  $("s-eventi").textContent  = `${s.radarEventi} / ${s.pirEventi}`;
  $("s-ultima").textContent  = s.ultimaRilevazioneT === null ? "mai"
    : `${((ultimo.t - s.ultimaRilevazioneT) / 1000).toFixed(0)} s fa`;
  $("s-dist").textContent    = s.distN ? `${s.distMin} / ${(s.distSum / s.distN).toFixed(0)} / ${s.distMax} cm` : "—";
  $("s-menergy").textContent = s.menergyN ? (s.menergySum / s.menergyN).toFixed(1) : "—";
  $("s-vit").textContent     = s.vitN ? `${s.vitMin} / ${s.vitMax}` : "—";
}

function sessioneCampione(m) {
  if (!sessione.attiva) return;
  if (sessione.rows.length === 0) { sessione.t0Pc = Date.now(); sessione.tPrimo = m.t; }
  sessione.rows.push(m);
  updateStats(m);
  if (sessione.meta.durata && (m.t - sessione.tPrimo) / 1000 >= sessione.meta.durata) {
    sessioneStop(`durata di ${sessione.meta.durata} s raggiunta`);
  }
}

function formAbilita(on) {
  for (const el of $("form-sessione").querySelectorAll("input, select")) el.disabled = !on;
  $("b-avvia").disabled = !on;
  $("b-stop").disabled  = on;
}

function sessioneAvvia(ev) {
  ev.preventDefault();
  if (!state.live || !state.live.radar_ok) {
    $("sessione-msg").textContent = "Nessun dato dal radar: sessione non avviata.";
    return;
  }
  sessione.meta = {
    scenario: $("f-scenario").value.trim(), trial: $("f-trial").value.trim(), gruppo: $("f-gruppo").value.trim(),
    gt: Number($("f-gt").value), gts: $("f-gts").value.trim(),
    durata: $("f-durata").value ? Number($("f-durata").value) : 0,
  };
  sessione.rows = []; sessione.stats = statsVuote(); sessione.t0Pc = null; sessione.tPrimo = null;
  sessione.attiva = true;
  formAbilita(false);
  $("b-csv").disabled = true; $("b-reset").disabled = true;
  $("rec").hidden = false;
  $("sessione-msg").textContent = `Registrazione di ${sessione.meta.scenario}_${sessione.meta.trial}` +
    (sessione.meta.durata ? `, stop automatico a ${sessione.meta.durata} s.` : ", stop manuale.");
  for (const id of STAT_IDS) $(id).textContent = "—";
  sessione.timer = setInterval(() => {
    renderStats();
    if (sessione.rows.length) $("rec-durata").textContent = formattaDurata((sessione.rows[sessione.rows.length - 1].t - sessione.tPrimo) / 1000);
  }, 1000);
}

function sessioneStop(motivo) {
  if (!sessione.attiva) return;
  sessione.attiva = false;
  clearInterval(sessione.timer);
  renderStats();
  formAbilita(true);
  $("rec").hidden = true;
  $("b-csv").disabled = sessione.rows.length === 0;
  $("b-reset").disabled = false;
  $("sessione-msg").textContent = `Sessione ferma (${motivo || "stop manuale"}): ${sessione.rows.length} campioni in memoria. ` +
    "Scarica il CSV prima di avviarne un'altra o ricaricare la pagina.";
}

function sessioneReset() {
  sessione.rows = []; sessione.stats = null;
  $("b-csv").disabled = true; $("b-reset").disabled = true;
  for (const id of STAT_IDS) $(id).textContent = "—";
  $("sessione-msg").textContent = "";
}

function scaricaCSV() {
  if (!sessione.rows.length) return;
  const meta = sessione.meta;
  const righe = [CSV_COLONNE_FW.concat(CSV_COLONNE_META, CSV_COLONNE_EXTRA).join(",")];
  for (const r of sessione.rows) {
    // pc_time_s come acquire.py: orologio del PC alla prima riga + tempo trascorso sull'ESP32
    const pcTime = (sessione.t0Pc / 1000 + (r.t - sessione.tPrimo) / 1000).toFixed(6);
    righe.push([
      r.t, r.presence, r.moving, r.still, r.mdist, r.sdist, r.menergy, r.senergy, r.pir,
      ...r.gates_m, ...r.gates_s, r.light, r.out,
      pcTime, meta.gruppo, meta.trial, meta.scenario, meta.gt, meta.gts,
      r.vitality, r.vitality_class,
    ].join(","));
  }
  const blob = new Blob([righe.join("\n") + "\n"], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${meta.scenario}_${meta.trial}.csv`;     // stessa convenzione della campagna
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 5000);
  $("sessione-msg").textContent = `Scaricato ${a.download}: ${sessione.rows.length} righe, ${CSV_COLONNE_FW.length + CSV_COLONNE_META.length + CSV_COLONNE_EXTRA.length} colonne (35 di acquire.py + 2 di vitalita').`;
}

$("form-sessione").addEventListener("submit", sessioneAvvia);
$("b-stop").addEventListener("click", () => sessioneStop("stop manuale"));
$("b-csv").addEventListener("click", scaricaCSV);
$("b-reset").addEventListener("click", sessioneReset);
// Refresh o chiusura con dati non scaricati: il browser chiede conferma
window.addEventListener("beforeunload", (e) => {
  if (sessione.attiva || (sessione.rows.length && !$("b-csv").disabled)) { e.preventDefault(); e.returnValue = ""; }
});

// ---------------------------------------------------------------- avvio
connetti();
aggiornaInfo();
setInterval(aggiornaInfo, 5000);
