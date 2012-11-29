
%.eps: %.dvi
	dvips -E -o $@ $<

%.dvi: %.tex
	latex $<

default: vi.001.eps vi.002.eps vi.001.dvi vi.002.dvi

.PHONY: clean
clean:
	rm -f *.eps *.dvi *.log *.aux
