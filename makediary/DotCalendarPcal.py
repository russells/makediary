#!/usr/bin/env python

import os
from os.path import expanduser
import subprocess
from makediary.DT import DT

class DotCalendar:

    EUROPEAN = 1
    AMERICAN = 2

    def __init__(self):
        self.datelist = {}
        self.dateStyle = self.EUROPEAN

    def setYears(self, years):
        self.yearlist = years

    def readCalendarFile(self):
        self.cfilename = self.findCalendarFileName()
        if self.cfilename is None:
            return

        for year in self.yearlist:
            output = subprocess.Popen(["pcal",
                                       "-c",
                                       "-f", self.cfilename,
                                       "1", str(year), "12"],
                                      stdout=subprocess.PIPE).communicate()[0]
            eventlines = output.split('\n')
            for eventline in eventlines:
                self.addEventLine(year, eventline)
        #print(self.datelist)

    def addEventLine(self, year, eventline):
        #print("Event line:", eventline)
        event = {}
        parts = eventline.split(None, 1)
        if len(parts) == 1 or len(parts) == 0: return
        if parts[0] == "opt":
            if parts[1] == "-A":
                self.dateStyle = self.AMERICAN
                print("Setting date style to AMERICAN")
            elif parts[1] == "-E":
                self.dateStyle = self.EUROPEAN
            return
        if parts[0] == "year": return
        if len(parts[0]) != 5: return
        if parts[0][2] != "/": return
        if self.dateStyle == self.EUROPEAN:
            day = int(parts[0][0:2])
            month = int(parts[0][3:])
        elif self.dateStyle == self.AMERICAN:
            month = int(parts[0][0:2])
            day = int(parts[0][3:])
        event['text'] = parts[1].strip()
        event['short'] = event['text']
        #print("Adding event", year, month, day, "=", event['text'])
        index = DT(year, month, day)
        if index in self.datelist:
            self.datelist[ index ].append(event)
        else:
            self.datelist[ index ] = [event,]


    def findCalendarFileName(self):
        try:
            #print("Trying DIARY_FILE")
            name = expanduser(os.environ['DIARY_FILE'])
            if os.path.isfile(name):
                return name
        except KeyError as args:
            pass
        try:
            #print("Trying DIARY_DIR")
            diarydir = expanduser(os.environ['DIARY_DIR'])
            name = os.path.join(diarydir, '.calendar')
            if os.path.isfile(name):
                return name
        except KeyError as args:
            pass
        try:
            #print("Trying PCAL_DIR")
            pcaldir = expanduser(os.environ['PCAL_DIR'])
            name = os.path.join(pcaldir, '.calendar')
            if os.path.isfile(name):
                return name
        except KeyError as args:
            pass
        try:
            #print("Trying current dir")
            name = '.calendar'
            if os.path.isfile(name):
                return name
        except KeyError as args:
            pass
        try:
            #print("Trying HOME")
            home = expanduser(os.environ['HOME'])
            name = os.path.join(home, '.calendar')
            if os.path.isfile(name):
                return name
        except KeyError as args:
            pass
        return None

if __name__ == '__main__':
    d = DotCalendar()
    import sys
    if len(sys.argv) > 1:
        y = int(sys.argv[1])
    else:
        y = DT.now().year
    d.setYears([y-1,y,y+1,y+2])
    d.readCalendarFile()
    print("Calendar file was", d.cfilename)
    keys = sorted(d.datelist.keys())
    for key in keys:
        print("date %s" % key)
        for date in d.datelist[key]:
            print("---")
            for datekey in date:
                print(datekey,":",date[datekey])
        print()
