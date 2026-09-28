# -*- coding: utf-8 -*-
"""
Schemi per il capitolo 3 (non derivano dai CSV).

  fig28_collegamenti   §3.4.2  collegamento dei tre sensori all'ESP32: alimentazioni,
                                le due UART hardware (Serial2 per il LD2410B, Serial1 sui
                                GPIO16/17 per il LD2420), uscita del PIR su GPIO34.
                                Riassume le Tabelle 3.2, 3.8 e 3.13.
  fig29_piattaforma    §3.4    la catena di acquisizione e analisi: sensori -> ESP32 ->
                                seriale USB -> acquire.py -> CSV -> script -> materiali,
                                con il formato dati unico al centro e il ramo della web UI.

Stesso stile di grafici_schemi.py; uscita in overleaf/figures/ (.png 300 dpi) e origin/ (.pdf).
Uso:  python analisi/grafici_schemi_cap3.py
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, FancyArrowPatch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from uscita_figure import salva  # noqa: E402

plt.rcParams.update({"font.size": 9, "figure.dpi": 110})

C_BOARD = "#1f3b73"
C_VCC = "#d1495b"
C_GND = "#333333"
C_TX = "#1b6ca8"
C_RX = "#2a9d8f"
C_OUT = "#e07b39"
C_GRIGIO = "#6c757d"
C_BOX = "#eef3f8"



# ----------------------------------------------------------------- fig28
def fig_collegamenti():
    fig, ax = plt.subplots(figsize=(9.2, 5.6))
    ax.set_xlim(0, 100); ax.set_ylim(-1, 61); ax.axis("off")

    # ESP32 al centro
    ex0, ex1, ey0, ey1 = 38, 62, 6, 56
    ax.add_patch(Rectangle((ex0, ey0), ex1 - ex0, ey1 - ey0, color=C_BOARD, zorder=2))
    ax.add_patch(Rectangle((ex0 + 3, ey1 - 12), 18, 9, color="#9aa7bd", zorder=3))
    ax.text(50, ey1 - 7.5, "ESP32", ha="center", va="center", fontsize=7.5, color="white",
            zorder=4)
    ax.text(50, 9.5, "USB", ha="center", va="center", fontsize=7.5, color="white", zorder=4)
    ax.add_patch(Rectangle((46, ey0 - 0.2), 8, 2.2, color="#b8c2d6", zorder=3))

    # pin usati sull'ESP32: (lato, y, etichetta)
    pins = {"VIN": ("R", 50), "GND_r": ("R", 45), "D26 (TX2)": ("R", 40), "D25 (RX2)": ("R", 35),
            "D17 (TX)": ("R", 22), "D16 (RX)": ("R", 17),
            "3V3": ("L", 50), "GND_l": ("L", 45), "D34": ("L", 30)}
    for name, (side, y) in pins.items():
        x = ex1 if side == "R" else ex0
        ax.add_patch(Rectangle((x - 1.2, y - 1), 2.4, 2, color="#c9a227", zorder=5))
        lab = name.replace("_r", "").replace("_l", "")
        ax.text(x + (2.2 if side == "R" else -2.2), y, lab, ha="left" if side == "R" else "right",
                va="center", fontsize=7.5, color="white", zorder=6,
                bbox=dict(boxstyle="round,pad=0.15", fc=C_BOARD, ec="none"))

    def modulo(x0, y0, w, h, titolo, sottotitolo, pinlist, lato_pin):
        ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle="round,pad=0.4", fc=C_BOX, ec=C_BOARD, lw=1.2, zorder=2))
        ax.text(x0 + w / 2, y0 + h - 2.2, titolo, ha="center", va="center", fontsize=9, fontweight="bold", color=C_BOARD)
        ax.text(x0 + w / 2, y0 + h - 5.2, sottotitolo, ha="center", va="center", fontsize=7.2, color=C_GRIGIO)
        ys = {}
        for i, (nome, col) in enumerate(pinlist):
            y = y0 + h - 9 - i * 4.0
            px = x0 if lato_pin == "L" else x0 + w
            ax.add_patch(Rectangle((px - 1, y - 0.9), 2, 1.8, color=col, zorder=5))
            ax.text(px + (1.8 if lato_pin == "L" else -1.8), y, nome, ha="left" if lato_pin == "L" else "right",
                    va="center", fontsize=7.5, color="#222")
            ys[nome] = (px, y)
        return ys

    # LD2410B in alto a destra
    p1 = modulo(76, 31.5, 22, 27.5, "HLK-LD2410B", "5 V · UART 256000 · Serial2",
                [("VCC", C_VCC), ("GND", C_GND), ("UART_Rx", C_RX), ("UART_Tx", C_TX), ("OUT", C_GRIGIO)], "L")
    # LD2420 in basso a destra
    p2 = modulo(76, 0.5, 22, 27.5, "HLK-LD2420", "3,3 V · UART 115200 · Serial1",
                [("3V3", C_VCC), ("GND", C_GND), ("RX", C_RX), ("OT1", C_TX), ("OT2", C_GRIGIO)], "L")
    # PIR a sinistra
    p3 = modulo(2, 18, 22, 24, "HC-SR501 (PIR)", "5 V · uscita 3,3 V · 1 bit",
                [("VCC", C_VCC), ("OUT", C_OUT), ("GND", C_GND)], "R")

    def filo(pa, pb, col, xm=None, ls="-"):
        (xa, ya), (xb, yb) = pa, pb
        if xm is None:
            xm = (xa + xb) / 2
        ax.plot([xa, xm, xm, xb], [ya, ya, yb, yb], color=col, lw=1.6, ls=ls, zorder=1, solid_capstyle="round")

    R = lambda name: (ex1, pins[name][1])
    L = lambda name: (ex0, pins[name][1])
    # LD2410B
    filo(R("VIN"), p1["VCC"], C_VCC, xm=66)
    filo(R("GND_r"), p1["GND"], C_GND, xm=67.5)
    filo(R("D26 (TX2)"), p1["UART_Rx"], C_RX, xm=69)
    filo(R("D25 (RX2)"), p1["UART_Tx"], C_TX, xm=70.5)
    ax.text(82.5, p1["OUT"][1], "non collegato", va="center", fontsize=6.5, color=C_GRIGIO, style="italic")
    # LD2420
    # 3V3 (pin a sinistra) -> LD2420: sopra la scheda e giu' a destra fra scheda e moduli
    ax.plot([ex0, 34, 34, 74.5, 74.5, p2["3V3"][0]], [pins["3V3"][1], pins["3V3"][1], 58.5, 58.5, p2["3V3"][1], p2["3V3"][1]],
            color=C_VCC, lw=1.6, zorder=1)
    filo(R("GND_r"), p2["GND"], C_GND, xm=67.5)
    filo(R("D17 (TX)"), p2["RX"], C_RX, xm=69)
    filo(R("D16 (RX)"), p2["OT1"], C_TX, xm=70.5)
    ax.text(82.5, p2["OT2"][1], "non collegato", va="center", fontsize=6.5, color=C_GRIGIO, style="italic")
    # PIR
    # PIR VCC -> VIN (pin a destra): sopra la scheda
    ax.plot([p3["VCC"][0], 31, 31, 65, 65, ex1], [p3["VCC"][1], p3["VCC"][1], 59.5, 59.5, pins["VIN"][1], pins["VIN"][1]],
            color=C_VCC, lw=1.6, zorder=1)
    filo(p3["OUT"], L("D34"), C_OUT, xm=28.5)
    filo(p3["GND"], L("GND_l"), C_GND, xm=27)

    # legenda
    for i, (lab, col, ls) in enumerate([("alimentazione", C_VCC, "-"), ("massa", C_GND, "-"),
                                        ("radar → ESP32 (TX del radar)", C_TX, "-"),
                                        ("ESP32 → radar (RX del radar)", C_RX, "-"),
                                        ("uscita digitale di presenza", C_OUT, "-")]):
        y = 57.5 - i * 2.4
        ax.plot([2, 6], [y, y], color=col, lw=1.6, ls=ls)
        ax.text(7, y, lab, va="center", fontsize=7.2)
    ax.text(50, 3.6, "verso il PC: alimentazione, programmazione\ne righe CSV sulla seriale USB",
            ha="center", va="top", fontsize=7.0, color=C_GRIGIO)
    salva(fig, "fig28_collegamenti")


# ----------------------------------------------------------------- fig29
def fig_piattaforma():
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    ax.set_xlim(-1, 101); ax.set_ylim(0, 44); ax.axis("off")

    def box(x, y, w, h, titolo, righe, fc=C_BOX, ec=C_BOARD, tc=C_BOARD):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4", fc=fc, ec=ec, lw=1.2, zorder=2))
        ax.text(x + w / 2, y + h - 2.6, titolo, ha="center", va="center", fontsize=9, fontweight="bold", color=tc)
        for i, r in enumerate(righe):
            ax.text(x + w / 2, y + h - 5.6 - i * 2.9, r, ha="center", va="center", fontsize=7.3, color="#222")

    def freccia(x0, y0, x1, y1, lab=None, col=C_BOARD, dy=1.4):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=12, color=col, lw=1.3, zorder=3))
        if lab:
            ax.text((x0 + x1) / 2, (y0 + y1) / 2 + dy, lab, ha="center", va="bottom", fontsize=6.8, color=col)

    # riga principale
    box(0.5, 22, 13.5, 17, "Sensori", ["HLK-LD2410B (5 Hz)", "HLK-LD2420 (10 Hz)", "HC-SR501 (1 bit)"])
    box(19, 22, 16, 17, "ESP32", ["ld2410b_logger", "ld2420_logger_bin", "ld2410b_web", "sketch di configurazione"])
    box(43, 22, 17.5, 17, "PC: acquire.py", ["ricostruisce l'intestazione", "+ 6 colonne di metadati", "beep / annunci vocali"])
    box(66, 22, 13.5, 17, "CSV", ["HLK-LD2410x/data/", "un file per trial", "+ registro sessioni"])
    box(85, 22, 14, 17, "Analisi", ["verifica_engineering", "analizza_test", "analizza_respiro", "vitalita_proto"])

    freccia(14, 30, 19, 30); ax.text(16.5, 31.4, "UART", ha="center", fontsize=6.6, color=C_BOARD)
    freccia(35, 30, 43, 30); ax.text(39, 31.4, "seriale USB", ha="center", fontsize=6.6, color=C_BOARD)
    ax.text(39, 28.8, "righe CSV", ha="center", va="top", fontsize=6.6, color=C_BOARD)
    freccia(60.5, 30, 66, 30)
    freccia(79.5, 30, 85, 30)

    # formato dati unico
    ax.add_patch(FancyBboxPatch((13, 4), 74, 9.5, boxstyle="round,pad=0.4", fc="#fff6e0", ec=C_OUT, lw=1.2, zorder=2))
    ax.text(50, 10.6, "Un solo formato dati (Tabella 3.15)", ha="center", fontsize=8.5, fontweight="bold", color=C_OUT)
    ax.text(50, 6.9, "9 colonne comuni  +  colonne del radar (20 per il LD2410B, 18 per il LD2420)  +  6 metadati  [+ 2 indice a bordo]",
            ha="center", fontsize=6.5, color="#222")
    for x in (27, 51.75, 72.75):
        ax.plot([x, x], [13.9, 21.6], color=C_OUT, lw=1, ls=":", zorder=1)

    # ramo web UI
    freccia(27, 39.5, 27, 42.3, col=C_TX)
    ax.text(28.5, 42.0, "ld2410b_web: Wi-Fi (Access Point) + WebSocket → browser con dashboard, indice di vitalità\ned export CSV con le stesse colonne (Capitolo 6)",
            ha="left", va="center", fontsize=7.2, color=C_TX)

    # uscita
    ax.text(92, 18.6, "figure · foglio Excel\npagina di riepilogo", ha="center", va="top", fontsize=7.2, color=C_GRIGIO)
    freccia(92, 22, 92, 19.4, col=C_GRIGIO)
    salva(fig, "fig29_piattaforma")


if __name__ == "__main__":
    fig_collegamenti()
    fig_piattaforma()
