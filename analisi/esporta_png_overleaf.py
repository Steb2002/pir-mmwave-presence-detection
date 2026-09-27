"""Converte le figure PDF di overleaf/figures in PNG con il nome usato nel LaTeX di Overleaf.

Regola del nome: fig27_geometrie.pdf -> Geometrie.png (tolto "figNN_", iniziale maiuscola).
Converte solo le figure citate da un \\includegraphics nei .tex (in forma figures/figNN_nome
oppure Nome); con --aggiorna-tex riscrive anche i percorsi nei .tex nella forma "Nome".
Usa pdftoppm di MiKTeX a 300 dpi. Da rilanciare dopo ogni rigenerazione delle figure.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

O = Path(__file__).resolve().parent.parent / 'overleaf'
F = O / 'figures'
PDFTOPPM = Path(os.environ['LOCALAPPDATA']) / 'Programs/MiKTeX/miktex/bin/x64/pdftoppm.exe'
DPI = 300


def nuovo_nome(stem):
    base = re.sub(r'^fig\d+_', '', stem)
    return base[:1].upper() + base[1:]


def main():
    aggiorna = '--aggiorna-tex' in sys.argv
    usati = set()
    for tex in O.glob('*.tex'):
        for m in re.finditer(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', tex.read_text(encoding='utf-8')):
            usati.add(Path(m.group(1)).stem)
    fatti = []
    for pdf in sorted(F.glob('fig*.pdf')):
        n = nuovo_nome(pdf.stem)
        if pdf.stem not in usati and n not in usati:
            continue
        out = F / n
        subprocess.run([str(PDFTOPPM), '-png', '-r', str(DPI), '-singlefile', str(pdf), str(out)], check=True)
        fatti.append((pdf.name, n + '.png'))
        print(f'  {pdf.name:40s} -> {n}.png')
    if aggiorna:
        for tex in O.glob('*.tex'):
            s = tex.read_text(encoding='utf-8')
            s2 = re.sub(r'(\\includegraphics(?:\[[^\]]*\])?\{)figures/(fig\d+_[^}]+)\}',
                        lambda m: m.group(1) + nuovo_nome(m.group(2)) + '}', s)
            if s2 != s:
                tex.write_text(s2, encoding='utf-8')
                print('  aggiornato', tex.name)
    print(len(fatti), 'PNG in', F)


if __name__ == '__main__':
    main()
