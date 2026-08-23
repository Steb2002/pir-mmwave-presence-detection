#!/usr/bin/env python3
"""
Diagnostica cruda per HLK-LD2420 via adattatore CH340E (collegamento diretto al PC).

ATTENZIONE: il LD2420 si alimenta a 3.3V, NON 5V. Usare l'uscita 3.3V del CH340E.

Il pin di uscita seriale (TX) e il baud rate dipendono dalla versione firmware:
  - firmware >= 1.5.3 : TX = Pin 3 (OT1), baud 115200
  - firmware <= 1.5.2 : TX = Pin 5 (OT2), baud 256000
Non sapendo il firmware, questo script prova entrambi i baud e stampa i byte grezzi.
Procedura: collega prima OT1 al RX dell'adattatore e lancia; se "Nessun byte",
sposta il filo su OT2 e rilancia.

Uso:
    python ld2420_diag.py COM3
"""

import sys
import time
import serial

PORTA = sys.argv[1] if len(sys.argv) > 1 else "COM3"
BAUD_DA_PROVARE = [115200, 256000]   # i due baud possibili del LD2420

for baud in BAUD_DA_PROVARE:
    print(f"\n===== Provo {PORTA} @ {baud} baud per 4 secondi (muovi la mano!) =====")
    try:
        with serial.Serial(PORTA, baud, timeout=0.2) as ser:
            fine = time.time() + 4
            totale = bytearray()
            while time.time() < fine:
                chunk = ser.read(256)
                if chunk:
                    totale += chunk
            if totale:
                print(f"  Ricevuti {len(totale)} byte. Primi 96 in hex:")
                print("  " + totale[:96].hex(" "))
                # prova a mostrarli anche come testo: alcune modalita' del 2420 sono ASCII
                testo = "".join(chr(b) if 32 <= b < 127 else "." for b in totale[:96])
                print(f"  Come testo: {testo}")
                # header dati binario tipico famiglia HLK
                if b"\xf4\xf3\xf2\xf1" in totale:
                    print("  >>> Trovato header dati binario (f4 f3 f2 f1) <<<")
                if b"\xfd\xfc\xfb\xfa" in totale:
                    print("  >>> Trovato header comando/ACK (fd fc fb fa) <<<")
                print(f"  >>> ARRIVANO DATI a {baud} baud: questo e' il pin/baud giusto <<<")
            else:
                print("  Nessun byte ricevuto.")
    except serial.SerialException as e:
        print(f"  Errore: {e}")
        break

print("\nSe entrambi i baud danno 'Nessun byte':")
print("  1) sposta il filo dati sull'altro pin di uscita (OT1 <-> OT2) e rilancia;")
print("  2) verifica 3.3V tra Pin1 e Pin2 del sensore;")
print("  3) se ancora nulla, il LD2420 potrebbe non trasmettere di default in questo")
print("     firmware: si passa al tool HiLink (Test 0.5) per leggere versione e modalita'.")
