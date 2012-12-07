# Make makediary stuff.

default:

.PHONY: eps
eps:
	make -C eps

.PHONY: man
man:
	make -C man

.PHONY: clean
clean:
	make -C eps clean
	make -C man clean

.PHONY: realclean
realclean: clean
	rm -rf dist dist-deb build tmp MANIFEST
	rm -f */*.pyc
	find . -type f -name \*~ -print0 | xargs -0 rm -f
