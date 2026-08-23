# Tesi — versione sul template UNICAM

Porting della bozza sul template **"(Unofficial) Unicam Template for Thesis"** di
Matteo Belenchia (LPPL 1.3c), classe `unicam-diss` basata su `tufte-book`.

La versione precedente, sulla classe standard `report`, resta in `../tesi/` come
riserva: compila e ha lo stesso testo.

## Come caricarla su Overleaf

1. Comprimere **il contenuto** di questa cartella (non la cartella stessa).
2. Overleaf: *New Project → Upload Project*.
3. *Menu → Compiler* = **pdfLaTeX**. Bibliografia con biblatex + biber
   (già configurata dalla classe), glossario con `glossaries-extra`.
4. Servono **due o tre passate**: cleveref e il glossario si assestano al
   secondo giro.

## Struttura

```
main.tex                        preambolo e ordine dei contenuti
unicam-diss.cls                 classe del template, NON modificata
frontmatter/proposte-titolo.tex prima pagina di lavoro con i titoli proposti
frontmatter/titlepage.tex       frontespizio, adattato alla laurea triennale
frontmatter/colophon.tex        colophon
frontmatter/abstract.tex        sommario (ambiente della classe)
frontmatter/indici.tex          indice, elenco figure, elenco tabelle
capitoli/01..08, A1, A2         gli otto capitoli e le due appendici
backmatter/abbreviazioni.tex    23 sigle per l'elenco delle abbreviazioni
bib/tesi.bib                    28 voci, tutte citate
figures/                        vuota: vedi figures/LEGGIMI.txt
```

## Cosa è cambiato rispetto alla versione su `report`

Il testo dei capitoli è lo stesso. Le modifiche sono strutturali, imposte dalla
classe.

**Preambolo.** La classe carica già geometry, setspace, fancyhdr, hyperref,
xcolor, inputenc, fontenc, titlesec, amsmath, biblatex, glossaries-extra e i
font: ricaricarli darebbe *Option clash*, quindi sono stati rimossi. Restano
solo gli undici pacchetti che mancano davvero: babel, csquotes, booktabs,
tabularx, array, multirow, enumitem, gensymb, eurosym, listings, cleveref.
Rimossi anche `caption` e `subcaption`, incompatibili con tufte (la classe
applica le proprie patch a `\@caption`).

**Tabelle e figure a piena larghezza.** Il blocco di testo della classe è di
125 mm su 210, perché i restanti 50 mm sono il margine per le note laterali.
Tutte e 19 le tabelle e l'unica figura sono state convertite in float
`table*`/`figure*`, che occupano 180 mm; i 13 `tabularx` passano da `\textwidth`
a `\linewidth` per adeguarsi. Glossario e bibliografia usano
`multipagefullwidth`, l'ambiente della classe per il testo largo su più pagine.

**Sottosezioni numerate.** La classe imposta `secnumdepth=1` e definisce
`\titleformat{\subsection}` con il campo del numero vuoto: le sottosezioni non
sarebbero numerate. Il documento ha molte sottosezioni richiamate con `\cref`,
che senza numerazione punterebbero al numero della sezione — riferimenti
sbagliati, non errori visibili. Nel preambolo si alza a 2 `secnumdepth` e
`tocdepth` e si ridefinisce il titolo con il numero. **È l'unico punto in cui il
comportamento del template viene alterato**: se il relatore preferisce il
template intatto, va rimosso quel blocco e vanno riformulati a mano i rimandi
alle sottosezioni.

**Italiano.** `italian` è passata come opzione della classe, non solo a babel:
la classe carica biblatex da sé, prima che babel sia disponibile, e senza
l'opzione globale la bibliografia resterebbe in inglese.

**Parti rimosse dal template.** Le divisioni `\part{Prologue}` /
`\part{Epilogue}`, la pagina *Declaration* (il testo è cablato nella classe e
parla di dottorato), *List of Publications*, *List of Algorithms*, l'elenco dei
simboli e i ringraziamenti. Il logo `Logo_ScuDo.png` non è stato copiato:
riguarda la School of Advanced Studies.

## Cosa resta da fare

Cercare `\todo` nei sorgenti. In sintesi:

- **titolo**: scegliere fra le proposte, aggiornare `\title` in
  `frontmatter/titlepage.tex`, poi togliere da `main.tex` la riga
  `\input{frontmatter/proposte-titolo}`;
- **frontespizio**: logo UNICAM, dicitura ufficiale del corso, eventuale
  matricola;
- **figure**: nessuna è ancora inserita, elenco in `figures/LEGGIMI.txt`;
- **`bib/tesi.bib`**: completare la voce `callisto2023dt` (autori, pagine, DOI);
- **capitolo 4**: le sezioni marcate *acquisizione in corso* (latenze, sotto il
  banco, ostacoli, respiro a metronomo, LD2420) e le righe 2–4 della tabella
  sull'accuratezza della distanza;
- prima della stampa: `\renewcommand{\todo}[1]{}` in `main.tex` per spegnere le
  note rosse.

## Punti da verificare alla prima compilazione

Non ho potuto compilare in locale (nessuna installazione LaTeX su questa
macchina), quindi questi tre sono i candidati più probabili a dare noie:

1. **`enumitem` con `paralist`** — la classe carica paralist, che ridefinisce
   gli elenchi. Il documento ha 46 elenchi con opzioni (`leftmargin`, `itemsep`,
   `label`). Se ci sono conflitti, la via più rapida è togliere le opzioni dai
   singoli elenchi e impostarle una volta con `\setlist`.
2. **`verbatim` dentro `figure*`** — lo schema della dashboard nel capitolo 6.
   Se protesta, si sposta fuori dal float in un blocco `fullwidth`.
3. **glossario** — `glossaries-extra` con `automake` richiede lo shell escape,
   che su Overleaf è attivo. Se l'elenco delle abbreviazioni resta vuoto, basta
   una seconda compilazione.
