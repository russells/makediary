#!/bin/sh

# Test script for makediary.  Make a diary that is printed on half a
# letter sized page, and post-processed with pstops so it prints like
# a book.

# $Id: test-halfletter.sh 70 2003-01-13 17:24:07Z anonymous $

# This expects to be run from the makediary source directory, ie you
# run 'bin/test-halfletter.sh'.

set -e -x

mkdir -p tmp
D=$(date +%Y%m%d-%H%M%S)
F1=tmp/test-halfletter.$$.$D.1.ps
F2=tmp/test-halfletter.$$.$D.2.ps
F3=tmp/test-halfletter.$$.$D.3.ps

echo Output in $F1 and $F2 and $F3
export PYTHONPATH=$(pwd)

bin/makediary --page-size=half-letter \
              --debug-whole-page-boxes \
              --page-x-offset=-4.22 \
              --page-y-offset=2.81 \
              --output-file=$F1

# This line gives a series of pages that can be cut in half and then bound.
#pstops -p letter '4:0L(8.5in,5.5in)+2L(8.5in,0),1R(0,11in)+3R(0,5.5in)' $F1 $F2


psselect -p2- $F1 $F2
pstops -p letter '2:0L(8.5in,0)+1L(8.5in,5.5in)' $F2 $F3
gv -media letter $F3
exit

# These lines give a booklet.

psbook -s4 $F1 $F2

#pstops -p letter '4:0L(8.5in,5.5in),1R(0,11in)' $F2 $F3


gv -media letter $F2

