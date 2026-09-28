#!/usr/bin/env python3
"""
Figure 14-22 della tesi: la campagna di settembre (Test 3.6, LD2420, Fase 8, vitalita').

    python analisi/grafici_tesi_2.py

Complementa grafici_tesi.py (figure 1-13, agosto) e ne riusa stile, cartella di uscita e
funzioni di analisi: i numeri escono dalle stesse funzioni di analizza_test.py e di
vitalita_proto.py con le convenzioni di scarto del registro. Soglie del LD2420 lette
dall'XML in flash (`ld2420_config_fondo120s_max_6_g0alto.xml`), non ricopiate a mano.

  fig14  Test 3.6      portata residua del LD2410B per materiale (1-5 m)
  fig15  Fase 3 / 3-2420 attenuazione per materiale: LD2410B in % e LD2420 in dB
  fig17  Fase 8        portata dei tre sensori nella stessa geometria (corridoio)
  fig18  Test 1.1      falsi positivi a stanza vuota: LD2410B vs LD2420 (due configurazioni)
  fig19  DIPME         riga a tre sensori: immobile / micro-movimenti a 1 m e sotto il banco
  fig20  angolare      copertura in azimut dei due radar
  fig21  vitalita'     distribuzione dell'indice per scenario (configurazione del firmware)
  fig22  vitalita'     indice a bordo vs ricalcolo offline (verifica dello step 5)
"""
import re
import statistics
import xml.etree.ElementTree as ET

import numpy as np
import matplotlib.pyplot as plt

from grafici_tesi import (DATI, OUT, RADICE, C_RADAR, C_PIR, C_GRIGIO, files, stats_scenario,
                          media_dev, salva)
from analizza_test import leggi_csv  # noqa: E402
import vitalita_proto as vp  # noqa: E402

C_2420 = "#e08e0b"          # LD2420 (arancione, come la scheda)
C_PIRMAX = "#8b1e2d"        # PIR a sensibilita' massima
XML_2420 = RADICE / "HLK-LD2420" / "Backup config" / "ld2420_config_fondo120s_max_6_g0alto.xml"


# ---------------------------------------------------------------- helper LD2420
def soglie_2420():
    """Trigger e hold grezzi per gate 0-15 dall'XML del tool (valori in dB -> 10^(dB/10))."""
    root = ET.parse(XML_2420).getroot()
    att = {}
    for el in root.iter():
        att.update(el.attrib)
    trig = [10 ** (float(att[f"TriggerGate{g}Threshold"]) / 10) for g in range(16)]
    hold = [10 ** (float(att[f"HoldGate{g}Threshold"]) / 10) for g in range(16)]
    return trig, hold


def righe_grezze(path, salta):
    """Righe di un CSV (dict per riga, valori stringa) dopo lo scarto del transitorio."""
    import csv
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        rs = [r for r in csv.DictReader(f) if (r.get("timestamp_ms") or "").isdigit()]
    t0 = int(rs[0]["timestamp_ms"])
    return [r for r in rs if (int(r["timestamp_ms"]) - t0) / 1000.0 >= salta]


def energie_2420(pattern, salta=20.0):
    """Media per gate (0-15) dell'energia LD2420 su tutti i trial del pattern."""
    acc = [[] for _ in range(16)]
    for f in files(pattern):
        for r in righe_grezze(f, salta):
            for g in range(16):
                acc[g].append(int(r[f"energy2420_gate{g}"]))
    return [statistics.mean(a) if a else float("nan") for a in acc]


def energia_gate2_per_trial(pattern, salta=20.0):
    return [statistics.mean(int(r["energy2420_gate2"]) for r in righe_grezze(f, salta))
            for f in files(pattern)]


def frazione_moving(pattern, salta=20.0):
    """% di campioni con moving_target = 1, per trial (LD2410B)."""
    out = []
    for f in files(pattern):
        rs = [r for r in leggi_csv(str(f))]
        t0 = rs[0]["t_ms"]
        rs = [r for r in rs if (r["t_ms"] - t0) / 1000.0 >= salta]
        out.append(100.0 * sum(r["moving"] for r in rs) / len(rs))
    return out


def eventi_ora(path, salta=60.0):
    """(riaccensioni 0->1 della presenza radar, ore osservate) dopo lo scarto."""
    rs = leggi_csv(str(path))
    t0 = rs[0]["t_ms"]
    rs = [r for r in rs if (r["t_ms"] - t0) / 1000.0 >= salta]
    ev = sum(1 for a, b in zip(rs, rs[1:]) if a["radar"] == 0 and b["radar"] == 1)
    ore = (rs[-1]["t_ms"] - rs[0]["t_ms"]) / 3.6e6
    return ev, ore


