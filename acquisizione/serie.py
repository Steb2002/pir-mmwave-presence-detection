"""
Esegue una serie di trial consecutivi chiamando acquire.py, per non lanciare a mano
decine di comandi (il Test 1.2 sono 30 acquisizioni: sbagliare l'etichetta del trial
o sovrascrivere un file e' facilissimo).

Esempio: 5 trial da 80 s a 2 m, persona che cammina sul posto (dalla radice del progetto):
    .venv\Scripts\python.exe acquisizione\serie.py --scenario movimento_2m --gt-state moving

Di default RIFIUTA di sovrascrivere file esistenti: serve --force.
Richiede solo la libreria standard (acquire.py ci pensa lui a pyserial).
"""

import argparse
import subprocess
import sys
import threading
import time
from pathlib import Path

# --- Segnali acustici -----------------------------------------------------------
# Sotto il banco non si vede lo schermo: i bip dicono in che fase sei.
#   grave lungo   = trial iniziato, VAI IN POSIZIONE
#   doppio acuto  = transitorio finito, DA QUI SI REGISTRA: stai fermo
#   medio doppio  = trial finito, puoi muoverti
#   scala di tre  = serie completata
#
# NB: si genera un vero tono PCM e lo si riproduce dalla scheda audio.
# winsound.Beep() usa il buzzer di sistema, che su molti PC moderni non e'
# collegato a nulla: sembra funzionare ma non si sente niente (verificato
# sul PC di sviluppo il 22/08/2026).
import io as _io
import math
import struct
import wave

try:
    import winsound
    _AUDIO = True
except ImportError:
    _AUDIO = False

_CACHE = {}


def _wav(freq, ms, volume=0.7, rate=22050):
    """Costruisce in memoria un WAV mono con un tono sinusoidale."""
    chiave = (freq, ms, volume)
    if chiave in _CACHE:
        return _CACHE[chiave]
    n = int(rate * ms / 1000)
    attacco = max(1, int(0.008 * rate))     # rampa per evitare il click
    campioni = bytearray()
    for i in range(n):
        env = min(1.0, i / attacco, (n - i) / attacco)
        campioni += struct.pack("<h", int(32767 * volume * env
                                          * math.sin(2 * math.pi * freq * i / rate)))
    buf = _io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(campioni))
    _CACHE[chiave] = buf.getvalue()
    return _CACHE[chiave]


MUTO = False
MODO = "voce"      # "voce" = sintesi vocale (default), "tono" = sinusoide, "sistema" = wav

# La sintesi vocale e' il metodo che funziona su questa macchina: winsound.Beep() pilota
# il buzzer di sistema (assente sui PC moderni) e PlaySound finisce sull'uscita audio
# predefinita, che qui e' un dispositivo virtuale muto. SAPI invece parla e si sente.
# Verificato il 22/08/2026.
_FRASI = {
    "via":      "vai in posizione",
    "fermo":    "stai fermo, registrazione utile iniziata",
    "fine":     "trial finito",
    "completa": "serie completata",
}
_SISTEMA = {
    "via":      r"C:\Windows\Media\Windows Balloon.wav",
    "fermo":    r"C:\Windows\Media\Alarm01.wav",
    "fine":     r"C:\Windows\Media\Windows Notify.wav",
    "completa": r"C:\Windows\Media\tada.wav",
}
_NOTE = {
    "via":      [(440, 400)],
    "fermo":    [(1320, 150), (1320, 150)],
    "fine":     [(880, 150), (880, 150)],
    "completa": [(660, 180), (880, 180), (1320, 350)],
}


def _parla(testo):
    # PowerShell impiega ~1 s ad avviarsi: irrilevante per i nostri annunci, e in cambio
    # non servono dipendenze (pywin32/comtypes non sono installati).
    testo = "".join(c for c in testo if c.isalnum() or c in " ,.àèéìòù")
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(New-Object -ComObject SAPI.SpVoice).Speak('{testo}')"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
    except Exception:
        pass


