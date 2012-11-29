
unix.eps: unix.dvi
	dvips -E -o unix.eps  unix.dvi

unix.dvi: unix.tex
	latex unix.tex

.PHONY: clean
clean:
	rm -f unix.dvi unix.log unix.aux
