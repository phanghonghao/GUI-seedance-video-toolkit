\documentclass[aspectratio=169,10pt,UTF8]{ctexbeamer}

\usetheme{Madrid}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{hyperref}

\definecolor{PrimaryTheme}{HTML}{<<PRIMARY_COLOR>>}
\definecolor{AccentTheme}{HTML}{<<ACCENT_COLOR>>}

\setbeamercolor{structure}{fg=PrimaryTheme}
\setbeamercolor{palette primary}{bg=PrimaryTheme,fg=white}
\setbeamercolor{palette secondary}{bg=PrimaryTheme,fg=white}
\setbeamercolor{frametitle}{bg=PrimaryTheme,fg=white}
\setbeamercolor{title}{fg=PrimaryTheme}
\setbeamercolor{block title}{bg=PrimaryTheme,fg=white}
\setbeamercolor{block body}{bg=AccentTheme,fg=black}
\setbeamertemplate{navigation symbols}{}

\title{<<TITLE>>}
\subtitle{<<SUBTITLE>>}
\author{<<AUTHOR>>}
\institute{<<ORG>>}
\date{\today}

\begin{document}

\begin{frame}
  \titlepage
\end{frame}

<<BODY>>

\end{document}
