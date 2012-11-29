# Make makediary stuff.

default: eps


.PHONY: eps
eps:
	for d in * ; do \
		if [ -d $$d ] ; then \
			make -C $$d || exit ; \
		fi ; \
	done

.PHONY: clean
clean:
	for d in * ; do \
		if [ -d $$d ] ; then \
			make -C $$d clean || exit ; \
		fi ; \
	done
