
sh.eps: sh.dvi
	dvips -E -o sh.eps  sh.dvi

sh.dvi: sh.tex
	latex sh.tex

.PHONY: clean
clean:
	rm -f sh.dvi sh.log sh.aux