# =========================================================== fig14 — Test 3.6
def fig_portata_ostacoli():
    dist = [1, 2, 3, 4, 5]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.0))
    # --- A: energia moving vs distanza, senza ostacolo (agosto) e con cartongesso (3.6)
    def curva(fmt, colore, etic, pat):
        xs, ms, ds = [], [], []
        for d in dist:
            fs = files(pat.format(d))
            if not fs:
                continue
            m, s = media_dev([r["menergy_media"] for r in stats_scenario(pat.format(d), skip=20.0)])
            xs.append(d); ms.append(m); ds.append(s)
        ax1.errorbar(xs, ms, yerr=ds, fmt=fmt, color=colore, capsize=3, lw=1.6, ms=6, label=etic)
    curva("o-", C_RADAR, "senza ostacolo", "movimento_{}m_T*.csv")
    curva("s--", "#7a5c00", "cartongesso 10 mm", "ost36_cartongesso_{}m_T*.csv")
    for etic, pat, mk, col in [("legno 10 mm", "ost36_legno_{}m_T*.csv", "^", "#8c5a2b"),
                               ("vetro 5 mm", "ost36_vetro_{}m_T*.csv", "D", "#3a9d8f"),
                               ("porta a 3,8 m", "ost36_porta_{}m*_T*.csv", "v", "#5c4d7d")]:
        xs, ms = [], []
        for d in dist:
            if "porta" in pat and d < 4:   # porta a ~3,8 m: a 3 m il soggetto le sta davanti
                continue
            fs = [f for f in files(pat.format(d)) if "congelato" not in f.name and "vuoto" not in f.name]
            if not fs:
                continue
            rs = [stats_scenario(f.name, skip=20.0)[0] for f in fs]
            xs.append(d); ms.append(statistics.mean(r["menergy_media"] for r in rs))
        ax1.plot(xs, ms, mk, color=col, ms=7, label=etic)
    ax1.set_xlabel("distanza [m]"); ax1.set_ylabel("energia moving media [0-100]")
    ax1.set_ylim(0, 105); ax1.set_xticks(dist)
    ax1.set_title("A · LD2410B: energia del bersaglio, pannelli a 20 cm\n"
                  "presenza 100 % e distanza corretta in tutti i trial")
    ax1.legend(fontsize=8, loc="upper right")
    # --- B: frazione di campioni col canale moving attivo a 3-4-5 m
    gruppi = [("senza ostacolo", "movimento_{}m_T*.csv", C_RADAR),
              ("cartongesso", "ost36_cartongesso_{}m_T*.csv", "#7a5c00"),
              ("vetro", "ost36_vetro_{}m_T*.csv", "#3a9d8f"),
              ("legno", "ost36_legno_{}m_T*.csv", "#8c5a2b"),
              ("porta a 3,8 m", "ost36_porta_{}m*_T*.csv", "#5c4d7d")]
    dd = [3, 4, 5]; w = 0.16; x = np.arange(len(dd))
    for i, (etic, pat, col) in enumerate(gruppi):
        vals = []
        for d in dd:
            fs = [f for f in files(pat.format(d)) if "congelato" not in f.name and "vuoto" not in f.name]
            if "porta" in pat and d < 4:
                fs = []
            if not fs:
                vals.append((float("nan"), 0)); continue
            fr = []
            for f in fs:
                fr += frazione_moving(f.name)
            vals.append(media_dev(fr))
        ax2.bar(x + (i - 2) * w, [v[0] for v in vals], w, yerr=[v[1] for v in vals], capsize=2,
                color=col, edgecolor="white", label=etic)
    ax2.set_xticks(x); ax2.set_xticklabels([f"{d} m" for d in dd])
    ax2.set_ylabel("campioni con canale moving attivo [%]"); ax2.set_ylim(0, 128); ax2.set_yticks(range(0, 101, 20))
    ax2.set_title("B · cosa degrada: il canale moving\n(la presenza la tiene il canale stazionario)")
    ax2.legend(fontsize=8, loc="upper center", ncol=3)
    salva(fig, "fig14_portata_ostacoli")


