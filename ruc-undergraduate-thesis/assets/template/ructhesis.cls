% Derived formatting: Copyright 2022 Qiu Renxiang, LPPL; see PROVENANCE.md.
% Modified and renamed 2026-11-18 by this project's maintainers.
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{ructhesis}[2026/11/18 RUC undergraduate thesis historical profile]
\newif\ifrucportable
\newif\ifrucauthoryear
\DeclareOption{portable}{\rucportabletrue}
\DeclareOption{author-year}{\rucauthoryeartrue}
\DeclareOption{numeric}{}
\ProcessOptions\relax
\RequirePackage{iftex}
\RequireXeTeX
\LoadClass[UTF8,12pt,a4paper,fontset=none]{ctexart}
\ifrucportable
  \setCJKmainfont[BoldFont=FandolSong-Bold.otf,ItalicFont=FandolKai-Regular.otf]{FandolSong-Regular.otf}
  \setCJKsansfont[BoldFont=FandolHei-Bold.otf]{FandolHei-Regular.otf}
  \setCJKmonofont{FandolFang-Regular.otf}
  \setCJKfamilyfont{zhsong}[BoldFont=FandolSong-Bold.otf]{FandolSong-Regular.otf}
  \setCJKfamilyfont{zhhei}[BoldFont=FandolHei-Bold.otf]{FandolHei-Regular.otf}
  \setCJKfamilyfont{zhkai}{FandolKai-Regular.otf}
  \setCJKfamilyfont{zhfs}{FandolFang-Regular.otf}
  \setmainfont{texgyretermes}[Extension=.otf,UprightFont=*-regular,BoldFont=*-bold,ItalicFont=*-italic,BoldItalicFont=*-bolditalic]
  \setsansfont{texgyreheros}[Extension=.otf,UprightFont=*-regular,BoldFont=*-bold,ItalicFont=*-italic,BoldItalicFont=*-bolditalic]
  \setmonofont{texgyrecursor}[Extension=.otf,UprightFont=*-regular,BoldFont=*-bold,ItalicFont=*-italic,BoldItalicFont=*-bolditalic]
  \ClassWarningNoLine{ructhesis}{PORTABLE FONTS: preview only}
\else
  \setCJKmainfont[AutoFakeBold=2.5,ItalicFont=KaiTi]{SimSun}
  \setCJKsansfont[AutoFakeBold=2.5]{SimHei}
  \setCJKmonofont{FangSong}
  \setCJKfamilyfont{zhsong}[AutoFakeBold=2.5]{SimSun}
  \setCJKfamilyfont{zhhei}[AutoFakeBold=2.5]{SimHei}
  \setCJKfamilyfont{zhkai}{KaiTi}
  \setCJKfamilyfont{zhfs}{FangSong}
  \setmainfont{Times New Roman}
  \setsansfont{Arial}
  \setmonofont{Courier New}
\fi
\providecommand{\songti}{\CJKfamily{zhsong}}
\providecommand{\heiti}{\CJKfamily{zhhei}}
\providecommand{\kaishu}{\CJKfamily{zhkai}}
\providecommand{\fangsong}{\CJKfamily{zhfs}}
\RequirePackage{amsmath,amssymb}
\RequirePackage{unicode-math}
\setmathfont{texgyretermes-math.otf}
\RequirePackage{geometry}
\geometry{left=2cm,right=1.5cm,top=2cm,bottom=2cm,headheight=34pt,headsep=8pt,footskip=24pt}
\RequirePackage{graphicx,booktabs,longtable,array,multirow,threeparttable,float}
\floatplacement{figure}{htbp}
\floatplacement{table}{htbp}
\newcounter{none}
\RequirePackage{calc}
\RequirePackage{setspace,fancyhdr,titlesec,titletoc,caption,enumitem,xcolor}
\RequirePackage{tikz}
\RequirePackage[perpage]{footmisc}
\RequirePackage{etoolbox}
\RequirePackage{fancyvrb}
\RequirePackage[normalem]{ulem}
\ifrucauthoryear
  \RequirePackage[backend=biber,style=gb7714-2015ay]{biblatex}
