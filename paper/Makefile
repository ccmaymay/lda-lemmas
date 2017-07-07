PROJECT := russian

TEX_FILES := $(wildcard *.tex)
BIB_FILES := $(wildcard *.bib)
UID := $(shell id -u)

all: russian.pdf title.pdf

russian.pdf: russian.tex russian.bib abstract.tex
	pdflatex russian && \
		bibtex russian && \
		pdflatex russian && \
		pdflatex russian && \
		pdflatex russian || rm -f $@

title.pdf: title.tex
	pdflatex title && pdflatex title

.PHONY: clean
clean:
	rm -f russian.pdf title.pdf *.lot *.lof *.toc *.aux *.bbl *.log *.dvi *.blg *.out

.PHONY: docker
docker:
	sed s/UID-REPLACE/$(UID)/g < Dockerfile.template > Dockerfile && \
		docker build -t $(PROJECT) . && \
		docker run -it -v $(PWD):/tmp/paper $(PROJECT)
