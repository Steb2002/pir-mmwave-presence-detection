#!/usr/bin/env python3
"""
Genera le figure della tesi dai CSV della campagna sperimentale.

    python analisi/grafici_tesi.py

Scrive ogni figura come .png a 300 dpi in overleaf/figures/, con il nome usato nella
tesi, e come .pdf vettoriale in overleaf/figures/origin/ (vedi uscita_figure.py).

I numeri sono ricalcolati dai CSV riusando le funzioni di analizza_test.py, con le
stesse convenzioni di scarto del transitorio usate nel capitolo 4:
  20 s scenari ordinari · 40 s sotto il banco · 120 s scenari di selettivita'.
"""
import sys, math, statistics, csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

QUI = Path(__file__).resolve().parent
RADICE = QUI.parent
DATI = RADICE / "data"
sys.path.insert(0, str(QUI))
from uscita_figure import PNG as OUT, salva  # noqa: E402
from analizza_test import leggi_csv, analizza_file, impulsi_pir  # noqa: E402

# ---------------------------------------------------------------- stile comune
C_RADAR = "#1b6ca8"
C_PIR   = "#d1495b"
C_GRIGIO = "#6c757d"
C_2420 = "#e08e0b"     # LD2420, stesso colore di grafici_tesi_2.py
plt.rcParams.update({
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.6,
    "legend.frameon": False,
    "figure.dpi": 110,
})

SKIP = {"sel": 120.0, "sotto_banco": 40.0, "default": 20.0}


def skip_per(scenario):
    if scenario.startswith("sel_"):
        return SKIP["sel"]
    if scenario.startswith("sotto_banco"):
        return SKIP["sotto_banco"]
    return SKIP["default"]


def files(pattern):
    return sorted(DATI.glob(pattern))


def stats_scenario(pattern, skip=None, scenario=None):
    """Ritorna la lista dei dizionari di analizza_file per i trial dello scenario."""
    fs = files(pattern)
    if skip is None:
        skip = skip_per(scenario or fs[0].stem)
    out = []
    for f in fs:
        r = analizza_file(str(f), salta_inizio_s=skip)
        if r:
            out.append(r)
    return out


def media_dev(vals):
    vals = [v for v in vals if isinstance(v, (int, float))]
    if not vals:
        return float("nan"), 0.0
    return statistics.mean(vals), (statistics.stdev(vals) if len(vals) > 1 else 0.0)


def serie(path, colonne):
    """Legge un CSV grezzo e ritorna dict colonna -> np.array, più 't' in secondi."""
    t, dati = [], {c: [] for c in colonne}
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        for r in csv.DictReader(f):
            try:
                ts = int(r["timestamp_ms"])
                vals = [float(r[c]) for c in colonne]
            except (KeyError, ValueError, TypeError):
                continue
            t.append(ts)
            for c, v in zip(colonne, vals):
                dati[c].append(v)
    t = np.array(t, dtype=float)
    t = (t - t[0]) / 1000.0
    return t, {c: np.array(v) for c, v in dati.items()}


# =========================================================== OBIETTIVO 3
def fig_doserisposta():
    """Il grafico centrale: a geometria costante (1 m, jumper H) cambia solo il movimento."""
    cond = [
        ("stanza vuota\n(nessuno)",      "stanza_vuota_T01.csv",        None),
        ("persona\nimmobile",            "fermo_1m_H_T*.csv",           "fermo_1m_H"),
        ("micro-\nmovimenti",            "micromovimenti_1m_H_T*.csv",  "micromovimenti_1m_H"),
        ("cammino\nsul posto",           "movimento_1m_H_T*.csv",       "movimento_1m_H"),
    ]
    et_pir, ed_pir, et_rad, ed_rad, lab = [], [], [], [], []
    for nome, pat, sc in cond:
        # La stanza vuota richiede uno scarto piu' lungo: a 20 s la coda di presenza
        # dell'operatore che esce vale ancora 0,6 % e non e' un falso positivo.
        rs = stats_scenario(pat, skip=60.0 if sc is None else 20.0, scenario=sc or "x")
        mp, dp = media_dev([r["pir_rate_%"] for r in rs])
        mr, dr = media_dev([r["radar_rate_%"] for r in rs])
        lab.append(nome); et_pir.append(mp); ed_pir.append(dp)
        et_rad.append(mr); ed_rad.append(dr)

    # LD2420: stessa geometria, sessione separata, soglie tarate. La stanza vuota non e'
    # riportata: dipende dalla configurazione ed e' discussa a parte (falsi positivi).
    cond_c = [None,
              ("fermo2420_1m_T*.csv", 90.0),
              ("micromovimenti2420_1m_T*.csv", 90.0),
              ("movimento2420_1m_T*.csv", 20.0)]
    et_c, ed_c = [], []
    for c in cond_c:
        if c is None:
            et_c.append(None); ed_c.append(None); continue
        rs = stats_scenario(c[0], skip=c[1], scenario="x")
        m_, d_ = media_dev([r["radar_rate_%"] for r in rs])
        et_c.append(m_); ed_c.append(d_)

    fig, ax = plt.subplots(figsize=(7.8, 4.0))
    x = np.arange(len(lab)); w = 0.27
    ax.bar(x - w, et_rad, w, yerr=ed_rad, capsize=4, color=C_RADAR,
           label="mmWave LD2410B", edgecolor="white")
    xc = [xi for xi, v in zip(x, et_c) if v is not None]
    ax.bar(xc, [v for v in et_c if v is not None], w, yerr=[d for d in ed_c if d is not None],
           capsize=4, color=C_2420, label="mmWave LD2420 (sessione separata)", edgecolor="white")
    ax.bar(x + w, et_pir, w, yerr=ed_pir, capsize=4, color=C_PIR,
           label="PIR HC-SR501 (jumper H)", edgecolor="white")
    for xi, v, d in zip(x - w, et_rad, ed_rad):
        ax.text(xi, v + 2.5, f"{v:.0f}" if v in (0, 100) else f"{v:.1f}", ha="center", fontsize=8.5,
                color=C_RADAR, fontweight="bold")
    for xi, v in zip(x, et_c):
        if v is not None:
            ax.text(xi, v + 2.5, f"{v:.0f}" if v in (0, 100) else f"{v:.1f}", ha="center", fontsize=8.5,
                    color=C_2420, fontweight="bold")
    for xi, v, d in zip(x + w, et_pir, ed_pir):
        ax.text(xi, v + d + 2.5, f"{v:.0f}" if v == 0 else f"{v:.1f}", ha="center", fontsize=8.5,
                color=C_PIR, fontweight="bold")
    for xi, v in zip(x, et_c):
        if v is None:
            ax.text(xi, 2.5, "n.d.", ha="center", fontsize=8, color=C_GRIGIO)
    ax.set_xticks(x); ax.set_xticklabels(lab)
    ax.set_ylabel("tempo con presenza rilevata [%]")
    ax.set_ylim(0, 112)
    ax.set_yticks(range(0, 101, 20))
    ax.set_title("Rilevamento in funzione della quantità di movimento\n"
                 "(soggetto a 1 m, stessa postura e stesso setup: cambia solo il movimento)", pad=26)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, frameon=False, fontsize=8.5)
    salva(fig, "fig01_dose_risposta")
    return list(zip(lab, et_rad, et_pir, ed_pir))