def segnale(nome, testo=None):
    """Emette il segnale logico: via | fermo | fine | completa."""
    if MUTO:
        return
    if MODO == "voce":
        _parla(testo or _FRASI[nome])
        return
    if not _AUDIO:
        return
    if MODO == "sistema":
        import os
        p = _SISTEMA.get(nome)
        if not p or not os.path.exists(p):
            p = r"C:\Windows\Media\Alarm01.wav"
        try:
            winsound.PlaySound(p, winsound.SND_FILENAME | winsound.SND_SYNC)
        except Exception:
            pass
        return
    for freq, ms in _NOTE[nome]:
        try:
            winsound.PlaySound(_wav(freq, ms), winsound.SND_MEMORY | winsound.SND_SYNC)
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenario", required=True,
                    help="nome scenario, es. movimento_2m (la distanza nel nome viene "
                         "riconosciuta dallo script di analisi)")
    ap.add_argument("--port", default="COM3")
    ap.add_argument("--duration", type=int, default=80,
                    help="durata di OGNI trial in s (default 80: 20 s per raggiungere "
                         "la posizione + 60 s utili)")
    ap.add_argument("--transitorio", type=int, default=20,
                    help="secondi iniziali che servono a raggiungere la posizione e che "
                         "andranno scartati in analisi (default 20; per posizioni "
                         "scomode come 'sotto il banco' alzarlo a 40)")
    ap.add_argument("--trials", type=int, default=5)
    ap.add_argument("--pausa", type=int, default=12,
                    help="pausa tra i trial, in s (serve a far ripartire il radar da "
                         "uno stato pulito)")
    ap.add_argument("--gt-presence", type=int, default=1)
    ap.add_argument("--gt-state", default="moving")
    ap.add_argument("--beep-at", type=float, default=None, metavar="SEC",
                    help="test 2.1/2.2: beep di evento a SEC secondi dalla prima riga di "
                         "dati (vedi acquire.py --beep-at). Lo stesso SEC va passato ad "
                         "analizza_test.py come --event-time o --release-time")
    ap.add_argument("--force", action="store_true", help="sovrascrivi file esistenti")
    ap.add_argument("--muto", action="store_true", help="niente segnali acustici")
    ap.add_argument("--evento", choices=("entra", "esci"), default="entra",
                    help="con --beep-at: cosa deve fare il soggetto all'istante "
                         "dell'evento. 'entra' per il Test 2.1, 'esci' per il 2.2. "
                         "Il primo annuncio e' automaticamente l'azione opposta")
    ap.add_argument("--prova-suono", action="store_true",
                    help="riproduce i quattro segnali e esce, per regolare il volume")
    ap.add_argument("--suono", choices=("voce", "tono", "sistema"), default="voce",
                    help="voce = sintesi vocale (default, l'unica che si sente su questo "
                         "PC); tono = sinusoide generata; sistema = suoni WAV di Windows")
    args = ap.parse_args()

    global MUTO, MODO
    MUTO = args.muto
    MODO = args.suono

    if args.prova_suono:
        print(f"(modalita' suono: {MODO})")
        print("1/4 trial iniziato, vai in posizione");  segnale("via")
        print("2/4 transitorio finito, STAI FERMO");    segnale("fermo")
        print("3/4 trial finito, puoi muoverti");       segnale("fine")
        print("4/4 serie completata");                  segnale("completa")
        return

    qui = Path(__file__).parent
    dati = qui.parent / "data"   # data/ nella radice del progetto, accanto ad acquisizione/
    dati.mkdir(exist_ok=True)

    # Controllo PRIMA di iniziare: meglio fermarsi ora che a metà serie
    attesi = [dati / f"{args.scenario}_T{i:02d}.csv" for i in range(1, args.trials + 1)]
    esistenti = [f for f in attesi if f.exists()]
    if esistenti and not args.force:
        print("Questi file esistono gia':")
        for f in esistenti:
            print(f"  {f.name}")
        sys.exit("Cambia --scenario oppure usa --force per sovrascriverli.")

    utili = args.duration - args.transitorio
    print(f"Serie '{args.scenario}': {args.trials} trial da {args.duration} s "
          f"(~{utili} s utili ciascuno), pausa {args.pausa} s")
    print(f"Tempo totale stimato: {(args.duration + args.pausa) * args.trials / 60:.0f} min\n")

    for i in range(1, args.trials + 1):
        out = dati / f"{args.scenario}_T{i:02d}.csv"
        print(f"===== TRIAL {i}/{args.trials} -> {out.name} =====")
        if args.beep_at is not None:
            # Nei test di latenza il riferimento non e' un tempo dall'avvio del comando ma
            # il beep: dire "vai in posizione entro N s" sarebbe fuorviante.
            print(f"      BEEP GRAVE = via; BEEP ACUTO (fra {args.beep_at:.0f} s) = "
                  f"esegui l'evento ADESSO")
            avviso = None      # con --beep-at i bip li emette acquire.py
        else:
            print(f"      VAI IN POSIZIONE (hai ~{args.transitorio} s), "
                  f"poi resta la' fino alla fine")
            segnale("via")
            # avviso a fine transitorio: da qui in poi i dati contano davvero
            avviso = threading.Timer(args.transitorio, segnale, ["fermo"])
            avviso.daemon = True
            avviso.start()
        cmd = [
            sys.executable, str(qui / "acquire.py"),
            "--port", args.port,
            "--duration", str(args.duration),
            "--output", str(out),
            "--scenario", args.scenario,
            "--trial", f"T{i:02d}",
            "--ground_truth_presence", str(args.gt_presence),
            "--ground_truth_state", args.gt_state,
        ]
        if args.beep_at is not None:
            cmd += ["--beep-at", str(args.beep_at), "--evento", args.evento]
        # stdout soppresso (sono le righe di dati), stderr NO: e' dove acquire.py scrive
        # a che istante ha suonato il beep. Quel numero e' il riferimento temporale del
        # trial, va visto.
        esito = subprocess.run(cmd, stdout=subprocess.DEVNULL)

        if avviso is not None:
            avviso.cancel()
        segnale("fine", f"trial {i} finito")   # puoi muoverti

        if esito.returncode != 0:
            sys.exit(f"\nacquire.py ha restituito {esito.returncode} sul trial {i}. "
                     f"Serie interrotta: i trial gia' fatti restano validi.")

        righe = sum(1 for _ in out.open(encoding="utf-8", errors="ignore")) - 1
        print(f"      fatto: {righe} righe in {out.name}")
        if righe < args.duration * 4:   # atteso ~5 Hz
            print(f"      ATTENZIONE: attese ~{args.duration * 5} righe, il file e' corto")

        if i < args.trials:
            print(f"      pausa {args.pausa} s - muoviti/fermati per resettare lo stato")
            time.sleep(args.pausa)
        print()

    segnale("completa")                          # serie completata
    print(f"Serie completata. Analisi:")
    print(rf"  .venv\Scripts\python.exe analisi\analizza_test.py "
          rf"data\{args.scenario}_*.csv --salta-inizio {args.transitorio}")


if __name__ == "__main__":
    main()
