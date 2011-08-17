# Create the formatted man page for makediary from asciidoc source.


.PHONY: default
default: makediary.1.gz makediary.1.html


.PHONY: ps pdf
ps: makediary.1.ps
pdf: makediary.1.pdf


# I would use 'xmlto pdf makediary.1.xml' here, but xmltex puts lots
# of formatting stuff into the visible part of the pdf.
makediary.1.pdf: makediary.1.ps
	ps2pdf $<

makediary.1.ps: makediary.1
	man -t ./makediary.1 > $@

makediary.1.html: makediary.1.txt
	asciidoc -b html4 -d manpage $<

makediary.1.gz: makediary.1
	gzip -c $< > $@

makediary.1: makediary.1.xml
	xmlto $(if $(NV),--skip-validation) man $<

makediary.1.xml: makediary.1.txt
	asciidoc -b docbook -d manpage $<


.PHONY: clean
clean:
	rm -f makediary.1.xml makediary.1.gz makediary.1 \
		makediary.1.html makediary.1.ps makediary.1.pdf