def fig_timeline_dipme():
    """Traccia appaiata radar/PIR sulla persona immobile, nelle due geometrie del capitolo 4:
    seduta a 2,3 m (Test 1.3, scarto 20 s) e sotto il banco a ~60 cm (Test 1.4, scarto 40 s)."""
    casi = [("fermo_seduto_T01.csv", 20.0, "Seduto immobile a 2,3 m"),
            ("sotto_banco_immobile_H_T01.csv", 40.0, "Immobile sotto il banco, ~60 cm")]
    fig, axes = plt.subplots(3, 2, figsize=(10.4, 5.0), sharex="col",
                             gridspec_kw={"height_ratios": [1, 1, 1.5]})
    for j, (nome, skip, titolo) in enumerate(casi):
        t, d = serie(DATI / nome, ["radar_presence", "pir_presence", "stationary_distance_cm"])
        m = t >= skip
        t, d = t[m] - skip, {k: v[m] for k, v in d.items()}
        a0, a1, a2 = axes[0, j], axes[1, j], axes[2, j]
        a0.fill_between(t, 0, d["radar_presence"], step="post", color=C_RADAR, alpha=0.85)
        a1.fill_between(t, 0, d["pir_presence"], step="post", color=C_PIR, alpha=0.85)
        for a, lab, col in ((a0, "mmWave", C_RADAR), (a1, "PIR", C_PIR)):
            a.set_ylim(-0.1, 1.65); a.set_yticks([0, 1]); a.set_yticklabels(["no", "sì"])
            a.grid(False)
            if j == 0:
                a.set_ylabel(lab, color=col)
        a0.set_title(titolo)
        a0.text(0.99, 0.86, f"presenza rilevata {100 * d['radar_presence'].mean():.1f} % del tempo",
                transform=a0.transAxes, ha="right", fontsize=9, color=C_RADAR)
        a1.text(0.99, 0.86, f"presenza rilevata {100 * d['pir_presence'].mean():.1f} % del tempo",
                transform=a1.transAxes, ha="right", fontsize=9, color=C_PIR)
        a2.plot(t, d["stationary_distance_cm"], lw=0.8, color=C_RADAR)
        a2.set_xlabel("tempo dall'inizio della finestra utile [s]")
        if j == 0:
            a2.set_ylabel("distanza\nbersaglio fermo [cm]")
        a2.set_ylim(0, max(140, float(np.nanmax(d["stationary_distance_cm"])) * 1.15))
    fig.subplots_adjust(wspace=0.12)
    salva(fig, "fig02_timeline_sotto_banco")