# =========================================================== fig15 — attenuazione in % e dB
def fig_attenuazione_materiali():
    trig, hold = soglie_2420()
    # LD2410B, 30/08, soggetto a 3 m: baseline = media di nessuno + nessuno_fine
    base10 = statistics.mean(r["menergy_media"] for p in ("ostacolo_nessuno_T*.csv", "ostacolo_nessuno_fine_T*.csv")
                             for r in stats_scenario(p, skip=20.0))
    mat10 = [("plastica", "ostacolo_plastica_T*.csv"), ("cartone", "ostacolo_cartone_scatola_T*.csv"),
             ("vetroresina", "ostacolo_vetroresina_T*.csv"), ("vetro", "ostacolo_vetro_T*.csv"),
             ("legno", "ostacolo_legno_T*.csv"), ("metallo", None)]
    att10 = []
    for nome, pat in mat10:
        if pat is None:
            att10.append(100.0); continue
        e = statistics.mean(r["menergy_media"] for r in stats_scenario(pat, skip=20.0))
        att10.append(100.0 * (1 - e / base10))
    # cartongesso LD2410B dal Test 3.6 a 3 m (sessione 09/09, baseline della stessa sera)
    base36 = statistics.mean(r["menergy_media"] for p in ("ost36_nessuno_3m_bis_T*.csv", "ost36_nessuno_3m_fine_T*.csv")
                             for r in stats_scenario(p, skip=20.0))
    e36 = statistics.mean(r["menergy_media"] for r in stats_scenario("ost36_cartongesso_3m_T*.csv", skip=20.0))
    att36 = 100.0 * (1 - e36 / base36)
    # LD2420, 09/09, soggetto a 1 m: gate 2 grezzo, baseline nessuno + nessuno_fine, fondo dal check
    base20 = statistics.mean(energia_gate2_per_trial("ost2420_nessuno_T*.csv") + energia_gate2_per_trial("ost2420_nessuno_fine_T*.csv"))
    fondo20 = energie_2420("check2420_fondo_ost_T01.csv", salta=20.0)[2]
    mat20 = [("plastica", "ost2420_plastica_T*.csv"), ("cartongesso", "ost2420_cartongesso_T*.csv"),
             ("cartone", "ost2420_cartone_scatola_T*.csv"), ("vetroresina", "ost2420_vetroresina_T*.csv"),
             ("vetro", "ost2420_vetro_T*.csv"), ("legno", "ost2420_legno_T*.csv"), ("metallo", "ost2420_metallo_T*.csv")]
    db20, limite = [], []
    for nome, pat in mat20:
        e = statistics.mean(energia_gate2_per_trial(pat))
        db20.append(10 * np.log10(base20 / e)); limite.append(e <= fondo20 * 1.1)
    dinamica = 10 * np.log10(base20 / fondo20)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.0))
    nomi10 = [m[0] for m in mat10[:5]] + ["cartongesso", "metallo"]
    vals10 = att10[:5] + [att36, 100.0]
    cols = [C_RADAR] * 5 + ["#7a5c00", C_GRIGIO]
    b = ax1.bar(range(len(nomi10)), vals10, color=cols, edgecolor="white")
    b[-1].set_hatch("////")
    for i, v in enumerate(vals10):
        ax1.text(i, v + 2, "blocca" if i == len(vals10) - 1 else f"−{v:.0f} %", ha="center", fontsize=8.5)
    ax1.set_xticks(range(len(nomi10))); ax1.set_xticklabels(nomi10, fontsize=8.5, rotation=20, ha="right")
    ax1.set_ylabel("riduzione dell'energia moving [%]"); ax1.set_ylim(0, 112)
    ax1.set_title(f"A · LD2410B a 3 m, pannello a 20 cm\nbaseline {base10:.1f} su 6 trial · ".replace(".", ",") +
                  "energia in movimento, scala 0-100", fontsize=10)
    b2 = ax2.bar(range(len(mat20)), db20, color=[C_GRIGIO if l else C_2420 for l in limite], edgecolor="white")
    for i, (v, l) in enumerate(zip(db20, limite)):
        if l:
            b2[i].set_hatch("////")
        ax2.text(i, v + 0.15, ("≥ " if l else "") + f"{v:.1f}".replace(".", ","), ha="center", fontsize=8.5)
    ax2.axhline(dinamica, color=C_GRIGIO, ls=":", lw=1)
    ax2.text(-0.4, dinamica + 0.15, f"limite di dinamica {dinamica:.1f} dB (gate 2 al fondo)".replace(".", ","),
             ha="left", fontsize=8, color=C_GRIGIO)
    ax2.set_xticks(range(len(mat20))); ax2.set_xticklabels([m[0] for m in mat20], fontsize=8.5, rotation=20, ha="right")
    ax2.set_ylabel("attenuazione 10·log10(E0/E) [dB]"); ax2.set_ylim(0, dinamica + 1.2)
    ax2.set_title(f"B · LD2420 a 1 m, pannello a 20 cm\nbaseline {base20:.1f} su 6 trial · ".replace(".", ",") +
                  "energia grezza del gate 2", fontsize=10)
    salva(fig, "fig15_attenuazione_materiali")
    return att10, att36, db20


