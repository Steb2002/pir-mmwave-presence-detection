#!/usr/bin/env python3
"""
Genera le figure della tesi dai CSV della campagna sperimentale.

    python analisi/grafici_tesi.py

Scrive in tesi-unicam/figures/ una coppia .pdf (vettoriale, per LaTeX) e .png
(300 dpi, per slide/anteprima) per ogni figura.

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
DATI = RADICE / "HLK-LD2410x" / "data"
OUT = RADICE / "tesi-unicam" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(QUI))
from analizza_test import leggi_csv, analizza_file, impulsi_pir  # noqa: E402

# ---------------------------------------------------------------- stile comune
C_RADAR = "#1b6ca8"
C_PIR   = "#d1495b"
C_GRIGIO = "#6c757d"
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


def salva(fig, nome):
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{nome}.{ext}", bbox_inches="tight",
                    dpi=300 if ext == "png" else None)
    plt.close(fig)
    print(f"  ok  {nome}.pdf / .png")


def serie(path, colonne):
    """Legge un CSV grezzo e ritorna dict colonna -> np.array, piu' 't' in secondi."""
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

    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    x = np.arange(len(lab)); w = 0.38
    ax.bar(x - w/2, et_rad, w, yerr=ed_rad, capsize=4, color=C_RADAR,
           label="mmWave LD2410B", edgecolor="white")
    ax.bar(x + w/2, et_pir, w, yerr=ed_pir, capsize=4, color=C_PIR,
           label="PIR HC-SR501 (jumper H)", edgecolor="white")
    for xi, v, d in zip(x - w/2, et_rad, ed_rad):
        ax.text(xi, v + 2.5, f"{v:.1f}", ha="center", fontsize=9, color=C_RADAR, fontweight="bold")
    for xi, v, d in zip(x + w/2, et_pir, ed_pir):
        ax.text(xi, v + d + 2.5, f"{v:.1f}", ha="center", fontsize=9, color=C_PIR, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(lab)
    ax.set_ylabel("tempo con presenza rilevata [%]")
    ax.set_ylim(0, 118)
    ax.set_title("Rilevamento in funzione della quantità di movimento\n"
                 "(soggetto a 1 m, stessa postura e stesso setup: cambia solo il movimento)")
    ax.legend(loc="upper left", bbox_to_anchor=(0.005, 0.97))
    ax.axhline(100, color=C_GRIGIO, lw=0.7, ls=":")
    salva(fig, "fig01_dose_risposta")
    return list(zip(lab, et_rad, et_pir, ed_pir))


def fig_timeline_uprise():
    """Traccia appaiata radar/PIR nello scenario del progetto: persona ferma sotto il banco."""
    f = DATI / "sotto_banco_immobile_H_T01.csv"
    t, d = serie(f, ["radar_presence", "pir_presence", "stationary_distance_cm",
                     "stationary_energy"])
    m = t >= 40.0                       # convenzione sotto-banco
    t, d = t[m] - 40.0, {k: v[m] for k, v in d.items()}

    fig, axes = plt.subplots(3, 1, figsize=(7.6, 4.8), sharex=True,
                             gridspec_kw={"height_ratios": [1, 1, 1.5]})
    axes[0].fill_between(t, 0, d["radar_presence"], step="post", color=C_RADAR, alpha=0.85)
    axes[0].set_ylim(-0.1, 1.2); axes[0].set_yticks([0, 1]); axes[0].set_yticklabels(["no", "sì"])
    axes[0].set_ylabel("mmWave", color=C_RADAR)
    axes[0].set_title("Persona immobile sotto il banco (~60 cm) — scenario UPRISE, trial T01")

    axes[1].fill_between(t, 0, d["pir_presence"], step="post", color=C_PIR, alpha=0.85)
    axes[1].set_ylim(-0.1, 1.2); axes[1].set_yticks([0, 1]); axes[1].set_yticklabels(["no", "sì"])
    axes[1].set_ylabel("PIR", color=C_PIR)

    axes[2].plot(t, d["stationary_distance_cm"], lw=0.8, color=C_RADAR)
    axes[2].set_ylabel("distanza\nbersaglio fermo [cm]")
    axes[2].set_xlabel("tempo dall'inizio della finestra utile [s]")
    axes[2].set_ylim(0, max(140, np.nanmax(d["stationary_distance_cm"]) * 1.15))

    pir_pct = 100 * d["pir_presence"].mean()
    rad_pct = 100 * d["radar_presence"].mean()
    axes[0].text(0.99, 0.82, f"presenza rilevata {rad_pct:.1f} % del tempo",
                 transform=axes[0].transAxes, ha="right", fontsize=9, color=C_RADAR)
    axes[1].text(0.99, 0.82, f"presenza rilevata {pir_pct:.1f} % del tempo",
                 transform=axes[1].transAxes, ha="right", fontsize=9, color=C_PIR)
    for a in axes[:2]:
        a.grid(False)
    salva(fig, "fig02_timeline_sotto_banco")


def fig_uprise_barre():
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
    salva(fig, "fig03_uprise_sotto_banco")


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
    axes[0].plot(xx, xx, color=C_GRIGIO, ls="--", lw=1, label="identita' (misurata = reale)")
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
    axes[1].set_ylim(-8, 8)
    axes[1].text(0.99, 0.08, f"residuo massimo sulle medie: {np.abs(res_m).max():.1f} cm",
                 transform=axes[1].transAxes, ha="right", fontsize=9, color=C_GRIGIO)
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

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.6))
    axes[0].errorbar(dists, en_m, yerr=en_d, marker="o", color=C_RADAR, capsize=4, lw=1.6)
    for x, y in zip(dists, en_m):
        axes[0].annotate(f"{y:.1f}", (x, y), textcoords="offset points", xytext=(0, 9),
                         ha="center", fontsize=9, color=C_RADAR)
    axes[0].set_xlabel("distanza reale [m]"); axes[0].set_ylabel("energia media del bersaglio [0-100]")
    axes[0].set_title("Energia del canale moving")
    axes[0].set_ylim(0, 115); axes[0].set_xticks(dists)

    axes[1].bar([d - 0.0 for d in dists], pir_m, 0.55, yerr=pir_d, capsize=4,
                color=C_PIR, edgecolor="white")
    for x, y in zip(dists, pir_m):
        axes[1].annotate(f"{y:.1f} %", (x, y), textcoords="offset points", xytext=(0, 5),
                         ha="center", fontsize=9, color=C_PIR)
    axes[1].axhline(100, color=C_RADAR, lw=1.6, ls="-")
    axes[1].text(3, 103, "mmWave: 100 % a tutte le distanze", ha="center",
                 fontsize=9, color=C_RADAR)
    axes[1].set_xlabel("distanza reale [m]"); axes[1].set_ylabel("tempo rilevato dal PIR [%]")
    axes[1].set_title("Portata utile del PIR (movimento sul posto)")
    axes[1].set_ylim(0, 118); axes[1].set_xticks(dists)
    fig.suptitle("Comportamento in distanza dei due sensori (serie 1-5 m, 25 trial)", y=1.03)
    salva(fig, "fig05_energia_e_portata")


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

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 4.0))
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
    axes[0].set_xticks([0, 1]); axes[0].set_xticklabels(["mmWave", "PIR"])
    axes[0].set_xlim(-0.35, 1.35)
    axes[0].set_ylabel("latenza di rilevamento [s]")
    axes[0].set_title(f"Ingresso — {len(lat_r)} trial appaiati\n"
                      f"{mr:.2f} ± {dr:.2f} s  vs  {mp:.2f} ± {dp:.2f} s")
    axes[0].text(0.5, min(lat_r + lat_p) - 0.35,
                 f"differenza appaiata radar−PIR: {md:+.2f} ± {dd:.2f} s\n"
                 f"il radar rileva per primo in {sum(1 for x in delta if x < 0)}/{len(delta)} trial",
                 ha="center", fontsize=9)
    axes[0].set_ylim(min(lat_r + lat_p) - 0.9, max(lat_r + lat_p) + 0.35)

    # (b) rilascio
    x = np.arange(2)
    mrr, drr = media_dev(ril_r); mpp, dpp = media_dev(ril_p)
    axes[1].bar(x, [mrr, mpp], 0.5, yerr=[drr, dpp], capsize=5,
                color=[C_RADAR, C_PIR], edgecolor="white")
    for xi, v, d in zip(x, [mrr, mpp], [drr, dpp]):
        axes[1].text(xi, v + d + 0.5, f"{v:.2f} ± {d:.2f} s", ha="center", fontsize=9,
                     fontweight="bold")
    axes[1].axhline(5, color=C_GRIGIO, ls="--", lw=1)
    axes[1].annotate("timeout configurato nel radar: 5 s", xy=(0.5, 5), xytext=(0.5, 8.5),
                     ha="center", fontsize=8.5, color=C_GRIGIO,
                     arrowprops=dict(arrowstyle="->", color=C_GRIGIO, lw=0.8))
    axes[1].set_xticks(x); axes[1].set_xticklabels(["mmWave", "PIR"])
    axes[1].set_ylabel("tempo per dichiarare la stanza vuota [s]")
    axes[1].set_title(f"Uscita — {len(ril_r)} trial\nil radar tiene la presenza più a lungo")
    axes[1].set_ylim(0, max(mrr + drr, mpp + dpp) * 1.35)
    salva(fig, "fig06_latenze")
    return mr, dr, mp, dp, md, dd, mrr, drr, mpp, dpp