def fig_dipme_barre():
    """Sotto il banco: con micro-movimenti il PIR va bene, da fermo no. Il radar sempre 100%."""
    gruppi = [("con micro-movimenti", "sotto_banco_movimenti_H_T*.csv"),
              ("immobile",            "sotto_banco_immobile_H_T*.csv")]
    fig, ax = plt.subplots(figsize=(5.6, 3.9))
    x = np.arange(len(gruppi)); w = 0.38
    for i, (nome, pat) in enumerate(gruppi):
        rs = stats_scenario(pat, skip=40.0)
        mr, dr = media_dev([r["radar_rate_%"] for r in rs])
        mp, dp = media_dev([r["pir_rate_%"] for r in rs])
        ax.bar(x[i] - w/2, mr, w, yerr=dr, capsize=4, color=C_RADAR, edgecolor="white",
               label="mmWave LD2410B" if i == 0 else None)
        ax.bar(x[i] + w/2, mp, w, yerr=dp, capsize=4, color=C_PIR, edgecolor="white",
               label="PIR HC-SR501" if i == 0 else None)
        ax.text(x[i] - w/2, mr + 3, f"{mr:.2f}", ha="center", fontsize=9,
                color=C_RADAR, fontweight="bold")
        ax.text(x[i] + w/2, mp + dp + 3, f"{mp:.2f}", ha="center", fontsize=9,
                color=C_PIR, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels([g[0] for g in gruppi])
    ax.set_ylabel("tempo con presenza rilevata [%]"); ax.set_ylim(0, 118)
    ax.set_title("Scenario del progetto: persona sotto il banco (~60 cm)\n"
                 "5 trial per condizione, jumper H")
    ax.legend(loc="center right")
    salva(fig, "fig03_dipme_sotto_banco")


def fig_distanza():
    """Accuratezza della distanza 1-5 m: regressione + residui.

    I 25 trial servono a mostrare la dispersione; la retta e il R2 riportati nel
    capitolo 4 sono calcolati sulle 5 medie per distanza, che e' la grandezza
    di interesse (l'errore sistematico del sensore, non la variabilita' fra trial).
    """
    per_dist, xs, ys = {}, [], []
    for d in (1, 2, 3, 4, 5):
        rs = stats_scenario(f"movimento_{d}m_T*.csv", skip=20.0)
        vals = [r["mdist_media_cm"] for r in rs if "mdist_media_cm" in r]
        per_dist[d] = (vals, [r["mdist_dev_cm"] for r in rs if "mdist_dev_cm" in r])
        for v in vals:
            xs.append(d * 100.0)
            ys.append(v)
    xs, ys = np.array(xs), np.array(ys)
    xm = np.array([d * 100.0 for d in (1, 2, 3, 4, 5)])
    ym = np.array([statistics.mean(per_dist[d][0]) for d in (1, 2, 3, 4, 5)])
    ysd = np.array([statistics.stdev(per_dist[d][0]) for d in (1, 2, 3, 4, 5)])

    a, b = np.polyfit(xm, ym, 1)
    res_m = ym - (a * xm + b)
    r2 = 1 - float((res_m ** 2).sum()) / float(((ym - ym.mean()) ** 2).sum())

    fig, axes = plt.subplots(2, 1, figsize=(6.6, 5.6), sharex=True,
                             gridspec_kw={"height_ratios": [2.4, 1]})
    xx = np.linspace(80, 520, 50)
    axes[0].plot(xx, xx, color=C_GRIGIO, ls="--", lw=1, label="identità (misurata = reale)")
    axes[0].plot(xx, a * xx + b, color=C_RADAR, lw=1.6,
                 label=f"regressione sulle medie:  $y = {a:.4f}\\,x {b:+.2f}$   ($R^2 = {r2:.5f}$)")
    axes[0].scatter(xs, ys, s=16, color=C_RADAR, alpha=0.35, zorder=2,
                    label="25 trial singoli")
    axes[0].errorbar(xm, ym, yerr=ysd, fmt="o", ms=7, color=C_RADAR, capsize=4,
                     zorder=3, markeredgecolor="white", markeredgewidth=0.8,
                     label="media dei 5 trial per distanza")
    axes[0].set_ylabel("distanza misurata dal radar [cm]")
    axes[0].set_title("Accuratezza della distanza - LD2410B, canale moving\n"
                      "soggetto che cammina sul posto a distanza nota")
    axes[0].legend(loc="upper left", fontsize=8.5)

    axes[1].axhline(0, color=C_GRIGIO, lw=0.8)
    axes[1].scatter(xs, ys - (a * xs + b), s=14, color=C_RADAR, alpha=0.3)
    axes[1].scatter(xm, res_m, s=55, color=C_RADAR, zorder=3,
                    edgecolor="white", linewidth=0.8)
    axes[1].set_ylabel("residuo [cm]")
    axes[1].set_xlabel("distanza reale [cm]")
    axes[1].set_ylim(-9, 11)
    axes[1].text(0.99, 0.93, f"residuo massimo sulle medie: {np.abs(res_m).max():.1f} cm",
                 transform=axes[1].transAxes, ha="right", va="top", fontsize=9, color=C_GRIGIO)
    salva(fig, "fig04_distanza_regressione")
    return a, b, r2, per_dist


def fig_energia_distanza(per_dist=None):
    """Energia del bersaglio in funzione della distanza + dispersione entro il trial."""
    dists = [1, 2, 3, 4, 5]
    en_m, en_d, disp_m, disp_d, pir_m, pir_d = [], [], [], [], [], []
    for d in dists:
        rs = stats_scenario(f"movimento_{d}m_T*.csv", skip=20.0)
        m, s = media_dev([r.get("menergy_media") for r in rs]); en_m.append(m); en_d.append(s)
        m, s = media_dev([r.get("mdist_dev_cm") for r in rs]); disp_m.append(m); disp_d.append(s)
        m, s = media_dev([r["pir_rate_%"] for r in rs]); pir_m.append(m); pir_d.append(s)

    # Un solo pannello: la portata del PIR sul posto sta ora in fig28 (tipo di movimento).
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.errorbar(dists, en_m, yerr=en_d, marker="o", color=C_RADAR, capsize=4, lw=1.6,
                label="energia media del bersaglio in movimento")
    for x, y in zip(dists, en_m):
        ax.annotate(f"{y:.1f}", (x, y), textcoords="offset points", xytext=(0, 9),
                    ha="center", fontsize=9, color=C_RADAR)
    ax2 = ax.twinx()
    ax2.bar(dists, disp_m, 0.35, yerr=disp_d, capsize=3, color=C_GRIGIO, alpha=0.35,
            edgecolor="white", label="dispersione della distanza entro il trial")
    ax2.set_ylabel("dispersione entro il trial [cm]", color=C_GRIGIO)
    ax2.set_ylim(0, 130); ax2.set_yticks(range(0, 31, 10)); ax2.grid(False); ax2.spines["right"].set_visible(True)
    ax.axhline(15, color=C_PIR, lw=1.0, ls=":", label="soglia di fabbrica dei gate lontani (15)")
    ax.set_xlabel("distanza reale [m]"); ax.set_ylabel("energia media del bersaglio [0-100]")
    ax.set_ylim(0, 115); ax.set_xticks(dists)
    ax.set_title("LD2410B, cammino sul posto a 1-5 m (25 trial)")
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=8.5)
    salva(fig, "fig05_energia_distanza")