# ============================================ LD2420 in corridoio (dati per la fig17)
def dati_2420_corridoio():
    """Per ogni distanza 1-8 m: rapporto energia/fondo del gate del bersaglio e % di campioni
    sopra il trigger. Fino al 28/09/2026 era anche disegnato come fig16 (energia vs distanza),
    tolta perche' ripeteva la Figura 5.8 e il testo della Sezione 5.10."""
    trig, hold = soglie_2420()
    fondo = energie_2420("vuoto2420_corr_T01.csv", salta=120.0)
    xs, snr, over = [], [], []
    for d in (1, 2, 3, 4, 5, 6, 7, 8):
        g0 = min(d * 100 // 70, 11)
        e = energie_2420(f"corr2420_{d}m_T*.csv")
        cand = [(e[g] / fondo[g], g) for g in (g0, g0 + 1) if fondo[g] > 0]
        r, g = max(cand)
        xs.append(d); snr.append(r)
        # % campioni sopra il trigger nel gate scelto
        n = tot = 0
        for f in files(f"corr2420_{d}m_T*.csv"):
            for row in righe_grezze(f, 20.0):
                tot += 1; n += int(row[f"energy2420_gate{g}"]) > trig[g]
        over.append(100.0 * n / tot)
    return list(zip(xs, snr, over))


# =========================================================== fig17 — portata dei tre sensori
def fig_portata_tre_sensori(snr2420):
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    # LD2410B presenza: stanza 1-5, corridoio 5-7
    xs, ys, es = [], [], []
    for d in (1, 2, 3, 4, 5):
        m, s = media_dev([r["radar_rate_%"] for r in stats_scenario(f"movimento_{d}m_T*.csv", skip=20.0)]); xs.append(d); ys.append(m); es.append(s)
    for d in (5, 6, 7):
        m, s = media_dev([r["radar_rate_%"] for r in stats_scenario(f"movimento_{d}m_corridoio_T*.csv", skip=20.0)]); xs.append(d + 0.08); ys.append(m); es.append(s)
    ax.errorbar(xs, ys, yerr=es, fmt="o-", color=C_RADAR, capsize=3, lw=1.8, ms=6, label="LD2410B, presenza")
    # PIR attraversamento a meta' corsa: 2-5 m agosto + 6 m corridoio
    xs, ys, es = [], [], []
    for d in (2, 3, 4, 5):
        m, s = media_dev([r["pir_rate_%"] for r in stats_scenario(f"attraversamento_{d}m_T*.csv", skip=20.0)]); xs.append(d); ys.append(m); es.append(s)
    m, s = media_dev([r["pir_rate_%"] for r in stats_scenario("attrav_6m_corridoio_T*.csv", skip=20.0)]); xs.append(6); ys.append(m); es.append(s)
    ax.errorbar(xs, ys, yerr=es, fmt="s-", color=C_PIR, capsize=3, lw=1.6, ms=6, label="PIR a metà corsa, attraversamento")
    # PIR al massimo 5-8 m
    xs, ys, es = [], [], []
    for d in (5, 6, 7, 8):
        m, s = media_dev([r["pir_rate_%"] for r in stats_scenario(f"attrav_smax_{d}m_T*.csv", skip=20.0)]); xs.append(d); ys.append(m); es.append(s)
    ax.errorbar(xs, ys, yerr=es, fmt="D--", color=C_PIRMAX, capsize=3, lw=1.6, ms=6, label="PIR al massimo, attraversamento")
    # LD2420: % campioni sopra il trigger nel gate del bersaglio (corridoio)
    ax.plot([x for x, _, _ in snr2420], [o for _, _, o in snr2420], "^-", color=C_2420, lw=1.6, ms=7,
            label="LD2420 (esemplare), acquisizione: campioni sopra il trigger")
    p12 = [media_dev([r["radar_rate_%"] for r in stats_scenario(f"corr2420_{d}m_T*.csv", skip=20.0)])[0] for d in (1, 2)]
    ax.plot([1, 2], p12, "^", mfc="white", mec=C_2420, mew=1.8, ms=8, label="LD2420, presenza mantenuta (1-2 m)")
    ax.set_xlabel("distanza [m]"); ax.set_ylabel("rilevamento [%]"); ax.set_ylim(-3, 108); ax.set_xticks(range(1, 9))
    ax.set_title("Portata dei tre sensori")
    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, frameon=False)
    salva(fig, "fig17_portata_tre_sensori")


