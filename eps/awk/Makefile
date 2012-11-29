
awk.001.eps: awk.dvi
	dvips -E -i -o awk. awk.dvi
	for z in awk.00? ; do mv $$z $$z.eps ; done

awk.dvi: awk.tex
	latex awk.tex

awk.tex: awk-input-header.tex ../compile-1line.py awk1line-input.txt awk-input-trailer.tex
	( \
		set -e -x ; \
		cat awk-input-header.tex ; \
		../compile-1line.py < awk1line-input.txt ; \
		cat awk-input-trailer.tex ; \
	) > awk.tex

.PHONY: clean
clean:
	rm -f awk.??? awk.00?.eps
