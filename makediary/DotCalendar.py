#!/usr/bin/python

# Read and parse the .calendar file used by pcal.

# vim: set shiftwidth=4 expandtab smartindent textwidth=95:

__revision__ = """0.2.98"""

import sys
import os
from os.path import expanduser
import re
import copy
from mx.DateTime import *

class DotCalendar:

    """Read and parse the pcal(1) .calendar file.

    Information about the .calendar file is returned in a dictionary.  The keys are tuples of
    (year,month,day).  The values are a list of events for that day.

    Each event is another dictionary.  The entries in this dictionary can be:

    'raw text' The text as it existed in the file, after backslash continuation.
    'pre text' The text after key:value extraction, before % substitution
    'text'     The text to display for that event.
    'image'    The image to print next to that event.
    'holiday'  Exists if this day has been marked as a holiday.
    'year'     The year that the event occurred.
    'recur'    If true, print this entry on that day in every year.
    'years'    Years since the event occurred.
    'warn'     Set if this meant to have a warning event attached.

    Entries starting with '_' are put in by the program.  They can be:

    '_warning'  Set if this is a warning event.
    '_warndate' Date of the real event, if this is a warning event.

    Internally, whenever we pass around a date, it should always be a DateTime object.  This
    will ensure consistency of interface to methods.

    Any variable called 'date' must be a DateTime object.

    Any variable called 'event' must be a dictionary containing key-value pairs for that event,
    as described above."""


    # Match <ordinal> <day_spec> in <month_spec>{*} {<text>}
    # This one seems to work.
    re1 = re.compile("""
    # <ordinal>
    (?:(?P<ordinal>[1-9][0-9]*(?:st|nd|rd|th)?)
       |(?P<ordinal_word>first|second|third|fourth|fifth|even|odd|last))
    \s+

    # <day_spec>
    (?P<day_spec>(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)(?:day)?
    |(?:(?:non)?(?:day|weekday|workday|holiday)))\s+

    # The mandatory keyword
    (?:in|of)\s+

    # <month_spec>
    (?P<month_spec>(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)|year)
    # optional *, holiday spec
    (?P<holiday>\*?)

    # <text>
    \s+(?P<text>.*)
    """, re.VERBOSE)

    # Match {<ordinal>} <day_spec> <prep> <date_spec>{*} {<text>}
    # This one seems to work.
    re2 = re.compile("""
    # optional <ordinal>
    (?:(?:(?P<ordinal>[1-9][0-9]*(?:st|nd|rd|th)?)
       |(?P<ordinal_word>first|second|third|fourth|fifth|even|odd|last))
    \s+)?

    # <day_spec>
    (?P<day_spec>(?:(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)(?:day))
    |(?:(?:non)?(?:day|weekday|workday|holiday)))\s+

    # <prep>
    (?P<prep>before|preceding|after|following|on_or_before|oob|on_or_after|ooa
    |nearest|nearest_before|nearest_after)\s+

    # <date_spec> day part
    (?P<date_spec_day>[1-9]|(?:[12][0-9])|(?:3[01]))\s+
    # <date_spec> month part in words
    (?P<date_spec_month>(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)
    # <date_spec> month part in numbers
    |(?:[1-9]|(?:1[012])))\s*

    # optional *, holiday spec
    (?P<holiday>\*?)\s+

    # <text>
    (?P<text>.*)
    """, re.VERBOSE)

    # Match <date_spec>{*} {<text>}
    re3 = re.compile("""
    # The day
    (?P<day>[1-9]|(?:[012][0-9])|(?:3[012]))
    # Followed by white space or a separator
    (?:  \s+|[^0-9*\ ])
    # the month
    (?P<month>(?:[0-9][0-9]?)
              |(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*))
    # Optional, white space or a separator, then a year
    (?:  (?:\s+|[^0-9*\ ])
         (?P<year>[0-9]{2,4}))?
    # Optional holiday specifier
    (?P<holiday>\*)?
    \s+
    (?P<text>.*)
    """, re.VERBOSE)

    # Match <holiday>
    re4 = re.compile("""
    (?P<name>Christmas|Boxing Day|ANZAC Day|Easter)
    (?:\s+(?P<text>.*))?
    """, re.VERBOSE)

    # Match <<key:value>> pairs
    reKey = re.compile("""
    # Indicator for the start of the key:value
    \#<<
    # The key
    (?P<key>[a-zA-Z][a-zA-Z0-9_]+)
    # Optional ':'
    :?
    # The optional value, cannot contain '>'
    (?P<value>[^>]+)?
    # Indicator for the end of the key:value
    >>
    """, re.VERBOSE)

    # Match a '\' at the end of a line
    reBackslash = re.compile("\\\\$")

    # List of month names
    monthnames = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6,
                  'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}


    def __init__(self):
        """ Initialise some internal stuff."""

        self.cfilename = '';

        # The dictionary of dates and events, before %-substitution
        self.predatelist = {}

        # The dictionary of dates and events, after %-substitution
        self.datelist = {}

        # The list of years that we are interested in...
        self.yearlist = []

        self.debugflag = 0

    def debug(self,s):
        if self.debugflag:
            sys.stderr.write(s)


    def setYears(self, years):
        """Set the list of years we are interested in.  This must be done before the calendar
        file is parsed.  It will overwrite any previous list (ie it will not merge the old list
        and the new list."""
        self.yearlist = years


    def addYear(self,year):
        """Add a year to the list of years we are interested in.  This must be done before the
        calendar file is parsed."""
        if self.yearlist.count(year) == 0:
            self.yearlist.append(year)
            self.yearlist.sort()


    def hasYear(self,year):
        """Return true if the year specified is in our list of required years."""
        return self.yearlist.count(year)

    def findCalendarFileName(self):
        try:
            #print "Trying DIARY_FILE"
            name = expanduser(os.environ['DIARY_FILE'])
            if os.path.isfile(name):
                return name
        except KeyError, args:
            pass
        try:
            #print "Trying DIARY_DIR"
            diarydir = expanduser(os.environ['DIARY_DIR'])
            name = os.path.join(diarydir, '.calendar')
            if os.path.isfile(name):
                return name
        except KeyError, args:
            pass
        try:
            #print "Trying PCAL_DIR"
            pcaldir = expanduser(os.environ['PCAL_DIR'])
            name = os.path.join(pcaldir, '.calendar')
            if os.path.isfile(name):
                return name
        except KeyError, args:
            pass
        try:
            #print "Trying current dir"
            name = '.calendar'
            if os.path.isfile(name):
                return name
        except KeyError, args:
            pass
        try:
            #print "Trying HOME"
            home = expanduser(os.environ['HOME'])
            name = os.path.join(home, '.calendar')
            if os.path.isfile(name):
                return name
        except KeyError, args:
            pass
        return None


    def readCalendarFile(self):

        """Read the calendar file and return a list of dates and events.  FIXME more detail is
        needed here."""

        self.cfilename = self.findCalendarFileName()
        if self.cfilename is None:
            return []
        try:
            self.cfile = open(self.cfilename, 'r')
        except:
            return []
        return self.parseCalendarFile()


    def parseCalendarFile(self):
        lines = self.cfile.readlines()
        nlines = len(lines)
        for i in range(nlines):
            self.debug("doing line %d\n" % i)
            # Muck around a bit to handle \-continued lines
            line = lines[i].strip()
            while self.reBackslash.search(line):
                self.debug( "doing backslash substitution\n")
                line = self.reBackslash.sub('', line, 1)
                if i < nlines-1:
                    line2 = lines[i+1].strip()
                    self.debug("adding 2 lines...\n")
                    self.debug("%s\n" % line)
                    self.debug("%s\n" % line2)
                    line = line + ' ' + lines[i+1].strip()
                    i = i + 1           #FIXME can this be done in the middle of a range loop?
            m = self.parseLine(line)
            if m is not None:
                self.debug("match: %s\n" % m)
                self.debug("--- dictionary groups\n")
                gd = m.groupdict()
                for gk in gd.keys():
                    g = gd.get(gk)
                    if g is None:
                        self.debug("Group %s is None\n" % gk)
                    else:
                        self.debug("Group: %s: '%s'\n" % (gk,g))
        #percentSubEvents
                

    def parseLine(self, line):
        line = line.strip()
        self.debug("-------- parseLine('%s')\n" % line)
        if re.match("^\s+#.*", line): return None
        date = self.match1(line)
        if date is not None:
            self.debug('re1 matched\n')
            return date
        date = self.match2(line)
        if date is not None:
            self.debug('re2 matched\n')
            return date
        date = self.match3(line)
        if date is not None:
            self.debug('re3 matched\n')
            return date
        date = self.match4(line)
        if date is not None:
            self.debug('re4 matched\n')
            return date
        return None


    def match1(self,line):

        """Handles <ordinal> <day_spec> <month_spec>{*} <text>."""

        match = self.re1.match(line)
        if match is None: return None   # Fail


    def match2(self,line):
        match = self.re2.match(line)
        return match


    def match3(self,line):
        match = self.re3.match(line)
        if match is None:
            return None
        gd = match.groupdict()
        day = int(gd['day'])
        if self.monthnames.has_key(gd['month']):
            month = self.monthnames[gd['month']]
        else:
            month = int(gd['month'])
        year = -1
        if gd.has_key('year'):
            if gd['year'] is not None:
                year = int(gd['year'])
        text = gd['text']
        # Hack warning....
        if gd.has_key('holiday') and gd['holiday'] is not None:
            text = text + " #<<holiday>> "
        self.addEvent(DateTime(year,month,day), text)
        self.debug('re3: dmy=%d,%d,%d\n' % (day,month,year))
        return match


    def match4(self,line):
        match = self.re4.match(line)
        if match is None:
            return None
        return match


    def addEvent(self,date,text):
        """Add an event to the list of events.  Extract #<<key:value>> pairs out of the text
        and add them as entries in the dictionary for that event.  This will allow us to add
        extra arbitrary information to events, effectively extending the pcal(1) .calendar file
        format."""
        event = {}
        event['raw text'] = text
        # Now get the key:value pairs...
        t = text
        mkey = self.reKey.search(t)
        while mkey is not None:
            key = mkey.group('key')
            value = mkey.group('value')
            self.debug("Found key:%s value:%s\n" % (key, value))
            if value is not None:
                event[key] = value
            else:
                event[key] = 1
            t = self.reKey.sub('', t, 1)
            mkey = self.reKey.search(t)
        t = t.strip()
        event['pre text'] = t.strip()
        #event['text'] = self.percentSubEvent(event)
        if date.year==-1:               # For every year
            for y in self.yearlist:
                newdate = DateTime(y, date.month, date.day)
                # We need a new copy here, or we just keep modifying the same one
                newevent = copy.deepcopy(event)
                self.addEventToDate(newdate, newevent)
        else:
            self.addEventToDate(date, event)


    def isHoliday(self, date):
        """Find out if a particular date is a holiday or not.  Weekend days are not counted as
        holidays, unless specified as a holiday previously."""
        if datelist.has_key(date):
            d = datelist[date]
            if d.has_key('holiday'):
                return 1
        return 0


    def isWeekday(self, date):
        """Find out if a particular date is a week day or not."""
        weekday = date.day_of_week
        if weekday==Saturday or weekday==Sunday:
            return 0
        return 1


    def addEventToDate(self,date,event):
        
        """Add an event to a particular date.  If the entry for that date does not already
        exist it will be created.  This will be the normal way to create date entries.  Also,
        do %-substitution on the event text."""

        self.debug("--- adding event: %s to date: %s\n" % (date,event))

        # Do % substitution
        text = ''
        pretext = event['pre text']
        pretextlen = len(pretext)
        #year = date[0] ; month = date[1] ; day = date[2]
        i=0
        while i < pretextlen:
            L = pretext[i]              # L for letter
            if L=='%':
                done = 0
                ordinal_flag = 0
                zero_flag = 0
                while not done:
                    i = i+1
                    L2 = pretext[i]
                    if L2=='o':
                        ordinal_flag = 1
                    elif L2=='0':
                        zero_flag = 1
                    elif L2=='N':
                        nyears = date.year - int(event['year'])
                        text = text + str(nyears)
                        if ordinal_flag:
                            if nyears >=4  and  nyears <= 20: text = text + 'th'
                            elif nyears%10 == 1: text = text + 'st'
                            elif nyears%10 == 2: text = text + 'nd'
                            elif nyears%10 == 3: text = text + 'rd'
                            else:                text = text + 'th'
                        done = 1
                    elif L2=='A':
                        text = text + date.strftime("%A")
                        done = 1
                    elif L2=='a':
                        text = text + date.strftime("%a")
                        done = 1
                    elif L2=='B':
                        text = text + date.strftime("%B")
                        done = 1
                    elif L2=='b':
                        text = text + date.strftime("%b")
                        done = 1
                    elif L2=='d':
                        if zero_flag: text = text + ("%02d" % date.day)
                        else:         text = text + ("%d"   % date.day)
                        done = 1
                    elif L2=='j':
                        jday = int(date.strftime("%j"))
                        if zero_flag: text = text + ("%03d" % jday)
                        else:         text = text + ("%d"   % jday)
                        done = 1
                    elif L2=='l':
                        jday = int(date.strftime("%j"))
                        if date.is_leapyear: daysleft = 366-jday
                        else:                daysleft = 365-jday
                        if zero_flag: text = text + ("%03d" % daysleft)
                        else:         text = text + ("%d"   % daysleft)
                        done = 1
                    elif L2=='m':
                        text = text + ("%02d" % date.month)
                        done = 1
                    elif L2=='U':
                        text = text + date.strftime("%U")
                        done = 1
                    elif L2=='Y':
                        text = text + ("%04d" % date.year)
                        done = 1
                    elif L2=='y':
                        text = text + ("%02d" % (date.year%100))
                        done = 1
                    elif L2=='%':
                        text = text + '%'
                        done = 1
            else:
                text = text + L
            ordinal_flag = 0
            zero_flag = 0
            i = i + 1
        event['text'] = text
        # Add the event to the date, creating the list for that date if necessary.
        if not self.datelist.has_key(date):
            self.datelist[date] = []
        self.datelist[date].append(event)
        
        # Now check for a warning period
        if event.has_key('warn'):
            warn = event['warn']
            warnm = re.match('^\s*(?P<n>[0-9]+)\s+(?P<period>day|week|month)s?\s*$', warn, re.I)
            if warnm:
                n = int(warnm.group('n'))
                period = warnm.group('period')
                warnevent = copy.deepcopy(event)
                warndate = 'dummy warning date'
                if period=='day':
                    warndate = self.dateMinusDays(date, n)
                elif period=='week':
                    warndate = self.dateMinusDays(date, n*7)
                elif period=='month':
                    warndate = self.dateMinusMonths(date, n)
                warnevent['grey'] = 1
                # Add the correct date to the warning event
                if period=='day'  and  n==1:
                    warntimetext = 'tomorrow'
                elif period=='day'  and  n==2:
                    warntimetext = 'day after tomorrow'
                else:
                    warntimetext = date.strftime("%b %d")
                warnevent['text'] = "(" + warnevent['text'] + " -- " + warntimetext + ")"
                warnevent['_warning'] = 1
                warnevent['_warndate'] = copy.deepcopy(date)
                if not self.datelist.has_key(warndate):
                    self.datelist[warndate] = []
                self.datelist[warndate].append(warnevent)


    def dateMinusDays(self,date,n):
        """Return a date for a date n days before this one."""
        return date - n*oneDay


    def dateMinusMonths(self,date,n):
        """Return a date 3-tuple for a date n months before this one."""
        newmonth = date.month - n
        newyear = date.year
        # Month wraparound between years.
        while newmonth <= 0:
            newmonth = newmonth + 12
            newyear = newyear - 1
        # Cater for wraparound with n<0.
        while newmonth > 12:
            newmonth = newmonth - 12
            newyear = newyear + 1
        return DateTime(newyear, newmonth, date.day, date.hour, date.minute, date.second)


# End of class definition


if __name__ == '__main__':
    d = DotCalendar()
    if len(sys.argv) > 1:
        y = int(sys.argv[1])
    else:
        y = now().year
    d.setYears([y-1,y+1,y+2])
    d.addYear(y)
    print "hasYear(2002)==%s" % d.hasYear(2002)
    print "hasYear(2005)==%s" % d.hasYear(2005)
    print "--- yearlist == %s" % d.yearlist
    print
    d.readCalendarFile()
    keys = d.datelist.keys()
    keys.sort()
    for key in keys:
        print "date %s" % key
        for date in d.datelist[key]:
            print "---"
            for datekey in date:
                print datekey,":",date[datekey]
        print
    print "Calendar file was %s" % d.cfilename
    print "--- yearlist == %s" % d.yearlist