def fig_latenza():
    """Test 2.1 (ingresso, 10 trial appaiati) e Test 2.2 (rilascio, 5 trial)."""
    lat_r, lat_p = [], []
    for f in files("ingresso_T*.csv"):
        r = analizza_file(str(f), event_time_s=30.0)
        if r and isinstance(r.get("latenza_radar_s"), float) and isinstance(r.get("latenza_pir_s"), float):
            lat_r.append(r["latenza_radar_s"]); lat_p.append(r["latenza_pir_s"])
    ril_r, ril_p = [], []
    for f in files("uscita_T*.csv"):
        r = analizza_file(str(f), release_time_s=30.0)
        if not r:
            continue
        if isinstance(r.get("rilascio_radar_s"), float):
            ril_r.append(r["rilascio_radar_s"])
        if isinstance(r.get("rilascio_pir_s"), float):
            ril_p.append(r["rilascio_pir_s"])
    # LD2420: sessione separata, PIR non cablato, ritardo di scomparsa 5 s all'uscita.
    # Il rilascio e' la PRIMA caduta dopo l'evento: in 2 trial su 3 seguono brevi
    # riaccensioni a stanza vuota (falsi positivi residui del modulo).
    lat_c = []
    for f in files("ingresso2420_porta2_T0[2-6].csv"):
        r = analizza_file(str(f), event_time_s=30.0)
        if r and isinstance(r.get("latenza_radar_s"), float):
            lat_c.append(r["latenza_radar_s"])
    ril_c, riacc_c = [], 0
    for f in files("uscita2420_rit5_T*.csv"):
        with open(f, encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        t0 = float(rows[0]["timestamp_ms"])
        ev = [((float(x["timestamp_ms"]) - t0) / 1000.0, int(x["radar_presence"])) for x in rows]
        prima = next(t for t, p_ in ev if t >= 30.0 and p_ == 0)
        ril_c.append(prima - 30.0)
        if any(p_ == 1 for t, p_ in ev if t > prima):
            riacc_c += 1

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    fig.subplots_adjust(wspace=0.32)
    # (a) slopegraph appaiato
    for a_, b_ in zip(lat_r, lat_p):
        axes[0].plot([0, 1], [a_, b_], color=C_GRIGIO, lw=0.9, alpha=0.65, zorder=1)
    axes[0].scatter([0] * len(lat_r), lat_r, s=42, color=C_RADAR, zorder=3,
                    edgecolor="white", linewidth=0.7)
    axes[0].scatter([1] * len(lat_p), lat_p, s=42, color=C_PIR, zorder=3,
                    edgecolor="white", linewidth=0.7)
    mr, dr = media_dev(lat_r); mp, dp = media_dev(lat_p)
    delta = [a_ - b_ for a_, b_ in zip(lat_r, lat_p)]
    md, dd = media_dev(delta)
    axes[0].scatter([0, 1], [mr, mp], marker="_", s=900, color="black", zorder=4, linewidth=2)
    mc, dc = media_dev(lat_c)
    axes[0].scatter([2] * len(lat_c), lat_c, s=46, color=C_2420, marker="^", zorder=3,
                    edgecolor="white", linewidth=0.7)
    axes[0].scatter([2], [mc], marker="_", s=900, color="black", zorder=4, linewidth=2)
    axes[0].text(2, max(lat_c) + 0.25, f"{mc:.2f} ± {dc:.2f} s", ha="center", va="bottom", fontsize=8.5)
    axes[0].axvline(1.5, color=C_GRIGIO, lw=0.8, ls=":")
    axes[0].set_xticks([0, 1, 2])
    axes[0].set_xticklabels(["LD2410B", "PIR", "LD2420\n(sessione separata)"])
    axes[0].set_xlim(-0.35, 2.45)
    axes[0].set_ylabel("latenza di rilevamento [s]")
    axes[0].set_title(f"Ingresso — {len(lat_r)} trial appaiati ({len(lat_c)} per l'LD2420)\n"
                      f"{mr:.2f} ± {dr:.2f} s  vs  {mp:.2f} ± {dp:.2f} s")
    axes[0].text(0.5, max(lat_r + lat_p) + 1.3,
                 f"differenza appaiata radar−PIR\n{md:+.2f} ± {dd:.2f} s\n"
                 f"radar primo in {sum(1 for x in delta if x < 0)}/{len(delta)} trial",
                 ha="center", va="center", fontsize=8.5)
    axes[0].set_ylim(min(lat_r + lat_p) - 0.5, max(lat_r + lat_p + lat_c) + 0.9)

    # (b) rilascio
    x = np.arange(3)
    mrr, drr = media_dev(ril_r); mpp, dpp = media_dev(ril_p); mcc, dcc = media_dev(ril_c)
    axes[1].bar(x, [mrr, mpp, mcc], 0.5, yerr=[drr, dpp, dcc], capsize=5,
                color=[C_RADAR, C_PIR, C_2420], edgecolor="white")
    axes[1].text(2, mcc + dcc + 2.4, f"prima caduta,\nriaccensioni in {riacc_c}/{len(ril_c)}",
                 ha="center", va="bottom", fontsize=7.5, color=C_GRIGIO)
    for xi, v, d in zip(x, [mrr, mpp, mcc], [drr, dpp, dcc]):
        axes[1].text(xi, v + d + 0.5, f"{v:.2f} ± {d:.2f} s", ha="center", fontsize=9,
                     fontweight="bold")
    axes[1].axhline(5, color=C_GRIGIO, ls="--", lw=1)
    axes[1].annotate("ritardo\n5 s", xy=(0.5, 5), xytext=(0.5, 7.2),
                     ha="center", va="bottom", fontsize=8, color=C_GRIGIO,
                     arrowprops=dict(arrowstyle="->", color=C_GRIGIO, lw=0.8))
    axes[1].set_xticks(x); axes[1].set_xticklabels(["LD2410B", "PIR", "LD2420\n(sessione separata)"])
    axes[1].set_ylabel("tempo per dichiarare la stanza vuota [s]")
    axes[1].set_title(f"Uscita — {len(ril_r)} trial ({len(ril_c)} per l'LD2420)\n"
                      "l'LD2410B tiene la presenza più a lungo")
    axes[1].set_ylim(0, max(mrr + drr, mpp + dpp) * 1.35); axes[1].set_xlim(-0.65, 2.65)
    salva(fig, "fig06_latenze")
    return mr, dr, mp, dp, md, dd, mrr, drr, mpp, dpp


def fig_impulsi_pir():
    """L'uscita del PIR è un monostabile: in L durata fissa, in H il ritrigger la allunga."""
    def raccogli(patterns, skip):
        comp, tron = [], []
        for pat in patterns:
            for f in files(pat):
                c, t = impulsi_pir(leggi_csv(str(f)), skip)
                comp += c
                tron += t
        return comp, tron

    L_c, L_t = raccogli(["movimento_1m_T*.csv", "sotto_banco_movimenti_T*.csv"], 20.0)
    H_c, H_t = raccogli(["movimento_1m_H_T*.csv", "sotto_banco_movimenti_H_T*.csv"], 20.0)

    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.9))
    axes[0].hist(L_c, bins=np.arange(2.5, 6.1, 0.1), color=C_PIR, edgecolor="white")
    m, d = media_dev(L_c)
    axes[0].set_title(f"Modalità L (non ripetibile)\n"
                      f"{len(L_c)} impulsi - {m:.2f} +/- {d:.2f} s - nessuno oltre 5 s")
    axes[0].set_xlabel("durata dell'impulso [s]")
    axes[0].set_ylabel("conteggio")
    axes[0].set_xlim(2.5, 6.0)

    # In H gli impulsi sono pochi e lunghissimi: un istogramma non li descrive.
    # Si riportano uno per uno, distinguendo i troncati dalla fine del file.
    dati = sorted([(v, False) for v in H_c] + [(v, True) for v in H_t])
    y = np.arange(len(dati))
    col = [C_GRIGIO if t else C_PIR for _, t in dati]
    axes[1].barh(y, [v for v, _ in dati], color=col, edgecolor="white", height=0.8)
    axes[1].set_yticks([])
    axes[1].set_xlabel("durata dell'impulso [s]")
    axes[1].set_ylabel(f"i {len(dati)} impulsi, ordinati", labelpad=10)
    axes[1].axvline(m, color="black", ls="--", lw=1, label=f"durata fissa in L ({m:.2f} s)")
    axes[1].plot([], [], color=C_PIR, lw=6, label=f"{len(H_c)} impulsi completi")
    axes[1].plot([], [], color=C_GRIGIO, lw=6,
                 label=f"{len(H_t)} troncati dalla fine del trial\n(durata reale >= barra)")
    axes[1].legend(fontsize=8.5, loc="lower right")
    axes[1].set_title(f"Modalità H (repeat trigger)\n"
                      f"{len(dati)} impulsi - il più lungo >= {max(v for v, _ in dati):.0f} s")
    fig.suptitle("L'uscita del PIR non misura la presenza: conta eventi di movimento", y=1.04)
    salva(fig, "fig07_impulsi_pir")
    return len(L_c), media_dev(L_c), len(H_c), media_dev(H_c), H_t