# =========================================================== fig18 — falsi positivi a stanza vuota
def fig_falsi_positivi():
    e10, h10 = eventi_ora(DATI / "stanza_vuota_notte_T01.csv")
    e20a, h20a = eventi_ora(DATI / "notturna2420_T01.csv")
    e20b, h20b = eventi_ora(DATI / "vuoto2420_g0alto_1h_T01.csv")
    r10 = 3.0 / h10 if e10 == 0 else e10 / h10        # regola del tre se zero eventi
    r20a, r20b = e20a / h20a, e20b / h20b
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    nomi = [f"LD2410B\nsoglie di fabbrica\n{h10:.1f} h, {e10} eventi",
            f"LD2420 soglie tarate\n(fondo 120 s)\n{h20a:.1f} h, {e20a} eventi",
            f"LD2420 gate 0\nsopra la coda\n{h20b:.1f} h, {e20b} eventi"]
    vals = [r10, r20a, r20b]
    b = ax.bar(range(3), vals, color=[C_RADAR, C_2420, C_2420], edgecolor="white")
    if e10 == 0:
        b[0].set_hatch("////")
    ax.set_yscale("log"); ax.set_ylim(0.1, 100)
    for i, v in enumerate(vals):
        ax.text(i, v * 1.15, ("≤ " if i == 0 and e10 == 0 else "") + f"{v:.1f} /h", ha="center", fontsize=9.5, fontweight="bold")
    ax.set_xticks(range(3)); ax.set_xticklabels(nomi, fontsize=8.5)
    ax.set_ylabel("riaccensioni della presenza a stanza vuota [eventi/h]")
    ax.set_title("Falsi positivi a stanza vuota, notte, porta chiusa\n"
                 "LD2410B: zero eventi → limite superiore 3/T (regola del tre)")
    salva(fig, "fig18_falsi_positivi")
    return r10, r20a, r20b


# =========================================================== fig19 — DIPME a tre sensori
def fig_dipme_tre_sensori():
    cond = [("immobile\n1 m in piedi", "fermo_1m_H_T*.csv", 20.0, "fermo2420_1m_T*.csv", 90.0),
            ("micro-movimenti\n1 m in piedi", "micromovimenti_1m_H_T*.csv", 20.0, "micromovimenti2420_1m_T*.csv", 90.0),
            ("immobile\nsotto il banco", "sotto_banco_immobile_H_T*.csv", 40.0, "banco2420_immobile_T*.csv", 90.0),
            ("micro-movimenti\nsotto il banco", "sotto_banco_movimenti_H_T*.csv", 40.0, "banco2420_movimenti_T*.csv", 90.0)]
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    x = np.arange(len(cond)); w = 0.26
    for i, (nome, p10, s10, p20, s20) in enumerate(cond):
        r10 = stats_scenario(p10, skip=s10); r20 = stats_scenario(p20, skip=s20)
        mp, dp = media_dev([r["pir_rate_%"] for r in r10])
        mr, dr = media_dev([r["radar_rate_%"] for r in r10])
        m2, d2 = media_dev([r["radar_rate_%"] for r in r20])
        for k, (m, d, col, etic) in enumerate([(mp, dp, C_PIR, "PIR HC-SR501"), (mr, dr, C_RADAR, "LD2410B"), (m2, d2, C_2420, "LD2420 (esemplare)")]):
            ax.bar(x[i] + (k - 1) * w, m, w, yerr=d, capsize=3, color=col, edgecolor="white", label=etic if i == 0 else None)
            ax.text(x[i] + (k - 1) * w, m + d + 2.5, f"{m:.1f}", ha="center", fontsize=8, color=col, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels([c[0] for c in cond])
    ax.set_ylabel("tempo con presenza rilevata [%]"); ax.set_ylim(0, 112); ax.set_yticks(range(0, 101, 20))
    ax.set_title("Lo scenario DIPME a tre sensori · 5 trial per condizione\n"
                 "stessa geometria per i tre sensori · LD2420 con soglie tarate e scarto iniziale di 90 s", pad=26)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=8.5, ncol=3, frameon=False)
    salva(fig, "fig19_dipme_tre_sensori")


