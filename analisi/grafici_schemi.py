# -*- coding: utf-8 -*-
"""
Schemi di principio per il capitolo 2 (non derivano dai CSV).

  fig23_zone_fresnel   §2.1.2  le zone di rilevamento create dalla lente di Fresnel
                                del PIR, alternate fra i due elementi piroelettrici,
                                con il movimento trasversale che le attraversa e quello
                                radiale che resta in una zona sola.
  fig24_trigger_lh     §2.1.3  uscita del PIR in modalita' L (single) e H (repeat)
                                a parita' di movimenti, con ritenuta e block time
                                (sul modello dello schema di Wolles Elektronikkiste).
  fig25_fmcw           §2.2.1  principio FMCW: chirp trasmesso e ricevuto, ritardo,
                                frequenza di battimento.
  fig26_pir_due_elementi §2.1.1 due elementi piroelettrici in serie opposta: zone A/B,
                                segnale bipolare al passaggio, nullo da fermo.
  fig30_percorsi_dati  §4.5    i due percorsi dei dati del firmware ld2410b_web: seriale ->
                                acquire.py -> CSV e Access Point -> browser -> CSV, che
                                arrivano allo stesso file letto da analizza_test.py
                                (architettura A e verifica di equivalenza, §4.5.1 e §4.5.3).

Geometria delle zone ispirata alla vista dall'alto del datasheet Panasonic PaPIRs
(serie WL/VZ standard: ventaglio a ±47°, fasci alternati per polarita') e, per
l'impostazione grafica, al tutorial video "Lesson 12: Interfacing HC-SR501 PIR
Motion Sensor with Arduino". Stesso stile di grafici_tesi.py; uscita in
overleaf/figures/ (.png a 300 dpi) e overleaf/figures/origin/ (.pdf vettoriale).

Uso:  python analisi/grafici_schemi.py
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle, Wedge, FancyArrowPatch, Ellipse, FancyBboxPatch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from uscita_figure import salva  # noqa: E402

plt.rcParams.update({
    "font.size": 10,
    "axes.titlesize": 11,
    "figure.dpi": 110,
})

C_A = "#f2c14e"      # zone viste dall'elemento A
C_B = "#7fc4e6"      # zone viste dall'elemento B
C_BOARD = "#1f3b73"
C_TRIM = "#e07b39"
C_GRIGIO = "#6c757d"
C_TRASV = "#1b6ca8"
C_RAD = "#d1495b"


def fig23_zone_fresnel():
    fig, ax = plt.subplots(figsize=(7.0, 5.6))
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- il modulo, visto di fronte, con la cupola della lente in basso
    bx, by, bw, bh = -1.05, 4.55, 2.1, 0.55
    ax.add_patch(Rectangle((bx, by), bw, bh, color=C_BOARD, zorder=3))
    # due trimmer, il jumper e un condensatore, per far riconoscere l'HC-SR501
    for cx in (-0.62, 0.62):
        ax.add_patch(Rectangle((cx - 0.17, by + bh), 0.34, 0.34, color="#9aa3ad", zorder=3))
        ax.add_patch(Circle((cx, by + bh + 0.17), 0.12, color=C_TRIM, zorder=4))
        ax.plot([cx - 0.07, cx + 0.07], [by + bh + 0.17] * 2, color="#7a3e12", lw=1.2, zorder=5)
        ax.plot([cx] * 2, [by + bh + 0.10, by + bh + 0.24], color="#7a3e12", lw=1.2, zorder=5)
    ax.add_patch(Rectangle((-0.16, by + bh), 0.32, 0.42, color="#222", zorder=3))
    ax.add_patch(Rectangle((-0.98, by + bh), 0.16, 0.30, color=C_TRIM, zorder=3))
    ax.add_patch(Rectangle((0.84, by + bh), 0.14, 0.14, color="#f1c40f", zorder=3))
    # cupola della lente di Fresnel: semicerchio con gli anelli concentrici
    apex = (0.0, by)
    r_lens = 0.62
    ax.add_patch(Wedge(apex, r_lens, 180, 360, color="#f6f6f2", ec="#b5b5ad", lw=1.0, zorder=4))
    for r in (0.20, 0.34, 0.48):
        ax.add_patch(Wedge(apex, r, 180, 360, fill=False, ec="#c9c9c0", lw=0.7, zorder=5))
    ax.text(0.78, by - 0.28, "lente di Fresnel", fontsize=9, color=C_GRIGIO, va="center")
    ax.text(0.0, by + bh + 1.12, "modulo PIR (HC-SR501)", fontsize=9, color=C_GRIGIO,
            ha="center")

    # ---- il ventaglio di zone: il fuoco e' il centro della cupola, i fasci scendono
    focus = (0.0, by - 0.02)
    half = 47.0                       # ±47° come la vista dall'alto Panasonic (WL standard)
    n = 16                            # 16 zone, 8 per elemento, alternate
    pitch = 2 * half / n              # passo angolare
    fill = 0.62                       # frazione del passo occupata dal fascio: il resto e' cieco
    L = 4.6                           # lunghezza dei fasci
    for i in range(n):
        a0 = -half + i * pitch
        ac = a0 + pitch / 2
        w = pitch * fill / 2
        th = np.radians(np.array([ac - w, ac + w]))
        col = C_A if i % 2 == 0 else C_B
        # i fasci partono stretti (dal fuoco) e si allargano: triangolo
        tip = [(focus[0] + L * np.sin(t), focus[1] - L * np.cos(t)) for t in th]
        poly = Polygon([focus, tip[0], tip[1]], closed=True, color=col, alpha=0.95,
                       ec="white", lw=0.4, zorder=2)
        ax.add_patch(poly)

    # ---- le due frecce: trasversale (attraversa le zone) e radiale (resta in una zona)
    y_arr = focus[1] - L - 0.35
    ax.add_patch(FancyArrowPatch((-3.3, y_arr), (3.3, y_arr), arrowstyle="<|-|>",
                                 mutation_scale=16, lw=2.2, color=C_TRASV, zorder=6))
    ax.text(0.0, y_arr - 0.30, "movimento trasversale: attraversa le zone, molte transizioni",
            ha="center", va="top", fontsize=9, color=C_TRASV)

    a_rad = np.radians(27.5)          # dentro una zona gialla, a destra dell'asse
    p1 = (focus[0] + 4.3 * np.sin(a_rad), focus[1] - 4.3 * np.cos(a_rad))
    p2 = (focus[0] + 1.6 * np.sin(a_rad), focus[1] - 1.6 * np.cos(a_rad))
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=16, lw=2.2,
                                 color=C_RAD, zorder=6))
    ax.annotate("movimento radiale:\nresta nella stessa zona",
                xy=((p1[0] + p2[0]) / 2 + 0.05, (p1[1] + p2[1]) / 2), xytext=(1.75, 3.55),
                fontsize=9, color=C_RAD, ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=C_RAD, lw=0.8))

    # ---- legenda
    hx, hy = -4.35, 5.15
    ax.add_patch(Rectangle((hx, hy), 0.32, 0.22, color=C_A))
    ax.text(hx + 0.42, hy + 0.11, "zone dell'elemento A", va="center", fontsize=9)
    ax.add_patch(Rectangle((hx, hy - 0.36), 0.32, 0.22, color=C_B))
    ax.text(hx + 0.42, hy - 0.25, "zone dell'elemento B", va="center", fontsize=9)
    ax.text(hx, hy - 0.66, "fra i fasci: spazio cieco", va="center", fontsize=9,
            color=C_GRIGIO)

    ax.set_xlim(-4.4, 3.7)
    ax.set_ylim(y_arr - 0.75, by + bh + 1.35)
    salva(fig, "fig23_zone_fresnel")


def fig24_trigger_lh():
    """Due righe temporali: stessi quattro movimenti, uscita in L e in H."""
    fig, axes = plt.subplots(2, 1, figsize=(7.6, 3.6), sharex=True)
    T = 1.0          # tempo di ritenuta (unita' arbitrarie)
    B = 0.35         # block time
    moti = [0.6, 3.2, 3.9, 4.6]      # istanti dei movimenti
    C_HI = "#1b6ca8"; C_BLK = "#b8bec4"; C_MOT = "#d1495b"

    def disegna(ax, impulsi, titolo):
        ax.set_ylim(-0.25, 1.9); ax.set_xlim(0, 8.4)
        ax.axis("off")
        ax.plot([0, 6.3], [0, 0], color="#333", lw=1.2, zorder=1)
        for (t0, t1) in impulsi:
            ax.add_patch(Rectangle((t0, 0), t1 - t0, 1.0, color=C_HI, zorder=2))
            ax.add_patch(Rectangle((t1, 0), B, 1.0, color=C_BLK, zorder=2))
            ax.plot([t0, t0, t1, t1], [0, 1, 1, 0], color="#333", lw=1.2, zorder=3)
        for i, m in enumerate(moti):
            ax.annotate("", xy=(m, 1.02), xytext=(m, 1.62),
                        arrowprops=dict(arrowstyle="-|>", color=C_MOT, lw=1.4))
            ax.text(m, 1.72, str(i + 1), ha="center", va="bottom", fontsize=9, color=C_MOT)
        ax.text(6.55, 0.5, titolo, ha="left", va="center", fontsize=10, fontweight="bold")

    # L: il movimento 1 apre un impulso di durata T; 2 riapre; 3 e 4 cadono nella
    # ritenuta o nel block time e non prolungano nulla; dopo il block time di 2
    # il movimento 4 (a 4.6) riapre un terzo impulso.
    l_imp = [(0.6, 0.6 + T), (3.2, 3.2 + T), (4.6, 4.6 + T)]
    # H: ogni movimento durante la ritenuta la fa ripartire: 2, 3, 4 concatenati
    h_imp = [(0.6, 0.6 + T), (3.2, 4.6 + T)]
    disegna(axes[0], l_imp, "modalità L\n(single trigger)")
    disegna(axes[1], h_imp, "modalità H\n(repeat trigger)")
    # quote della ritenuta
    for ax, (a, b) in ((axes[0], (0.6, 0.6 + T)), (axes[1], (4.6, 4.6 + T))):
        ax.annotate("", xy=(a, -0.12), xytext=(b, -0.12),
                    arrowprops=dict(arrowstyle="<->", color="#333", lw=0.8))
        ax.text((a + b) / 2, -0.2, "ritenuta", ha="center", va="top", fontsize=8)
    # legenda in basso
    lx = 0.0; ly = -1.05
    ax = axes[1]
    ax.annotate("", xy=(lx + 0.1, ly + 0.05), xytext=(lx + 0.1, ly + 0.5),
                arrowprops=dict(arrowstyle="-|>", color=C_MOT, lw=1.4), annotation_clip=False)
    ax.text(lx + 0.25, ly + 0.25, "movimento rilevato dal cristallo", va="center",
            fontsize=8.5, clip_on=False)
    ax.add_patch(Rectangle((lx + 3.0, ly + 0.05), 0.35, 0.4, color=C_HI, clip_on=False))
    ax.text(lx + 3.45, ly + 0.25, "uscita alta", va="center", fontsize=8.5, clip_on=False)
    ax.add_patch(Rectangle((lx + 4.6, ly + 0.05), 0.35, 0.4, color=C_BLK, clip_on=False))
    ax.text(lx + 5.05, ly + 0.25, "block time (cieco)", va="center", fontsize=8.5,
            clip_on=False)
    fig.subplots_adjust(hspace=0.05, bottom=0.24)
    salva(fig, "fig24_trigger_lh")


def fig25_fmcw():
    """Chirp TX e RX in frequenza-tempo: ritardo e frequenza di battimento."""
    fig, a1 = plt.subplots(figsize=(6.8, 3.4))
    C_TX = "#1b6ca8"; C_RX = "#d1495b"
    Tc = 1.0; f0, B = 0.0, 1.0; S = B / Tc
    tau = 0.18
    t = np.linspace(0, Tc, 200)
    a1.plot(t, f0 + S * t, color=C_TX, lw=2.2, label="segnale trasmesso (chirp)")
    a1.plot(t + tau, f0 + S * t, color=C_RX, lw=2.2, ls="--", label="eco ricevuta")
    a1.annotate("", xy=(tau, 0.0), xytext=(0.0, 0.0),
                arrowprops=dict(arrowstyle="<->", color="#333", lw=0.9))
    a1.text(tau + 0.03, -0.03, r"ritardo $\tau = 2d/c$", ha="left", va="top", fontsize=9)
    tm = 0.6
    a1.plot([tm, tm], [S * (tm - tau), S * tm], color="#333", lw=1.0)
    a1.plot([tm - 0.02, tm + 0.02], [S * tm] * 2, color="#333", lw=1.0)
    a1.plot([tm - 0.02, tm + 0.02], [S * (tm - tau)] * 2, color="#333", lw=1.0)
    a1.text(tm + 0.04, S * (tm - tau) - 0.06,
            r"battimento $f_b = S\,\tau$" + "\n(costante, proporzionale a $d$)",
            va="top", ha="left", fontsize=9)
    a1.set_xlim(-0.02, Tc + tau + 0.05); a1.set_ylim(-0.18, B + 0.12)
    a1.set_xlabel("tempo"); a1.set_ylabel("frequenza")
    a1.set_xticks([0, Tc]); a1.set_xticklabels(["0", r"$T_c$"])
    a1.set_yticks([0, B]); a1.set_yticklabels([r"$f_0$", r"$f_0 + B$"])
    a1.grid(False)
    a1.legend(loc="upper left", fontsize=9)
    salva(fig, "fig25_fmcw")



def _omino(ax, x, y, h=0.9, color="#d1495b"):
    """Figura umana stilizzata (testa + corpo) centrata in x, con i piedi in y."""
    ax.add_patch(Circle((x, y + h * 0.88), h * 0.12, color=color, zorder=6))
    ax.add_patch(Rectangle((x - h * 0.13, y + h * 0.30), h * 0.26, h * 0.45,
                           color=color, zorder=6))
    ax.plot([x - h * 0.08, x - h * 0.16], [y + h * 0.30, y], color=color, lw=3, zorder=6,
            solid_capstyle="round")
    ax.plot([x + h * 0.08, x + h * 0.16], [y + h * 0.30, y], color=color, lw=3, zorder=6,
            solid_capstyle="round")


def fig26_pir_due_elementi():
    """Due elementi in serie opposta: la persona che attraversa le due zone da' un
    segnale bipolare, la persona ferma non da' nulla."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.6, 3.4),
                                 gridspec_kw={"width_ratios": [1.35, 1.0], "wspace": 0.25})
    for ax in (a1, a2):
        ax.axis("off")

    # --- pannello 1: sensore a destra, due zone che si aprono verso sinistra
    a1.set_xlim(-0.2, 6.4); a1.set_ylim(-0.6, 3.2); a1.set_aspect("equal")
    sx, sy = 5.6, 1.3                     # posizione del sensore
    # zone: due triangoli con vertice sul sensore
    for dy, col, lab in ((+0.28, C_A, "A"), (-0.28, C_B, "B")):
        y_far = sy + dy * 2.3
        a1.add_patch(Polygon([(sx - 0.55, sy + dy * 0.35), (0.3, y_far + 0.36), (0.3, y_far - 0.36)],
                             closed=True, color=col, alpha=0.9, ec="white", lw=0.5, zorder=2))
        a1.text(0.5, y_far, f"zona {lab}", ha="left", va="center", fontsize=9,
                color="#333", zorder=7)
    # lente (arco) e corpo del sensore con i due elementi
    a1.add_patch(Wedge((sx + 0.05, sy), 0.62, 90, 270, color="#f6f6f2", ec="#b5b5ad", lw=1.0, zorder=3))
    a1.add_patch(Rectangle((sx - 0.05, sy - 0.45), 0.6, 0.9, color="#9aa3ad", zorder=4))
    a1.add_patch(Rectangle((sx + 0.05, sy + 0.05), 0.4, 0.3, color=C_A, zorder=5))
    a1.add_patch(Rectangle((sx + 0.05, sy - 0.35), 0.4, 0.3, color=C_B, zorder=5))
    a1.text(sx + 0.25, sy + 0.2, "A", ha="center", va="center", fontsize=8, zorder=6)
    a1.text(sx + 0.25, sy - 0.2, "B", ha="center", va="center", fontsize=8, zorder=6)
    a1.text(sx + 0.25, sy + 0.72, "elementi\npiroelettrici", ha="center", va="bottom",
            fontsize=8, color=C_GRIGIO)
    a1.text(sx - 0.55, sy - 0.85, "lente di Fresnel", ha="center", va="top", fontsize=8,
            color=C_GRIGIO)
    # persona che attraversa le due zone, dall'alto verso il basso
    px = 2.1
    _omino(a1, px, sy + 0.35)
    a1.add_patch(FancyArrowPatch((px + 0.55, sy + 1.05), (px + 0.55, sy - 0.95),
                                 arrowstyle="-|>", mutation_scale=14, lw=1.8,
                                 color="#333", zorder=7))
    a1.text(px + 0.75, sy + 1.15, "persona in" + chr(10) + "movimento", fontsize=8.5,
            va="bottom", ha="left")
    a1.set_title("Le due zone di rilevamento", fontsize=10)

    # --- pannello 2: segnale differenziale nel tempo
    a2.set_xlim(-0.3, 10.8); a2.set_ylim(-3.5, 3.6)
    t = np.linspace(0, 10, 600)
    def imp(c, w):
        return np.exp(-0.5 * ((t - c) / w) ** 2)
    # in movimento: entra in A (positivo), passa in B (negativo)
    s_mov = 1.0 * imp(3.0, 0.55) - 1.0 * imp(4.6, 0.55)
    a2.plot([0, 10], [1.0, 1.0], color="#999", lw=0.8)
    a2.plot(t, 1.0 + 1.2 * s_mov, color="#333", lw=1.8)
    a2.text(0, 3.05, "persona che attraversa le zone", fontsize=9, va="center")
    a2.annotate("entra in A", xy=(2.75, 1.9), xytext=(0.4, 2.35), fontsize=8, color=C_GRIGIO,
                arrowprops=dict(arrowstyle="-", color=C_GRIGIO, lw=0.6))
    a2.annotate("passa in B", xy=(4.85, 0.1), xytext=(6.0, -0.15), fontsize=8, color=C_GRIGIO,
                arrowprops=dict(arrowstyle="-", color=C_GRIGIO, lw=0.6))
    # ferma: entrambe le zone vedono lo stesso flusso, differenza nulla
    a2.plot([0, 10], [-2.2, -2.2], color="#999", lw=0.8)
    a2.plot(t, -2.2 + 0.04 * np.sin(3 * t), color="#333", lw=1.8)
    a2.text(0, -1.1, "persona ferma in una zona", fontsize=9, va="center")
    a2.text(10.3, -2.2, "0", ha="left", va="center", fontsize=8, color=C_GRIGIO)
    a2.text(10.3, 1.0, "0", ha="left", va="center", fontsize=8, color=C_GRIGIO)
    a2.annotate("", xy=(10.2, -3.2), xytext=(-0.2, -3.2),
                arrowprops=dict(arrowstyle="-|>", color="#333", lw=0.8))
    a2.text(10.2, -3.3, "tempo", ha="right", va="top", fontsize=8)
    a2.set_title("Segnale differenziale A − B", fontsize=10, pad=10)
    salva(fig, "fig26_pir_due_elementi")


