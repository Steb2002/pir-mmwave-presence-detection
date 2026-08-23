"""
Verifica di qualita' di un CSV prodotto da firmware/ld2410b_logger (engineering mode).

Serve per il Test 0.1 passo B e il Test 0.2 del PIANO_TEST: controlla che
l'acquisizione sia usabile PRIMA di costruirci sopra le analisi della tesi.

Cosa controlla:
  1. cadenza di campionamento reale (attesa: 5.00 Hz, cioe' dt = 200 ms costante)
  2. presenza delle 18 colonne per-gate (prova che l'engineering mode e' attivo)
  3. saturazione delle energie a 100 (un segnale clippato non porta informazione)
  4. coerenza gate di picco <-> distanza misurata (valida la mappa 0.75 m/gate)
  5. rumore di fondo per-gate a stanza vuota (base per tarare le soglie)
  6. transizioni di presenza (falsi positivi e tempi di rilascio)
  7. confronto PIR vs radar, se il PIR e' collegato (anteprima dell'obiettivo 3)
  8. coerenza tra il pin OUT del radar e la presenza letta via UART

Uso:
    python verifica_engineering.py ..\HLK-LD2410x\data\20260818_test01B_ld2410b_engineering.csv

Requisiti: solo libreria standard.
"""

import argparse
import collections
import csv
import statistics
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # console Windows cp1252

RISOLUZIONE_GATE_CM = 75  # risoluzione di fabbrica: 0.75 m per gate
MGATE = [f"menergy_gate{i}" for i in range(9)]
SGATE = [f"senergy_gate{i}" for i in range(9)]


INTESTAZIONE = ([
    "timestamp_ms", "radar_presence", "moving_target", "stationary_target",
    "moving_distance_cm", "stationary_distance_cm", "moving_energy",
    "stationary_energy", "pir_presence",
] + MGATE + SGATE + ["light_level", "out_level"])
NUMERICHE = set(INTESTAZIONE)


def leggi(path):
    """Legge il CSV del logger. Due accorgimenti necessari:
    1. se manca la riga di intestazione (Serial Monitor aperto a sketch gia' avviato)
       la ricostruisce d'ufficio;
    2. converte a intero SOLO le colonne numeriche del logger. I file prodotti da
       acquire.py hanno in coda colonne testuali (group_id, trial_id, scenario,
       ground_truth_state): convertirle tutte faceva scartare ogni riga e lo script
       diceva "Nessuna riga valida" su file perfettamente buoni.
    """
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        prima = f.readline()
        f.seek(0)
        senza_header = prima.split(",")[0].strip().isdigit()
        if senza_header:
            print("NB: intestazione assente, uso i nomi di colonna standard del logger")
            lettore = csv.DictReader(f, fieldnames=INTESTAZIONE)
        else:
            lettore = csv.DictReader(f)
        righe = []
        for r in lettore:
            riga = {}
            for k, v in r.items():
                if k is None or k not in NUMERICHE or v in (None, ""):
                    continue
                try:
                    riga[k] = int(v)
                except ValueError:
                    pass          # colonna numerica ma valore sporco: la si ignora
            if "timestamp_ms" in riga:
                righe.append(riga)
    return righe