# =========================================================== fig28 — il tipo di movimento decide il PIR
def fig_tipo_movimento():
    """PIR sul posto vs attraversamento trasversale a 1-5 m; il radar e' al 100 % in entrambi.

    Sul posto: a 1 e 2 m le serie ripetute in H; a 3-5 m le serie originali (in L), che
    contengono zero eventi PIR e quindi non dipendono dal ponticello. Attraversamento:
    le serie del 29/08 (H) a 2-5 m e del 25/09 a 1 m, 3 trial per distanza.
    """
    dists = [1, 2, 3, 4, 5]
    posto = {1: "movimento_1m_H_T*.csv", 2: "movimento_2m_H_T*.csv", 3: "movimento_3m_T*.csv",
             4: "movimento_4m_T*.csv", 5: "movimento_5m_T*.csv"}
    attr = {d: f"attraversamento_{d}m_T*.csv" for d in (1, 2, 3, 4, 5)}
    pm, pdv, am, adv, rm = [], [], [], [], []
    for d in dists:
        rs = stats_scenario(posto[d], skip=20.0)
        m, s = media_dev([r["pir_rate_%"] for r in rs]); pm.append(m); pdv.append(s)
        rr = [r["radar_rate_%"] for r in rs]
        if d in attr:
            ra = stats_scenario(attr[d], skip=20.0)
            m, s = media_dev([r["pir_rate_%"] for r in ra]); am.append(m); adv.append(s)
            rr += [r["radar_rate_%"] for r in ra]
        else:
            am.append(float("nan")); adv.append(0.0)
        rm.append(media_dev(rr)[0])
    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    x = np.arange(len(dists)); w = 0.36
    ax.bar(x - w / 2, pm, w, yerr=pdv, capsize=3, color=C_PIR, alpha=0.5, edgecolor="white",
           label="PIR, cammino sul posto")
    ax.bar(x + w / 2, am, w, yerr=adv, capsize=3, color=C_PIR, edgecolor="white",
           label="PIR, attraversamento trasversale")
    for i in range(len(dists)):
        ax.text(x[i] - w / 2, pm[i] + pdv[i] + 2, f"{pm[i]:.1f}", ha="center", fontsize=8.5, color=C_PIR)
        if np.isnan(am[i]):
            ax.text(x[i] + w / 2, 3, "n.d.", ha="center", fontsize=8.5, color=C_GRIGIO)
        else:
            ax.text(x[i] + w / 2, am[i] + adv[i] + 2, f"{am[i]:.1f}", ha="center", fontsize=8.5,
                    color=C_PIR, fontweight="bold")
    ax.plot(x, rm, "o-", color=C_RADAR, lw=1.8, ms=6, label="LD2410B, con entrambi i movimenti")
    ax.set_xticks(x); ax.set_xticklabels([f"{d} m" for d in dists])
    ax.set_ylabel("tempo con presenza rilevata [%]"); ax.set_ylim(0, 112)
    ax.set_yticks(range(0, 101, 20))
    # Il ponticello non va nel titolo: il sul posto a 3-5 m e' in L (zero eventi, vedi docstring)
    ax.set_title("Il PIR con due tipi di movimento a parità di distanza e sensibilità\n"
                 "cammino sul posto: 5 trial per distanza · attraversamento: 3 trial per distanza", pad=26)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=8.5, frameon=False)
    salva(fig, "fig28_tipo_movimento")
    return pm, am


# =========================================================== fig20 — copertura angolare
def fig_angolare():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.0))
    az10 = [0, 45, 60, 75, 90, 120]
    mr, dr, mp, dp = [], [], [], []
    for a in az10:
        rs = stats_scenario(f"angolo_{a:03d}_T*.csv", skip=20.0)
        m, s = media_dev([r["radar_rate_%"] for r in rs]); mr.append(m); dr.append(s)
        m, s = media_dev([r["pir_rate_%"] for r in rs]); mp.append(m); dp.append(s)
    ax1.errorbar(az10, mr, yerr=dr, fmt="o-", color=C_RADAR, capsize=3, lw=1.8, ms=6, label="LD2410B, presenza")
    ax1.errorbar(az10, mp, yerr=dp, fmt="s-", color=C_PIR, capsize=3, lw=1.6, ms=6, label="PIR")
    ax1.axvspan(-5, 60, color=C_RADAR, alpha=0.07); ax1.text(2, 5, "±60° dichiarati", fontsize=8, color=C_RADAR)
    ax1.set_xlabel("azimut [°]"); ax1.set_ylabel("rilevamento [%]"); ax1.set_ylim(-3, 118); ax1.set_yticks(range(0, 101, 20)); ax1.set_xticks(az10)
    ax1.set_title("A · LD2410B e PIR, r = 1 m, busto laterale da seduto\n3 trial per azimut, gate max 2")
    ax1.legend(fontsize=8.5, loc="lower left", bbox_to_anchor=(0.0, 0.1))
    az20 = [0, 45, 60, 75, 90]
    me, de = [], []
    for a in az20:
        v = energia_gate2_per_trial(f"angolo2420_{a:03d}_T*.csv"); m, s = media_dev(v); me.append(m); de.append(s)
    fondo = energie_2420("vuoto2420_sera_T01.csv", salta=120.0)[2]
    trig, hold = soglie_2420()
    ax2.errorbar(az20, me, yerr=de, fmt="^-", color=C_2420, capsize=3, lw=1.8, ms=7, label="LD2420, energia gate 2")
    ax2.axhline(fondo, color=C_GRIGIO, ls="--", lw=1); ax2.text(2, fondo - 0.8, f"fondo a vuoto {fondo:.0f}", ha="left", va="top", fontsize=8, color=C_GRIGIO)
    ax2.axhline(hold[2], color=C_2420, ls=":", lw=1); ax2.text(90, hold[2] + 0.6, f"hold del gate 2 = {hold[2]:.0f} (media sotto, p95 sopra)", ha="right", fontsize=8, color=C_2420)
    ax2.set_ylim(0, max(hold[2], max(me) + max(de)) + 8)
    ax2.axvspan(-5, 45, color=C_2420, alpha=0.07); ax2.text(2, fondo + 3, "±45° dichiarati (manuale §5.2)", fontsize=8, color=C_2420)
    ax2.set_xlabel("azimut [°]"); ax2.set_ylabel("energia grezza gate 2 (70-140 cm)"); ax2.set_xticks(az20)
    ax2.set_title("B · LD2420 (esemplare), stessa prova\nal fondo a 90°: fascio utile fino a ~75°")
    ax2.legend(fontsize=8.5, loc="upper right")
    salva(fig, "fig20_angolare")


