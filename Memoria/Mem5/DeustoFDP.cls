\NeedsTeXFormat{LaTeX2e}[1999/01/01]
\ProvidesClass{DeustoFDP}[2013/07/26 v0.1 Final Degree Proyect template for University of Deusto]

\LoadClass[a4paper,10pt]{book}          % Leemos la plantilla book sobre la que nos basamos

\RequirePackage[spanish,es-tabla]{babel}% Castellanizamos LaTeX
\RequirePackage{csquotes}               % Usamos comillas espa\~nolas
\RequirePackage[citestyle=numeric-comp, % Paquete para definir el estilo de la Bibliograf\'ia
                bibstyle=numeric,
                %style=trad-plain,
                %backref=true,
                maxnames=99,
                backrefstyle=two,
                abbreviate=false,
                backend=biber]
                {biblatex}
                                        % M\'argenes del documento
\RequirePackage[tmargin=3cm,bmargin=3cm,lmargin=3.5cm,rmargin=2.5cm]{geometry}
\RequirePackage{setspace}               % Interlineado a linea y media
\onehalfspacing
                                        % Espacio entre p\'arrafos
\setlength{\parskip}{1ex plus 0.5ex minus 0.2ex}
\setlength\parindent{0pt}               % Sin sangr\'ia

\RequirePackage{enumitem}
\setitemize{noitemsep,topsep=0pt,parsep=0pt,partopsep=0pt}
\setenumerate{noitemsep,topsep=0pt,parsep=0pt,partopsep=0pt}
\setlist[description,2]{font=\normalfont\itshape}
\setlist[description,3]{font=\normalfont\itshape}

\RequirePackage{fontspec}               % Cargamos las fuentes
\setmainfont{Arial}                     % Arial para el cuerpo del texto

\RequirePackage{fancyhdr}               % Paquete para personalizar la cabecera y los pie de p\'agina

\makeatletter                           % Paginas completamente en blanco en saltos de capitulo
\def\cleardoublepage{\clearpage\if@twoside \ifodd\c@page\else%
\hbox{} \thispagestyle{empty} \newpage%
\if@twocolumn\hbox{}\newpage\fi\fi\fi}%
\makeatother

\fancypagestyle{plain}{                 % Redefinimos el estilo de p\'agina que comienza los cap\'itulos
  \fancyhf{}
  \fancyfoot[LE,RO]{\thepage}
  \renewcommand{\headrulewidth}{0pt}
  \renewcommand{\footrulewidth}{0pt}
}

\fancypagestyle{phdthesis}{             % Redefinimos el estilo de p\'agina principal
  \fancyhf{}
  \fancyhead[RO]{\itshape\MakeUppercase{Proyecto Fin de Grado}}
  \fancyhead[LE]{\sectionfont\itshape\thechapter. \leftmark}
  \fancyfoot[LE,RO]{\thepage}
  \renewcommand{\headrulewidth}{0pt}
  \renewcommand{\footrulewidth}{0pt}
}
\pagestyle{phdthesis}
\renewcommand{\chaptermark}[1]{\markboth{\MakeUppercase{#1}}{}}

\makeatletter                           % Pongo la primera pagina de chapter con el estilo de la pfg
\renewcommand\chapter{\if@openright\cleardoublepage\else\clearpage\fi
                    \global\@topnum\z@
                    \@afterindentfalse
                    \secdef{\thispagestyle{phdthesis}\@chapter}{\thispagestyle{plain}\@schapter}}
\makeatother

\RequirePackage{graphicx}               % Paquete para incluir im\'agenes
\RequirePackage{booktabs}               % Paquete para hacer tablas profesionales
\RequirePackage{subcaption}             % Paquete para hacer subfiguras
\RequirePackage[chapter]{minted}        % Paquete para introducir c\'odigo fuente
                                        % Personalizaci\'on del entorno para el c\'odigo fuente
\renewcommand\listingscaption{Algoritmo}
\renewcommand\listoflistingscaption{\'Indice de algoritmos}
\renewcommand{\listoflistings}{%
  %\addcontentsline{toc}{chapter}{\listoflistingscaption}%
  \listof{listing}{\listoflistingscaption}%
}

\RequirePackage{titlesec}               % Paquete para personalizar los cap\'itulos
\newfontfamily\sectionfont[]{TeX Gyre Bonum}% Fuente Bookman Old para los t\'itulos

                                        % Formatos especiales para los cap\'itulos y las secciones
\titleformat{\chapter}[display]{\sectionfont\bfseries}{}{0pt}{\filleft\Large\thechapter.\quad\uppercase}[\titlerule\vspace{-2em}]
\titleformat{name=\chapter,numberless}{\sectionfont\bfseries}{}{0pt}{\Large}[\vspace{-2em}]
\titleformat{\section}{\sectionfont\bfseries}{}{0pt}{\Large\thesection. \uppercase}
\titleformat*{\subsection}{\large\bfseries\sectionfont}
\titleformat*{\subsubsection}{\large\bfseries\sectionfont}

\RequirePackage{etoolbox}
%\RequirePackage{tocbibind}              % Paquete para incluir los distintos \'indices en el \'indice
\RequirePackage[titles]{tocloft}        % Paquete para personalizar el \'indce
\preto\section{\ifnum\value{section}=0\addtocontents{toc}{\vskip10pt}\fi}
\preto\figure{\ifnum\value{figure}=0\addtocontents{lof}{{\bfseries Cap\'itulo \thechapter\vskip10pt}}\fi}
\preto\table{\ifnum\value{table}=0\addtocontents{lot}{{\bfseries Cap\'itulo \thechapter\vskip10pt}}\fi}
\preto\listing{\ifnum\value{listing}=0\addtocontents{lol}{{\bfseries Cap\'itulo \thechapter\vskip10pt}}\fi}

\RequirePackage{hyperref}               % Paquete para introducir hiperv\'inculos en el documento
\hypersetup{
  unicode=true,
  bookmarksopen,
  breaklinks,
  plainpages=false,
  pdfborder={0 0 0},
}
\RequirePackage{microtype}              % Paquete que incluye microtipado

\RequirePackage{flafter}                % No permite a los objetos flotantes ir hacia atras
