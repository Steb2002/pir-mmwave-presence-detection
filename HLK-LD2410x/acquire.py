import argparse
import csv
import sys
import threading
import time
import serial

try:
    import winsound  # solo Windows: usato per i segnali acustici di --beep-at
except ImportError:
    winsound = None

# --- Aggiunta per la tesi (18/08/2026) ------------------------------------------
# Lo script originale scrive righe solo DOPO aver visto la riga di intestazione, che
# l'ESP32 stampa una volta sola in setup(). Se il reset all'apertura della porta non
# scatta, il CSV resta vuoto senza alcun avviso: dopo 30 minuti di acquisizione e' un
# disastro. Qui l'intestazione viene ricostruita dal numero di colonne della prima riga
# di dati, cosi' l'acquisizione non si perde mai.
BASE = [
    "timestamp_ms", "radar_presence", "moving_target", "stationary_target",
    "moving_distance_cm", "stationary_distance_cm", "moving_energy",
    "stationary_energy", "pir_presence",
]
GATE = [f"menergy_gate{i}" for i in range(9)] + [f"senergy_gate{i}" for i in range(9)]
LUCE = ["light_level", "out_level"]


def intestazione_di_riserva(n_colonne):
    """Nomi di colonna dedotti dal numero di campi della riga di dati."""
    if n_colonne == len(BASE):
        return BASE
    if n_colonne == len(BASE) + len(GATE):
        return BASE + GATE
    if n_colonne == len(BASE) + len(GATE) + len(LUCE):
        return BASE + GATE + LUCE
    return None
# -------------------------------------------------------------------------------


# --- Segnale acustico per i test di latenza (fase 2) ----------------------------
# I test 2.1 e 2.2 richiedono che l'evento (ingresso o uscita del soggetto) avvenga a un
# istante NOTO rispetto all'inizio del file. Con un timer sul telefono avviato quando si
# premo Invio l'errore e' sistematico e grosso: tra l'apertura della porta seriale e la
# prima riga di dati passano ~2-3 s (reset dell'ESP32 + setup del logger + i 2 s di attesa
# qui sotto), quindi il "t=10 s" del telefono cadrebbe a t=7-8 s nel file. Su una latenza
# di 0.5-3 s e' un errore piu' grande della grandezza misurata.
# Soluzione: il beep viene emesso da QUESTO script, contando da quando arriva la prima
# riga di dati — cioe' esattamente dall'origine dei tempi che poi usa analizza_test.py.
def beep(freq, durata_ms):
    """Suona in un thread separato: winsound.Beep e' bloccante e fermerebbe la lettura."""
    if winsound is not None:
        threading.Thread(target=winsound.Beep, args=(freq, durata_ms), daemon=True).start()
    else:
        sys.stderr.write("\a")
        sys.stderr.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True, help="Porta seriale, es. COM5 o /dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--output", required=True)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--trial", required=True)
    parser.add_argument("--group", default="G1")
    parser.add_argument("--ground_truth_presence", type=int, required=True)
    parser.add_argument("--ground_truth_state", default="unknown")
    parser.add_argument("--beep-at", type=float, default=None, metavar="SEC",
                        help="emette un beep grave all'inizio dell'acquisizione e un beep "
                             "acuto SEC secondi dopo la prima riga di dati: e' il momento "
                             "in cui il soggetto deve entrare (test 2.1) o uscire (2.2). "
                             "Passare lo stesso SEC ad analizza_test.py come --event-time "
                             "o --release-time")

    args = parser.parse_args()

    ser = serial.Serial(args.port, args.baud, timeout=2)
    time.sleep(2)

    start = time.time()

    t_prima_riga = None   # istante PC della prima riga di dati = origine dei tempi
    beep_fatto = False

    with open(args.output, "w", newline="") as f:
        writer = None

        while time.time() - start < args.duration:
            line = ser.readline().decode(errors="ignore").strip()

            if not line:
                continue

            if line.startswith("ERROR"):
                print(line)
                continue

            parts = line.split(",")

            if parts[0] == "timestamp_ms":
                header = parts + [
                    "pc_time_s",
                    "group_id",
                    "trial_id",
                    "scenario",
                    "ground_truth_presence",
                    "ground_truth_state"
                ]
                writer = csv.writer(f)
                writer.writerow(header)
                print(",".join(header))
                continue

            if writer is None:
                # Nessuna intestazione ricevuta: la ricostruiamo dal numero di colonne
                nomi = intestazione_di_riserva(len(parts)) if parts[0].isdigit() else None
                if nomi is None:
                    continue
                print(f"ATTENZIONE: intestazione non ricevuta dall'ESP32, "
                      f"ricostruita da {len(parts)} colonne")
                header = nomi + [
                    "pc_time_s",
                    "group_id",
                    "trial_id",
                    "scenario",
                    "ground_truth_presence",
                    "ground_truth_state"
                ]
                writer = csv.writer(f)
                writer.writerow(header)

            if t_prima_riga is None:
                t_prima_riga = time.time()
                if args.beep_at is not None:
                    beep(600, 200)   # grave = acquisizione partita, il conto e' iniziato
                    sys.stderr.write(f"Acquisizione partita: beep di evento fra "
                                     f"{args.beep_at:.0f} s\n")
                    sys.stderr.flush()

            if (args.beep_at is not None and not beep_fatto
                    and time.time() - t_prima_riga >= args.beep_at):
                beep_fatto = True
                beep(1400, 400)      # acuto = ADESSO (entra / esci)
                sys.stderr.write(f"EVENTO: beep a t=+{time.time() - t_prima_riga:.2f} s "
                                 f"dalla prima riga\n")
                sys.stderr.flush()

            row = parts + [
                time.time(),
                args.group,
                args.trial,
                args.scenario,
                args.ground_truth_presence,
                args.ground_truth_state
            ]

            writer.writerow(row)
            print(",".join(map(str, row)))

    if args.beep_at is not None and not beep_fatto:
        sys.stderr.write("ATTENZIONE: il beep di evento NON e' stato emesso (durata "
                         "troppo breve o nessun dato). Trial da rifare.\n")

    ser.close()

if __name__ == "__main__":
    main()