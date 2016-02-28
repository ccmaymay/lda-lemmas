all:	clean russian.pdf

russian.pdf:	russian.tex russian.bib
	pdflatex russian
	bibtex russian
	pdflatex russian
	pdflatex russian

clean:
	rm -f *.lot *.lof *.toc *.aux *.bbl *.log *.dvi *.blg *.out *~
	rm -f russian.pdf
