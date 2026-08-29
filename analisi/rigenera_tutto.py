#!/usr/bin/env python3
"""
Rigenera tutti i materiali derivati dai dati sperimentali, in un colpo solo.

    python analisi/rigenera_tutto.py

Esegue in ordine:
  1. analisi/grafici_tesi.py    -> tesi-unicam/figures/*.pdf + *.png   (13 figure)
  2. analisi/esporta_excel.py   -> analisi/dati_tesi.xlsx              (11 fogli)
  3. analisi/genera_pagina.py   -> RIEPILOGO_INCONTRO.html
  4. stampa headless            -> RIEPILOGO_INCONTRO.pdf              (A4)

L'ordine e' obbligato: la pagina incorpora i PNG del passo 1 e il PDF stampa la
pagina del passo 3. Lanciando solo un pezzo si rischia di mescolare figure nuove
con testo vecchio, o viceversa.

Opzioni:
  --salta-figure   riusa i PNG gia' presenti (utile se hai cambiato solo il testo
                   della pagina: il passo 1 e' il piu' lento, ~10 s)
  --senza-pdf      si ferma all'HTML, senza cercare un browser

Tutte le cifre vengono ricalcolate dai CSV grezzi in HLK-LD2410x/data/ a ogni
esecuzione: non esistono numeri copiati a mano in nessuno dei tre script.
"""
import argparse
import os
import shutil
import tempfile
import subprocess
import sys
import time
from pathlib import Path

QUI = Path(__file__).resolve().parent
RADICE = QUI.parent
HTML = RADICE / "RIEPILOGO_INCONTRO.html"
PDF = RADICE / "RIEPILOGO_INCONTRO.pdf"

MODULI = {
    "matplotlib": "grafici",
    "numpy": "grafici",
    "openpyxl": "Excel",
    "PIL": "pagina HTML",
}


def controlla_dipendenze():
    mancanti = []
    for modulo in MODULI:
        try:
            __import__(modulo)
        except ImportError:
            mancanti.append(modulo)
    if mancanti:
        pacchetti = " ".join("pillow" if m == "PIL" else m for m in mancanti)
        sys.exit(f"Mancano dei pacchetti Python: {', '.join(mancanti)}\n"
                 f"Installali con:\n\n    python -m pip install {pacchetti}\n")


def passo(numero, titolo, script):
    print(f"\n[{numero}/4] {titolo}")
    t0 = time.time()
    esito = subprocess.run([sys.executable, str(QUI / script)], cwd=str(RADICE))
    if esito.returncode != 0:
        sys.exit(f"\nFALLITO al passo {numero} ({script}). "
                 f"Niente e' stato sovrascritto dai passi successivi.")
    print(f"      ({time.time() - t0:.0f} s)")


def trova_browser():
    """Chrome o Edge, per la stampa headless. Ritorna il percorso o None."""
    candidati = []
    for var in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        base = os.environ.get(var)
        if base:
            candidati += [
                Path(base) / "Google/Chrome/Application/chrome.exe",
                Path(base) / "Microsoft/Edge/Application/msedge.exe",
            ]
    for p in candidati:
        if p.is_file():
            return str(p)
    for nome in ("chrome", "google-chrome", "chromium", "msedge"):
        trovato = shutil.which(nome)
        if trovato:
            return trovato
    return None


def stampa_pdf():
    browser = trova_browser()
    if not browser:
        print("\n[4/4] PDF SALTATO: non ho trovato ne' Chrome ne' Edge.")
        print(f"      Puoi comunque aprire {HTML.name} e stampare in PDF a mano.")
        return False

    print(f"\n[4/4] Stampa in PDF con {Path(browser).stem}")
    t0 = time.time()
    # Profilo usa-e-getta: evita di litigare con una finestra di Chrome gia' aperta.
    # Sta fuori dal progetto apposta, cosi' se qualcosa va storto non resta una
    # cartella spuria che finirebbe in un "git add -A".
    profilo = Path(tempfile.mkdtemp(prefix="chrome-stampa-"))
    cmd = [
        browser,
        "--headless=new", "--disable-gpu", "--no-sandbox",
        "--no-pdf-header-footer",
        f"--user-data-dir={profilo}",
        # Serve tempo perche' i font di Google Fonts arrivino: senza, il PDF
        # esce con i font di ripiego e l'impaginazione cambia.
        "--virtual-time-budget=20000",
        f"--print-to-pdf={PDF}",
        HTML.as_uri(),
    ]
    esito = subprocess.run(cmd, capture_output=True, text=True)
    shutil.rmtree(profilo, ignore_errors=True)

    if esito.returncode != 0 or not PDF.is_file():
        print("      FALLITO. Output del browser:")
        print((esito.stderr or esito.stdout or "(nessun messaggio)").strip()[-800:])
        return False

    pagine = ""
    try:
        import pypdfium2
        pagine = f", {len(pypdfium2.PdfDocument(str(PDF)))} pagine"
    except Exception:
        pass
    print(f"  ok  {PDF.name}  ({PDF.stat().st_size/1024/1024:.2f} MB{pagine})")
    print(f"      ({time.time() - t0:.0f} s)")
    return True


def main():
    ap = argparse.ArgumentParser(
        description="Rigenera figure, Excel, pagina di riepilogo e PDF dai CSV.")
    ap.add_argument("--salta-figure", action="store_true",
                    help="riusa i PNG gia' presenti in tesi-unicam/figures/")
    ap.add_argument("--senza-pdf", action="store_true",
                    help="si ferma all'HTML, senza cercare un browser")
    args = ap.parse_args()

    # Senza questo, quando l'output e' rediretto le righe del padre restano nel
    # buffer e compaiono DOPO quelle dei sotto-processi: l'ordine dei passi
    # risulta incomprensibile.
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except AttributeError:
        pass

    controlla_dipendenze()
    print(f"Progetto: {RADICE}")
    t0 = time.time()

    if args.salta_figure:
        print("\n[1/4] Figure: saltate su richiesta, si riusano quelle esistenti")
    else:
        passo(1, "Figure della tesi (PDF vettoriale + PNG 300 dpi)", "grafici_tesi.py")

    passo(2, "Foglio Excel con tutti i trial", "esporta_excel.py")
    passo(3, "Pagina di riepilogo HTML", "genera_pagina.py")

    pdf_ok = False if args.senza_pdf else stampa_pdf()
    if args.senza_pdf:
        print("\n[4/4] PDF saltato su richiesta")

    print(f"\nFatto in {time.time() - t0:.0f} s. Prodotti:")
    print(f"  tesi-unicam/figures/   13 figure (.pdf per LaTeX, .png per slide)")
    print(f"  analisi/dati_tesi.xlsx foglio con tutti i trial + grafici Excel")
    print(f"  {HTML.name}   pagina di riepilogo")
    if pdf_ok:
        print(f"  {PDF.name}    la stessa pagina, stampabile")


if __name__ == "__main__":
    main()
