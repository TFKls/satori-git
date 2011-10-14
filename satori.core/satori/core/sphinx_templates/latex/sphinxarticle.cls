%
% sphinxhowto.cls for Sphinx (http://sphinx.pocoo.org/)
%

\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{sphinxarticle}[2009/06/02 Document class (Sphinx Article)]

\LoadClass[english, 11pt, a4paper, notitlepage]{article}

\renewcommand{\tableofcontents}{
}  

\usepackage[margin=2.5cm]{geometry}%
\usepackage[utf8]{inputenc}%
\usepackage{polski}%
\usepackage{fancyhdr}%
\usepackage[pdftex]{graphicx,pstricks}%
\usepackage{amssymb}%
\usepackage{amsmath}%
\usepackage{indentfirst}

\pagestyle{fancy}%
\addtolength{\headheight}{2cm} %
\addtolength{\textheight}{-2.5cm}
\renewcommand{\footrulewidth}{1pt}

\setlength{\headwidth}{16cm}
\newcommand{\headerlinewidth}{13,8cm}
\renewcommand{\headrule}{\rule{\headerlinewidth}{1,5pt}}
% \parindent=0in

\lhead{\sf \small \logo} %
\rhead{\sf \small \raisebox{-0.3cm}{\data}} %
\rfoot{\sf \small Strona \thepage/\pageref*{LastPage}} %
\cfoot{}
\lfoot{\sf \small \@title} %

\hyphenpenalty=100000

\newcommand{\logo}{   \begin{tabular}{@{}ll}
                        \vspace{-1,45cm}%położenie loga ASD
                         \PDFleftlogo %
                            \begin{minipage}{8cm}
                               \begin{flushleft}
                                  \vspace*{-0.6cm} %położenie napisu Alogrytmy....
                                  \PDFcontestname \\
                                  \PDFcontestdate
                               \end{flushleft}
                            \end{minipage}
                      \end{tabular}
                  }


\newcommand{\data}{

\begin{tabular}{cc}
\hspace{5,2cm} %przesuniecie poziome \data
        \begin{minipage}{8cm} 
            \begin{flushright}      
            \vspace*{-1.34cm} %wysokość Kraków i daty
            \PDFplace \\
            \PDFdate
            \end{flushright}\end{minipage} &
            \vspace{-0.39cm} %wysokość logo TCS
    \scalebox{1}{\PDFrightlogo} 
        
\end{tabular}       
}
\renewcommand{\maketitle}{\noindent \textbf{\Large{\@title}} \bigskip}
\newcommand{\chapter}[1]{\subsection*{#1}}
\renewcommand{\tableofcontents}{}

\AtEndDocument{\label{LastPage}}

\newcommand{\PDFdate}{\ }
\newcommand{\PDFleftlogo}{\vbox to 0.96cm {\vfil }}
\newcommand{\PDFrightlogo}{\vbox to 2.13cm {\vfil }}
\newcommand{\PDFcontestname}{\ }
\newcommand{\PDFcontestdate}{\ }
\newcommand{\PDFplace}{\ }
