"""
Analisi delle metriche di rilevamento dai CSV prodotti da acquire.py (repo del professore).

Calcola per ogni file e aggrega per scenario:
- tasso di rilevamento radar e PIR vs ground truth (accuratezza per campione)
- falsi positivi (scenari con ground_truth_presence=0) e falsi negativi (=1)
- latenza di rilevamento (scenari di ingresso, con --event-time)
- statistiche di distanza ed energia del radar

Uso:
    python analizza_test.py data/*.csv
    python analizza_test.py data/ingresso_*.csv --event-time 10
    python analizza_test.py data/*.csv --out riepilogo.csv

Requisiti: nessuno oltre la libreria standard (opzionale: nessun numpy necessario).
"""

import argparse
import csv
import glob
import statistics
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # console Windows cp1252
from collections import defaultdict
from pathlib import Path


def leggi_csv(path):
    """Legge un CSV di acquire.py e restituisce la lista di righe (dict)."""
    righe = []
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        for r in csv.DictReader(f):
            try:
                righe.append({
                    "t_ms": int(r["timestamp_ms"]),
                    "radar": int(r["radar_presence"]),
                    "moving": int(r["moving_target"]),
                    "stationary": int(r["stationary_target"]),
                    "mdist": int(r["moving_distance_cm"]),
                    "sdist": int(r["stationary_distance_cm"]),
                    "menergy": int(r["moving_energy"]),
                    "senergy": int(r["stationary_energy"]),
                    "pir": int(r["pir_presence"]),
                    "scenario": r.get("scenario", "?"),
                    "trial": r.get("trial_id", "?"),
                    "gt": int(r.get("ground_truth_presence", -1)),
                    "gt_state": r.get("ground_truth_state", "?"),
                })
            except (KeyError, ValueError):
                continue  # riga malformata o troncata
    return righe


def latenza_s(righe, event_time_s, colonna):
    """Prima rilevazione (colonna=1) dopo event_time_s dall'inizio del file. None se mai."""
    if not righe:
        return None
    t0 = righe[0]["t_ms"]
    for r in righe:
        t_rel = (r["t_ms"] - t0) / 1000.0
        if t_rel >= event_time_s and r[colonna] == 1:
            return t_rel - event_time_s
    return None


def analizza_file(path, event_time_s=None):
    righe = leggi_csv(path)
    if not righe:
        return None

    n = len(righe)
    durata_s = (righe[-1]["t_ms"] - righe[0]["t_ms"]) / 1000.0
    gt = righe[0]["gt"]
    ris = {
        "file": Path(path).name,
        "scenario": righe[0]["scenario"],
        "trial": righe[0]["trial"],
        "gt": gt,
        "gt_state": righe[0]["gt_state"],
        "n_campioni": n,
        "durata_s": round(durata_s, 1),
        "radar_rate_%": round(100 * sum(r["radar"] for r in righe) / n, 1),
        "pir_rate_%": round(100 * sum(r["pir"] for r in righe) / n, 1),
    }

    # Accuratezza per campione rispetto alla ground truth
    if gt in (0, 1):
        ris["radar_acc_%"] = round(100 * sum(1 for r in righe if r["radar"] == gt) / n, 1)
        ris["pir_acc_%"] = round(100 * sum(1 for r in righe if r["pir"] == gt) / n, 1)
        if gt == 0:
            # Falsi positivi: eventi di attivazione (fronti di salita) per ora
            for col, nome in (("radar", "radar"), ("pir", "pir")):
                fronti = sum(1 for a, b in zip(righe, righe[1:]) if a[col] == 0 and b[col] == 1)
                ore = durata_s / 3600 if durata_s > 0 else 1
                ris[f"fp_{nome}_eventi_h"] = round(fronti / ore, 2)
        else:
            # Falsi negativi: % di tempo in cui il sensore perde la persona
            ris["fn_radar_%"] = round(100 - ris["radar_acc_%"], 1)
            ris["fn_pir_%"] = round(100 - ris["pir_acc_%"], 1)

    # Latenza (solo per scenari di ingresso, con evento a tempo noto)
    if event_time_s is not None:
        lr = latenza_s(righe, event_time_s, "radar")
        lp = latenza_s(righe, event_time_s, "pir")
        ris["latenza_radar_s"] = round(lr, 2) if lr is not None else "MAI"
        ris["latenza_pir_s"] = round(lp, 2) if lp is not None else "MAI"

    # Statistiche distanza/energia (solo campioni con rilevamento)
    sdist = [r["sdist"] for r in righe if r["stationary"] == 1 and r["sdist"] > 0]
    sen = [r["senergy"] for r in righe if r["stationary"] == 1]
    men = [r["menergy"] for r in righe if r["moving"] == 1]
    if sdist:
        ris["sdist_media_cm"] = round(statistics.mean(sdist), 1)
        ris["sdist_dev_cm"] = round(statistics.stdev(sdist), 1) if len(sdist) > 1 else 0
    if sen:
        ris["senergy_media"] = round(statistics.mean(sen), 1)
    if men:
        ris["menergy_media"] = round(statistics.mean(men), 1)

    return ris


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="CSV da analizzare (glob ok)")
    ap.add_argument("--event-time", type=float, default=None,
                    help="istante (s dall'inizio) in cui avviene l'evento, per il calcolo latenza")
    ap.add_argument("--out", default=None, help="salva il riepilogo in un CSV")
    args = ap.parse_args()

    paths = []
    for pattern in args.files:
        paths.extend(glob.glob(pattern))
    if not paths:
        sys.exit("Nessun file trovato.")

    risultati = [r for p in sorted(paths) if (r := analizza_file(p, args.event_time))]
    if not risultati:
        sys.exit("Nessun dato valido nei file indicati.")

    # Stampa per file
    chiavi = sorted({k for r in risultati for k in r}, key=lambda k: (k != "file", k))
    print("\n=== RISULTATI PER FILE ===")
    for r in risultati:
        print("  " + " | ".join(f"{k}={r[k]}" for k in chiavi if k in r))

    # Aggregazione per scenario (media ± dev.std sulle prove)
    print("\n=== AGGREGATO PER SCENARIO (media su trial) ===")
    per_scenario = defaultdict(list)
    for r in risultati:
        per_scenario[r["scenario"]].append(r)
    numeriche = [k for k in chiavi if k not in ("file", "scenario", "trial", "gt", "gt_state")]
    for sc, rs in per_scenario.items():
        print(f"\n[{sc}] ({len(rs)} prove, gt={rs[0]['gt']})")
        for k in numeriche:
            vals = [r[k] for r in rs if isinstance(r.get(k), (int, float))]
            if vals:
                m = statistics.mean(vals)
                s = statistics.stdev(vals) if len(vals) > 1 else 0
                print(f"  {k}: {m:.2f} ± {s:.2f}")
        mai = sum(1 for r in rs if r.get("latenza_radar_s") == "MAI")
        if mai:
            print(f"  ⚠ radar MAI rilevato in {mai}/{len(rs)} prove")

    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=chiavi)
            w.writeheader()
            w.writerows(risultati)
        print(f"\nRiepilogo salvato in {args.out}")


if __name__ == "__main__":
    main()