def fig_due_persone():
    """Due persone: i due canali le separano se sono in stati diversi; in fila no."""
    casi = [("Sfalsate di ~50 cm di lato\n(A ferma a 2 m, B cammina a 4 m)", "due_persone_T01.csv"),
            ("In fila sull'asse\n(B esattamente dietro A)", "due_persone_infila_T01.csv")]
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.8), sharey=True)
    for ax, (titolo, nome) in zip(axes, casi):
        t, d = serie(DATI / nome, ["moving_distance_cm", "stationary_distance_cm",
                                   "moving_target", "stationary_target"])
        m = t >= 20.0
        t = t[m] - 20.0
        md = np.where(d["moving_target"][m] == 1, d["moving_distance_cm"][m], np.nan)
        sd = np.where(d["stationary_target"][m] == 1, d["stationary_distance_cm"][m], np.nan)
        ax.plot(t, md, ".", ms=2.2, color=C_RADAR, label="canale moving")
        ax.plot(t, sd, ".", ms=2.2, color="#e08214", label="canale stazionario")
        ax.axhline(200, color=C_GRIGIO, ls="--", lw=0.9)
        ax.axhline(400, color=C_GRIGIO, ls="--", lw=0.9)
        ax.set_title(titolo); ax.set_xlabel("tempo [s]"); ax.set_ylim(0, 520)
    axes[0].set_ylabel("distanza riportata [cm]")
    for yv, et in ((200, "A\n(ferma, 2 m)"), (400, "B\n(cammina, 4 m)")):
        axes[1].text(1.02, yv, et, transform=axes[1].get_yaxis_transform(), fontsize=8,
                     color=C_GRIGIO, ha="left", va="center")
    axes[0].legend(loc="lower left", fontsize=9, markerscale=4)
    fig.suptitle("L'LD2410B riporta un bersaglio per canale, e chi sta dietro è invisibile", y=1.09)
    salva(fig, "fig08_due_persone")


