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