# =========================================================== fig21 — vitalita' per scenario
VIT = dict(alpha_m=0.05, alpha_v=0.01, k=0.5)      # = firmware/ld2410b_web/config.h
SOGLIE_VIT = [45.0, 95.0]


def indici_scenario(pattern, gate, fondo, salta=None):
    out = []
    for f in files(pattern):
        righe = vp.leggi(str(f))
        if not righe:
            continue
        s = vp.calcola(righe, VIT["alpha_m"], VIT["alpha_v"], VIT["k"], gate, fondo, sorgente="gate")
        sk = vp.transitorio_atteso(f.stem) if salta is None else salta
        out += [x["vitality"] for x in s if x["t_s"] >= sk]
    return out


def fig_vitalita_scenari():
    fondo = vp.fondo_per_gate(str(DATI / "stanza_vuota_notte_T01.csv"))
    sc = [("stanza vuota\n(gate di presenza)", "stanza_vuota_T01.csv", "distanza", 60.0, C_GRIGIO),
          ("immobile\n1 m", "fermo_1m_H_T*.csv", "distanza", None, C_RADAR),
          ("micro-movimenti\n1 m", "micromovimenti_1m_H_T*.csv", "distanza", None, C_RADAR),
          ("movimento\n1 m", "movimento_1m_H_T*.csv", "distanza", None, C_RADAR),
          ("immobile sotto\nil banco", "sotto_banco_immobile_H_T*.csv", "distanza", None, "#0d3b5e"),
          ("immobile sotto il\nbanco, gate fisso 2", "sotto_banco_immobile_H_T*.csv", 2, None, "#9fc5dd"),
          ("movimenti sotto\nil banco", "sotto_banco_movimenti_H_T*.csv", "distanza", None, "#0d3b5e")]
    dati = [indici_scenario(p, g, fondo, sk) for _, p, g, sk, _ in sc]
    fig, ax = plt.subplots(figsize=(11.0, 4.4))
    bp = ax.boxplot(dati, widths=0.55, showfliers=False, patch_artist=True, medianprops=dict(color="black", lw=1.4))
    for patch, (_, _, _, _, col) in zip(bp["boxes"], sc):
        patch.set_facecolor(col); patch.set_alpha(0.85); patch.set_edgecolor("white")
    ax.axhspan(0, SOGLIE_VIT[0], color="#ff453a", alpha=0.07); ax.axhspan(SOGLIE_VIT[0], SOGLIE_VIT[1], color="#ffb020", alpha=0.07); ax.axhspan(SOGLIE_VIT[1], 100, color="#34c759", alpha=0.07)
    for y, t, c in [(SOGLIE_VIT[0] / 2, "bassa (priorità alta)", "#b3261e"), ((SOGLIE_VIT[0] + SOGLIE_VIT[1]) / 2, "moderata", "#9a6700"), ((SOGLIE_VIT[1] + 100) / 2, "alta", "#1e7d3a")]:
        ax.text(len(sc) + 0.45, y, t, va="center", fontsize=8.5, color=c, rotation=90)
    ax.set_xticks(range(1, len(sc) + 1)); ax.set_xticklabels([s[0] for s in sc], fontsize=8.5)
    ax.set_ylabel("indice di vitalità [0-100]"); ax.set_ylim(0, 100); ax.set_xlim(0.4, len(sc) + 0.8)
    for i, d in enumerate(dati, start=1):
        ax.text(i, 2, f"med {statistics.median(d):.0f}", ha="center", fontsize=7.5, color="#333")
    ax.set_title("Indice di vitalità v3 con la configurazione del firmware (gate dalla distanza, fondo notturno)\n"
                 r"$\alpha_m$ = 0,05 · $\alpha_v$ = 0,01 · $\beta$ = 0,5 · soglie 45 e 95 · la sesta scatola usa il gate fisso 2 della taratura",
                 fontsize=10.5, pad=14)
    salva(fig, "fig21_vitalita_scenari")
    return [(s[0].replace("\n", " "), statistics.median(d)) for s, d in zip(sc, dati)]