def fig_selettivita():
    """Test 2.4: con gate massimo 2 il taglio in distanza funziona; il vicino a 90° non entra."""
    sc = [("occupante a 1 m\nsull'asse",   "sel_dentro_1m_T*.csv"),
          ("persona a 3 m\n(oltre il taglio)", "sel_fuori_3m_T*.csv"),
          ("persona a 1 m\na 90°",          "sel_laterale_1m_T*.csv"),
          ("occupante\n+ vicino a 90°",     "sel_con_vicino_T*.csv")]
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    x = np.arange(len(sc)); w = 0.38
    for i, (nome, pat) in enumerate(sc):
        c0 = x[i]
        r20 = stats_scenario(pat, skip=20.0)
        r120 = stats_scenario(pat, skip=120.0)
        m20, d20 = media_dev([r["radar_rate_%"] for r in r20])
        m120, d120 = media_dev([r["radar_rate_%"] for r in r120])
        ax.bar(c0 - w/2, m20, w, yerr=d20, capsize=4, color="#9fc5dd", edgecolor="white",
               label="finestra ordinaria: scarto dei primi 20 s" if i == 0 else None)
        ax.bar(c0 + w/2, m120, w, yerr=d120, capsize=4, color=C_RADAR, edgecolor="white",
               label="a regime: scarto dei primi 120 s" if i == 0 else None)
        ax.text(c0 + w/2, m120 + d120 + 3, f"{m120:.1f}", ha="center", fontsize=9,
                color=C_RADAR, fontweight="bold")
        ax.text(c0 - w/2, m20 + d20 + 3, f"{m20:.1f}", ha="center", fontsize=9,
                color=C_GRIGIO)
    ax.set_xticks(x); ax.set_xticklabels([s[0] for s in sc])
    ax.set_ylabel("tempo con presenza rilevata [%]"); ax.set_ylim(0, 112); ax.set_yticks(range(0, 101, 20))
    ax.set_title("Selettività spaziale con gate massimo 2 (portata tagliata a 150 cm)\n"
                 "tutti i soggetti fermi · 3 trial per scenario", pad=26)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=8.5, ncol=2, frameon=False)
    salva(fig, "fig09_selettivita")


def fig_transitorio():
    """Sezione 4.3.3: perche' negli scenari di selettivita' lo scarto iniziale e' 120 s e non 20.
    I tre trial della persona ferma a 1 m a 90 gradi (gate massimo 2): la presenza e' attiva
    dall'istante zero, si spegne una volta sola e non si riaccende. E' la coda del
    posizionamento, non un rilevamento; con 20 s entrerebbe nella statistica."""
    fig, axes = plt.subplots(3, 1, figsize=(8.6, 4.6), sharex=True)
    for i, ax in enumerate(axes):
        nome = f"sel_laterale_1m_T0{i + 1}.csv"
        t, d = serie(DATI / nome, ["radar_presence"])
        r20 = analizza_file(str(DATI / nome), salta_inizio_s=20.0)["radar_rate_%"]
        r120 = analizza_file(str(DATI / nome), salta_inizio_s=120.0)["radar_rate_%"]
        ax.axvspan(0, 20, color="#e9ecef", zorder=0)
        ax.axvspan(20, 120, color="#fde2c8", zorder=0)
        ax.fill_between(t, 0, d["radar_presence"], step="post", color=C_RADAR, alpha=0.85, zorder=2)
        spegne = t[np.argmax(d["radar_presence"] == 0)] if (d["radar_presence"] == 0).any() else None
        if spegne is not None:
            ax.annotate(f"si spegne a {spegne:.0f} s\ne non si riaccende", xy=(spegne, 0.5),
                        xytext=(spegne + 6, 0.62), fontsize=8, color=C_RADAR,
                        arrowprops=dict(arrowstyle="-", color=C_RADAR, lw=0.8))
        ax.set_ylim(-0.1, 1.25); ax.set_yticks([0, 1]); ax.set_yticklabels(["no", "sì"])
        ax.grid(False)
        ax.set_ylabel(f"T0{i + 1}", rotation=0, ha="right", va="center")
        ax.text(1.01, 0.5, f"scarto 20 s:  {r20:4.1f} %\nscarto 120 s: {r120:4.1f} %",
                transform=ax.transAxes, fontsize=8.5, va="center", family="monospace")
        ax.set_xlim(0, t[-1])
    axes[0].text(10, 1.12, "scarto\nordinario", ha="center", va="bottom", fontsize=8, color=C_GRIGIO)
    axes[0].text(70, 1.12, "scarto negli scenari di selettività (120 s)", ha="center",
                 va="bottom", fontsize=8, color="#b35c1e")
    axes[-1].set_xlabel("tempo dall'inizio del trial [s]")
    fig.suptitle("Presenza riportata dall'LD2410B con la persona ferma a 1 m a 90° (gate massimo 2)",
                 fontsize=10.5, y=1.0)
    fig.subplots_adjust(hspace=0.35, right=0.80)
    salva(fig, "fig32_transitorio")


# =========================================================== OBIETTIVO 2
GATE_M = [f"menergy_gate{i}" for i in range(9)]
GATE_S = [f"senergy_gate{i}" for i in range(9)]