\else
  \RequirePackage[backend=biber,style=gb7714-2015,sorting=none]{biblatex}
\fi
\RequirePackage[hidelinks]{hyperref}
\RequirePackage{bookmark}
\hypersetup{unicode=true}
\setlength{\parindent}{2\ccwd}
\setlength{\parskip}{0pt}
\setcounter{secnumdepth}{4}
\setcounter{tocdepth}{3}
\titleformat{\section}{\singlespacing\centering\heiti\bfseries\zihao{3}}{\thesection}{2\ccwd}{}
\titleformat{\subsection}{\singlespacing\heiti\bfseries\zihao{4}}{\thesubsection}{2\ccwd}{}
\titleformat{\subsubsection}{\singlespacing\heiti\bfseries\zihao{-4}}{\thesubsubsection}{2\ccwd}{}
\titleformat{\paragraph}[block]{\singlespacing\heiti\bfseries\zihao{5}}{\theparagraph}{2\ccwd}{}
\titlespacing{\section}{0pt}{\baselineskip}{\baselineskip}
\titlespacing{\subsection}{0pt}{\baselineskip}{\baselineskip}
\titlespacing{\subsubsection}{0pt}{\baselineskip}{\baselineskip}
\titlespacing{\paragraph}{0pt}{\baselineskip}{\baselineskip}
\titlecontents{section}[2.3em]{\heiti}{\contentslabel{2.3em}}{\hspace*{-2.3em}}{\titlerule*[1pc]{.}\contentspage}
\captionsetup{font=small,labelfont=bf,skip=3pt}
\renewcommand{\thefootnote}{\arabic{footnote}}
\renewcommand{\@makefnmark}{\hbox{\@textsuperscript{\normalfont\tikz[baseline=(n.base)]\node[draw,circle,inner sep=.6pt,font=\scriptsize](n){\@thefnmark};}}}
\newcommand{\rucpage}{\songti\fontsize{10.5pt}{12pt}\selectfont 第\thepage 页}
\fancypagestyle{ruc}{\fancyhf{}\fancyhead[C]{\includegraphics[width=4.13cm,height=.98cm]{assets/head.png}}\fancyfoot[C]{\rucpage}\renewcommand{\headrulewidth}{.4pt}}
\fancypagestyle{rucfront}{\fancyhf{}\fancyhead[C]{\includegraphics[width=4.13cm,height=.98cm]{assets/head.png}}\fancyfoot[C]{\songti\fontsize{10.5pt}{12pt}\selectfont\thepage}\renewcommand{\headrulewidth}{.4pt}}
\fancypagestyle{rucempty}{\fancyhf{}\fancyhead[C]{\includegraphics[width=4.13cm,height=.98cm]{assets/head.png}}\renewcommand{\headrulewidth}{.4pt}}
\pagestyle{ruc}
\newcommand{\rucsetup}[1]{\pgfkeys{/ruc/.cd,#1}}
\pgfkeys{/ruc/.is family,/ruc,
 title/.store in=\ructitle,subtitle/.store in=\rucsubtitle,
 author/.store in=\rucauthor,college/.store in=\ruccollege,
 major/.store in=\rucmajor,grade/.store in=\rucgrade,
 student-id/.store in=\rucstudentid,supervisor/.store in=\rucsupervisor,
 score/.store in=\rucscore,date/.store in=\rucdate,code/.store in=\ruccode,
 title={},subtitle={},author={},college={},major={},grade={},student-id={},supervisor={},score={},date={},code={}}
\newcommand{\ruccoverfield}[2]{\noindent\makebox[40mm][s]{#1：}\parbox[t]{90mm}{\centering #2\strut\par\vspace{-3pt}\hrule}\par\vspace{3mm}}
\newcommand{\makethesiscover}{%
 \begin{titlepage}\thispagestyle{rucempty}
 \noindent\hfill{\heiti\bfseries\fontsize{12pt}{16pt}\selectfont 论文编码：\ruccode}\par
 \vspace{4mm}
 {\centering\heiti\bfseries\fontsize{28pt}{36pt}\selectfont 中国人民大学本科毕业论文（设计）\par}
 \vspace{16mm}
 {\centering\heiti\bfseries\fontsize{28pt}{36pt}\selectfont\ructitle\par}
 \ifdefempty{\rucsubtitle}{}{\vspace{3mm}{\centering\heiti\bfseries\fontsize{20pt}{26pt}\selectfont ——\rucsubtitle\par}}
 \vfill
 \begin{center}\begin{minipage}{132mm}\heiti\bfseries\fontsize{20pt}{25pt}\selectfont
 \ruccoverfield{作\hfill 者}{\rucauthor}
 \ruccoverfield{学\hfill 院}{\ruccollege}
 \ruccoverfield{专\hfill 业}{\rucmajor}
 \ruccoverfield{年\hfill 级}{\rucgrade}
 \ruccoverfield{学\hfill 号}{\rucstudentid}
 \ruccoverfield{指导教师}{\rucsupervisor}
 \ruccoverfield{论文成绩}{\rucscore}
 \ruccoverfield{完成日期}{\rucdate}
 \end{minipage}\end{center}\vspace{8mm}
 \end{titlepage}}
\newcommand{\rucfrontmatter}{\clearpage\pagenumbering{Roman}\pagestyle{rucfront}}
\newcommand{\rucmainmatter}{\clearpage\pagenumbering{arabic}\pagestyle{ruc}\songti\normalsize\setstretch{1.25}}
\newenvironment{cnabstract}{\clearpage\phantomsection\pdfbookmark[0]{摘要}{zhabstract}\begingroup\songti\fontsize{12pt}{14.4pt}\selectfont\setstretch{1.5}\begin{center}\heiti\bfseries\fontsize{16pt}{20pt}\selectfont 摘要\end{center}\noindent\hspace*{2\ccwd}}{\par\endgroup\clearpage}
\newenvironment{enabstract}{\clearpage\phantomsection\pdfbookmark[0]{Abstract}{enabstract}\begingroup\rmfamily\fontsize{12pt}{14.4pt}\selectfont\setstretch{2}\begin{center}\bfseries\fontsize{16pt}{20pt}\selectfont Abstract\end{center}\noindent\hspace*{2\ccwd}}{\par\endgroup\clearpage}
\newcommand{\cnkeywords}[1]{\par\vspace{\baselineskip}\noindent{\heiti\bfseries 关键词：}#1\par}
\newcommand{\enkeywords}[1]{\par\vspace{\baselineskip}\begingroup\raggedright\noindent\textbf{Keywords: }#1\par\endgroup}
\newcommand{\keywordsep}{\penalty0\hskip3\ccwd\relax}
\renewcommand{\contentsname}{内容目录}
\renewcommand{\listfigurename}{插图目录}
\renewcommand{\listtablename}{表格目录}
\newcommand{\ruccontents}{\clearpage\pagestyle{rucempty}\tableofcontents\clearpage}
\newcommand{\rucbacksection}[1]{\clearpage\phantomsection\section*{#1}\addcontentsline{toc}{section}{#1}}
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\providecommand{\passthrough}[1]{#1}
\newsavebox{\rucimagebox}
\providecommand{\pandocbounded}[1]{%
 \sbox{\rucimagebox}{#1}%
 \ifdim\wd\rucimagebox>\linewidth
   \sbox{\rucimagebox}{\resizebox{\linewidth}{!}{\usebox{\rucimagebox}}}%
 \fi
 \ifdim\dimexpr\ht\rucimagebox+\dp\rucimagebox\relax>.85\textheight
   \resizebox{!}{.85\textheight}{\usebox{\rucimagebox}}%
 \else\usebox{\rucimagebox}\fi}
\providecommand{\real}[1]{#1}
\AtBeginDocument{\hypersetup{pdftitle={\ructitle},pdfauthor={\rucauthor}}}
