"""
Analisi FFT del respiro dai log del radar LD2410B.

Prende la serie temporale di un segnale di energia e cerca il picco spettrale
nella banda respiratoria 0.1-0.5 Hz (6-30 atti/min).

⚠ Richiede un campionamento >= 2 Hz (meglio 5-10 Hz): il firmware originale del
professore campiona a 1 Hz, che per Nyquist copre a malapena 0.5 Hz — usare il
firmware modificato con periodo 100-200 ms (vedi PIANO_TEST.md, Test 0.2).

⚠ ATTENZIONE ALLA SATURAZIONE: le energie del LD2410B sono limitate a 0-100. A
distanza ravvicinata o con soglie basse il canale va a fondoscala e la serie
diventa una riga piatta a 100, che NON contiene respiro. Prima di fidarsi di un
risultato, controllare la percentuale di campioni a 100 (lo script la stampa).
Su una prova reale a 40 cm (18/08/2026) stationary_energy era saturo al 100%
mentre il respiro era perfettamente leggibile su menergy_gate2: da qui --scan.

Uso:
    python analizza_respiro.py data/respiro_T01.csv --scan
    python analizza_respiro.py data/respiro_T01.csv --colonna menergy_gate2
    python analizza_respiro.py data/respiro_T01.csv --colonna senergy_gate3 --spettro-out spettro.csv

Requisiti: numpy  (pip install numpy)
"""

import argparse
import csv
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # console Windows cp1252

try:
    import numpy as np
except ImportError:
    sys.exit("Serve numpy: pip install numpy")

BANDA_RESPIRO = (0.1, 0.5)  # Hz
MGATE = [f"menergy_gate{i}" for i in range(9)]
SGATE = [f"senergy_gate{i}" for i in range(9)]
INTESTAZIONE = ([
    "timestamp_ms", "radar_presence", "moving_target", "stationary_target",
    "moving_distance_cm", "stationary_distance_cm", "moving_energy",
    "stationary_energy", "pir_presence",
] + MGATE + SGATE + ["light_level", "out_level"])
CANALI = ["moving_energy", "stationary_energy"] + MGATE + SGATE


def apri(path):
    """Legge il CSV del logger. Ricostruisce l'intestazione se manca (capita
    quando si apre il Serial Monitor a sketch gia' avviato)."""
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        prima = f.readline()
        f.seek(0)
        if prima.split(",")[0].strip().isdigit():
            print("NB: intestazione assente, uso i nomi di colonna standard del logger")
            reader = csv.DictReader(f, fieldnames=INTESTAZIONE)
            campi = INTESTAZIONE
        else:
            reader = csv.DictReader(f)
            campi = reader.fieldnames or []
        righe = [r for r in reader]
    return righe, campi


def serie(righe, colonna):
    """Ritorna (tempi_s, valori) dalla colonna scelta."""
    tempi, valori = [], []
    for r in righe:
        try:
            tempi.append(int(r["timestamp_ms"]) / 1000.0)
            valori.append(float(r[colonna]))
        except (KeyError, TypeError, ValueError):
            continue
    return np.array(tempi), np.array(valori)


def analizza(t, x):
    """FFT in banda respiratoria. Ritorna un dict con fs, picco, snr, saturazione."""
    fs = 1.0 / np.median(np.diff(t))
    sat = 100.0 * np.mean(x >= 100)
    piatto = float(np.std(x))

    y = x - np.mean(x)
    coeff = np.polyfit(t - t[0], y, 1)          # toglie anche la deriva lenta
    y = (y - np.polyval(coeff, t - t[0])) * np.hanning(len(y))

    freq = np.fft.rfftfreq(len(y), d=1.0 / fs)
    amp = np.abs(np.fft.rfft(y))
    banda = (freq >= BANDA_RESPIRO[0]) & (freq <= BANDA_RESPIRO[1])
    if not banda.any():
        return None
    i = np.argmax(amp * banda)
    fondo = np.median(amp[banda]) or 1e-9
    return {"fs": fs, "sat": sat, "std": piatto, "freq": freq, "amp": amp,
            "f_picco": freq[i], "snr": amp[i] / fondo}


def gruppi_concordi(esiti, toll):
    """Raggruppa le stime che concordano entro 'toll'. Ritorna una lista di gruppi,
    dal piu' numeroso, senza duplicati."""
    gruppi = []
    for _, _, r_rif in esiti:
        f_rif = r_rif["f_picco"]
        g = [e for e in esiti if abs(e[2]["f_picco"] - f_rif) / f_rif <= toll]
        if len(g) >= 2 and not any(set(x[1] for x in g) == set(x[1] for x in h)
                                   for h in gruppi):
            gruppi.append(g)
    gruppi.sort(key=len, reverse=True)
    return gruppi


def solo_moving(g):
    return all(n.startswith("menergy") or n == "moving_energy" for _, n, _ in g)