def fig_gate_heatmap():
    """Cosa produce davvero il mmWave: 18 canali di energia per-gate, 5 volte al secondo."""
    # Il pilota PIR-vs-radar: e' l'unico file lungo in engineering mode con il PIR
    # davvero collegato (254 attivazioni su 1699 campioni). In 20260818_test01B il
    # PIR e' a zero su tutti i campioni, quindi qui darebbe un confronto falso.
    f = DATI / "pir_vs_radar_T01.csv"
    t, d = serie(f, GATE_M + GATE_S + ["moving_distance_cm", "moving_target",
                                       "radar_presence", "pir_presence"])
    M = np.vstack([d[c] for c in GATE_M])
    S = np.vstack([d[c] for c in GATE_S])

    # Colorbar in una colonna propria: cosi' i tre assi del tempo hanno la stessa
    # larghezza e le barre di presenza in basso stanno in colonna con le energie sopra.
    fig = plt.figure(figsize=(8.2, 5.6))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.3, 1.3, 0.6], width_ratios=[1, 0.025],
                          hspace=0.12, wspace=0.03)
    axes = [fig.add_subplot(gs[0, 0])]
    axes.append(fig.add_subplot(gs[1, 0], sharex=axes[0]))
    axes.append(fig.add_subplot(gs[2, 0], sharex=axes[0]))
    caxes = [fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, 1]), fig.add_subplot(gs[2, 1])]
    caxes[2].axis("off")
    ext = [t[0], t[-1], -0.5, 8.5]
    for ax, cax, Z, nome in ((axes[0], caxes[0], M, "moving"),
                             (axes[1], caxes[1], S, "stazionario")):
        im = ax.imshow(Z, aspect="auto", origin="lower", extent=ext,
                       cmap="magma", vmin=0, vmax=100, interpolation="nearest")
        ax.set_ylabel(f"gate\n({nome})")
        ax.set_yticks(range(0, 9, 2))
        ax.grid(False)
        ax.tick_params(labelbottom=False)
        fig.colorbar(im, cax=cax, label="energia [0-100]")
    dist = np.where(d["moving_target"] == 1, d["moving_distance_cm"] / 75.0, np.nan)
    axes[0].plot(t, dist, color="#7fd4ff", lw=1.0, label="gate atteso = distanza / 0,75 m")
    axes[0].legend(loc="upper right", fontsize=8.5, labelcolor="white",
                   facecolor="black", framealpha=0.35, frameon=True)

    axes[2].fill_between(t, 0.05, 0.05 + d["radar_presence"] * 0.9, step="post",
                         color=C_RADAR, alpha=0.85, lw=0)
    axes[2].fill_between(t, -0.05, -0.05 - d["pir_presence"] * 0.9, step="post",
                         color=C_PIR, alpha=0.85, lw=0)
    axes[2].axhline(0, color="black", lw=0.6)
    axes[2].set_xlim(t[0], t[-1])
    axes[2].set_ylim(-1.15, 1.15)
    axes[2].set_yticks([-0.5, 0.5])
    axes[2].set_yticklabels(["PIR\n(mod. L)", "LD2410B"])
    axes[2].set_xlabel("tempo [s]")
    axes[2].grid(False)
    # percentuali di presenza nella colonna delle colorbar, fuori dalle barre
    caxes[2].text(0.0, 0.72, f"{100*d['radar_presence'].mean():.0f} %", transform=caxes[2].transAxes,
                  ha="left", va="center", fontsize=9, color=C_RADAR, fontweight="bold")
    caxes[2].text(0.0, 0.28, f"{100*d['pir_presence'].mean():.0f} %", transform=caxes[2].transAxes,
                  ha="left", va="center", fontsize=9, color=C_PIR, fontweight="bold")
    axes[0].set_title("Dati prodotti dai due sensori nello stesso istante\n"
                      "LD2410B: 18 canali di energia per gate a 5 Hz  vs  PIR: 1 bit")
    salva(fig, "fig10_gate_engineering")


def fig_saturazione():
    """Il limite del dato: l'energia è un uint8 0-100 che satura sul bersaglio vicino."""
    f = DATI / "fermo_1m_H_T01.csv"
    t, d = serie(f, ["moving_energy", "stationary_energy", "moving_target", "stationary_target"])
    m = t >= 20.0
    men = d["moving_energy"][m][d["moving_target"][m] == 1]
    sen = d["stationary_energy"][m][d["stationary_target"][m] == 1]

    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.5))
    bins = np.arange(0, 102, 2)
    for ax, v, nome, col in ((axes[0], men, "canale moving", C_RADAR),
                             (axes[1], sen, "canale stazionario", "#e08214")):
        ax.hist(v, bins=bins, color=col, edgecolor="white")
        sat = 100 * float((v >= 100).mean())
        ax.set_title(f"{nome}\nsaturo al fondoscala nel {sat:.1f} % dei campioni")
        ax.set_xlabel("energia riportata [0-100]")
        ax.axvline(100, color=C_PIR, lw=1.4, ls="--")
    axes[0].set_ylabel("conteggio campioni")
    fig.suptitle("Limite del dato di energia: soggetto fermo a 1 m", y=1.05)
    salva(fig, "fig11_saturazione")


def spettro(x, fs=5.0):
    x = np.asarray(x, dtype=float)
    x = x - x.mean()
    n = len(x)
    w = np.hanning(n)
    X = np.abs(np.fft.rfft(x * w))
    f = np.fft.rfftfreq(n, d=1.0 / fs)
    return f, X


def fig_respiro():
    """Base misurata dell'obiettivo 6: il micro-movimento respiratorio nell'energia per-gate."""
    f_csv = DATI / "fermo_seduto_T01.csv"
    t, d = serie(f_csv, GATE_M + ["stationary_distance_cm"])
    m = t >= 20.0
    t = t[m] - t[m][0]
    best = None
    for c in GATE_M:
        v = d[c][m]
        if float((v >= 100).mean()) > 0.05 or v.std() < 0.5:
            continue
        fr, X = spettro(v)
        banda = (fr >= 0.10) & (fr <= 0.50)
        if not banda.any():
            continue
        i = int(np.argmax(X[banda]))
        picco_f = fr[banda][i]
        picco_a = X[banda][i]
        fondo = float(np.median(X[(fr >= 0.05) & (fr <= 1.5)]))
        snr = picco_a / fondo if fondo > 0 else 0
        if best is None or snr > best[0]:
            best = (snr, c, picco_f, fr, X, v)
    snr, canale, picco_f, fr, X, v = best

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.5))
    axes[0].plot(t[:600], v[:600], lw=0.9, color=C_RADAR)
    axes[0].set_xlabel("tempo [s]")
    axes[0].set_ylabel(f"energia {canale} [0-100]")
    axes[0].set_title("Energia per-gate nel tempo (primi 120 s)")

    banda = (fr >= 0.0) & (fr <= 1.2)
    axes[1].plot(fr[banda], X[banda], lw=1.1, color=C_RADAR)
    axes[1].axvspan(0.10, 0.50, color=C_PIR, alpha=0.10)
    axes[1].axvline(picco_f, color=C_PIR, lw=1.3, ls="--")
    axes[1].annotate(f"{picco_f:.3f} Hz = {picco_f*60:.1f} atti/min\nSNR ~ {snr:.1f}x",
                     (picco_f, X[banda].max()), textcoords="offset points", xytext=(12, -12),
                     fontsize=9, color=C_PIR)
    axes[1].set_xlabel("frequenza [Hz]")
    axes[1].set_ylabel("ampiezza FFT")
    axes[1].set_title("Spettro, banda respiratoria 0,1-0,5 Hz")
    fig.suptitle("Micro-movimento respiratorio su soggetto immobile a 2,3 m", y=1.05)
    salva(fig, "fig12_respiro")
    return canale, picco_f, snr


