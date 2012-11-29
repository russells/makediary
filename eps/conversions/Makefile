
conversions.eps: conversions.dvi
	dvips -E -o conversions.eps  conversions.dvi

conversions.dvi: conversions.tex
	latex conversions.tex

conversions.tex: conversions-input.tex compile-conversions.awk
	awk -f compile-conversions.awk < conversions-input.tex > conversions.tex
	test $$(grep -c conformability conversions.tex) -eq 0
	test $$(grep -ci 'parse error' conversions.tex) -eq 0

.PHONY: clean
clean:
	rm -f conversions.???
