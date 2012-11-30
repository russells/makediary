
conversions.001.eps: conversions.dvi
	dvips -E -i -o conversions.eps  conversions.dvi
	for f in *.0?? ; do mv $$f $$f.eps ; done

conversions.dvi: conversions.tex
	latex conversions.tex

conversions.tex: conversions-input.tex compile-conversions.awk
	awk -f compile-conversions.awk < conversions-input.tex > conversions.tex
	test $$(grep -c conformability conversions.tex) -eq 0
	test $$(grep -ci 'parse error' conversions.tex) -eq 0

.PHONY: clean
clean:
	rm -f conversions.??? conversions.0?? conversions.0??.eps
