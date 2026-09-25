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
- **figure da fare a mano** (le 22 generate sono in `figures/`, rigenerabili con
  `python analisi/rigenera_tutto.py`): schema del sistema nel cap. 1, foto del
  setup, screenshot della dashboard nel cap. 6 — elenco in `figures/LEGGIMI.txt`;
- **`bib/tesi.bib`**: completare la voce `callisto2023dt` (autori, pagine, DOI);
- prima della stampa: `\renewcommand{\todo}[1]{}` in `main.tex` per spegnere le
  note rosse.

I capitoli sono completi (settembre 2026): il 4 copre le fasi 0-8 e il secondo
radar, il 6 la web UI realizzata e verificata, il 7 l'indice di vitalità tarato,
validato e portato a bordo.

## Compilazione in locale (fatta il 13/09/2026)

Il documento compila **senza errori** con MiKTeX 25.12 (installato in modalità
utente con `winget install MiKTeX.MiKTeX --scope user`, pacchetti mancanti
scaricati da soli alla prima passata). Catena, dalla cartella `tesi-unicam/`,
con `B` una cartella di build fuori dal repo:

```
pdflatex -interaction=nonstopmode -shell-escape -output-directory=B main.tex
biber --input-directory=. B/main
makeindex -s B/main.ist -t B/main.glg-abr -o B/main.gls-abr B/main.glo-abr
pdflatex ... (altre due passate)
```

Esito: 135 pagine, zero riferimenti o citazioni non risolti, zero avvisi LaTeX,
glossario e bibliografia popolati. Il PDF sta in `main.pdf` (non versionato: si
rifà). I tre punti temuti (enumitem con paralist, verbatim nel float, glossario)
non hanno dato problemi; quelli veri erano di impaginazione, e sono già corretti:

- la classe non imposta `\emergencystretch`: le righe con nomi in `\texttt`
  uscivano nel margine (33 sconfinamenti); ora è 3 em in `main.tex`;
- una figura a tutta larghezza seguita subito da una tabella sovrappone le due
  didascalie nel margine (la didascalia di `figure*` sta sotto, quella di `table`
  accanto): nel capitolo 4 le tabelle precedono ora le figure;
- una `tabularx` non spezzabile più alta della pagina (appendice B) tagliava le
  righe finali: divisa in due;
- lo schema della dashboard è un `lstlisting` (Listato 6.2), non più un
  `verbatim` dentro `figure*`;
- gli URL della bibliografia si spezzano grazie ai `biburl*penalty`.

Restano tre sconfinamenti sotto i 7 pt (uno è la nota `\todo` dello screenshot).

### Nota del 20/09/2026: label dei float e cartella di build

- I `\label` dentro `figure`/`table` puntavano alla **sezione** e non alla figura
  (`\cref{fig:x}` stampava "sezione 4.1"): con il kernel attuale il `\label` dentro il
  float non viene catturato da tufte-book e viene scritto prima che la didascalia
  differita incrementi il contatore. Corretto con una patch nel preambolo di
  `main.tex` (`\xpatchcmd{\@tufte@float}`) che ripristina la cattura. Il `\label` va
  messo **dopo** `\caption`, uno solo per float (tufte ne conserva uno) e mai dentro
  l'argomento di `\caption`.
- Le didascalie dei float a tutta larghezza finiscono nel margine del lato in cui il
  float e' stato *letto*, non di quello in cui e' stampato: per i float differiti alla
  pagina dopo si forza il lato con `\forcerectofloat` (pagina impari) o
  `\forceversofloat` (pagina pari) subito dopo `\begin{figure*}`. Il capitolo 4 li ha
  gia'; se la paginazione cambia vanno ricontrollati nel PDF.
- Compilare sempre con `-output-directory=B`: i file ausiliari lasciati nella cartella
  di lavoro (`main.aux`, `main.toc`, ...) vengono letti al posto di quelli in `B/` e
  producono riferimenti non risolti fantasma. `B/` e' nel `.gitignore`.
