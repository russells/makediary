#!/bin/bash

# Attempt to build all the versions of diaries so we get reasonable python
# code coverage.


export PYTHONPATH=`pwd` #:`pwd`/makediary
P=${P:-python3}
MD=${MD:-./bin/makediary}

set -x

$P $MD
$P $MD --output=d.ps
$P $MD --pdf
$P $MD --pdf --output=d.pdf

$P $MD --layout=day-to-page
$P $MD --layout=logbook
$P $MD --layout=week-to-opening
$P $MD --layout=week-to-2-openings
$P $MD --layout=week-to-page
$P $MD --layout=week-with-notes
$P $MD --layout=work

$P $MD --address-pages=0
$P $MD --address-pages=44
$P $MD --calendar-pages=no
$P $MD --calendar-pages=yes
$P $MD --colour
$P $MD --day-title-shading=all
$P $MD --day-title-shading=holidays
$P $MD --day-title-shading=none
$P $MD --debug-boxes
$P $MD --debug-version
$P $MD --debug-whole-page-boxes
$P $MD --expense-pages=0
$P $MD --expense-pages=2
$P $MD --expense-pages=4
$P $MD --expense-pages=40
$P $MD --gridded-notes
$P $MD --large-planner
$P $MD --line-colour=red
$P $MD --line-thickness=1
$P $MD --margins-multiplier=3
$P $MD --northern-hemisphere-moon
$P $MD --no-appointment-times
$P $MD --no-shading
$P $MD --no-smiley
$P $MD --notes-pages=0
$P $MD --notes-pages=100
$P $MD --notes-pages=-7
$P $MD --page-numbers
$P $MD --page-registration-marks
$P $MD --page-x-offset=7 --page-y-offset=18
$P $MD --planner-years=16
$P $MD --pcal
$P $MD --pcal-planner
$P $MD --perpetual-calendars
$P $MD --personal-info-no-work
$P $MD --shading=no
$P $MD --shading=yes
$P $MD --sed-ref --sh-ref
$P $MD --unix-ref --vi-ref
$P $MD --weeks-before=17 --weeks-after=31
$P $MD --page-size=filofax --paper-size=a0
$P $MD --page-size=letter --paper-size=a3
$P $MD --page-size=a4 --paper-size=a3
$P $MD --page-size=a5 --paper-size=a4

