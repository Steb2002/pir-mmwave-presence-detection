# Bozza tesi — sorgenti LaTeX per Overleaf

Generata il 21/08/2026 dal materiale in `analisi/`, `PIANO_TEST.md`,
`SCALETTA_TESI.md`, `HLK-LD2410x/data/REGISTRO_SESSIONI.md` e `CLAUDE.md`.

## Come caricarla su Overleaf

1. Comprimere **il contenuto** di questa cartella (non la cartella stessa) in uno zip:
   `main.tex`, `capitoli/`, `bib/`, `img/`.
2. Su Overleaf: *New Project → Upload Project* e caricare lo zip.
3. Impostare *Menu → Compiler* su **pdfLaTeX** (il default va bene).
   La bibliografia usa `biblatex` con backend **biber**, che Overleaf gestisce
   automaticamente.
4. Prima compilazione: servono **due passate** perché `cleveref` risolva i
   riferimenti in avanti (Overleaf le fa da solo al secondo clic su *Recompile*).

## Struttura

```
main.tex                            preambolo, ordine dei capitoli
capitoli/00-proposte-titolo.tex     PRIMA PAGINA: proposte di titolo (da eliminare
                                    dopo la scelta)
capitoli/00-frontespizio.tex        frontespizio (titolo provvisorio, da aggiornare)
capitoli/00-sommario.tex            abstract
capitoli/01-introduzione.tex        contesto UPRISE/SAFE, problema, 6 obiettivi
capitoli/02-sensori-stato-arte.tex  O1 — PIR, mmWave, UWB, tabella comparativa
capitoli/03-moduli-e-dati.tex       O2 — LD2410B, LD2420, HC-SR501, piattaforma,
                                    saturazione / canali nulli / coda di presenza
capitoli/04-confronto-sperimentale  O3 — protocollo, risultati, discussione, limiti
capitoli/05-consumo-energetico.tex  O4 — consumi da datasheet, architettura ibrida
capitoli/06-web-ui.tex              O5 — progetto della dashboard
capitoli/07-indice-vitalita.tex     O6 — algoritmo, classi, taratura
capitoli/08-conclusioni.tex         risposta alla domanda di partenza, sviluppi
capitoli/A1-appendice-protocollo    protocollo seriale LD2410B
capitoli/A2-appendice-codice.tex    software realizzato e comandi
bib/tesi.bib                        30 voci, tutte con url + urldate
img/                                vuota: qui vanno figure e screenshot
```

## Cose da fare prima della consegna

Cercare `\todo` nei sorgenti: ogni occorrenza è un punto da completare. Le
macro `\todo{...}` si spengono tutte in un colpo decommentando in `main.tex`:

```latex
\renewcommand{\todo}[1]{}
```

In sintesi, i punti aperti sono:

- **Titolo**: scegliere fra le proposte, aggiornare `00-frontespizio.tex`, poi
  rimuovere la riga `\input{capitoli/00-proposte-titolo}` da `main.tex`.
- **Frontespizio**: verificare la dicitura ufficiale del corso di laurea e il
  nome esatto del relatore; inserire il logo in `img/`.
- **`bib/tesi.bib`**: la voce `callisto2023dt` (paper EDOC 2023) va completata
  con autori esatti, pagine e DOI.
- **Figure**: nessuna figura reale è ancora inserita. Servono almeno lo schema
  di sistema (cap. 1), la foto del setup (cap. 4), un grafico di traccia
  temporale radar vs PIR (cap. 4), lo spettro del respiro (cap. 4) e gli
  screenshot della dashboard (cap. 6).
- **Sezioni marcate *acquisizione in corso*** nel cap. 4: latenze, sotto il
  banco, ostacoli, respiro a metronomo, confronto LD2420. La collocazione e le
  metriche sono già scritte: va inserito solo il risultato.
- **Tabella 4.3** (accuratezza della distanza): completare le righe 2, 3 e 4 con
  i valori puntuali dall'output di `analizza_test.py`.

## Convenzioni adottate nel testo

- Ogni valore nella forma `μ ± σ` è calcolato su 5 trial indipendenti.
- I dati tecnici hanno la fonte citata; le voci del `.bib` marcate PRIMARIA sono
  documenti ufficiali del produttore.
- I risultati non ancora acquisiti sono dichiarati come tali, non anticipati.
- I limiti dello studio sono in una sezione dedicata (§4.13.3), non sparsi.
