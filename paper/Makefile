<<<<<<< HEAD
PAPER 		= paper

CLS_FILES	= $(shell find . -name '*.cls')
LATEX_FILES = $(shell find . -name '*.latex')
BIB_FILES	= $(shell find . -name '*.bib')
FIG_FILES	= $(shell find ./figures)
MD_FILES	= $(shell find ./sections -name '*.md' | sort)
EXTRA_FILES	= $(shell find ./extra -name '*.md' | sort)

DEP_FILES	= Makefile metadata.yaml $(CLS_FILES) $(BIB_FILES) $(LATEX_FILES) $(MD_FILES) $(FIG_FILES)
=======
PAPER     = paper
LATEX     = pdflatex -halt-on-error
BIBTEX    = bibtex

CLS_FILES = $(shell find . -name '*.cls')
TEX_FILES = $(shell find . -name '*.tex')
BIB_FILES = $(shell find . -name '*.bib')
GFX_FILES = $(shell find ./figures)

DEP_FILES = $(CLS_FILES) $(TEX_FILES) $(BIB_FILES) $(GFX_FILES)
>>>>>>> 8556d4883b4e26f396d793c41352670bc1d9cc24

all: $(PAPER).pdf

.ONESHELL edit:
	make view &> /dev/null
	while true; do \
		sleep 1 && \
		inotifywait -r -e modify,attrib,close_write,move,create,delete . && \
		make; done &> /dev/null &
<<<<<<< HEAD
	$(EDITOR) $(MD_FILES) && kill %1

$(PAPER).pdf: $(PAPER).tex
	pdflatex -halt-on-error $(PAPER) || bibtex $(PAPER)
	bibtex $(PAPER) || pdflatex -halt-on-error $(PAPER)
	pdflatex -halt-on-error $(PAPER) || bibtex $(PAPER)

$(PAPER).tex: $(DEP_FILES)
	pandoc \
		--standalone \
		--natbib \
		--smart \
		--listings \
		--template=./template.latex \
		-H custom.latex \
		--from=markdown \
		metadata.yaml $(MD_FILES) -o $(PAPER).tex

tidy:
	$(RM) *.aux
	$(RM) *.bbl
	$(RM) *.bcf
	$(RM) *.blg
	$(RM) *.ilg
	$(RM) *.lof
	$(RM) *.log
	$(RM) *.lot
	$(RM) *.nlo
	$(RM) *.nls
	$(RM) *.out
	$(RM) *.out
	$(RM) *.run.xml
	$(RM) *.toc


clean: tidy
	$(RM) $(PAPER).pdf
	$(RM) $(PAPER).tex
	$(RM) $(PAPER).html
	$(RM) -r tmp

=======
	$(EDITOR) $(TEX_FILES) && kill %1

$(PAPER).pdf: $(DEP_FILES)
	$(LATEX) $(PAPER) || $(BIBTEX) $(PAPER)
	$(BIBTEX) $(PAPER) || $(LATEX) $(PAPER)
	$(LATEX) $(PAPER) || $(BIBTEX) $(PAPER)
	$(LATEX) $(PAPER)

tidy:
	$(RM) *.aux
	$(RM) *.log
	$(RM) *.out
	$(RM) *.toc
	$(RM) *.bbl
	$(RM) *.blg

clean: tidy
	$(RM) $(PAPER).pdf
>>>>>>> 8556d4883b4e26f396d793c41352670bc1d9cc24

OS = $(shell uname -s)
ifeq ($(strip $(OS)),Linux)
	PDF_VIEW = xdg-open
else
	PDF_VIEW = open -a /Applications/Preview.app
endif

view: $(PAPER).pdf
	$(PDF_VIEW) $(PAPER).pdf &
