
sed.001.eps: sed.dvi
	dvips -E -i -o sed. sed.dvi
	for z in sed.00? ; do mv $$z $$z.eps ; done

sed.dvi: sed.tex
	latex sed.tex

sed.tex: sed-input-header.tex ../compile-1line.py sed1line-input.txt sed-input-trailer.tex
	( \
		set -e -x ; \
		cat sed-input-header.tex ; \
		../compile-1line.py < sed1line-input.txt ; \
		cat sed-input-trailer.tex ; \
	) > sed.tex

.PHONY: clean
clean:
	rm -f sed.??? sed.00?.eps