def fig_impulsi_pir():
    """L'uscita del PIR e' un monostabile: in L durata fissa, in H il ritrigger la allunga."""
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
    axes[0].set_title(f"Modalita' L (non ripetibile)\n"
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
    axes[1].set_ylabel(f"i {len(dati)} impulsi, ordinati")
    axes[1].axvline(m, color="black", ls="--", lw=1)
    axes[1].text(m * 1.15, len(dati) * 0.5, f"durata fissa in L\n({m:.2f} s)",
                 fontsize=8.5, rotation=90, va="center")
    axes[1].plot([], [], color=C_PIR, lw=6, label=f"{len(H_c)} impulsi completi")
    axes[1].plot([], [], color=C_GRIGIO, lw=6,
                 label=f"{len(H_t)} troncati dalla fine del trial\n(durata reale >= barra)")
    axes[1].legend(fontsize=8.5, loc="lower right")
    axes[1].set_title(f"Modalita' H (repeat trigger)\n"
                      f"{len(dati)} impulsi - il piu' lungo >= {max(v for v, _ in dati):.0f} s")
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
        for yv, et in ((200, "A (ferma, 2 m)"), (400, "B (cammina, 4 m)")):
            ax.text(t.max() * 0.99, yv + 12, et, fontsize=8, color=C_GRIGIO, ha="right",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
        ax.set_title(titolo); ax.set_xlabel("tempo [s]"); ax.set_ylim(0, 520)
    axes[0].set_ylabel("distanza riportata [cm]")
    axes[0].legend(loc="lower left", fontsize=9, markerscale=4)
    fig.suptitle("Il LD2410B riporta un bersaglio per canale — chi sta dietro è invisibile", y=1.03)
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
        r20 = stats_scenario(pat, skip=20.0)
        r120 = stats_scenario(pat, skip=120.0)
        m20, d20 = media_dev([r["radar_rate_%"] for r in r20])
        m120, d120 = media_dev([r["radar_rate_%"] for r in r120])
        ax.bar(x[i] - w/2, m20, w, yerr=d20, capsize=4, color="#9fc5dd", edgecolor="white",
               label="finestra standard (scarto 20 s)" if i == 0 else None)
        ax.bar(x[i] + w/2, m120, w, yerr=d120, capsize=4, color=C_RADAR, edgecolor="white",
               label="a regime (scarto 120 s)" if i == 0 else None)
        ax.text(x[i] + w/2, m120 + d120 + 3, f"{m120:.1f}", ha="center", fontsize=9,
                color=C_RADAR, fontweight="bold")
        ax.text(x[i] - w/2, m20 + d20 + 3, f"{m20:.1f}", ha="center", fontsize=9,
                color=C_GRIGIO)
    ax.set_xticks(x); ax.set_xticklabels([s[0] for s in sc])
    ax.set_ylabel("tempo con presenza rilevata [%]"); ax.set_ylim(0, 118)
    ax.set_title("Selettività spaziale con gate massimo 2 (portata tagliata a 150 cm)\n"
                 "tutti i soggetti fermi · 3 trial per scenario")
    ax.legend(loc="center right", fontsize=9)
    salva(fig, "fig09_selettivita")


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

    fig, axes = plt.subplots(3, 1, figsize=(8.2, 5.6), sharex=True,
                             gridspec_kw={"height_ratios": [1.3, 1.3, 0.6]})
    ext = [t[0], t[-1], -0.5, 8.5]
    for ax, Z, nome in ((axes[0], M, "moving"), (axes[1], S, "stazionario")):
        im = ax.imshow(Z, aspect="auto", origin="lower", extent=ext,
                       cmap="magma", vmin=0, vmax=100, interpolation="nearest")
        ax.set_ylabel(f"gate\n({nome})")
        ax.set_yticks(range(0, 9, 2))
        ax.grid(False)
        fig.colorbar(im, ax=ax, pad=0.012, label="energia [0-100]")
    dist = np.where(d["moving_target"] == 1, d["moving_distance_cm"] / 75.0, np.nan)
    axes[0].plot(t, dist, color="#7fd4ff", lw=1.0, label="gate atteso = distanza / 0,75 m")
    axes[0].legend(loc="upper right", fontsize=8.5, labelcolor="white",
                   facecolor="black", framealpha=0.35, frameon=True)

    axes[2].fill_between(t, 0.05, 0.05 + d["radar_presence"] * 0.9, step="post",
                         color=C_RADAR, alpha=0.85, lw=0)
    axes[2].fill_between(t, -0.05, -0.05 - d["pir_presence"] * 0.9, step="post",
                         color=C_PIR, alpha=0.85, lw=0)
    axes[2].axhline(0, color="black", lw=0.6)
    axes[2].set_ylim(-1.15, 1.15)
    axes[2].set_yticks([-0.5, 0.5])
    axes[2].set_yticklabels(["PIR", "mmWave"])
    axes[2].set_xlabel("tempo [s]")
    axes[2].grid(False)
    axes[2].text(0.09, 0.78, f"presenza {100*d['radar_presence'].mean():.1f} % del tempo",
                 transform=axes[2].transAxes, ha="left", fontsize=8.5, color=C_RADAR)
    axes[2].text(0.09, 0.10, f"presenza {100*d['pir_presence'].mean():.1f} % del tempo",
                 transform=axes[2].transAxes, ha="left", fontsize=8.5, color=C_PIR)
    axes[0].set_title("Dati prodotti dai due sensori nello stesso istante\n"
                      "mmWave: 18 canali di energia per-gate a 5 Hz  vs  PIR: 1 bit")
    salva(fig, "fig10_gate_engineering")


def fig_saturazione():
    """Il limite del dato: l'energia e' un uint8 0-100 che satura sul bersaglio vicino."""
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
    fig.suptitle("Limite del dato di energia: soggetto fermo a 1 m (trial fermo_1m_H_T01)", y=1.05)
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
    axes[0].set_title("Serie temporale dell'energia per-gate (primi 120 s)")

    banda = (fr >= 0.0) & (fr <= 1.2)
    axes[1].plot(fr[banda], X[banda], lw=1.1, color=C_RADAR)
    axes[1].axvspan(0.10, 0.50, color=C_PIR, alpha=0.10)
    axes[1].axvline(picco_f, color=C_PIR, lw=1.3, ls="--")
    axes[1].annotate(f"{picco_f:.3f} Hz = {picco_f*60:.1f} atti/min\nSNR ~ {snr:.1f}x",
                     (picco_f, X[banda].max()), textcoords="offset points", xytext=(12, -12),
                     fontsize=9, color=C_PIR)
    axes[1].set_xlabel("frequenza [Hz]")
    axes[1].set_ylabel("ampiezza FFT")
    axes[1].set_title("Spettro - banda respiratoria 0,1-0,5 Hz evidenziata")
    fig.suptitle("Micro-movimento respiratorio su soggetto immobile a 2,3 m "
                 "(trial fermo_seduto_T01)", y=1.05)
    salva(fig, "fig12_respiro")
    return canale, picco_f, snr


# =========================================================== OBIETTIVO 4
def fig_consumi():
    """Consumi da datasheet e autonomia stimata (nessuna misura: valori dichiarati)."""
    comp = [("PIR HC-SR501", 0.05, "#f0a202"),
            ("HLK-LD2420", 50.0, "#4c9f70"),
            ("HLK-LD2410B", 80.0, C_RADAR),
            ("ESP32 (WiFi attivo)", 100.0, C_GRIGIO)]
    nodi = [("deep-sleep + PIR\n(guardiano)", 0.06),
            ("PIR sempre attivo\n(modem-sleep)", 25.0),
            ("mmWave, senza\nWiFi continuo", 130.0),
            ("mmWave + WiFi\nsempre attivo", 200.0)]
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.9))
    fig.subplots_adjust(wspace=0.55)

    y = np.arange(len(comp))
    axes[0].barh(y, [c[1] for c in comp], color=[c[2] for c in comp], edgecolor="white")
    axes[0].set_yticks(y)
    axes[0].set_yticklabels([c[0] for c in comp])
    axes[0].set_xscale("log")
    axes[0].set_xlabel("corrente media dichiarata [mA, scala log]")
    for yi, c in zip(y, comp):
        axes[0].text(c[1] * 1.25, yi, f"{c[1]:g} mA", va="center", fontsize=9)
    axes[0].set_xlim(0.02, 400)
    axes[0].set_title("Singoli componenti\n(valori da datasheet, non misurati)")

    aut_h = [3000 * 0.85 / n[1] for n in nodi]
    y2 = np.arange(len(nodi))
    axes[1].barh(y2, aut_h, color=[C_PIR, "#f0a202", "#4c9f70", C_RADAR], edgecolor="white")
    axes[1].set_yticks(y2)
    axes[1].set_yticklabels([n[0] for n in nodi], fontsize=9)
    axes[1].set_xscale("log")
    axes[1].set_xlabel("autonomia stimata [ore, scala log]")
    for yi, h in zip(y2, aut_h):
        if h > 8760:
            et = f"{h/8760:.1f} anni"
        elif h > 48:
            et = f"{h/24:.0f} giorni"
        else:
            et = f"{h:.0f} h"
        axes[1].text(h * 1.3, yi, et, va="center", fontsize=9)
    axes[1].set_xlim(5, 1e6)
    axes[1].set_title("Nodo completo su batteria 18650 3000 mAh\n(efficienza regolatore 85 %)")
    fig.suptitle("Obiettivo 4 - consumo energetico: perche' serve l'architettura ibrida "
                 "PIR + mmWave", y=1.05)
    salva(fig, "fig13_consumi")


def main():
    print(f"Figure -> {OUT}")
    dose = fig_doserisposta()
    fig_timeline_uprise()
    fig_uprise_barre()
    a, b, r2, _ = fig_distanza()
    fig_energia_distanza()
    lat = fig_latenza()
    imp = fig_impulsi_pir()
    fig_due_persone()
    fig_selettivita()
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
