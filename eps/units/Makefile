
units.eps: units.dvi
	dvips -E -o units.eps  units.dvi

units.dvi: units.tex
	latex units.tex

units.tex: units-input.tex compile-units.awk
	awk -f compile-units.awk < units-input.tex > units.tex
	test $$(grep -c conformability units.tex) -eq 0
	test $$(grep -ci 'parse error' units.tex) -eq 0

.PHONY: clean
clean:
	rm -f units.???
