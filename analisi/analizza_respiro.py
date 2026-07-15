"""
Analisi FFT del respiro dai log del radar LD2410B.

Prende la serie temporale di un segnale di energia (default: stationary_energy)
e cerca il picco spettrale nella banda respiratoria 0.1-0.5 Hz (6-30 atti/min).

⚠ Richiede un campionamento >= 2 Hz (meglio 5-10 Hz): il firmware originale del
professore campiona a 1 Hz, che per Nyquist copre a malapena 0.5 Hz — usare il
firmware modificato con periodo 100-200 ms (vedi PIANO_TEST.md, Test 0.2).

Uso:
    python analizza_respiro.py data/respiro_T01.csv
    python analizza_respiro.py data/respiro_T01.csv --colonna senergy_gate3
    python analizza_respiro.py data/respiro_T01.csv --spettro-out spettro.csv

Requisiti: numpy  (pip install numpy)
"""

import argparse
import csv
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # console Windows cp1252

try:
    import numpy as np
except ImportError:
    sys.exit("Serve numpy: pip install numpy")

BANDA_RESPIRO = (0.1, 0.5)  # Hz


def leggi_serie(path, colonna):
    """Ritorna (tempi_s, valori) dalla colonna scelta del CSV."""
    tempi, valori = [], []
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        if colonna not in (reader.fieldnames or []):
            sys.exit(f"Colonna '{colonna}' non trovata. Disponibili: {reader.fieldnames}")
        for r in reader:
            try:
                tempi.append(int(r["timestamp_ms"]) / 1000.0)
                valori.append(float(r[colonna]))
            except (KeyError, ValueError):
                continue
    if len(valori) < 32:
        sys.exit(f"Solo {len(valori)} campioni validi: servono almeno 32 (>60 s di acquisizione).")
    return np.array(tempi), np.array(valori)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help="CSV di acquisizione (persona ferma davanti al sensore)")
    ap.add_argument("--colonna", default="stationary_energy",
                    help="colonna da analizzare (default: stationary_energy; "
                         "con engineering mode usare il gate della persona, es. senergy_gate3)")
    ap.add_argument("--spettro-out", default=None, help="salva lo spettro completo in CSV")
    args = ap.parse_args()

    t, x = leggi_serie(args.file, args.colonna)

    # Frequenza di campionamento effettiva dai timestamp
    dt = np.diff(t)
    fs = 1.0 / np.median(dt)
    print(f"Campioni: {len(x)}   Durata: {t[-1]-t[0]:.1f} s   Fs effettiva: {fs:.2f} Hz")
    if fs < 1.5:
        print("⚠ ATTENZIONE: Fs < 1.5 Hz — banda respiro non osservabile in modo affidabile.")
        print("  Modificare il firmware per campionare ogni 100-200 ms.")

    # Detrend (rimuove la componente DC e la deriva lenta) + finestra di Hann
    x = x - np.mean(x)
    coeff = np.polyfit(t - t[0], x, 1)
    x = x - np.polyval(coeff, t - t[0])
    x = x * np.hanning(len(x))

    # FFT
    freq = np.fft.rfftfreq(len(x), d=1.0 / fs)
    ampiezza = np.abs(np.fft.rfft(x))

    # Picco nella banda respiratoria
    banda = (freq >= BANDA_RESPIRO[0]) & (freq <= BANDA_RESPIRO[1])
    if not banda.any():
        sys.exit("Nessun bin FFT nella banda 0.1-0.5 Hz: acquisizione troppo corta o Fs troppo bassa.")
    i_picco = np.argmax(ampiezza * banda)
    f_picco = freq[i_picco]
    a_picco = ampiezza[i_picco]

    # Rapporto picco/fondo nella banda come indicatore di confidenza
    fondo = np.median(ampiezza[banda]) or 1e-9
    snr = a_picco / fondo

    print(f"\nPicco respiratorio: {f_picco:.3f} Hz  →  {f_picco*60:.1f} atti/min")
    print(f"Rapporto picco/fondo in banda: {snr:.1f}  "
          f"({'respiro PRESENTE' if snr > 3 else 'debole/incerto — ripetere la prova'})")

    # Confronto con eventuale conteggio manuale
    print("\nSuggerimento: durante la prova conta manualmente gli atti respiratori")
    print("(o usa un metronomo respiratorio) e confronta con il valore stimato.")

    if args.spettro_out:
        with open(args.spettro_out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["freq_hz", "atti_min", "ampiezza"])
            for fr, am in zip(freq, ampiezza):
                w.writerow([round(fr, 4), round(fr * 60, 2), round(float(am), 3)])
        print(f"Spettro salvato in {args.spettro_out} (grafico a dispersione in Excel)")


if __name__ == "__main__":
    main()
