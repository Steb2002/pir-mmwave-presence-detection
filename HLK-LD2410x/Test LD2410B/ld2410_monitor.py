#!/usr/bin/env python3
"""
Serial monitor per sensore mmWave LD2410B collegato via adattatore CH340E.

Il sensore comunica in UART a 256000 baud e invia in continuo dei frame
"report". Questo script apre la porta COM (auto-detect del CH340), legge i
frame, li decodifica e stampa lo stato del target e le distanze.

Uso:
    pip install pyserial
    python ld2410_monitor.py            # auto-detect porta CH340
    python ld2410_monitor.py COM5       # porta forzata a mano
"""

import sys
import serial
from serial.tools import list_ports

BAUD = 256000                     # baud rate di default del LD2410B
HEADER = b"\xf4\xf3\xf2\xf1"      # inizio frame report
FOOTER = b"\xf8\xf7\xf6\xf5"      # fine frame report

STATI = {
    0x00: "nessun target",
    0x01: "target in movimento",
    0x02: "target fermo",
    0x03: "movimento + fermo",
}


def trova_porta():
    """Cerca una porta seriale che sembri un CH340."""
    for p in list_ports.comports():
        descr = f"{p.description} {p.manufacturer or ''}".lower()
        if "ch340" in descr or "ch34" in descr or "usb-serial" in descr:
            return p.device
    # fallback: se c'è una sola porta, usa quella
    porte = list_ports.comports()
    if len(porte) == 1:
        return porte[0].device
    return None


def leggi_uint16_le(dati, offset):
    """Legge un intero a 16 bit little-endian."""
    return dati[offset] | (dati[offset + 1] << 8)


def decodifica(dati):
    """
    Decodifica il payload di un frame report.
    Layout (modalità base):
      [0]    tipo dato (0x02 base, 0x01 engineering)
      [1]    head 0xAA
      [2]    stato target
      [3:5]  distanza target in movimento (cm)
      [5]    energia movimento
      [6:8]  distanza target fermo (cm)
      [8]    energia fermo
      [9:11] distanza di rilevamento (cm)
    """
    if len(dati) < 11 or dati[1] != 0xAA:
        return None
    stato = dati[2]
    return {
        "stato": STATI.get(stato, f"sconosciuto ({stato:#04x})"),
        "dist_movimento": leggi_uint16_le(dati, 3),
        "energia_movimento": dati[5],
        "dist_fermo": leggi_uint16_le(dati, 6),
        "energia_fermo": dati[8],
        "dist_rilevamento": leggi_uint16_le(dati, 9),
    }


def main():
    porta = sys.argv[1] if len(sys.argv) > 1 else trova_porta()
    if not porta:
        print("Porta non trovata. Passa la COM a mano, es: python ld2410_monitor.py COM5")
        print("Porte disponibili:")
        for p in list_ports.comports():
            print(f"  {p.device} - {p.description}")
        sys.exit(1)

    print(f"Apro {porta} a {BAUD} baud... (Ctrl+C per uscire)\n")

    with serial.Serial(porta, BAUD, timeout=1) as ser:
        buffer = bytearray()
        while True:
            buffer += ser.read(ser.in_waiting or 1)

            # cerca frame completi header...footer nel buffer
            while True:
                i = buffer.find(HEADER)
                if i < 0:
                    # niente header: tieni solo la coda per non gonfiare
                    del buffer[:-3]
                    break
                j = buffer.find(FOOTER, i + 4)
                if j < 0:
                    del buffer[:i]   # header trovato ma frame incompleto: aspetta
                    break

                # payload = tra header+lunghezza(2 byte) e footer
                payload = bytes(buffer[i + 6 : j])
                del buffer[: j + 4]

                info = decodifica(payload)
                if info:
                    print(
                        f"{info['stato']:<20} | "
                        f"mov: {info['dist_movimento']:>4} cm (E{info['energia_movimento']:>3}) | "
                        f"fermo: {info['dist_fermo']:>4} cm (E{info['energia_fermo']:>3}) | "
                        f"rilev: {info['dist_rilevamento']:>4} cm"
                    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nUscita.")
    except serial.SerialException as e:
        print(f"Errore seriale: {e}")
