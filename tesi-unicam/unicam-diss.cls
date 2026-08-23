\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{unicam-diss}[2025 Unicam Template]
\RequirePackage{silence}
\WarningFilter{xcolor}{Package option `usenames' is obsolete}
\WarningFilter{biblatex}{Patching footnotes failed.}
\WarningFilter*{latex}{Marginpar on page \thepage\space moved}

\RequirePackage{regexpatch}
\RequirePackage{mparhack}


%%% pass all options to tufte-book class
\newif\if@useeuler %\@useeulerfalse
\DeclareOption{euler}{\@useeulertrue}

\newif\if@useconcrete %\@useconcretefalse
\DeclareOption{concrete}{\@useconcretetrue}

\newif\if@dropfolios
\DeclareOption{dropfolio}{\@dropfoliostrue}

\newif\if@sidecite
\DeclareOption{sidecite}{\@sidecitetrue}

\newif\if@symmetric
\DeclareOption{symmetric}{\@symmetrictrue\PassOptionsToClass{\CurrentOption}{tufte-book}}

\DeclareOption{twoside}{\PassOptionsToClass{\CurrentOption}{tufte-book}}

\DeclareOption{a4paper}{\PassOptionsToClass{\CurrentOption}{tufte-book}}

\DeclareOption{b5paper}{\PassOptionsToClass{\CurrentOption}{tufte-book}}

\DeclareOption{sfsidenotes}{\PassOptionsToClass{\CurrentOption}{tufte-book}}

\DeclareOption{justified}{\PassOptionsToClass{\CurrentOption}{tufte-book}}

\ProcessOptions\relax
\LoadClass[nofonts,notoc,nobib,nohyper]{tufte-book}



 % For A4 paper 210mm
\geometry{
  a4paper,
  left=15mm, % left margin
  top=28mm,
  textwidth=125mm,
  marginparsep=5mm, % gutter between main text block and margin notes
  marginparwidth=50mm % width of margin notes
}

% \renewenvironment{fullwidth}
%   {\ifthenelse{\boolean{@tufte@symmetric}}%
%      {\ifthenelse{\boolean{@tufte@changepage}}{\begin{adjustwidth*}{}{-\@tufte@overhang}}{\begin{adjustwidth}[]{}{-\@tufte@overhang}}}%
%      {\begin{adjustwidth}{}{-\@tufte@overhang}}%
%   }%
%   {\ifthenelse{\boolean{@tufte@symmetric}}%
%     {\ifthenelse{\boolean{@tufte@changepage}}{\end{adjustwidth*}}{\end{adjustwidth}}}%
%     {\end{adjustwidth}}%
%   }


\newenvironment{multipagefullwidth}%
{\newgeometry{
  textwidth=180mm,
  marginparwidth=0pt,
  marginparsep=0pt,
  left=15mm,
  top=28mm
}
\fancyheadoffset{0pt}}%
{\restoregeometry}%


% L I N K S 
\RequirePackage[hyperfootnotes=false]{hyperref}
\hypersetup{%
    linktocpage,
    bookmarksdepth = section,
    colorlinks = true,
    linkcolor = Burgundy,
    urlcolor = Burgundy,
    citecolor = Burgundy,
    pdfpagelayout=TwoPageLeft,
}

% C A P T I O N S
% we need to patch caption otherwise tufte-latex will bitch a lot
\xpatchcmd
  {\@caption}% <cmd>
  {\normalsize}% <search>
  {\@tufte@caption@font\@tufte@caption@justification}% <replace>
  {\typeout{caption patched}}% <success>
  {}% <failure

% we patch twice because there are two occurrences to patch
\xpatchcmd
  {\@caption}% <cmd>
  {\@makecaption{\csname  fnum@#1\endcsname}}% <search>
  {\@makecaption{\noindent \csname  fnum@#1\endcsname}}% <replace>
  {\typeout{caption patched}}% <success>
  {\typeout{caption fail}}% <failure

\xpatchcmd
  {\@caption}% <cmd>
  {\@makecaption{\csname  fnum@#1\endcsname}}% <search>
  {\@makecaption{\noindent \csname  fnum@#1\endcsname}}% <replace>
  {\typeout{caption patched}}% <success>
  {\typeout{caption fail}}% <failure


% T A B L E  O F  C O N T E N T S
\RequirePackage[titles]{tocloft}
\setcounter{tocdepth}{1}
\setcounter{secnumdepth}{1}

\definecolor{Burgundy}{RGB}{144, 0, 32}
\renewcommand{\cftpartfont}{%
\bfseries\color{Burgundy}\scshape%
}

\renewcommand{\cftchapfont}{%
\scshape\MakeTextLowercase%
}
% Width for chapter numbers
\setlength{\cftchapnumwidth}{2em}
% Indentation for section numbers
\setlength{\cftsecindent}{2em}
% Width for figure numbers
\setlength{\cftfignumwidth}{3em}
% Width for table numbers
\setlength{\cfttabnumwidth}{3em}
% Width of page number box
\cftsetpnumwidth{2em}



% D R O P  F O L I O
\if@dropfolios
\fancypagestyle{plain}{\fancyhead{}\fancyfoot[C]{\thepage}\fancyhead{}}
\fi

% H E A D I N G S
\setlength{\headheight}{26pt}
% part format
% it might look like a mistake but it isn't
\titleformat{\part}[display]%
{\begin{fullwidth}\centering\scshape\Huge\color{Burgundy}}% format applied to label+text
  {\Huge\partname\ \thepart }% label
  {2pt}% horizontal separation between label and title body
  {}% before the title body
  [\end{fullwidth}]% after the title body
  
% chapter format
\titleformat{\chapter}[display]%
  {\Huge\rmfamily\itshape\color{darkgray}}% format applied to label+text
  {\color{black}\fontsize{72pt}{96pt}\selectfont\upshape\thechapter}% label
  {2pt}% horizontal separation between label and title body
  {}% before the title body
  [{\titlerule[0.8pt]}]% after the title body
  
% section format
\titleformat{\section}%
  {\LARGE\scshape\MakeTextLowercase}% format applied to label+text
  {\upshape\thesection} % label
  {1em}% horizontal separation between label and title body
  {}% before the title body
  []% after the title body

% subsection format
\titleformat{\subsection}%
  {\Large\itshape}% format applied to label+text
  {} % label
  {1em}% horizontal separation between label and title body
  {}% before the title body
  []% after the title body

% F O N T S
\RequirePackage[utf8]{inputenc}
\RequirePackage[LGR,T1]{fontenc}
%%% dont move this if below otherwise everything becomes concrete!
\if@useconcrete
    \RequirePackage{ccfonts}
\fi
\if@useeuler
    \RequirePackage[euler-digits,small]{eulervm}
\fi
\RequirePackage{XCharter}
\RequirePackage{beramono}
\RequirePackage{tgheros}
\renewcommand{\rmdefault}{bch}
\renewcommand{\sfdefault}{qhv}


% B I B L I O G R A P H Y
\RequirePackage[backend=biber,natbib=true,style=numeric,citetracker=true,pagetracker=true]{biblatex}

% M A T H   E N V S
\RequirePackage{amsmath, amsthm, amssymb, mathtools, geometry}
\theoremstyle{definition}
\newtheorem{definition}{Definition}[chapter]
\newtheorem{example}[definition]{Example}
\newtheorem{exercise}[definition]{Exercise}
\newtheorem{property}[definition]{Property}
\newtheorem{question}[definition]{Question}
\newtheorem{solution}[definition]{Solution}

\theoremstyle{plain}
\newtheorem{theorem}[definition]{Theorem}
\newtheorem{proposition}[definition]{Proposition}
\newtheorem{problem}[definition]{Problem}
\newtheorem{lemma}[definition]{Lemma}
\newtheorem{conjecture}[definition]{Conjecture}
\newtheorem{corollary}[definition]{Corollary}
\newtheorem*{claim}{Claim}
\newtheorem{assumption}[definition]{Assumption}
\newtheorem{hypothesis}[definition]{Hypothesis}
\newtheorem{heuristic}[definition]{Heuristic}

\theoremstyle{remark}
\newtheorem{remark}[definition]{Remark}
\newtheorem{note}[definition]{Note}
\newtheorem{case}[definition]{Case}

% A L G O R I T H M S
\RequirePackage{algpseudocode}
\RequirePackage{algorithmicx}
\RequirePackage{algorithm}
\numberwithin{algorithm}{chapter}
\newenvironment{tuftealgorithm}[2] % #1 = label, #2 = caption
{%
    \marginnote[0.65cm]{Algorithm~\ref*{#1}: #2}%
    \begin{algorithm}%
        \refstepcounter{algorithm}%
        \addcontentsline{loa}{algorithm}{\protect\numberline{\thealgorithm}#2}%

        \label{#1}%
}
{%
    \end{algorithm}%
}



% F R O N T I S P I C E
\RequirePackage{titling}


% E P I G R A P H
% Prints an epigraph and speaker in sans serif, all-caps type.
\newcommand{\openepigraph}[2]{%
  %\sffamily\fontsize{14}{16}\selectfont
  \begin{fullwidth}
    \vphantom{.}
    \vfill
  \sffamily\large\flushright
  \begin{doublespace}
  \noindent\textit{#1}\\% epigraph
  \noindent\allcaps{#2}% author
  \end{doublespace}
  \vfill
  \vfill
  \end{fullwidth}
}


\newcommand{\epigraph}[2]{%
  \marginnote{%
    \footnotesize%
    \flushright%
    %\justifying{%
    \textit{#1}%
    %}%

    {\raggedleft{\hfill{}---{#2}}}% author
  }
}


% A B B R E V I A T I O N S  &  N O M E N C L A T U R E

\RequirePackage[abbreviations,style=index,automake,nonumberlist]{glossaries-extra}
\RequirePackage[stdsubgroups,intoc,english]{nomencl}
\RequirePackage{glossary-mcols}
\RequirePackage{multicol}
\renewcommand\nompreamble{\begin{multicols}{2}}
\renewcommand\nompostamble{\end{multicols}}
\renewcommand{\nomname}{List of Symbols}
\makenomenclature


% M A R G I N   C I T A T I O N S

% commands to cite only once per page
\newcommand*{\scbx@registerkey}{%
  \ifcsundef{cbx@instcount@curr@\the\c@refsection @\thefield{entrykey}}
    {\csnumgdef{cbx@instcount@curr@\the\c@refsection @\thefield{entrykey}}{0}}
    {}%
  \csnumgdef{cbx@instcount@last@\the\c@refsection @\thefield{entrykey}}{%
    \csuse{cbx@instcount@curr@\the\c@refsection @\thefield{entrykey}}}%
  \csnumgdef{cbx@instcount@curr@\the\c@refsection @\thefield{entrykey}}{\value{instcount}}}


\def\iflastciteonsamepage{%
  \ifsamepage
    {\number\csuse{cbx@instcount@curr@\the\c@refsection @\thefield{entrykey}}}
    {\number\csuse{cbx@instcount@last@\the\c@refsection @\thefield{entrykey}}}}

\newcommand*{\scbx@savepunctstate}{%
  \let\scbx@saved@unitpunct\blx@unitpunct
  \let\scbx@saved@tgl@unit\etb@tgl@blx@unit
  \let\scbx@saved@tgl@block\etb@tgl@blx@block
  \let\scbx@saved@tgl@insert\etb@tgl@blx@insert
  \let\scbx@saved@tgl@lastins\etb@tgl@blx@lastins
  \let\scbx@saved@tgl@keepunit\etb@tgl@blx@keepunit
}

\newcommand*{\scbx@restorepunctstate}{%
  \global\let\blx@unitpunct\scbx@saved@unitpunct
  \global\let\etb@tgl@blx@unit\scbx@saved@tgl@unit
  \global\let\etb@tgl@blx@block\scbx@saved@tgl@block
  \global\let\etb@tgl@blx@insert\scbx@saved@tgl@insert
  \global\let\etb@tgl@blx@lastins\scbx@saved@tgl@lastins
  \global\let\etb@tgl@blx@keepunit\scbx@saved@tgl@keepunit
}

\newcommand*{\scbx@resetpunctstate}{%
  \let\blx@unitpunct\@empty
  \global\togglefalse{blx@block}%
  \global\togglefalse{blx@unit}%
  \global\togglefalse{blx@insert}%
  \global\togglefalse{blx@lastins}%
  \global\togglefalse{blx@keepunit}%
}


\newbibmacro{sidecite}{%
  \scbx@savepunctstate
  \scbx@resetpunctstate
  \marginnote{%
    \footnotesize%
    [\printfield{labelnumber}]%
    \setunit{\addnbspace}%
    \printnames{labelname}%
    \setunit{\printdelim{nametitledelim}}%
    \printfield[citetitle]{labeltitle}%
  }%
    \scbx@restorepunctstate
  }
  

% manual side cite command
\DeclareCiteCommand{\scite}
  {\usebibmacro{prenote}} % prenote
  {\scbx@registerkey
  \usebibmacro{citeindex}%
  \mkbibbrackets{\usebibmacro{cite}}%
     \iflastciteonsamepage%
     {}%
     {\ifinner\else\usebibmacro{sidecite}\fi}%
   }%
  {\multicitedelim} % sep
  {\usebibmacro{postnote}} % postnote

  \DeclareCiteCommand{\scitebless}
  {\usebibmacro{prenote}} % prenote
  {\scbx@registerkey
  \usebibmacro{citeindex}%
  \usebibmacro{cite}%
     \iflastciteonsamepage%
     {}%
     {\ifinner\else\usebibmacro{sidecite}\fi}%
   }%
  {\multicitedelim} % sep
  {\usebibmacro{postnote}} % postnote

  \DeclareMultiCiteCommand{\scite}[\mkbibbrackets]
  {\scitebless}{\multicitedelim}



  % manual text cite command
  \DeclareCiteCommand{\stextcite}
  {\usebibmacro{textcite:init}}
  {\scbx@registerkey
   \usebibmacro{citeindex}%
   \printnames[last]{labelname}~%
   \mkbibbrackets{\usebibmacro{cite}}%
   \iflastciteonsamepage%
   {}%
   {\ifinner \else \usebibmacro{sidecite} \fi }%
   }%
  {\textcitedelim}
  {\usebibmacro{textcite:postnote}}

\if@sidecite
% rewrites cite command for sidecites
% if not in outer par mode, cites normally
\DeclareCiteCommand{\cite}
  {\usebibmacro{prenote}} % prenote
  {\scbx@registerkey
  \usebibmacro{citeindex}%
  \mkbibbrackets{\usebibmacro{cite}}%
     \iflastciteonsamepage%
     {}%
     {\ifinner \else \usebibmacro{sidecite} \fi }%
   }%
  {\multicitedelim} % sep
  {\usebibmacro{postnote}} % postnote

  \DeclareCiteCommand{\cbx@textcite}
  {\usebibmacro{textcite:init}}
  {\scbx@registerkey
   \usebibmacro{citeindex}%
   \printnames[last]{labelname}~%
   \mkbibbrackets{\usebibmacro{cite}}%
   \iflastciteonsamepage%
   {}%
   {\ifinner \else \usebibmacro{sidecite} \fi }%
   }%
  {\textcitedelim}
  {\usebibmacro{textcite:postnote}}

\fi


% F I G U R E S

% fixes figures fucking on wrong side on new page if using symmetric opt
\if@symmetric

\xpatchcmd
  {\figure}% <cmd>
  {{}}% <search>
  {{}\checkoddpage \ifoddpage \forcerectofloat \else \forceversofloat \fi}% <replace>
  {\typeout{fig patched}}% <success>
  {\typeout{fig fail}}% <failure

\xpatchcmd
  {\table}% <cmd>
  {{}}% <search>
  {{}\checkoddpage \ifoddpage \forcerectofloat \else \forceversofloat \fi}% <replace>
  {\typeout{tab patched}}% <success>
  {\typeout{tab fail}}% <failure

\xpatchcmd
  {\table}% <cmd>
  {{figure}}% <search>
  {{figure}\checkoddpage \ifoddpage \forcerectofloat \else \forceversofloat \fi}% <replace>
  {\typeout{margin fig patched}}% <success>
  {\typeout{margin fig fail}}% <failure

\xpatchcmd
  {\table}% <cmd>
  {{table}}% <search>
  {{table}\checkoddpage \ifoddpage \forcerectofloat \else \forceversofloat \fi}% <replace>
  {\typeout{margin tab patched}}% <success>
  {\typeout{margin tab fail}}% <failure


\fi

% F O O T N O T E N U M S I Z E
% num size in text
\renewcommand{\@makefnmark}{\hbox{\@textsuperscript{\scriptsize\@thefnmark}}}
% num size in footnote
\renewcommand{\@makefntext}[1]{%
\noindent\hbox{\@textsuperscript{\scriptsize\@thefnmark}}\,#1%
}



% ******************************* Declaration **********************************
% The declaration environment puts a large, bold, centered
% "Declaration" label at the top of the page.
%\makeatletter
\newcommand{\@degreedate}{\the\year}
\newcommand{\degreedate}[1]{\renewcommand{\@degreedate}{#1}}

\newenvironment{declaration}{
\newpage
\thispagestyle{empty}
\begin{multipagefullwidth}
\begin{Huge} \begin{center} \scshape DECLARATION \end{center} \end{Huge} \vspace{1em} \hrule \vspace{2em}
\noindent\ignorespaces
}{
\flushright
\@author{}\\
\@degreedate{}
\vfill
\flushleft
* This dissertation is presented in partial fulfillment of the requirements for \textbf{Ph.D. degree} in the School of Advanced Studies of University of Camerino. 
\end{multipagefullwidth}
\newpage
}


% ************************* Abstract ***********************

\newenvironment{abstract} {
\newpage
\thispagestyle{empty}
\begin{multipagefullwidth}
\begin{LARGE} \begin{center} Abstract \end{center} \end{LARGE} \vspace{1em} \hrule \vspace{2em}
\noindent\ignorespaces
}{\end{multipagefullwidth}\newpage}

% ****************************** Acknowledgements ******************************
% The acknowledgements environment puts a large, bold, centered
% "Acknowledgements" label at the top of the page.

\newenvironment{acknowledgements}{
\cleardoublepage
\chapter*{Acknowledgements}
\thispagestyle{empty}
\begin{fullwidth}
\noindent\ignorespaces
}{\end{fullwidth}}