def fig27_geometrie():
    """Le quattro geometrie di prova del capitolo 4: stanza, sotto il banco, arco, corridoio.

    Schema qualitativo in scala: misure dal registro delle sessioni (tavolo a ~85 cm di
    altezza, tacche 1-5 m, persona a 50-60 cm sotto il piano, arco di raggio 1 m,
    corridoio 120 cm con vani a 4 m (70 cm) e 5 m (80 cm), sensori a 80 cm).
    """
    fig, axd = plt.subplot_mosaic([["a", "b", "c"], ["d", "d", "d"]],
                                  figsize=(12.0, 7.2),
                                  gridspec_kw={"height_ratios": [1.45, 1.0]})

    def sensore(ax, x, y, s=0.18):
        ax.add_patch(Rectangle((x - s / 2, y - s / 2), s, s, color=C_BOARD, zorder=7))

    # (a) stanza, vista in pianta
    ax = axd["a"]
    ax.add_patch(Wedge((0, 0), 6.0, -60, 60, color=C_TRASV, alpha=0.10, zorder=1))
    ax.add_patch(Wedge((0, 0), 5.35, -55, 55, fill=False, ls="--", ec=C_RAD, lw=1.0, zorder=2))
    for d in range(1, 6):
        ax.plot([d, d], [-0.3, 0.3], color=C_GRIGIO, lw=1.2, zorder=5)
        ax.text(d, -0.55, f"{d} m", ha="center", va="top", fontsize=9, color=C_GRIGIO)
        ax.add_patch(Circle((d, 0), 0.14, color=C_RAD, zorder=6))
    sensore(ax, 0, 0)
    ax.text(0, 0.45, "radar + PIR\nsul tavolo, h 85 cm", ha="center", va="bottom", fontsize=8.5)
    ax.plot([5.45, 5.45], [-2.9, 2.9], color="k", lw=2.5)
    ax.text(5.58, 1.6, "parete", ha="left", va="center", rotation=90, fontsize=8.5)
    ax.text(1.85, 2.2, "campo radar ±60°", color=C_TRASV, fontsize=8.5)
    ax.text(1.85, -2.3, "campo PIR < 110°", color=C_RAD, fontsize=8.5, va="top")
    ax.set_xlim(-0.7, 5.8); ax.set_ylim(-3.1, 3.1); ax.set_aspect("equal"); ax.set_axis_off()
    ax.set_title("(a) Stanza: tacche a 1-5 m", fontsize=10)

    # (b) sotto il banco, vista laterale
    ax = axd["b"]
    ax.plot([-0.3, 1.5], [0, 0], color="k", lw=1.5)                       # pavimento
    ax.add_patch(Rectangle((-0.1, 0.72), 1.3, 0.05, color="#8d6e63", zorder=3))
    for xl in (0.0, 1.13):
        ax.add_patch(Rectangle((xl, 0), 0.05, 0.72, color="#8d6e63", zorder=3))
    sensore(ax, 0.16, 0.66, s=0.08)
    ax.add_patch(Wedge((0.16, 0.66), 0.95, -62, 12, color=C_TRASV, alpha=0.12, zorder=1))
    ax.add_patch(Ellipse((0.72, 0.27), 0.36, 0.50, color=C_RAD, zorder=6))     # corpo rannicchiato
    ax.add_patch(Circle((0.78, 0.55), 0.09, color=C_RAD, zorder=6))            # testa
    ax.annotate("", xy=(0.56, 0.40), xytext=(0.20, 0.62),
                arrowprops=dict(arrowstyle="<->", color=C_GRIGIO, lw=1.2), zorder=8)
    ax.text(0.19, 0.53, "50-60 cm", fontsize=9, color=C_GRIGIO, rotation=-32, ha="left", va="top",
            rotation_mode="anchor")
    ax.text(0.16, 0.80, "sensori fissati\nsotto il piano", ha="center", va="bottom", fontsize=8.5)
    ax.set_xlim(-0.3, 1.5); ax.set_ylim(-0.1, 1.15); ax.set_aspect("equal"); ax.set_axis_off()
    ax.set_title("(b) Sotto il banco (vista laterale)", fontsize=10)

    # (c) arco a 1 m per la copertura angolare
    ax = axd["c"]
    ax.add_patch(Wedge((0, 0), 1.5, -60, 60, color=C_TRASV, alpha=0.10, zorder=1))
    th = np.radians(np.linspace(-55, 135, 300))
    ax.plot(np.cos(th), np.sin(th), color=C_GRIGIO, lw=1.0, ls="--", zorder=2)
    for a in (0, 45, 60, 75, 90, 120):
        x, y = np.cos(np.radians(a)), np.sin(np.radians(a))
        ax.plot([0, x], [0, y], color=C_GRIGIO, lw=0.6, zorder=2)
        ax.add_patch(Circle((x, y), 0.075, color=C_RAD, zorder=6))
        ax.text(1.2 * x, 1.2 * y, f"{a}°", ha="center", va="center", fontsize=9)
    sensore(ax, 0, 0, s=0.13)
    ax.text(0.0, -0.22, "sensori", ha="center", va="top", fontsize=8.5)
    ax.text(-1.4, -0.78, "raggio 1 m, soggetto seduto\nrivolto verso i sensori",
            ha="left", fontsize=8.5, color=C_GRIGIO)
    ax.set_xlim(-1.45, 1.6); ax.set_ylim(-0.85, 1.4); ax.set_aspect("equal"); ax.set_axis_off()
    ax.set_title("(c) Arco a 1 m, sei azimut", fontsize=10)

    # (d) corridoio, vista in pianta
    ax = axd["d"]
    W = 1.2
    for y in (-W / 2, W / 2):
        ax.plot([0, 9], [y, y], color="k", lw=2.2, zorder=3)
    for xd, larg in ((4.0, 0.70), (5.0, 0.80)):
        for y0, y1 in ((-W / 2, -larg / 2), (larg / 2, W / 2)):
            ax.plot([xd, xd], [y0, y1], color="k", lw=5, zorder=4, solid_capstyle="butt")
        ax.text(xd, W / 2 + 0.10, f"vano porta\n{int(round(larg * 100))} cm", ha="center",
                va="bottom", fontsize=8.5)
    ax.plot([9, 9], [-W / 2, W / 2], color="k", lw=3.5, zorder=3)
    ax.text(9.05, 0, "muro di fondo\nfinestra, termosifone", ha="left", va="center", fontsize=8)
    ax.add_patch(Wedge((0.12, 0), 6.0, -60, 60, color=C_TRASV, alpha=0.10, zorder=1))
    sensore(ax, 0.12, 0, s=0.16)
    ax.text(0.12, W / 2 + 0.10, "sensori, h 80 cm", ha="center", va="bottom", fontsize=8.5)
    for d in (5, 6, 7, 8):
        ax.add_patch(Circle((d, 0), 0.12, color=C_RAD, zorder=6))
        ax.text(d, -W / 2 - 0.12, f"{d} m", ha="center", va="top", fontsize=9, color=C_GRIGIO)
    ax.text(0.5, -W / 2 - 0.12, "distanze dalla faccia del modulo\ncorridoio largo 120 cm",
            ha="left", va="top", fontsize=8.5, color=C_GRIGIO)
    ax.set_xlim(-0.4, 10.6); ax.set_ylim(-1.35, 1.35); ax.set_aspect("equal"); ax.set_axis_off()
    ax.set_title("(d) Corridoio della prova di portata: tacche a 5-8 m viste attraverso i due vani")

    fig.subplots_adjust(hspace=0.12, wspace=0.10)
    salva(fig, "fig27_geometrie")


