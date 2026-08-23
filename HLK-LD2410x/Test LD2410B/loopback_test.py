#!/usr/bin/env python3
"""
Test di loopback per l'adattatore CH340E.
Collega TX e RX dell'adattatore tra loro con un ponticello, poi lancia:
    python loopback_test.py COM3

Se stampa "LOOPBACK OK" l'adattatore riceve correttamente.
Se stampa "NIENTE" TX e RX non sono ponticellati o l'adattatore ha un problema.
"""

import sys
import serial

PORTA = sys.argv[1] if len(sys.argv) > 1 else "COM3"
MSG = b"CIAO-LD2410\n"

with serial.Serial(PORTA, 115200, timeout=1) as ser:
    ser.reset_input_buffer()
    ser.write(MSG)
    ser.flush()
    risposta = ser.read(len(MSG))
    print(f"Inviato:  {MSG}")
    print(f"Ricevuto: {risposta}")
    if risposta == MSG:
        print("\n>>> LOOPBACK OK: l'adattatore trasmette e riceve. Il problema e' lato sensore.")
    elif risposta:
        print("\n>>> Ricevuto qualcosa ma diverso: controlla il ponticello / disturbi.")
    else:
        print("\n>>> NIENTE ricevuto: TX-RX non ponticellati oppure adattatore/driver KO.")