def scansiona(path, snr_min, toll):
    """Analizza un file. Ritorna (esiti, gruppi) oppure (None, None)."""
    righe, campi = apri(path)
    esiti = []
    for c in CANALI:
        if c not in campi:
            continue
        t, x = serie(righe, c)
        if len(x) < 32:
            continue
        r = analizza(t, x)
        if r is None or r["sat"] >= 20 or r["std"] < 1.5 or r["snr"] <= snr_min:
            continue
        esiti.append((r["snr"], c, r))
    if not esiti:
        return None, None
    return esiti, gruppi_concordi(esiti, toll)


def stima_moving(gruppi, minimo=3):
    """La stima dai soli canali moving: il gruppo moving piu' numeroso con >= minimo
    canali. E' il criterio giustificato dai dati — i canali stazionari producono in
    ogni sessione un artefatto compatto a ~6-7 atti/min."""
    candidati = [g for g in gruppi if solo_moving(g) and len(g) >= minimo]
    if not candidati:
        return None
    g = candidati[0]
    return float(np.median([e[2]["f_picco"] for e in g])), len(g)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="+",
                    help="uno o piu' CSV (glob ok). Con piu' file e --scan si ottiene il "
                         "riepilogo aggregato sui trial")
    ap.add_argument("--colonna", default="stationary_energy",
                    help="colonna da analizzare (default: stationary_energy — spesso "
                         "saturo da vicino: usare prima --scan)")
    ap.add_argument("--scan", action="store_true",
                    help="prova TUTTI i canali di energia e ordina per attendibilita'")
    ap.add_argument("--spettro-out", default=None, help="salva lo spettro completo in CSV")
    ap.add_argument("--snr-min", type=float, default=3.0,
                    help="SNR minimo perche' un canale sia 'utilizzabile' (default 3.0). "
                         "E' una soglia di comodo, non una proprieta' del sensore: "
                         "dichiarare nella tesi il valore usato")
    ap.add_argument("--tolleranza", type=float, default=0.10,
                    help="scarto relativo entro cui due canali si dicono concordi "
                         "(default 0.10)")
    args = ap.parse_args()

    import glob as _glob
    percorsi = []
    for pattern in args.file:
        percorsi.extend(sorted(_glob.glob(pattern)) or [pattern])

    if len(percorsi) > 1:
        if not args.scan:
            sys.exit("Con piu' file serve --scan.")
        print(f"--- riepilogo respiro su {len(percorsi)} file "
              f"(SNR>{args.snr_min:g}, tolleranza {args.tolleranza*100:g}%) ---")
        print("file                                stima moving   canali   gruppi")
        stime = []
        for path in percorsi:
            esiti, gruppi = scansiona(path, args.snr_min, args.tolleranza)
            if not esiti:
                print(f"{Path(path).name:35s} nessun canale utilizzabile")
                continue
            m = stima_moving(gruppi)
            if m is None:
                print(f"{Path(path).name:35s}      --        (nessun gruppo moving >=3)"
                      f"   {len(gruppi)}")
                continue
            f_hz, n = m
            stime.append(f_hz * 60)
            print(f"{Path(path).name:35s} {f_hz*60:6.1f} atti/min   {n:2d}      {len(gruppi)}")
        if len(stime) >= 2:
            media = sum(stime) / len(stime)
            dev = (sum((x - media) ** 2 for x in stime) / (len(stime) - 1)) ** 0.5
            print()
            print(f"AGGREGATO su {len(stime)} trial: {media:.1f} +- {dev:.1f} atti/min "
                  f"(min {min(stime):.1f}, max {max(stime):.1f})")
            print("Stima dai soli canali moving: i canali stazionari producono in ogni")
            print("sessione un artefatto a ~6-7 atti/min e sono esclusi per costruzione.")
        elif stime:
            print()
            print(f"Un solo trial utilizzabile: {stime[0]:.1f} atti/min")
        print()
        print("NB: senza ground truth queste restano stime. Serve un ritmo imposto noto.")
        return

    args.file = percorsi[0]
    righe, campi = apri(args.file)

    if args.scan:
        print(f"\n--- scansione di tutti i canali ({args.file}) ---")
        print("canale             %sat  std    picco        SNR   giudizio")
        esiti = []
        for c in CANALI:
            if c not in campi:
                continue
            t, x = serie(righe, c)
            if len(x) < 32:
                continue
            r = analizza(t, x)
            if r is None:
                continue
            if r["sat"] >= 20:
                giudizio = "SCARTATO: saturo"
            elif r["std"] < 1.5:
                giudizio = "SCARTATO: piatto"
            elif r["snr"] > 3:
                giudizio = "utilizzabile"
                esiti.append((r["snr"], c, r))
            else:
                giudizio = "debole"
            print(f"{c:18s} {r['sat']:4.0f}% {r['std']:5.1f}  "
                  f"{r['f_picco']:.3f} Hz={r['f_picco']*60:4.1f}/min  {r['snr']:5.1f}x  {giudizio}")

        if not esiti:
            sys.exit("\nNessun canale utilizzabile: probabile saturazione. "
                     "Ripetere piu' lontano (>=1.5 m) o abbassando le soglie.")
        # RAGGRUPPAMENTO. Non si sceglie "il gruppo piu' numeroso": i canali stazionari
        # producono in modo sistematico un picco a ~6-7 atti/min (osservato in TUTTE le
        # sessioni, anche dove i canali moving concordavano su 18-20), quindi formano un
        # gruppo compatto e numeroso che vincerebbe sempre pur essendo un artefatto.
        # Si riportano quindi TUTTI i gruppi, indicando di che famiglia di canali sono
        # fatti, e la decisione resta all'analista.
        TOLL = args.tolleranza
        gruppi = []
        for _, _, r_rif in esiti:
            f_rif = r_rif["f_picco"]
            g = [e for e in esiti if abs(e[2]["f_picco"] - f_rif) / f_rif <= TOLL]
            if len(g) >= 2 and not any(set(x[1] for x in g) == set(x[1] for x in h)
                                       for h in gruppi):
                gruppi.append(g)
        gruppi.sort(key=len, reverse=True)

        print(f"\nCanali utilizzabili: {len(esiti)} su {len(CANALI)}")
        if not gruppi:
            print("Nessun gruppo di canali concordi: stima non affidabile.")
            return
        print(f"Gruppi di canali concordi entro il {TOLL*100:.0f}% (dal piu' numeroso):")
        for g in gruppi[:3]:
            stime = np.array([e[2]["f_picco"] for e in g])
            nomi = sorted(e[1] for e in g)
            n_mov = sum(1 for x in nomi if x.startswith("menergy") or x == "moving_energy")
            n_sta = len(nomi) - n_mov
            fam = f"{n_mov} moving + {n_sta} stazionari"
            avviso = ""
            if n_mov == 0:
                avviso = "  <-- SOLO canali stazionari: sospetto artefatto"
            if np.median(stime) * 60 < 8:
                avviso += "  <-- sotto 8 atti/min: implausibile per un adulto sveglio"
            print(f"  {np.median(stime)*60:5.1f} atti/min ({np.median(stime):.3f} Hz)  "
                  f"{len(g)} canali ({fam}){avviso}")
            print(f"        {', '.join(nomi)}")
        print("\nNB: senza ground truth queste restano stime. La validazione richiede")
        print("un ritmo imposto noto (respiro a metronomo) da confrontare col valore stimato.")
        return

    if args.colonna not in campi:
        sys.exit(f"Colonna '{args.colonna}' non trovata. Disponibili: {campi}")
    t, x = serie(righe, args.colonna)
    if len(x) < 32:
        sys.exit(f"Solo {len(x)} campioni validi: servono almeno 32 (>60 s di acquisizione).")
    r = analizza(t, x)
    if r is None:
        sys.exit("Nessun bin FFT nella banda 0.1-0.5 Hz: acquisizione troppo corta o Fs troppo bassa.")

    print(f"Colonna: {args.colonna}")
    print(f"Campioni: {len(x)}   Durata: {t[-1]-t[0]:.1f} s   Fs effettiva: {r['fs']:.2f} Hz")
    if r["fs"] < 1.5:
        print("⚠ ATTENZIONE: Fs < 1.5 Hz — banda respiro non osservabile in modo affidabile.")
        print("  Modificare il firmware per campionare ogni 100-200 ms.")
    if r["sat"] >= 20:
        print(f"⚠ ATTENZIONE: {r['sat']:.0f}% dei campioni a fondoscala (100). Il segnale e'")
        print("  clippato: il risultato qui sotto NON e' attendibile. Lanciare --scan.")
    if r["std"] < 1.5:
        print("⚠ ATTENZIONE: serie quasi costante — nessuna informazione utile.")

    print(f"\nPicco respiratorio: {r['f_picco']:.3f} Hz  →  {r['f_picco']*60:.1f} atti/min")
    print(f"Rapporto picco/fondo in banda: {r['snr']:.1f}  "
          f"({'respiro PRESENTE' if r['snr'] > 3 else 'debole/incerto — ripetere la prova'})")

    print("\nSuggerimento: durante la prova conta manualmente gli atti respiratori")
    print("(o usa un metronomo respiratorio) e confronta con il valore stimato.")

    if args.spettro_out:
        with open(args.spettro_out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["freq_hz", "atti_min", "ampiezza"])
            for fr, am in zip(r["freq"], r["amp"]):
                w.writerow([round(float(fr), 4), round(float(fr) * 60, 2), round(float(am), 3)])
        print(f"Spettro salvato in {args.spettro_out} (grafico a dispersione in Excel)")


if __name__ == "__main__":
    main()
