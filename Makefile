# Make makediary stuff.

default: eps man

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
	rm -rf build tmp
	rm -f */*.pyc
	find . -type f -name \*~ -print0 | xargs -0 rm -f
