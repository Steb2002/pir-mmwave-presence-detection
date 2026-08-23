#!/usr/bin/env python3
"""
Diagnostica cruda per LD2410B via CH340E.
Prova diversi baud rate e stampa i byte grezzi che arrivano, in esadecimale.
Serve a capire se il sensore trasmette e a quale baud.

Uso:
    python ld2410_diag.py COM3
"""

import sys
import time
import serial

PORTA = sys.argv[1] if len(sys.argv) > 1 else "COM3"
BAUD_DA_PROVARE = [256000, 115200, 9600, 57600, 38400]

for baud in BAUD_DA_PROVARE:
    print(f"\n===== Provo {PORTA} @ {baud} baud per 3 secondi =====")
    try:
        with serial.Serial(PORTA, baud, timeout=0.2) as ser:
            fine = time.time() + 3
            totale = bytearray()
            while time.time() < fine:
                chunk = ser.read(256)
                if chunk:
                    totale += chunk
            if totale:
                print(f"  Ricevuti {len(totale)} byte. Primi 64 in hex:")
                print("  " + totale[:64].hex(" "))
                if b"\xf4\xf3\xf2\xf1" in totale:
                    print("  >>> Trovato header LD2410 (f4 f3 f2 f1): QUESTO E' IL BAUD GIUSTO <<<")
            else:
                print("  Nessun byte ricevuto.")
    except serial.SerialException as e:
        print(f"  Errore: {e}")
        break