# =========================================================== OBIETTIVO 4
def fig_consumi():
    """Consumi da datasheet e autonomia stimata (nessuna misura: valori dichiarati)."""
    comp = [("PIR HC-SR501", 0.05, "#f0a202"),
            ("HLK-LD2420", 50.0, "#4c9f70"),
            ("HLK-LD2410B", 80.0, C_RADAR),
            ("ESP32 (WiFi attivo)", 100.0, C_GRIGIO)]
    nodi = [("ESP32 in deep-sleep\n+ PIR", 0.06),
            ("ESP32 + PIR,\nWiFi spento", 25.0),
            ("ESP32 + HLK-LD2410B,\nWiFi spento", 130.0),
            ("ESP32 + HLK-LD2410B\n+ WiFi (web UI)", 200.0)]
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.9))
    fig.subplots_adjust(wspace=0.55)

    y = np.arange(len(comp))
    axes[0].barh(y, [c[1] for c in comp], color=[c[2] for c in comp], edgecolor="white")
    axes[0].set_yticks(y)
    axes[0].set_yticklabels([c[0] for c in comp])
    axes[0].set_xscale("log")
    axes[0].set_xlabel("corrente media dichiarata [mA, scala log]")
    for yi, c in zip(y, comp):
        axes[0].text(c[1] * 1.25, yi, f"{c[1]:g} mA".replace('.', ','), va="center", fontsize=9)
    axes[0].set_xlim(0.02, 400)
    axes[0].set_title("Singoli componenti\n(valori da datasheet, non misurati)")

    aut_h = [3000 * 0.85 / n[1] for n in nodi]
    y2 = np.arange(len(nodi))
    # stessi colori del pannello di sinistra: arancio per i nodi con il PIR, blu per quelli con l'HLK-LD2410B
    axes[1].barh(y2, aut_h, color=["#f0a202", "#f6c86b", "#7fb1dc", C_RADAR], edgecolor="white")
    axes[1].set_yticks(y2)
    axes[1].set_yticklabels([n[0] for n in nodi], fontsize=9)
    axes[1].set_xscale("log")
    axes[1].set_xlabel("autonomia stimata [ore, scala log]")
    for yi, h in zip(y2, aut_h):
        if h > 8760:
            et = f"{h/8760:.1f} anni".replace('.', ',')
        elif h > 48:
            et = f"{h/24:.0f} giorni"
        else:
            et = f"{h:.0f} h"
        axes[1].text(h * 1.3, yi, et, va="center", fontsize=9)
    axes[1].set_xlim(5, 1e6)
    axes[1].set_title("Nodo completo su batteria 18650 3000 mAh\n(efficienza regolatore 85 %)")
    fig.suptitle("Consumo dei componenti e autonomia del nodo completo", y=1.05)
    salva(fig, "fig13_consumi")


def main():
    print(f"Figure -> {OUT}")
    dose = fig_doserisposta()
    fig_timeline_dipme()
    fig_dipme_barre()
    a, b, r2, _ = fig_distanza()
    fig_energia_distanza()
    lat = fig_latenza()
    imp = fig_impulsi_pir()
    fig_due_persone()
    fig_selettivita()
    fig_transitorio()
    fig_gate_heatmap()
    fig_saturazione()
    resp = fig_respiro()
    fig_consumi()

    print("\n--- valori chiave ricalcolati dai CSV ---")
    for nome, r, p, dp in dose:
        etichetta = nome.replace("\n", " ")
        print(f"  {etichetta:28s} radar {r:6.2f} %   PIR {p:6.2f} +/- {dp:.2f} %")
    print(f"  regressione distanza: y = {a:.4f} x {b:+.2f} cm, R2 = {r2:.5f}")
    print(f"  latenza ingresso  radar {lat[0]:.2f} +/- {lat[1]:.2f} s | "
          f"PIR {lat[2]:.2f} +/- {lat[3]:.2f} s | delta {lat[4]:+.2f} +/- {lat[5]:.2f} s")
    print(f"  latenza rilascio  radar {lat[6]:.2f} +/- {lat[7]:.2f} s | "
          f"PIR {lat[8]:.2f} +/- {lat[9]:.2f} s")
    print(f"  impulsi PIR: L n={imp[0]} {imp[1][0]:.2f} +/- {imp[1][1]:.2f} s | "
          f"H n={imp[2]} {imp[3][0]:.1f} +/- {imp[3][1]:.1f} s, troncati {len(imp[4])}")
    print(f"  respiro: {resp[1]:.3f} Hz = {resp[1]*60:.1f} atti/min su {resp[0]}, SNR {resp[2]:.1f}x")


if __name__ == "__main__":
    main()