# =========================================================== fig22 — bordo vs offline
def fig_vitalita_bordo():
    fondo = vp.fondo_per_gate(str(DATI / "stanza_vuota_notte_T01.csv"))
    f = DATI / "Immobile_web_1m_T01.csv"
    righe = vp.leggi(str(f))
    off = vp.calcola(righe, VIT["alpha_m"], VIT["alpha_v"], VIT["k"], "distanza", fondo, sorgente="gate")
    grezze = righe_grezze(f, 0.0)
    t = np.array([x["t_s"] for x in off]); o = np.array([x["vitality"] for x in off])
    b = np.array([float(r["vitality_onboard"]) for r in grezze[:len(off)]])
    fig, ax = plt.subplots(figsize=(8.6, 3.6))
    ax.axvspan(0, 60, color=C_GRIGIO, alpha=0.12); ax.text(2, 96, "primi 60 s: EWMA del firmware\ngià a regime, quelle offline no", fontsize=8, color=C_GRIGIO, va="top")
    ax.plot(t, b, color=C_2420, lw=2.0, label="a bordo (ESP32, vitality.h)")
    ax.plot(t, o, color=C_RADAR, lw=1.1, ls="--", label="offline (vitalita_proto.py)")
    ax.axhline(45, color="#b3261e", ls=":", lw=1, label="soglia bassa/moderata (45)")
    ax.set_xlabel("tempo dall'avvio della sessione web [s]"); ax.set_ylabel("indice di vitalità"); ax.set_ylim(0, 100)
    coda = t >= 60
    entro = 100 * np.mean(np.abs(b[coda] - o[coda]) <= 1.0)
    ax.set_title(f"Verifica del porting: persona immobile a 1 m, sessione web di 90 s\n"
                 f"a regime bordo = offline entro ±1 nel {entro:.0f} % dei campioni")
    ax.legend(fontsize=8.5, loc="lower right")
    salva(fig, "fig22_vitalita_bordo")
    return entro


def main():
    print(f"Figure 14-22 -> {OUT}")
    fig_portata_ostacoli()
    att10, att36, db20 = fig_attenuazione_materiali()
    snr = dati_2420_corridoio()
    fig_portata_tre_sensori(snr)
    fp = fig_falsi_positivi()
    fig_dipme_tre_sensori()
    fig_angolare()
    pm, am = fig_tipo_movimento()
    med = fig_vitalita_scenari()
    entro = fig_vitalita_bordo()
    print("\n--- valori chiave ricalcolati dai CSV ---")
    print("  PIR sul posto 1-5 m [%]: " + ", ".join(f"{v:.1f}" for v in pm)
          + " | attraversamento 1-5 m [%]: " + ", ".join(f"{v:.1f}" for v in am))
    print("  attenuazione LD2410B [%]: " + ", ".join(f"{v:.1f}" for v in att10[:5]) + f" | cartongesso 3.6: {att36:.1f}")
    print("  attenuazione LD2420 [dB]: " + ", ".join(f"{v:.1f}" for v in db20))
    print("  LD2420 corridoio (d, E/fondo, %>trigger): " + "; ".join(f"{d} m {s:.2f} {o:.0f}%" for d, s, o in snr))
    print(f"  falsi positivi [eventi/h]: LD2410B <= {fp[0]:.2f} | LD2420 tarato {fp[1]:.1f} | g0alto {fp[2]:.1f}")
    print("  vitalità mediane: " + "; ".join(f"{n} {m:.1f}" for n, m in med))
    print(f"  bordo vs offline entro +-1 a regime: {entro:.1f} %")


if __name__ == "__main__":
    main()
