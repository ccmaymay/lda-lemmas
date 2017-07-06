PDF_FILES := russian.pdf
UID := $(shell id -u)

all: $(PDF_FILES)

$(PDF_FILES): %.pdf: $(TEX_FILES) $(BIB_FILES) $(IMAGE_FILES)
	pdflatex $* && \
		bibtex $* && \
		pdflatex $* && \
		pdflatex $* && \
		pdflatex $* || rm -f $@

.PHONY: clean
clean:
	rm -f $(PDF_FILES) *.lot *.lof *.toc *.aux *.bbl *.log *.dvi *.blg *.out

docker:
	sed s/UID-REPLACE/$(UID)/g < Dockerfile.template > Dockerfile && \
		docker build -t $(PDF_FILES) . && \
		docker run -it -v $(PWD):/tmp/paper $(PDF_FILES)
