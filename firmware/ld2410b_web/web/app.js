/* app.js — logica client della dashboard. Solo JavaScript puro, nessuna dipendenza.
   Step 2: WebSocket con riconnessione, watchdog dati, area A (stato live testuale),
   diagnostica via /info. Dallo step 3: buffer, grafici, statistiche, CSV
   (PROGETTO_SITO_DETTAGLIO.md §3). */
"use strict";

const $ = (id) => document.getElementById(id);

// ---------------------------------------------------------------- stato
const state = {
  live: null,          // ultimo messaggio ricevuto
  wsAperto: false,
  ultimoMsgMs: 0,      // Date.now() dell'ultimo messaggio (watchdog)
  contatore: 0,
  contatoreHz: 0,      // messaggi nell'ultimo secondo, per la stima dei Hz
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
  renderLive(m);
  // step 3: state.ring.push(m); renderCharts()
  // step 4: if (state.session) state.session.rows.push(m); updateStats(m)
}

// ---------------------------------------------------------------- render area A + testata
function renderLive(m) {
  // testata: pallone di stato e distanza del bersaglio prioritario
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

  // pillole radar / PIR
  if (!m.radar_ok)      setPillola("p-radar", "off", "assente");
  else if (m.presence)  setPillola("p-radar", m.moving ? "on" : "warn", m.moving ? "MOVING" : "STILL");
  else                  setPillola("p-radar", "off", "vuoto");
  setPillola("p-pir", m.pir ? "on" : "off", m.pir ? "ATTIVO" : "inattivo");

  // dettaglio
  $("mov").textContent   = m.moving ? `${m.mdist} cm` : "—";
  $("still").textContent = m.still  ? `${m.sdist} cm` : "—";
  $("barra-m").style.width = m.menergy + "%";
  $("barra-s").style.width = m.senergy + "%";
  $("menergy").textContent = m.menergy;
  $("senergy").textContent = m.senergy;
  $("light").textContent = m.light;
  $("out").textContent   = m.out ? "alto" : "basso";
  $("contatore").firstChild.textContent = state.contatore + " ";

  // gate grezzi (segnaposto dei grafici dello step 3)
  const pad = (v) => String(v).padStart(3, " ");
  $("gm").textContent = m.gates_m.map(pad).join(" ");
  $("gs").textContent = m.gates_s.map(pad).join(" ");
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
  } catch (e) {
    $("uptime").textContent = "ESP32 non raggiungibile";
  }
  $("ora").textContent = new Date().toLocaleTimeString("it-IT");
}

// ---------------------------------------------------------------- avvio
connetti();
aggiornaInfo();
setInterval(aggiornaInfo, 5000);
