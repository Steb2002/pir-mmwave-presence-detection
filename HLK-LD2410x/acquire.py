import argparse
import csv
import subprocess
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
# preme Invio l'errore e' sistematico e grosso: tra l'apertura della porta seriale e la
# prima riga di dati passano ~2-3 s (reset dell'ESP32 + setup del logger + i 2 s di attesa
# piu' sotto), quindi il "t=10 s" del telefono cadrebbe a t=7-8 s nel file. Su una latenza
# di 0.5-3 s e' un errore piu' grande della grandezza misurata.
# Soluzione: il segnale viene emesso da QUESTO script, contando da quando arriva la prima
# riga di dati — cioe' esattamente dall'origine dei tempi che poi usa analizza_test.py.
#
# Si pronunciano le PAROLE "entra"/"esci" invece di due bip: con i bip bisogna ricordare
# quale dei due significa cosa, e nei due test il significato e' invertito (nel 2.1 prima
# si esce e poi si entra, nel 2.2 il contrario). Il 22/08/2026 un trial e' stato perso
# proprio per questo. La parola elimina l'ambiguita'.
#
# Il processo PowerShell viene aperto e inizializzato all'avvio: al momento dell'evento
# resta solo da inviargli la riga, cosi' il ritardo e' di decine di ms invece del secondo
# che costerebbe avviarlo allora. Il residuo e' comunque un offset comune ai due sensori,
# quindi si cancella nella differenza appaiata `latenza_delta_s`.
class Segnale:
    """Annuncio vocale a bassa latenza, con ripiego sul buzzer se SAPI non parte."""

    def __init__(self):
        self.proc = None
        try:
            self.proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", "-"],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, text=True, bufsize=1)
            self.proc.stdin.write("$v = New-Object -ComObject SAPI.SpVoice\n")
            self.proc.stdin.write("$v.Volume = 100\n")
            self.proc.stdin.flush()
        except Exception as e:
            self.proc = None
            # Il ripiego va DETTO: un fallback silenzioso ha gia' fatto perdere tempo
            sys.stderr.write(f"[voce non disponibile ({type(e).__name__}), uso i bip: "
                             f"grave = primo segnale, acuto = evento]\n")
            sys.stderr.flush()

    def di(self, parola, freq_ripiego):
        if self.proc is None:
            if winsound is not None:
                threading.Thread(target=winsound.Beep, args=(freq_ripiego, 300),
                                 daemon=True).start()
            return
        try:
            self.proc.stdin.write(f"$v.Speak('{parola}', 1)\n")   # 1 = asincrono
            self.proc.stdin.flush()
        except Exception:
            pass

    def chiudi(self):
        if self.proc is not None:
            try:
                self.proc.stdin.close()
                self.proc.terminate()
            except Exception:
                pass


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
    parser.add_argument("--evento", choices=("entra", "esci"), default="entra",
                        help="cosa deve fare il soggetto all'istante dell'evento "
                             "(default: entra, cioe' il Test 2.1). Il primo segnale "
                             "annuncia automaticamente l'azione opposta, cosi' i due "
                             "non possono essere scambiati")
    parser.add_argument("--beep-at", type=float, default=None, metavar="SEC",
                        help="emette un beep grave all'inizio dell'acquisizione e un beep "
                             "acuto SEC secondi dopo la prima riga di dati: e' il momento "
                             "in cui il soggetto deve entrare (test 2.1) o uscire (2.2). "
                             "Passare lo stesso SEC ad analizza_test.py come --event-time "
                             "o --release-time")

    args = parser.parse_args()

    parola_evento = args.evento
    parola_inizio = "esci" if parola_evento == "entra" else "entra"
    segnale = Segnale() if args.beep_at is not None else None

    ser = serial.Serial(args.port, args.baud, timeout=2)
    time.sleep(2)   # reset ESP32; intanto PowerShell finisce di scaldarsi

    start = time.time()
    righe_scritte = 0
    scartate = []

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
                    if len(scartate) < 8:
                        scartate.append(line)
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
                    segnale.di(parola_inizio, 600)
                    sys.stderr.write(f"Acquisizione partita -> '{parola_inizio.upper()}'. "
                                     f"Fra {args.beep_at:.0f} s: '{parola_evento.upper()}'\n")
                    sys.stderr.flush()

            if (args.beep_at is not None and not beep_fatto
                    and time.time() - t_prima_riga >= args.beep_at):
                beep_fatto = True
                segnale.di(parola_evento, 1400)
                sys.stderr.write(f"EVENTO '{parola_evento.upper()}' a "
                                 f"t=+{time.time() - t_prima_riga:.2f} s "
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
            righe_scritte += 1
            print(",".join(map(str, row)))

    # Se non e' stata scritta nessuna riga, il file resta vuoto e senza questo blocco
    # non si capisce perche': "sketch sbagliato caricato sull'ESP32" e "nessun dato" hanno
    # lo stesso aspetto. Mostrare cosa e' arrivato davvero risolve il dubbio in un colpo.
    # (Capitato il 24/08/2026: sull'ESP32 c'era test04_set_gate, il cui menu di testo
    # veniva scartato in silenzio -> CSV di 0 byte.)
    if righe_scritte == 0:
        sys.stderr.write("\n*** NESSUNA RIGA DI DATI SCRITTA: il CSV e' vuoto ***\n")
        if scartate:
            sys.stderr.write("Sulla seriale e' arrivato questo, che non e' un CSV del "
                             "logger:\n")
            for r in scartate[:8]:
                sys.stderr.write(f"    | {r[:100]}\n")
            sys.stderr.write("Probabile causa: sull'ESP32 e' caricato uno sketch diverso "
                             "da firmware/ld2410b_logger.\n")
        else:
            sys.stderr.write("Sulla seriale non e' arrivato NULLA. Controlla: sketch "
                             "caricato, cavo USB, baud (atteso 115200),\n"
                             "e che il Serial Monitor dell'IDE sia chiuso.\n")
        sys.stderr.flush()

    if args.beep_at is not None and not beep_fatto:
        sys.stderr.write("ATTENZIONE: il beep di evento NON e' stato emesso (durata "
                         "troppo breve o nessun dato). Trial da rifare.\n")

    ser.close()
    if segnale is not None:
        segnale.chiudi()

if __name__ == "__main__":
    main()