def sezione(titolo):
    print(f"\n--- {titolo} ---")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", help="file CSV del logger")
    ap.add_argument("--hz-attesi", type=float, default=5.0)
    args = ap.parse_args()

    righe = leggi(args.csv)
    if not righe:
        sys.exit("Nessuna riga valida nel CSV.")

    eng = all(c in righe[0] for c in MGATE + SGATE)
    durata = (righe[-1]["timestamp_ms"] - righe[0]["timestamp_ms"]) / 1000
    print(f"File: {args.csv}")
    print(f"Campioni: {len(righe)}   Durata: {durata:.1f} s   Engineering mode: "
          f"{'SI (18 colonne per-gate)' if eng else 'NO'}")

    # 1. cadenza
    sezione("cadenza di campionamento")
    dt = [b["timestamp_ms"] - a["timestamp_ms"] for a, b in zip(righe, righe[1:])]
    medio = statistics.mean(dt)
    print(f"dt medio {medio:.1f} ms -> {1000/medio:.2f} Hz (attesi {args.hz_attesi:.2f} Hz)")
    print(f"dt: min={min(dt)} max={max(dt)} valori distinti={sorted(set(dt))[:6]}")
    if max(dt) - min(dt) > 20:
        print("!! jitter > 20 ms: la serie temporale non e' uniforme, attenzione alla FFT del respiro")

    # 2. PIR
    sezione("colonna pir_presence")
    pir = collections.Counter(r["pir_presence"] for r in righe)
    print(f"valori: {dict(pir)}", end="  ")
    print("(costante -> PIR non collegato, colonna da ignorare)" if len(pir) == 1
          else "(variabile -> PIR collegato)")

    # 2b. confronto PIR vs radar — l'anteprima del risultato centrale dell'obiettivo 3
    if len(pir) > 1:
        sezione("PIR vs radar (anteprima obiettivo 3)")
        n = len(righe)
        acc = sum(1 for r in righe if r["pir_presence"] == r["radar_presence"])
        solo_radar = [r for r in righe if r["radar_presence"] == 1 and r["pir_presence"] == 0]
        solo_pir = [r for r in righe if r["radar_presence"] == 0 and r["pir_presence"] == 1]
        print(f"concordi:            {acc}/{n} campioni ({100*acc/n:.1f}%)")
        print(f"solo radar (PIR=0):  {len(solo_radar):4d} ({len(solo_radar)*medio/1000:.0f} s) "
              f"<- persona ferma: e' QUI che il mmWave batte il PIR")
        if solo_radar:
            fermi = sum(1 for r in solo_radar if r["stationary_target"] == 1)
            print(f"   di cui col radar in stato 'fermo': {fermi}/{len(solo_radar)} "
                  f"({100*fermi/len(solo_radar):.0f}%)")
        print(f"solo PIR (radar=0):  {len(solo_pir):4d} ({len(solo_pir)*medio/1000:.0f} s) "
              f"<- se >0: da investigare (coda del PIR o mancato radar)")

    # 2c. pin OUT del radar (letto dal frame UART, non dal cavo blu)
    if "out_level" in righe[0]:
        sezione("pin OUT del radar vs presenza da UART")
        n = len(righe)
        d = [r for r in righe if r["out_level"] != r["radar_presence"]]
        print(f"discordanti: {len(d)}/{n} campioni ({100*len(d)/n:.1f}%)")
        print("(l'uscita hardware e il dato UART dovrebbero coincidere: uno scarto grande"
              " e' un risultato da riportare, non un errore di misura)")
        luci = {r["light_level"] for r in righe}
        print(f"light_level: valori osservati {sorted(luci)[:8]}"
              f"{' ...' if len(luci) > 8 else ''}")

    if not eng:
        return

    # 3. saturazione
    sezione("saturazione delle energie (valore 100 = fondoscala)")
    mv = [r for r in righe if r["moving_target"] == 1]
    st = [r for r in righe if r["stationary_target"] == 1]
    for nome, sel, col in (("moving", mv, "moving_energy"), ("stationary", st, "stationary_energy")):
        if sel:
            n = sum(1 for r in sel if r[col] == 100)
            print(f"{nome:10s}: {n}/{len(sel)} campioni a 100 ({100*n/len(sel):.1f}%)")

    # 4. gate di picco vs distanza
    sezione(f"coerenza gate di picco <-> distanza (1 gate = {RISOLUZIONE_GATE_CM} cm)")
    print("gate atteso (range)      | gate modale | entro +-1 gate")
    gruppi = collections.defaultdict(list)
    for r in mv:
        d = r["moving_distance_cm"]
        if d <= 0:
            continue
        atteso = min(8, d // RISOLUZIONE_GATE_CM)
        picco = max(range(9), key=lambda i: r[MGATE[i]])
        gruppi[atteso].append(picco)
    ok = tot = 0
    for atteso in sorted(gruppi):
        p = gruppi[atteso]
        modale = collections.Counter(p).most_common(1)[0][0]
        entro = sum(1 for x in p if abs(x - atteso) <= 1)
        ok += entro
        tot += len(p)
        print(f"  {atteso} ({atteso*RISOLUZIONE_GATE_CM:3d}-{(atteso+1)*RISOLUZIONE_GATE_CM:3d} cm) n={len(p):4d} |"
              f"      {modale}      | {entro}/{len(p)}")
    if tot:
        print(f"TOTALE entro +-1 gate: {ok}/{tot} = {100*ok/tot:.1f}%")

    # 5. rumore di fondo
    sezione("rumore di fondo per-gate (campioni con radar_presence = 0)")
    vuoto = [r for r in righe if r["radar_presence"] == 0]
    if not vuoto:
        print("nessun campione a stanza vuota in questo file")
    else:
        print(f"{len(vuoto)} campioni ({len(vuoto)*medio/1000:.0f} s)")
        print("gate |   moving: media  max |  stationary: media  max")
        for i in range(9):
            m = [r[MGATE[i]] for r in vuoto]
            s = [r[SGATE[i]] for r in vuoto]
            print(f"  {i}  | {statistics.mean(m):11.1f} {max(m):4d} | {statistics.mean(s):15.1f} {max(s):4d}")
        print("NB: una soglia impostata sotto il 'max' di un gate produce falsi positivi su quel gate")

    # 6. transizioni
    sezione("transizioni di presenza")
    t0 = righe[0]["timestamp_ms"]
    prec = righe[0]["radar_presence"]
    n = 0
    for r in righe[1:]:
        if r["radar_presence"] != prec:
            n += 1
            print(f"  t={(r['timestamp_ms']-t0)/1000:7.1f} s   presenza {prec} -> {r['radar_presence']}")
            prec = r["radar_presence"]
    if n == 0:
        print("  nessuna transizione (presenza costante per tutto il file)")


if __name__ == "__main__":
    main()
