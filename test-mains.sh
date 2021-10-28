#!/bin/bash

# set -x

PSVIEWER=${PSVIEWER:-gv}

Pylist=( )
PSlist=( )

if [ $# -eq 0 ] ; then
	for f in makediary/*.py ; do
		grep -q __main__ $f || continue
		BN=$(basename $f .py)
		[ x"${BN}" == x"DotCalendarPcal" ] && continue
		[ x"${BN}" == x"DotCalendar" ] && continue
		[ x"${BN}" == x"DSC" ] && continue
		[ x"${BN}" == x"makediary" ] && continue
		[ x"${BN}" == x"Moon" ] && continue
		Pylist=( "${Pylist[@]}" "$f" )
	done
else
	Pylist=( "$@" )
fi

PS="${BN}".ps

export PYTHONPATH=`pwd`

for f in "${Pylist[@]}" ; do

	PS="$(basename "$f" .py)".ps
	python3 $f --debug-boxes --paper-size=a4 --page-size=a4 > "$PS" || exit
	PSlist=( "${PSlist[@]}" $PS )

done

for PS in "${PSlist[@]}" ; do
	echo ----------- $PS
	"$PSVIEWER" $PS
	sleep 1
done
