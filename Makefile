all: test

web: always_make
	mkdir -p web
	git archive -o web/release.tar.gz --prefix="cfl/" HEAD
	make paper
	cp paper/paper.pdf web/
	pandoc -s -o web/index.html README.md --css="/css/pure-min.css" --css="/css/github.css" --css="/css/styles.css"

clean-web:
	rm -rf web/


paper: always_make
	make -C paper

always_make:
	true

test:
	nosetests tests/ || true
	find src tests -name '*.pyc' -exec rm {} \;

clean: clean-web clean-models
	find src tests -name '*.pyc' -exec rm {} \;

clean-corpora: clean-taser
	find data -name '*.mallet.gz.index' -exec rm {} \;
	find data -name '*.mallet.index.gz' -exec rm {} \;
	find data -name '*.mallet.gz' -exec rm {} \;
	find data -name '*.dict.gz' -exec rm {} \;

clean-models: clean-lda clean-lsi

clean-taser:
	rm -rf /tmp/taser_*

clean-lda:
	find data -name 'LDA*' -exec rm {} \;
	find data -name '*.lda*' -exec rm {} \;

clean-lsi:
	find data -name 'LSI*' -exec rm {} \;
	find data -name '*.lsi*' -exec rm {} \;

clean-results:
	find data -name '*-ranks.csv.gz' -exec rm {} \;

install: requirements
	pip install --editable .
	cd ../gensim-mod && git checkout eta_auto && pip install --editable .

requirements:
	pip install numpy==1.11.0
	pip install scipy==0.15.1
	pip install -r requirements-freeze.txt
