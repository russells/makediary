#!/bin/bash

# set -x

function usage () {
	cat 1>&2 <<EOF
Usage: $0 [-V|--view] [--viewer=psviewer] [makediary/F.py ...]
       $0 [-h|--help]
EOF
	exit 1
}


OPTS=$(getopt -o 'hV' --long 'help,view,viewer:' -n "$0" -- "$@")
eval set -- "$OPTS"

OptView=
VIEWER=${VIEWER:-gv}

while : ; do
	case "$1" in
	-h|--help)
		shift
		usage
		;;
	-V|--view)
		OptView=yes
		shift ;;
	--viewer)
		VIEWER="$2"
		shift 2 ;;
	--)
		shift
		break ;;
	*)
		echo 1>&2 Unknown option: "$1"
		exit 1
		;;
	esac
done


Pylist=( )

if [ $# -ne 0 ] ; then
	echo setting Pylist
	Pylist=( $* )
fi

if [ ${#Pylist[*]} -eq 0 ] ; then
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
fi


export PYTHONPATH=`pwd`

mkdir -p test-mains

for f in "${Pylist[@]}" ; do
	echo -- running "$f"
	PS=test-mains/"$(basename "$f" .py)".ps
	python3 $f --debug-boxes --paper-size=a4 --page-size=a4 > "$PS"
	PSlist=( "${PSlist[@]}" $PS )
	if [ yes == "$OptView" ] ; then
		echo -- viewing $PS
		"$VIEWER" $PS
		sleep 1
	fi
done