# ----------------------------------------------------------------- fig30
def fig30_percorsi_dati():
    C_BOX = "#eef3f8"
    C_WEB = C_TRASV
    C_SER = C_BOARD
    C_EQ = C_TRIM
    fig, ax = plt.subplots(figsize=(10.5, 4.9))
    ax.set_xlim(-1, 101); ax.set_ylim(-1, 51); ax.axis("off")

    def box(x, y, w, h, titolo, righe, ec=C_BOARD, fc=C_BOX, tc=None):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4", fc=fc, ec=ec, lw=1.2, zorder=2))
        cy = y + h / 2 + (len(righe) * 2.9) / 2
        ax.text(x + w / 2, cy + 0.6, titolo, ha="center", va="center", fontsize=9,
                fontweight="bold", color=tc or ec)
        for i, r in enumerate(righe):
            ax.text(x + w / 2, cy - 2.9 * (i + 1), r, ha="center", va="center", fontsize=7.3, color="#222")

    def freccia(x0, y0, x1, y1, col):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=12,
                                     color=col, lw=1.4, zorder=3))

    def etichetta(x, y, sopra, sotto, col):
        ax.text(x, y + 1.3, sopra, ha="center", va="bottom", fontsize=6.9, color=col)
        ax.text(x, y - 1.3, sotto, ha="center", va="top", fontsize=6.9, color=col)

    Y_S, Y_W = 40, 10          # quota dei due percorsi
    # sensori e nodo
    box(0.5, 12, 13, 26, "Sensori", ["HLK-LD2410B", "UART 256 000 baud", "", "HC-SR501", "GPIO34"])
    box(19.5, 1, 15, 48, "ESP32", ["ld2410b_web", "", "lettura a 5 Hz", "engineering mode", "",
                                   "indice di vitalità", "calcolato a bordo"])
    freccia(14, 25, 19.5, 25, C_BOARD)

    # percorso seriale (sopra)
    box(47, Y_S - 7, 17, 14, "PC", ["acquire.py", "+ 6 colonne di metadati"], ec=C_SER)
    box(70, Y_S - 7, 14.5, 14, "CSV seriale", ["29 + 6 colonne"], ec=C_SER)
    freccia(35.4, Y_S, 46.6, Y_S, C_SER); etichetta(41, Y_S, "seriale USB", "righe CSV", C_SER)
    freccia(64.4, Y_S, 69.6, Y_S, C_SER)

    # percorso web (sotto)
    box(47, Y_W - 7, 17, 14, "Browser", ["dashboard, statistiche", "export CSV"], ec=C_WEB)
    box(70, Y_W - 7, 14.5, 14, "CSV web", ["29 + 6 colonne", "+ 2 dell'indice"], ec=C_WEB)
    freccia(35.4, Y_W, 46.6, Y_W, C_WEB); etichetta(41, Y_W, "Access Point", "WebSocket", C_WEB)
    freccia(64.4, Y_W, 69.6, Y_W, C_WEB)
    ax.text(55.5, Y_W - 9.2, "nessuna rete esterna", ha="center", va="top", fontsize=6.9,
            color=C_WEB, style="italic")

    # equivalenza fra i due file
    ax.add_patch(FancyBboxPatch((68.5, 19.5), 17.5, 11, boxstyle="round,pad=0.4", fc="#fff6e0",
                                ec=C_EQ, lw=1.2, zorder=2))
    ax.text(77.25, 27.6, "stesso dato", ha="center", va="center", fontsize=8.5, fontweight="bold", color=C_EQ)
    ax.text(77.25, 24.3, "1346 campioni comuni", ha="center", va="center", fontsize=7, color="#222")
    ax.text(77.25, 21.6, "colonne identiche", ha="center", va="center", fontsize=7, color="#222")
    for y0, y1 in ((32.6, 31.2), (17.4, 18.8)):
        ax.plot([77.25, 77.25], [y0, y1], color=C_EQ, lw=1.1, ls=":", zorder=1)

    # analisi comune
    box(90, 17, 10, 16, "Analisi", ["analizza_test", "stesse metriche"])
    freccia(84.9, Y_S - 3, 89.6, 29, C_SER)
    freccia(84.9, Y_W + 3, 89.6, 21, C_WEB)
    salva(fig, "fig30_percorsi_dati")


if __name__ == "__main__":
    print("Schemi di principio del capitolo 2 e geometrie del capitolo 4")
    fig23_zone_fresnel()
    fig24_trigger_lh()
    fig25_fmcw()
    fig26_pir_due_elementi()
    fig27_geometrie()
    fig30_percorsi_dati()
