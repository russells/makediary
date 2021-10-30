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
		[ x"${BN}" == x"DT" ] && continue
		[ x"${BN}" == x"makediary_" ] && continue
		[ x"${BN}" == x"Moon" ] && continue
		Pylist=( "${Pylist[@]}" "$f" )
	done
else
	Pylist=( "$@" )
fi

PS="${BN}".ps

export PYTHONPATH=`pwd`

mkdir -p test-mains

for f in "${Pylist[@]}" ; do
	echo -- running "$f"
	PS=test-mains/"$(basename "$f" .py)".ps
	python3 $f --debug-boxes --paper-size=a4 --page-size=a4 > "$PS"
	PSlist=( "${PSlist[@]}" $PS )

done

for PS in "${PSlist[@]}" ; do
	echo -- viewing $PS
	"$PSVIEWER" $PS
	sleep 1
done
