#!/bin/bash

# Attempt to build all the versions of diaries so we get reasonable python
# code coverage.


export PYTHONPATH=`pwd` #:`pwd`/makediary
P=${P:-python3}
MD=${MD:-./bin/makediary}

function expect_success () {
	echo -n 'Expect success: `'"$@""' ... "
	"$@"
	local c=$?
	echo done
	[ 0 -ne "$c" ] && exit "$c"
}

function expect_FAILURE () {
	echo -n 'Expect FAILURE: `'"$@""' ... "
	"$@"
	local c=$?
	[ 0 -eq "$c" ] && exit 99
	echo done
}

expect_success $P $MD
expect_success $P $MD --output=d.ps
expect_success $P $MD --pdf
expect_success $P $MD --pdf --output=d.pdf

expect_success $P $MD --layout=day-to-page
expect_success $P $MD --layout=logbook
expect_success $P $MD --layout=week-to-opening
expect_success $P $MD --layout=week-to-2-openings
expect_success $P $MD --layout=week-to-page
expect_success $P $MD --layout=week-with-notes
expect_success $P $MD --layout=work

expect_success $P $MD --address-pages=0
expect_success $P $MD --address-pages=44
expect_success $P $MD --calendar-pages=no
expect_success $P $MD --calendar-pages=yes
expect_success $P $MD --colour
expect_success $P $MD --day-title-shading=all
expect_success $P $MD --day-title-shading=holidays
expect_success $P $MD --day-title-shading=none
expect_success $P $MD --debug-boxes
expect_success $P $MD --debug-version
expect_success $P $MD --debug-whole-page-boxes
expect_success $P $MD --expense-pages=0
expect_success $P $MD --expense-pages=2
expect_success $P $MD --expense-pages=4
expect_FAILURE $P $MD --expense-pages=40
expect_success $P $MD --gridded-notes
expect_success $P $MD --large-planner
expect_success $P $MD --line-colour=red
expect_success $P $MD --line-thickness=1
expect_success $P $MD --margins-multiplier=3
expect_success $P $MD --northern-hemisphere-moon
expect_success $P $MD --no-appointment-times
expect_success $P $MD --no-smiley
expect_success $P $MD --notes-pages=0
expect_success $P $MD --notes-pages=100
expect_success $P $MD --notes-pages=-7
expect_success $P $MD --page-numbers
expect_success $P $MD --page-registration-marks
expect_success $P $MD --page-x-offset=7 --page-y-offset=18
expect_success $P $MD --planner-years=16
expect_success $P $MD --pcal
expect_success $P $MD --pcal-planner
expect_success $P $MD --perpetual-calendars
expect_success $P $MD --personal-info-no-work
expect_success $P $MD --shading=no
expect_success $P $MD --shading=yes
expect_success $P $MD --sed-ref --sh-ref
expect_success $P $MD --unix-ref --vi-ref
expect_success $P $MD --man-page=ls
expect_success $P $MD --man-page=exit,2 --man-page=exit,3 --man-page=bash
expect_success $P $MD --weeks-before=17 --weeks-after=31
expect_success $P $MD --page-size=filofax --paper-size=a0
expect_success $P $MD --page-size=letter --paper-size=a3
expect_success $P $MD --page-size=a4 --paper-size=a3
expect_success $P $MD --page-size=a5 --paper-size=a4

