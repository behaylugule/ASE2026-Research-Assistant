# Build ACM paper PDF (requires Docker + texlive/texlive image)
.PHONY: paper pdf clean

pdf: paper

paper:
	cd acmart && latex acmart.ins
	cp acmart/acmart.cls acmart/ACM-Reference-Format.bst .
	pdflatex -interaction=nonstopmode main.tex
	bibtex main
	pdflatex -interaction=nonstopmode main.tex
	pdflatex -interaction=nonstopmode main.tex
	@echo "Built: main.pdf"

docker-pdf:
	docker run --rm -v "$(CURDIR):/work" -w /work texlive/texlive:latest \
	  bash -c 'cd acmart && latex acmart.ins && cd .. && cp acmart/acmart.cls acmart/ACM-Reference-Format.bst . && pdflatex -interaction=nonstopmode main && bibtex main && pdflatex -interaction=nonstopmode main && pdflatex -interaction=nonstopmode main'

clean:
	rm -f *.aux *.bbl *.blg *.log *.out main.pdf acmart.cls ACM-Reference-Format.bst
