#!/usr/bin/env python3
"""
verifica_vitalita_bordo.py — confronta l'indice di vitalita' calcolato A BORDO dall'ESP32
con quello ricalcolato offline da vitalita_proto.py sugli stessi campioni.

Ingresso: un CSV esportato dalla web UI (step 4-5), che oltre alle 35 colonne di
acquire.py ha in coda `vitality_onboard` e `vitality_class_onboard`.
Il prototipo viene eseguito con le STESSE costanti di firmware/ld2410b_web/config.h
(alpha_m 0,05 · alpha_v 0,01 · k 0,5 · soglie 45/95 · gate dalla distanza · fondo per gate
da stanza_vuota_notte_T01). Se bordo e offline coincidono entro ±1 (l'ESP32 arrotonda a
intero), il porting e' verificato: e' il criterio di accettazione dello step 5
(analisi/approfondimenti/PROGETTO_SITO_DETTAGLIO.md §5).

Uso:
    python analisi/verifica_vitalita_bordo.py data/vit_*.csv
    python analisi/verifica_vitalita_bordo.py file.csv --gate energia   # se il firmware usa argmax

Nota: le EWMA del prototipo partono dal primo campione del FILE, quelle del firmware dal
primo campione dopo l'accensione. Se la sessione e' iniziata a radar gia' caldo, le prime
decine di secondi possono differire: il confronto riporta anche la sola coda (dopo 60 s).
"""
import argparse
import csv
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vitalita_proto as vp  # noqa: E402

# Costanti = firmware/ld2410b_web/config.h (tenerle allineate a mano)
ALPHA_M, ALPHA_V, K = 0.05, 0.01, 0.5
SOGLIE = [45.0, 95.0]
FONDO = [17.58, 13.20, 4.35, 2.88, 5.29, 3.06, 3.87, 3.33, 4.41]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--gate", default="distanza", help="distanza (default, = config.h) | energia | N")
    ap.add_argument("--coda-da", type=float, default=60.0, help="secondi da cui confrontare anche la sola coda")
    args = ap.parse_args()
    criterio = int(args.gate) if args.gate.isdigit() else args.gate

    for f in args.files:
        righe = vp.leggi(f)
        with open(f, newline="", encoding="utf-8") as fh:
            grezze = [r for r in csv.DictReader(fh) if (r.get("timestamp_ms") or "").isdigit()]
        if not righe or "vitality_onboard" not in grezze[0]:
            print(f"{Path(f).name}: manca la colonna vitality_onboard (non e' un export della web UI >= BUILD 6)")
            continue
        serie = vp.calcola(righe, ALPHA_M, ALPHA_V, K, criterio, FONDO, sorgente="gate")
        n = min(len(serie), len(grezze))
        diff, cls_ok, cls_tot, coda = [], 0, 0, []
        t0 = int(grezze[0]["timestamp_ms"])
        for s, g in zip(serie[:n], grezze[:n]):
            bordo = float(g["vitality_onboard"] or 0)
            off = s["vitality"]
            d = bordo - off
            diff.append(d)
            if (int(g["timestamp_ms"]) - t0) / 1000.0 >= args.coda_da:
                coda.append(d)
            if int(g["radar_presence"]) == 1:
                cls_tot += 1
                cls_off = vp.classifica(off, SOGLIE, True)
                if g["vitality_class_onboard"] == cls_off:
                    cls_ok += 1
        entro1 = sum(1 for d in diff if abs(d) <= 1.0)
        print(f"\n{Path(f).name}: {n} campioni, criterio gate = {args.gate}")
        print(f"  bordo - offline: media {statistics.mean(diff):+.2f}, dev {statistics.pstdev(diff):.2f}, "
              f"max |diff| {max(abs(d) for d in diff):.1f}")
        print(f"  entro ±1: {100 * entro1 / n:.1f} %   ({entro1}/{n})")
        if coda:
            e1 = sum(1 for d in coda if abs(d) <= 1.0)
            print(f"  solo coda (t >= {args.coda_da:.0f} s): entro ±1 {100 * e1 / len(coda):.1f} %, "
                  f"max |diff| {max(abs(d) for d in coda):.1f}")
        if cls_tot:
            print(f"  classe uguale (campioni con presenza): {100 * cls_ok / cls_tot:.1f} %  ({cls_ok}/{cls_tot})")
        medio_b = statistics.mean(float(g["vitality_onboard"] or 0) for g in grezze[:n] if int(g["radar_presence"]) == 1) if cls_tot else 0
        medio_o = statistics.mean(s["vitality"] for s in serie[:n] if s["presenza"] == 1) if cls_tot else 0
        print(f"  indice medio con presenza: bordo {medio_b:.1f}, offline {medio_o:.1f}")


if __name__ == "__main__":
    main()
