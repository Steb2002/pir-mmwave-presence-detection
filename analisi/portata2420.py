#!/usr/bin/env python3
"""
Prova di portata del LD2420 in modalita' binaria (04/09/2026).

Legge un CSV di `ld2420_logger_bin` (via acquire.py) e lo spezza in finestre temporali
dichiarate a mano — perche' in questi file la ground truth NON e' statica: c'e' un tratto
a stanza vuota e poi il soggetto fermo a distanze note. Per ogni finestra riporta:
  - % di campioni con presenza
  - mediana e dispersione di `dist_raw_cm` (la distanza che il modulo riporta anche
    con presenza 0)
  - il gate con energia media massima e quella energia (per la mappa gate<->distanza:
    e' questa che decide se il gate 0 copre 0-70 cm)
  - il gate atteso con le due convenzioni, per confronto immediato

Uso:
  python portata2420.py data/portata2420_g8_T01.csv --finestre 0-60:vuoto 70-100:350 110-140:400 ...
    (secondi dall'inizio del file : etichetta; se l'etichetta e' un numero e' la distanza in cm)
  --gate-max N   (facoltativo, solo per stampare la portata attesa nelle due convenzioni)

Solo libreria standard.
"""
import argparse, csv, statistics as st, sys

GATE_CM = 70

def carica(path):
    with open(path, newline="", encoding="utf-8") as f:
        righe = [r for r in csv.DictReader(f) if r.get("frames_ok") == "1"]
    if not righe:
        sys.exit("nessun campione con frames_ok=1: il modulo non ha mai mandato frame")
    t0 = int(righe[0]["timestamp_ms"])
    for r in righe:
        r["_t"] = (int(r["timestamp_ms"]) - t0) / 1000.0
    return righe

def finestra(righe, a, b):
    return [r for r in righe if a <= r["_t"] < b]

def analizza(camp):
    n = len(camp)
    pres = sum(int(r["radar_presence"]) for r in camp)
    # `dist_raw_cm` esiste dal BUILD 2 del logger; i file del BUILD 1 hanno solo la
    # distanza gia' azzerata quando la presenza e' 0.
    col = "dist_raw_cm" if "dist_raw_cm" in camp[0] else "moving_distance_cm"
    dist = [int(r[col]) for r in camp]
    medie = [st.mean(int(r[f"energy2420_gate{g}"]) for r in camp) for g in range(16)]
    g_top = max(range(16), key=lambda g: medie[g])
    return dict(n=n, pres=100.0 * pres / n, dist_med=st.median(dist),
                dist_dev=st.pstdev(dist) if n > 1 else 0.0,
                g_top=g_top, e_top=medie[g_top], medie=medie)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--finestre", nargs="+", required=True, metavar="A-B:ETICHETTA")
    ap.add_argument("--gate-max", type=int, default=None)
    ap.add_argument("--tutte-le-energie", action="store_true", help="stampa i 16 valori medi per finestra")
    a = ap.parse_args()

    righe = carica(a.csv)
    print(f"{a.csv}: {len(righe)} campioni con frame, {righe[-1]['_t']:.0f} s")
    if a.gate_max is not None:
        print(f"gate max {a.gate_max}: portata {a.gate_max*GATE_CM} cm se 'N x 70', "
              f"{(a.gate_max+1)*GATE_CM} cm se '(N+1) x 70'")
    print()
    print(f"{'finestra':>10} {'etichetta':>9} {'n':>4} {'pres%':>6} {'dist_med':>8} {'dev':>5} "
          f"{'g_top':>5} {'E_top':>7} {'g atteso 0=0-70':>16} {'g atteso 0=escluso':>18}")
    for spec in a.finestre:
        try:
            intervallo, etich = spec.split(":", 1)
            ia, ib = (float(x) for x in intervallo.split("-"))
        except ValueError:
            sys.exit(f"finestra malformata: {spec!r} (atteso A-B:ETICHETTA)")
        camp = finestra(righe, ia, ib)
        if not camp:
            print(f"{intervallo:>10} {etich:>9}  -- nessun campione"); continue
        r = analizza(camp)
        try:
            d = float(etich)
            att1 = str(int(d // GATE_CM))            # gate 0 = 0-70
            att2 = str(int(d // GATE_CM) + 1)        # gate 0 escluso (gate 1 = 0-70)
        except ValueError:
            att1 = att2 = "-"
        print(f"{intervallo:>10} {etich:>9} {r['n']:>4} {r['pres']:>6.1f} {r['dist_med']:>8.0f} {r['dist_dev']:>5.0f} "
              f"{r['g_top']:>5} {r['e_top']:>7.0f} {att1:>16} {att2:>18}")
        if a.tutte_le_energie:
            print("           energie medie: " + " ".join(f"{m:.0f}" for m in r["medie"]))
    print()
    print("Lettura: se in ogni finestra a distanza nota g_top coincide con la colonna '0=0-70',")
    print("il gate 0 copre i primi 70 cm; se coincide con '0=escluso', la numerazione parte da 1.")
    print("pres% a stanza vuota > 0 con gate max 8 e = 0 con gate max 6 => era il muro (gate 7).")

if __name__ == "__main__":
    main()
