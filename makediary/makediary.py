#!/usr/bin/python

# vim: set shiftwidth=4 expandtab smartindent textwidth=95:

# Print a year diary.

versionNumber = "0.2.98"

import sys
import getopt
import re
import StringIO
import Image
import EpsImagePlugin
import PaperSize
import Moon
from mx import DateTime #import *
from math import pow
from os.path import join as path_join
from os.path import exists as path_exists
from os.path import basename
from os.path import expanduser
from glob import glob
from os import getcwd
from errno import EPIPE
import subprocess
from types import TupleType, ListType
from ConfigParser import SafeConfigParser as ConfigParser

# ############################################################################################

class DiaryInfo:

    """ This class holds configuration information for the rest of the program, parses command
    line args, prints the usage message."""

    points_mm = 2.8346457               # Do all our work in millimetres

    sectionSep = "%-----------------\n" # Separator inside the postscript

    options = [
               "address-pages=",
               "appointments",
               "appointment-width=",
               "awk-ref",
               "colour",
               "colour-images",
               "conversions-ref",
               "cover-image=",
               "cover-page-image=",
               "day-to-page",
               "debug-boxes",
               "debug-version",
               "debug-whole-page-boxes",
               "eps-page=",
               "eps-2page=",
               "event-images",
               "expense-pages=",
               "gridded-notes",
               "help",
               "image-page=",
               "image-2page=",
               "large-planner",
               "layout=",
               "line-spacing=",
               "man-page=",
               "margins-multiplier=",
               "moon",
               "northern-hemisphere-moon",
               "no-appointment-times",
               "no-smiley",
               "notes-pages=",
               "output-file=",
               "page-registration-marks",
               "page-size=",
               "page-x-offset=",
               "page-y-offset=",
               "paper-size=",
               "pcal",
               "pcal-planner",
               "pdf",
               "perpetual-calendars",
               "planner-years=",
               "ref=",
               "sed-ref",
               "sh-ref",
               "start-date=",
               "title=",
               "units-ref",
               "unix-ref",
               "vi-ref",
               "vim-ref",
               "week-to-opening",
               "weeks-before=",
               "weeks-after=",
               "version",
               "year=",
               ]

    usageStrings = \
                 [
                  "Usage: %s [--year=year | --start-date=yyyy-mm-dd]\n",
                  "    [--output-file=file] [--title=TITLE]\n",
                  "    [--address-pages=n] [--appointment-width=w] [--appointments]\n",
                  "    [--colour | --colour-images] [--cover-image=IMAGE]\n",
                  "    [--cover-page-image=IMAGE] [--day-to-page]\n",
                  "    [--debug-boxes] [--debug-whole-page-boxes] [--debug-version]\n",
                  "    [--eps-page=epsfile[|title]] [--eps-2page=epsfile[|title1[|title2]]]\n",
                  "    [--event-images] [--expense-pages=0|2|4] [--gridded-notes]\n",
                  "    [--image-page=IMAGEFILE[,title]] [--image-2page=IMAGEFILE[,title]]\n",
                  "    [--large-planner] [--line-spacing=mm] [--margins-multiplier=f] [--moon]\n",
                  "    [--layout=LAYOUT] [--man-page=MANPAGE] [--northern-hemisphere-moon]\n",
                  "    [--no-appointment-times] [--no-smiley] [--notes-pages=n]\n",
                  "    [--page-registration-marks] [--page-x-offset=Xmm]\n",
                  "    [--page-y-offset=Ymm] [--pdf] [--planner-years=n] \n",
                  "    [--pcal] [--pcal-planner] [--perpetual-calendars]\n",
                  "    [--ref=<refname>] [--awk-ref] [--conversions-ref]\n",
                  "    [--sed-ref] [--sh-ref] [--units-ref] [--unix-ref] [--vi[m]-ref]\n",
                  "    [--weeks-before=n] [--weeks-after=n] [--week-to-opening]\n",
                  "    [--help] [--version]\n",
                  ]
    sizesString = "|".join(PaperSize.getPaperSizeNames())
    usageStrings.append("    [--page-size=%s]\n" % sizesString)
    usageStrings.append("    [--paper-size=%s]\n" % sizesString)
    usageStrings.append("  Defaults:\n")
    usageStrings.append("    year = next year          line-spacing = 6.0mm\n")
    usageStrings.append("    page-size = a5            paper-size = a5\n")
    usageStrings.append("    weeks-before = 0          weeks-after = 0\n")
    usageStrings.append("    appointment-width = 35%   planner-years = 2\n")
    usageStrings.append("    address-pages = 6         notes-pages = 6\n")

    layouts = ( "day-to-page", "week-to-opening", "week-to-2-openings", "work" )
    defaultLayout = "week-to-2-openings"
    usageStrings.append("  Layouts: " + ", ".join(layouts) + "\n")
    usageStrings.append("  Default layout: " + defaultLayout + "\n")

    def usage(self, f=sys.stderr):
        for i in range(len(self.usageStrings)):
            f.write(self.usageStrings[i])
        sys.exit(1)

    def shortUsage(self, f=sys.stderr):
        print >>f, "%s --help for usage" % self.myname
        sys.exit(1)

    def __init__(self, myname, opts):

        self.myname = myname
        self.opts = opts
        self.usageStrings[0] = self.usageStrings[0] % myname

        # first init the instance variables.
        self.pageNumber = 0             # Page number count
        self.currentJDaysLeft = -1      # Days left in year
        self.setStartDate(DateTime.DateTime(DateTime.now().year+1)) # Adjusted time, next year
        self.paperSize = 'a5'            # Page sizes.  Default to a5.
        wh = PaperSize.getPaperSize(self.paperSize)
        self.pageWidth = wh[0]
        self.pageHeight = wh[1]
        self.paperWidth = wh[0]
        self.paperHeight = wh[1]
        self.pageXOffset = 0.0
        self.pageYOffset = 0.0
        self.translatePage = 0
        self.translateXOffset = 0.0
        self.translateYOffset = 0.0
        self.iMargin = 12.0             # Page layout options
        self.oMargin = 5.0              #
        self.bMargin = 5.0              #
        self.tMargin = 5.0              #
        self.coverTitleFontSize = 20.0  #
        self.titleFontSize = 7.0        #
        self.titleFontName = "Times-Bold" #
        self.subtitleFontSize = 4.0     #
        self.subtitleFontName = "Helvetica" #
        self.personalinfoFontName = "Times-Bold" #
        self.personalinfoFixedFontName = "Courier-Bold" #
        self.titleY = -1                # Distance from bottom to title, calc from page size
        self.titleLineY = -1            #
        self.titleGray = 0.8            # Background for titles on some pages
        self.underlineThick = 0.2       # Thickness of title lines etc
        self.lineSpacing = 6.0          # Spacing for writing lines
        self.evenPage = 0               # even and odd pages
        self.out = None                 # Output file
        self.outName = 'diary.ps'       # Output file name
        self.outNameSet = False         # True if the output name set by command line opt.
        self.nAddressPages = 6          # Default
        self.nNotesPages = 6            #
        self.nPlannerYears = 2          #
        self.largePlanner = False       # Default: no large planner
        self.coverImage = None          # Pic for the cover page.
        self.coverPageImage = None      # Pic for the whole cover page.
        self.appointments = False       # Different "styles" for different people.
        self.appointmentTimes = True    # Print appointment times or not
        self.appointmentWidth = 35      # Width of appointments (as percentage)
        self.colour = False             # If true, print images in colour
        self.moon = False               # If true, print moon phases
        self.northernHemisphereMoon = False # If true, print northern hemisphere moon phases
        self.layout = self.defaultLayout
        self.debugBoxes = False         # If true, draw faint boxes around things for debugging
        self.debugVersion = False       # If true, print version info on inside cover.
        self.debugWholePageBoxes = False# If true, draw faint boxes around all pages.
        self.pageRegistrationMarks=False# Print marks to show where to cut.
        self.events = {}                # Events to draw on each page, from .calendar file.
        self.drawEventImages = False    # If true, draw event images
        self.nWeeksBefore = 0           # Print this number of weeks before the current year.
        self.nWeeksAfter = 0
        self.smiley = True
        self.imagePages = []
        self.manPages = []
        self.epsPages = []
        self.title = None
        self.pdf = False
        self.pcal = False
        self.pcalPlanner = False
        self.perpetualCalendars = False
        self.nExpensePages = 2
        self.griddedNotesPages = False

        self.configOptions = ConfigParser()
        self.configOptions.read( (expanduser("~/.makediaryrc"), ".makediaryrc", "makediaryrc") )

        self.createMonthCalendars()

    def createMonthCalendars(self):
        '''Create all the month calendar names.

        There are only 14 possible yearly calendars - one for a year beginning on each day of
        the days of the week, and twice that for leap years.

        For each day of the week, we generate one set of month calendars that start on that day
        and finish on that day (ie 1JAN and 31DEC are the same day of the week) and another set
        where the year is an extra day longer.

        The idea is when something wants to print a month calendar, it can call in here with
        the year and month, and we will calculate exactly which calendar is to be printed, and
        return a name that will print that calendar in PostScript.
        '''
        self.monthCalendarList = {}
        for i in range(7):
            for m in range(1,13):
                self.monthCalendarList[ (m,i,i) ] = "M_m%02d_b%d_e%d" % (m,i,i)
                i2 = (i+1) % 7
                self.monthCalendarList[ (m,i,i2) ] = "M_m%02d_b%d_e%d" % (m,i,i2)

    def getMonthCalendarPsFnCall(self, year, month, addyear=True):
        '''Return the code to call a PostScript function that will print the appropriate
        calendar for a given year and month.

        If addYear==False, we return '() M_mMM_bB_eE', where MM is the month number, B is the
        day of week of the beginning of the year, and E is the day of week of the end of the
        year.

        If addYear is true, we return '(YYYY) M_mMM_bB_eE', where YYYY is the four digit year.
        '''
        dow_begin = DateTime.DateTime(year,  1,  1).day_of_week
        dow_end   = DateTime.DateTime(year, 12, 31).day_of_week
        k = (month, dow_begin, dow_end)
        if not self.monthCalendarList.has_key(k):
            print >>sys.stderr, "makediary: internal error:"
            print >>sys.stderr, "-- No month calendar for year=%s month=%s" % (str(year),str(month))
            sys.exit(1)
        procname = self.monthCalendarList[k]
        if addyear:
            return (" (%d) " % year) + procname
        else:
            return " () " + procname

    def parseOptions(self):
        args = self.opts
        # The first week day should be settable by command line option.
        #calendar.setfirstweekday(MONDAY)
        try:
            optlist,args = getopt.getopt(args,'',self.options)
        except getopt.error, reason:
            sys.stderr.write( "Error parsing options: " + str(reason) + "\n")
            self.shortUsage()
        if len(args) != 0:
            sys.stderr.write("Unknown arg: %s\n" % args[0] )
            self.shortUsage()
        for opt in optlist:
            if 0:  # Make it easier to move options around
                pass
            elif opt[0] == "--address-pages":
                self.nAddressPages = self.integerOption("address-pages",opt[1])
            elif opt[0] == "--appointment-width":
                self.appointments = True
                if opt[1][-1] == '%':
                    optstr = opt[1][0:-1] # Strip an optional trailing '%'
                else:
                    optstr = opt[1]
                self.appointmentWidth = self.floatOption("appointment-width",optstr)
                if self.appointmentWidth < 0 or self.appointmentWidth > 100:
                    sys.stderr.write("%s: appointment width must be >=0 and <=100\n" %
                                     self.myname)
                    sys.exit(1)
            elif opt[0] == "--appointments":
                self.appointments = True
            elif opt[0] == "--awk-ref":
                self.standardEPSRef( 'awk', ['Awk reference'] )
            elif opt[0] == "--colour" or opt[0] == "--colour-images":
                self.colour = True
            elif opt[0] == "--conversions-ref":
                self.standardEPSRef( 'conversions', ['Double conversion tables'] )
            elif opt[0] == "--cover-image":
                self.coverImage = opt[1]
            elif opt[0] == "--cover-page-image":
                self.coverPageImage = opt[1]
            elif opt[0] == "--day-to-page":
                self.layout = "day-to-page"
            elif opt[0] == "--debug-boxes":
                self.debugBoxes = 1
            elif opt[0] == "--debug-whole-page-boxes":
                self.debugWholePageBoxes = 1
            elif opt[0] == "--debug-version":
                self.debugVersion = True
            elif opt[0] == "--eps-page":
                self.epsFilePageOption(opt[1], 1)
            elif opt[0] == "--eps-2page":
                self.epsFilePageOption(opt[1], 2)
            elif opt[0] == "--expense-pages":
                if opt[1] == '0' or opt[1] == '2' or opt[1] == '4':
                    self.nExpensePages = int(opt[1])
                else:
                    print >>sys.stderr, \
                          "%s: number of expense pages must be 0, 2, or 4 (not \"%s\")." % \
                          (sys.argv[0], opt[1])
                    self.shortUsage()
            elif opt[0] == "--perpetual-calendars":
                self.perpetualCalendars = True
            elif opt[0] == "--ref":
                name_and_titles = opt[1].split('|')
                self.standardEPSRef(name_and_titles[0], name_and_titles[1:])
            elif opt[0] == "--event-images":
                self.drawEventImages = True
            elif opt[0] == "--gridded-notes":
                self.griddedNotesPages = True
            elif opt[0] == "--help":
                self.usage(sys.stdout)
            elif opt[0] == "--image-page":
                self.imagePageOption(opt[1], 1)
            elif opt[0] == "--image-2page":
                self.imagePageOption(opt[1], 2)
            elif opt[0] == "--large-planner":
                self.largePlanner = True
            elif opt[0] == "--layout":
                if opt[1] in self.layouts:
                    self.layout = opt[1]
                else:
                    print >>sys.stderr, "%s: Unknown layout %s" % (self.myname, opt[1])
                    self.shortUsage()
            elif opt[0] == "--line-spacing":
                self.lineSpacing = self.floatOption("line-spacing",opt[1])
            elif opt[0] == "--man-page":
                self.manPageOption(opt[1])
            elif opt[0] == "--margins-multiplier":
                multiplier = self.floatOption("margins-multiplier",opt[1])
                self.tMargin = self.tMargin * multiplier
                self.bMargin = self.bMargin * multiplier
                self.iMargin = self.iMargin * multiplier
                self.oMargin = self.oMargin * multiplier
            elif opt[0] == "--moon":
                self.moon = True
            elif opt[0] == "--northern-hemisphere-moon":
                self.moon = True
                self.northernHemisphereMoon = True
            elif opt[0] == "--no-appointment-times":
                self.appointmentTimes = False
            elif opt[0] == "--no-smiley":
                self.smiley = False
            elif opt[0] == "--notes-pages":
                self.nNotesPages = self.integerOption("notes-pages",opt[1])
            elif opt[0] == '--output-file':
                self.outName = opt[1]
                self.outNameSet = True
            elif opt[0] == "--page-registration-marks":
                self.pageRegistrationMarks = True
            elif opt[0] == "--page-size":
                self.pageSize = opt[1]
                self.setPageSize(self.pageSize)
            elif opt[0] == "--page-x-offset":
                self.pageXOffset = self.floatOption("page-x-offset", opt[1])
            elif opt[0] == "--page-y-offset":
                self.pageYOffset = self.floatOption("page-y-offset", opt[1])
            elif opt[0] == "--pdf":
                self.pdf = True
            elif opt[0] == "--paper-size":
                self.paperSize = opt[1]
                self.setPaperSize(self.paperSize)
            elif opt[0] == "--pcal":
                self.pcal = True
            elif opt[0] == '--pcal-planner':
                self.pcal = True
                self.pcalPlanner = True
            elif opt[0] == "--planner-years":
                self.nPlannerYears = self.integerOption("planner-years",opt[1])
            elif opt[0] == "--version":
                print "makediary, version " + versionNumber
                sys.exit(0)
            elif opt[0] == "--sed-ref":
                self.standardEPSRef( 'sed', ['sed reference'] )
            elif opt[0] == "--sh-ref":
                self.standardEPSRef( 'sh', ['Shell and utility reference'] )
            elif opt[0] == '--start-date':
                self.setStartDate(DateTime.strptime(opt[1], '%Y-%m-%d'))
            elif opt[0] == "--title":
                self.title = opt[1]
            elif opt[0] == "--units-ref":
                self.standardEPSRef( 'units', ['Units'] )
            elif opt[0] == "--unix-ref":
                self.standardEPSRef( 'unix', ['Unix reference',] )
            elif opt[0] == "--vim-ref" or opt[0] == "--vi-ref":
                self.standardEPSRef( 'vi', ['Vi reference', 'Vim extensions'] )
            elif opt[0] == "--week-to-opening":
                self.layout = "week-to-opening"
            elif opt[0] == "--weeks-after":
                self.nWeeksAfter = self.integerOption("weeks-after",opt[1])
            elif opt[0] == "--weeks-before":
                self.nWeeksBefore = self.integerOption("weeks-before",opt[1])
            elif opt[0] == '--year':
                self.setStartDate(DateTime.DateTime(self.integerOption("year",opt[1])))
            else:
                print >>sys.stderr, "Unknown option: %s" % opt[0]
                self.shortUsage()
        if self.pdf:
            # If the name is still diary.ps and it was not set by command line option, change
            # it to diary.pdf.
            if (not self.outNameSet) and self.outName == 'diary.ps':
                self.outName = 'diary.pdf'
            # If we are doing PDF output, let ps2pdf open the output file.
            pdfArgs = ( 'ps2pdf',
                        '-dAutoRotatePages=/None', # pdf2ps rotates some pages without this
                        '-sPAPERSIZE='+self.paperSize,
                        '-', self.outName)
            #print >>sys.stderr, "Running "+str(pdfArgs)
            self.pdfProcess = subprocess.Popen(pdfArgs, stdin=subprocess.PIPE)
            self.out = self.pdfProcess.stdin
        else:
            if self.outName == '-':
                self.out = sys.stdout
            else:
                try:
                    self.out = open(self.outName,'w')
                except IOError, reason:
                    sys.stderr.write(("Error opening '%s': " % self.outName) \
                                     + str(reason) + "\n")
                    #self.usage()
                    sys.exit(1)
        self.calcPageLayout()
        self.calcDateStuff()


    def epsFilePageOption(self, option, npages):
        if npages == 1:
            options = option.split('|', 1)
            filename = options[0]
            if len(options) == 2:
                title1 = options[1]
            else:
                title1 = None
            title2 = None
        elif npages == 2:
            options = option.split('|', 2)
            filename = options[0]
            if len(options) >= 2:
                title1 = options[1]
            else:
                title1 = None
            if len(options) == 3:
                title2 = options[2]
            else:
                title2 = None
        else:
            print >>sys.stderr, "Strange number of pages for eps-page: %d" % npages
            return
        self.epsPages.append( {"fileName" : filename, "pages"  : npages,
                               "title1"   : title1,   "title2" : title2} )


    def standardEPSRef(self, name, titles):
        '''Find a list of files that make up a standard reference.'''
        # A weirdness: if we have only one title, use that for all pages.  But if we have more
        # than one title, use them in order until we run out.  So we have to know at the start
        # if we have one or more than one.
        same_title = (1 == len(titles))
        files = self.findEPSFiles(name)
        if len(files) == 0:
            print >>sys.stderr, "%s: cannot find ref files for \"%s\"" % \
                (sys.argv[0], name)
            return
        for f in files:
            if len(titles) > 0:
                title = titles[0]
                if not same_title:
                    titles = titles[1:]
            else:
                title = None
            self.epsPages.append( {"fileName" : f,     "pages"  : 1,
                                   "title1"   : title, "title2" : None } )


    def integerOption(self,name,s):
        """Convert an arg to an int."""
        try:
            return int(s)
        except ValueError,reason:
            sys.stderr.write("Error converting integer: " + str(reason) + "\n")
            self.shortUsage()


    def manPageOption(self, opt):
        match = re.match('''^([_a-z0-9][-_a-z0-9:\.]*)\(([1-9])\)$''', opt, re.IGNORECASE)
        if match:
            self.manPages.append( (match.group(1), match.group(2)) )
            return
        match = re.match('''^([_a-z0-9][-_a-z0-9:\.]*),([1-9])$''', opt, re.IGNORECASE)
        if match:
            self.manPages.append( (match.group(1), match.group(2)) )
            return

        match = re.match('''^([_a-z0-9][-_a-z0-9:\.]*)$''', opt, re.IGNORECASE)
        if match:
            self.manPages.append( (match.group(1), None) )
            return

        print >>sys.stderr, "%s: unknown man page: %s" % (sys.argv[0], opt)


    def setStartDate(self,date):
        self.dtbegin = DateTime.DateTime(date.year, date.month, date.day)
        self.dt = DateTime.DateTime(date.year, date.month, date.day)
        self.dtend = self.dt + DateTime.RelativeDateTime(years=1)


    def imagePageOption(self, option, npages):
        commaindex = option.find(",")
        if commaindex != -1:
            self.imagePages.append( { "fileName" : option[0:commaindex],
                                      "title"    : option[commaindex+1:],
                                      "pages"    : npages } )
        else:
            self.imagePages.append( { "fileName" : option,
                                      "title"    : "",
                                      "pages"    : npages } )


    def floatOption(self,name,s):
        """Convert an arg to a float."""
        try:
            return float(s)
        except ValueError,reason:
            sys.stderr.write("Error converting float: " + str(reason) + "\n")
            self.shortUsage()

    def setPageSize(self,s):
        """Set the page size to a known size."""
        sizes = PaperSize.getPaperSize(s)
        if sizes is None:
            print >>sys.stderr, "Unknown page size: %s" % s
            self.shortUsage()
        self.pageWidth = sizes[0]
        self.pageHeight = sizes[1]
        # Adjust font sizes with respect to A5, on a square root scale.
        self.adjustSizesForPageSize()

    def setPaperSize(self,s):
        """Set the paper size to a known size."""
        sizes = PaperSize.getPaperSize(s)
        if sizes is None:
            print >>sys.stderr, "Unknown paper size: %s" % s
            self.shortUsage()
        self.paperWidth = sizes[0]
        self.paperHeight = sizes[1]

    def adjustSizesForPageSize(self):

        """Change various sizes for a different sized page.

        The reference page size is A5.  Things are scaled up or down from there, but not
        linearly.  There are many magic numbers in here to make things ``just look right.''"""

        pageMultiple = self.pageHeight/210.0

        fontMultiplier = pow(pageMultiple, 0.9)
        self.titleFontSize *= fontMultiplier
        self.subtitleFontSize *= fontMultiplier

        coverTitleFontMultiplier = pageMultiple
        self.coverTitleFontSize *= coverTitleFontMultiplier

        marginMultiplier = pow(pageMultiple, 0.5)
        self.tMargin *= marginMultiplier
        self.bMargin *= marginMultiplier
        self.iMargin *= marginMultiplier
        self.oMargin *= marginMultiplier

    def calcPageLayout(self):

        # This should only be called once, just after the page size has been determined.
        # self.titleY leaves a smaller gap than the font size because the font does not
        # completely fill the box.

        # Calculate the offset.
        if self.pageWidth != self.paperWidth \
               or self.pageXOffset != 0 \
               or self.pageYOffset != 0:
            self.translateXOffset = ( self.paperWidth  - self.pageWidth  )/2.0 \
                                    + self.pageXOffset
            self.translateYOffset = ( self.paperHeight - self.pageHeight )/2.0 \
                                    + self.pageYOffset
            self.translatePage = 1

        self.titleY = self.bMargin \
                      + (self.pageHeight-(self.bMargin+self.tMargin)) \
                      - 0.8*self.titleFontSize
        self.titleLineY = self.titleY - self.titleFontSize*0.3

    def getNextPageNumber(self):
        # Each page calls this to get its page number.
        self.pageNumber = self.pageNumber + 1
        if (self.pageNumber % 2) == 0:
            self.evenPage=1
        else:
            self.evenPage=0
        return self.pageNumber

    def gotoNextDay(self):
        self.dt = self.dt + DateTime.oneDay
        self.calcDateStuff()

    def gotoPreviousDay(self):
        self.dt = self.dt - DateTime.oneDay
        self.calcDateStuff()

    def calcDateStuff(self):
        # Call this every time the day changes.
        if self.dt.is_leapyear:
            self.currentJDaysLeft = 366 - self.dt.day_of_year
        else:
            self.currentJDaysLeft = 365 - self.dt.day_of_year
        #sys.stderr.write("calcDateStuff: currentsec = %d\n" % self.currentSecond )


    def readDotCalendar(self):
        if self.pcal:
            import DotCalendarPcal as DotCalendar
        else:
            import DotCalendar
        dc = DotCalendar.DotCalendar()
        years = []
        for i in range(self.nPlannerYears+4):
            years.append(self.dtbegin.year-2+i)
        dc.setYears(years)
        dc.readCalendarFile()
        self.events = dc.datelist


    def findEPSFiles(self, name):
        '''Find EPS files matching a name.

        Given the "base name" of an EPS file, we search for files matching that, and return the
        path names in a list.

        For example, if we are given "sh", as the name to search for, and
        /usr/lib/site-python/makediary/eps/sh/sh.eps exists, we return that path in a sequence
        on its own.

        If given "sh", and /usr/.../sh.001.eps, sh.002.eps etc exist, we return all those in a
        sequence.

        We construct the names to search for by taking each element of the search path and
        appending /makediary/eps/<name>/<name>.eps and then /makediary/eps/<name>/<name>.*.eps
        to each element of the search path and checking to see if there are one or more files
        that match.  The first time we get a match we construct the list and return that.

        The search path is sys.path.  If makediary is being run with a relative path, then we
        first check a series of relative paths.

        If we are given a relative or absolute path to a file, use that only, after globbing.
        '''

        names = []
        # If we are given a full or relative-to-pwd path to the file, use that only.
        if '/' in name:
            names = glob(name)
        else:
            # Otherwise, construct the full path to the file.  If we are running from the
            # development directory, or otherwise not from a full path name, look at relative
            # locations first.  In any case, we search the current directory first.
            if sys.argv[0].startswith('.'):
                searchpaths = ['.', '..', '../..']
            else:
                searchpaths = ['.']
            for p in sys.path:
                searchpaths.append(p)
            #print >>sys.stderr, "searchpath is %s" % str(searchpath)
            for searchpath in searchpaths:
                path = path_join(searchpath, "makediary", "eps", "%s" % name, "%s.eps" % name)
                names = glob(path)
                if len(names) != 0:
                    break
                path = path_join(searchpath, "makediary", "eps", "%s" % name, "%s.*.eps" % name)
                names = glob(path)
                if len(names) != 0:
                    # glob() returns random or directory order, ie unsorted.
                    names.sort()
                    break
        return names


# ############################################################################################

class BasicPostscriptPage:
    """The basic PostScript page.  Other pages do their thing by overriding the body()
    method."""

    def __init__(self, dinfo):
        self.di = dinfo
        self.pagenum = 0                #
        self.preamble = ""              #
        self.postamble = ""             #

        self.pLeft = 0                  # Page limits
        self.pRight = 0                 #
        self.pTop = 0                   #
        self.pBottom = 0                #
        self.pWidth = 0                 #
        self.pHeight = 0                #

        self.pagenum = self.di.getNextPageNumber()
        self.preamble =   self.di.sectionSep \
                        + ("%%%%Page: %d %d\n" % (self.pagenum,self.pagenum)) \
                        + "%%%%PageBoundingBox: 0 0 %.0f %.0f\n" % \
                        (self.di.paperWidth * self.di.points_mm,
                         self.di.paperHeight * self.di.points_mm) \
                        + "%%BeginPageSetup\n" \
                        + "SA MM\n"
        if self.di.translatePage:
            self.preamble = self.preamble \
                            + "%5.3f %5.3f TR\n" % (self.di.translateXOffset,
                                                    self.di.translateYOffset)
        self.preamble = self.preamble \
                        + "monthCalendars begin\n" \
                        + "%%EndPageSetup\n" \
                        + "%% This is for year beginning %04d-%02d-%02d, " % \
                        (self.di.dtbegin.year, self.di.dtbegin.month, self.di.dtbegin.day)
        if self.di.evenPage:
            self.preamble = self.preamble + "on an even page\n"
        else:
            self.preamble = self.preamble + "on an odd page\n"

        if self.di.debugWholePageBoxes:
            # Print faint boxes around all the pages.
            self.preamble = self.preamble \
                            + "% Faint box around the page\n" \
                            + "0 SLW 0 0 M 0 %5.3f RL " % self.di.pageHeight \
                            + " %5.3f 0 RL " % self.di.pageWidth \
                            + " 0 -%5.3f RL " % self.di.pageHeight \
                            + " -%5.3f 0 RL S\n" % self.di.pageWidth

        if self.di.pageRegistrationMarks:
            self.preamble = self.preamble \
                            + "% Registration marks, 10mm long\n" \
                            + "0.1 SLW 0 -2 M 0 -10 RL S\n" \
                            + "-2 0 M -10 0 RL S\n" \
                            + "0 %5.3f M 0 10 RL S\n" % (self.di.pageHeight+2,) \
                            + "-2 %5.3f M -10 0 RL S\n" % (self.di.pageHeight,) \
                            + "%5.3f %5.3f M 0 10 RL S\n" % (self.di.pageWidth,
                                                             self.di.pageHeight+2) \
                            + "%5.3f %5.3f M 10 0 RL S\n" % (self.di.pageWidth+2,
                                                             self.di.pageHeight) \
                            + "%5.3f -2 M 0 -10 RL S\n" % (self.di.pageWidth,) \
                            + "%5.3f 0 M 10 0 RL S\n" % (self.di.pageWidth+2,)
            self.preamble = self.preamble \
                            + "% Internal registration marks, 5mm long\n" \
                            + "2 0 M 5 0 RL S\n" \
                            + "0 2 M 0 5 RL S\n" \
                            + "0 %5.3f M 0 -5 RL S\n" % (self.di.pageHeight-2,) \
                            + "2 %5.3f M 5 0 RL S\n" % (self.di.pageHeight,) \
                            + "%5.3f %5.3f M -5 0 RL S\n" % (self.di.pageWidth-2, \
                                                              self.di.pageHeight) \
                            + "%5.3f %5.3f M 0 -5 RL S\n" % (self.di.pageWidth,
                                                              self.di.pageHeight-2) \
                            + "%5.3f 2 M 0 5 RL S\n" % (self.di.pageWidth,) \
                            + "%5.3f 0 M -5 0 RL S\n" % (self.di.pageWidth-2,)

        self.postamble =   "end RE SP\n" \
                         + "%% End of page %d\n" % (self.pagenum)
        self.setMargins()

    def page(self):
        if self.di.debugBoxes:
            return self.preamble + self.debugPageBox() + self.body() + self.postamble
        else:
            return self.preamble + self.body() + self.postamble

    def debugPageBox(self):

        bottom = self.di.bMargin
        top = self.di.pageHeight - self.di.tMargin
        if self.di.evenPage:
            left = self.di.oMargin
            right = self.di.pageWidth - self.di.iMargin
        else:
            left = self.di.iMargin
            right = self.di.pageWidth - self.di.oMargin
        #return "0 SLW %5.3f %5.3f %5.3f %5.3f 2 debugboxLBRTD\n" % (left,bottom,right,top)
        return "0 SLW %5.3f %5.3f %5.3f %5.3f debugboxLBRT\n" % (left,bottom,right,top)

    def body(self):
        return "% Nothing here\n"

    # Utility stuff
    def setMargins(self):
        if self.di.evenPage:
            self.pLeft  = self.di.oMargin
            self.pRight = self.di.pageWidth - self.di.iMargin
        else:
            self.pLeft  = self.di.iMargin
            self.pRight = self.di.pageWidth - self.di.oMargin
        self.pTop = self.di.titleLineY
        self.pBottom = self.di.bMargin
        self.pWidth = self.pRight - self.pLeft
        self.pHeight = self.pTop - self.pBottom

    def topline(self):
        s = ""
        s = s + "%5.3f SLW 1 setlinecap %5.3f %5.3f M %5.3f %5.3f L S\n" \
            % (self.di.underlineThick,self.pLeft,self.di.titleLineY,self.pRight,self.di.titleLineY)
        return s

    def bottomline(self):
        s = ""
        s = s + "%5.3f SLW 1 setlinecap %5.3f %5.3f M %5.3f %5.3f L S\n" \
            % (self.di.underlineThick,self.pLeft,self.di.bMargin,self.pRight,self.di.bMargin)
        return s

    def title(self,text1,text2=""):
        text1e = self.postscriptEscape(text1)
        s = self.topline()
        s = s + "/%s %5.3f selectfont " % (self.di.titleFontName,self.di.titleFontSize)
        if self.di.evenPage:
            s = s + ("%5.3f %5.3f M (%s) SH\n" % (self.pLeft,self.di.titleY,text1e))
        else:
            s = s + ("(%s) dup %5.3f exch SW pop sub %5.3f M SH\n" % \
                     (text1e,self.pRight,self.di.titleY))
        if text2 != "":
            text2e = self.postscriptEscape(text2)
            s = s + "/%s %5.3f selectfont " % (self.di.subtitleFontName, self.di.subtitleFontSize)
            if self.di.evenPage:
                s = s + "(%s) dup %5.3f exch SW pop sub %5.3f M SH\n" % \
                    (text2e,self.pRight,self.di.titleY)
            else:
                s = "%5.3f %5.3f M (%s) SH\n" % (self.pLeft,self.di.titleY,text2e)
        return s


    def smiley(self):
        """ Print a smiley at the current location.  The face will be one unit across, centred
        on currentpoint.  Use 'save n n scale ... restore' to make it an appropriate size, and
        translate to put it in the right place."""

        # The radius of the face here is 0.5 minus half the line width, to keep all the ink
        # inside the circle of diameter one unit.
        s =   "% smiley\n" \
            + "CP SA CP TR\n" \
            + "0.05 SLW 1 setlinecap\n" \
            + "newpath  0    0    0.475 0   360 arc S    % face\n" \
            + "newpath  0    0.10 0.375 230 310 arc S    % smiley mouth\n" \
            + "newpath -0.15 0.10 0.05  0   360 arc fill % left eye\n" \
            + "newpath  0.15 0.10 0.05  0   360 arc fill % right eye\n" \
            + "RE M\n" \
            + "% end smiley\n"
        return s


    def postscriptEscape(self,s):
        """Replace occurrences of PostScript special characters in a string.  The ones we
        replace are: '\' -> '\\', '(' -> '\(', ')' -> '\)'.  Note that the backslashes have to
        be done first, or they will be matched by the backslashes used to escape '(' and
        ')'."""

        s2 = re.sub( r"\\", r"\\\\", s )
        s3 = re.sub( r"\(", r"\(", s2 )
        s4 = re.sub( r"\)", r"\)", s3 )
        return s4


# ############################################################################################

class PostscriptPage(BasicPostscriptPage):
    """Basic PostScript page with images and embedded Postscript objects."""

    def image(self,file,x,y,xmaxsize,ymaxsize):

        """Print an image on the page.  The image will be scaled so it will fit within a box at
        (x,y), with size (xmaxsize,ymaxsize), and centred inside that box."""

        s = ""
        im = Image.open(file,"r")
        xsize,ysize = im.size
        if self.di.colour:
            if im.mode not in ("L", "RGB", "CMYK"):
                im = im.convert("RGB")
        else:
            im = im.convert("L")
        epsfile = StringIO.StringIO()

        rawxscale = float(xmaxsize)/xsize
        rawyscale = float(ymaxsize)/ysize
        if rawxscale == rawyscale:
            scale = rawxscale
            xpos = x
            ypos = y
        else:
            if rawxscale > rawyscale:
                scale = rawyscale
                ypos = y
                xpos = x + (xmaxsize - (xsize * scale))/2.0
            else:
                scale = rawxscale
                xpos = x
                ypos = y + (ymaxsize - (ysize * scale))/2.0

        s = s + self.di.sectionSep + "% Begin EPS image:\n"
        if self.di.debugBoxes:
            if rawxscale > rawyscale:
                dashlen = ymaxsize / 9.0
            else:
                dashlen = xmaxsize / 9.0
            s = s + "%% debug box\n%5.3f %5.3f %5.3f %5.3f debugboxLBWH\n" % \
                (x,y,xmaxsize,ymaxsize)
        s = s + "%% rawxscale=%5.3f rawyscale=%5.3f\n" % (rawxscale,rawyscale)
        s = s + "%% file=%s x=%5.3f y=%5.3f xmaxsize=%5.3f ymaxsize=%5.3f\n" % \
            (file,x,y,xmaxsize,ymaxsize)
        s = s + "%% xsize=%5.3f ysize=%5.3f rawxscale=%5.3f rawyscale=%5.3f\n" % \
            (xsize,ysize,rawxscale,rawyscale)
        s = s + "%% scale=%5.3f xpos=%5.3f ypos=%5.3f\n" % \
            (scale,xpos,ypos)
        s = s + "%% xmaxsize*scale=%5.3f ymaxsize*scale=%5.3f\n" % \
            (xmaxsize*scale,ymaxsize*scale)
        s = s + "5 dict begin /showpage { } bind def SA %5.3f %5.3f TR\n" % (xpos,ypos)
        s = s + "%5.3f %5.3f scale\n" % (scale, scale)
        s = s + "%%%%BeginDocument: %s\n" % file
        EpsImagePlugin._save(im,epsfile,None,1)
        eps = epsfile.getvalue()
        epsfile.close()
        #im.close()
        s = s + eps
        s = s + "\n%%EndDocument\n"
        s = s + "RE end\n" \
            + "% End EPS image\n" + self.di.sectionSep
        return s


    def findBoundingBoxInEPS(self, epsfilename, epsfile):
        '''Search for the BoundingBox comment, must be in the first 20 lines.'''

        filepos = epsfile.tell()

        boundingboxfound  = False
        for i in range(0,20):
            line = epsfile.readline()
            if line.startswith("%%BoundingBox:"):
                list = line.split()
                if len(list) != 5:
                    msg = "EPS file %s: can't split \"%s\"" % (epsfilename, line.strip())
                    return (msg, None)
                epsx1_pt = float(list[1])
                epsy1_pt = float(list[2])
                epsx2_pt = float(list[3])
                epsy2_pt = float(list[4])
                boundingboxfound = True
                break

        # Return the file to where we found it.
        epsfile.seek(filepos)

        if boundingboxfound:
            return (None, (epsx1_pt, epsy1_pt, epsx2_pt, epsy2_pt))
        else:
            return ("EPS file %s: no %%%%BoundingBox in first 20 lines" % epsfilename,
                    None)


    def embedEPS(self, filename, epsfile):
        '''Embed an EPS file within the diary.

        filename - name of file we are embedding, for error messages
        epsfile - file-like object that contains EPS
        '''

        s = ''

        # Redefine showpage so the EPS file doesn't muck up our page count, save the graphics
        # state, and scale so the EPS measurements in points are the correct size in our world
        # of millimetres.
        s = s + "5 dict begin /showpage { } bind def SA %5.6f %5.6f SC\n" % \
                (1.0/self.di.points_mm, 1.0/self.di.points_mm)
        s = s + "%%%%BeginDocument: %s\n" % filename

        for line in epsfile.readlines():
            s = s + line

        #s = s + "\n%%EndDocument\nRE end RE\n"
        s = s + "\n%%EndDocument\nRE end\n"

        # Remove the clipping region
        #s = s + "grestore\n"

        # Now draw a box so we can see where the image should be.
        #s = s + "%5.3f %5.3f %5.3f %5.3f 0 boxLBWH\n" % (x,y,maxwidth,maxheight)
        return s


    def searchfor(self, path, type, filename):
        '''Look for a file in the python search path, with a couple of optional prefixes.'''
        #print >>sys.stderr, "searchfor  (%s, %s)" % (path,filename)
        p = path_join(path, filename)
        pe = path_join(path, type, filename)
        pme = path_join(path, 'makediary', type, filename)
        #print >>sys.stderr, "Looking for %s, cwd is %s" % (p, getcwd())
        if path_exists(pme):
            #print "Found %s" % pme
            return pme
        elif path_exists(pe):
            #print "Found %s" % pe
            return pe
        elif path_exists(p):
            #print "Found %s" % p
            return p
        else:
            return None


# ############################################################################################

# A page whose content is made up of an image file.

class ImageFilePage(PostscriptPage):

    class Side:
        full  = "FULL"
        left  = "LEFT"
        right = "RIGHT"

    def __init__(self, dinfo, imgfilename, imagetitle=None, side=Side.full):
        PostscriptPage.__init__(self, dinfo)
        self.imgfilename = imgfilename
        self.imagetitle = imagetitle
        self.side = side


    def body(self):
        imgfilepathname = None
        # If we are given a full or relative-to-pwd path to the file, use that.
        if self.imgfilename.startswith('/') or self.imgfilename.startswith('./') \
               or self.imgfilename.startswith('../'):
            imgfilepathname = self.imgfilename
        else:
            # Otherwise, construct the full path to the file.  If we are running from the
            # development directory, or otherwise not from a full path name, look at relative
            # locations first.
            if self.di.myname.startswith('.'):
                searchpath = ['.', '..', '../..']
                for p in sys.path:
                    searchpath.append(p)
            else:
                searchpath = sys.path
            #print >>sys.stderr, "searchpath is %s" % str(searchpath)
            for path in searchpath:
                imgfilepathname = self.searchfor(path, 'image', self.imgfilename)
                if imgfilepathname:
                    break
        if imgfilepathname:
            inset = self.pWidth / 200.0
            if self.side == self.Side.full:
                sclip = ''
            elif self.side == self.Side.left or self.side == self.Side.right:
                sclip = "newpath %5.3f %5.3f %5.3f %5.3f rectclip\n" % \
                        (self.pLeft, self.pBottom, self.pWidth, self.pHeight)
            if self.side == self.Side.full:
                x = self.pLeft + inset
                y = self.pBottom + inset
                w = self.pWidth - 2*inset
                h = self.pHeight - 2*inset
            elif self.side == self.Side.left:
                x = self.pLeft    + inset
                y = self.pBottom  + inset
                w = self.pWidth*2 - 2*inset
                h = self.pHeight  - 2*inset
            elif self.side == self.Side.right:
                x = self.pLeft - self.pWidth + inset
                y = self.pBottom             + inset
                w = self.pWidth*2            - 2*inset
                h = self.pHeight             - 2*inset

            imgp = self.image(imgfilepathname, x, y, w, h)
            if self.imagetitle:
                return self.title(self.imagetitle) + sclip + imgp
            else:
                return sclip + imgp
        else:
            print >>sys.stderr, "Can't find %s" % self.imgfilename
            return "%% -- Can't find %s\n" % self.imgfilename


# ############################################################################################

# Two pages whose content is made up of two halves of one image file.

class TwoImageFilePages:

    def __init__(self, dinfo, imgfilename, imagetitle=None):
        self.dinfo = dinfo
        self.imgfilename = imgfilename
        self.imagetitle = imagetitle


    def page(self):
        s = ''
        s = s + ImageFilePage(self.dinfo, self.imgfilename, self.imagetitle,
                              ImageFilePage.Side.left).page()
        s = s + ImageFilePage(self.dinfo, self.imgfilename, self.imagetitle,
                              ImageFilePage.Side.right).page()
        return s


# ############################################################################################

# A page whose content is made up of an EPS file.

class EPSFilePage(PostscriptPage):

    def __init__(self, dinfo, epsfilename, epstitle=None):
        PostscriptPage.__init__(self, dinfo)
        self.epsfilename = epsfilename
        self.epstitle = epstitle


    def findEPSFile(self, epsfilename):
        epsfilepathname = None
        # If we are given a full or relative-to-pwd path to the file, use that.
        if self.epsfilename.startswith('/') or self.epsfilename.startswith('./') \
               or self.epsfilename.startswith('../'):
            epsfilepathname = self.epsfilename
        else:
            # Otherwise, construct the full path to the file.  If we are running from the
            # development directory, or otherwise not from a full path name, look at relative
            # locations first.  In any case, we search the current directory first.
            if sys.argv[0].startswith('.'):
                searchpath = ['.', '..', '../..']
            else:
                searchpath = ['.']
            for p in sys.path:
                searchpath.append(p)
            #print >>sys.stderr, "searchpath is %s" % str(searchpath)
            for path in searchpath:
                epsfilepathname = self.searchfor(path, 'eps', self.epsfilename)
                if epsfilepathname:
                    break
        return epsfilepathname


    # FIXME this method is intended to factor out the bounding box, scaling and translation
    # stuff for both EPSFilePage and HalfEPSFilePage.  It is not used (yet).
    def calculateEPSStuff(self, boundingbox, maxwidth, maxheight):
        epsx1_pt, epsy1_pt, epsx2_pt, epsy2_pt = boundingbox
        epsx1 = epsx1_pt/self.di.points_mm
        epsy1 = epsy1_pt/self.di.points_mm
        epsx2 = epsx2_pt/self.di.points_mm
        epsy2 = epsy2_pt/self.di.points_mm
        epswidth  = epsx2 - epsx1
        epsheight = epsy2 - epsy1

        # Some space for layout.
        inset = self.pWidth / 200.0


    def body(self):
        s = ''

        # If we were supplied a string, it's a file name, otherwise we assume it's a file like
        # object.
        if isinstance(self.epsfilename, ''.__class__):
            try:
                epsfile = open(self.epsfilename, 'r')
            except IOError, reason:
                print >>sys.stderr, "Can't open %s: %s" % (self.epsfilename, str(reason))
                return "%% +++ Error opening %s: %s\n" % (self.epsfilename, str(reason))
        else:
            epsfile = self.epsfilename

        errmsg, boundingbox = self.findBoundingBoxInEPS(self.epsfilename, epsfile)
        if errmsg:
            print >>sys.stderr, "%s: %s" % (sys.argv[0], errmsg)
            return "%% +++ %s\n" % self.postscriptEscape(errmsg)

        if self.epstitle:
            s = s + self.title(self.epstitle)

        epsx1_pt, epsy1_pt, epsx2_pt, epsy2_pt = boundingbox
        epsx1 = epsx1_pt/self.di.points_mm
        epsy1 = epsy1_pt/self.di.points_mm
        epsx2 = epsx2_pt/self.di.points_mm
        epsy2 = epsy2_pt/self.di.points_mm
        epswidth  = epsx2 - epsx1
        epsheight = epsy2 - epsy1

        # Some space for layout.
        inset = self.pWidth / 200.0

        x = self.pLeft+inset
        y = self.pBottom+inset
        maxwidth = self.pWidth-2*inset
        maxheight = self.pHeight-2*inset

        s = s + self.di.sectionSep + "%% Beginning embedded PS file: %s\n" % self.epsfilename
        s = s + "%% x=%5.3f y=%5.3f maxwidth=%5.3f maxheight=%5.3f\n" % \
                (x,y,maxwidth,maxheight)
        s = s + "%% epsx1_pt=%7.3f   epsy1_pt=%7.3f   epsx2_pt=%7.3f   epsy2_pt=%7.3f\n" % \
                (epsx1_pt, epsy1_pt, epsx2_pt, epsy2_pt)
        s = s + "%% epsx1   =%7.3f   epsy1   =%7.3f   epsx2   =%7.3f   epsy2   =%7.3f\n" % \
                (epsx1, epsy1, epsx2, epsy2)

        # Make a clipping region.
        #s = s + "% Clipping path to contain the EPS file.\n"
        #s = s + "gsave newpath %.3f %.3f %.3f %.3f rectclip\n" % (x, y, maxwidth, maxheight)

        # Move to the required origin for the EPS
        s = s + "%5.3f %5.3f M\n" % (x, y) #(x+xoffset,y+yoffset)

        # Find out which of the x or y axes has to be adjusted.
        rawxscale = maxwidth / epswidth
        rawyscale = maxheight / epsheight
        if rawxscale == rawyscale:
            scale = rawxscale
            xadj = 0
            yadj = 0
        elif rawxscale < rawyscale:
            scale = rawxscale
            xadj = 0
            yadj = (maxheight - (epsheight * scale))/2.0
        else:
            scale = rawyscale
            xadj = (maxwidth - (epswidth * scale))/2.0
            yadj = 0

        s = s + "% Results from scaling:\n"
        s = s + "%% rawxscale=%5.3f rawyscale=%5.3f scale=%5.3f xadj=%5.3f yadj=%5.3f\n" % \
                (rawxscale,rawyscale,scale,xadj,yadj)
        xadj -= epsx1*scale
        yadj -= epsy1*scale
        s = s + "%% Then, xadj=%5.3f yadj=%5.3f\n" % (xadj,yadj)
        # Now go there
        s = s + "SA %5.3f %5.3f RM %5.3f %5.3f SC CP TR\n" % (xadj,yadj,scale,scale)

        epsp = self.embedEPS(self.epsfilename, epsfile)
        epsfile.close()
        return s + epsp


# ############################################################################################

# One page whose content is made up of a half of an EPS file.

class HalfEPSFilePage(EPSFilePage):

    # Sides
    LEFT = "Left"
    RIGHT = "Right"


    def __init__(self, dinfo, epsfilepathname, epstitle=None, side=LEFT):
        EPSFilePage.__init__(self, dinfo, None, epstitle)
        self.epsfilepathname = epsfilepathname
        self.side = side


    def body(self):
        '''New body() method.'''
        pe = self.postscriptEscape
        s = ''
        s += '%% %s: file=%s side=%s\n' % (self.__class__.__name__,
                                           pe(self.epsfilepathname),
                                           pe(self.side))

        if self.epstitle:
            s = s + self.title(self.epstitle)

        if self.di.debugBoxes:
            # This is a bit of an abuse of the --debug-boxes flag, but I think that's ok since
            # we would not normally want to print the file name info like this unless we're
            # drawing the debug boxes.
            fontSize = 2.2*self.di.pageHeight/210.0
            s += "/Courier %5.3f selectfont " % fontSize
            s += '%5.3f %5.3f M (%s, %s, %s) SH\n' % (self.pLeft+1, self.pBottom+1,
                                                      pe(self.__class__.__name__),
                                                      pe(self.side),
                                                      pe(self.epsfilepathname))

        try:
            epsfile = open(self.epsfilepathname, 'r')
        except IOError, reason:
            print >>sys.stderr, "%s: Can't open %s: %s" % (sys.argv[0],
                                                           self.epsfilepathname,
                                                           str(reason))
            return "%% +++ Error opening %s: %s\n" % (pe(self.epsfilepathname),
                                                      pe(str(reason)))

        errmsg, boundingbox = self.findBoundingBoxInEPS(self.epsfilepathname, epsfile)
        if errmsg:
            print >>sys.stderr, "%s: %s" % (sys.argv[0], errmsg)
            return "%% +++ %s\n" % self.postscriptEscape(errmsg)
        s = s + "%% %s: bounding box = %s\n" % (self.__class__.__name__, str(boundingbox))

        # Now find out how big the bounding box will be on the page.
        epsx1_pt, epsy1_pt, epsx2_pt, epsy2_pt = boundingbox
        epsx1 = epsx1_pt / self.di.points_mm
        epsy1 = epsy1_pt / self.di.points_mm
        epsx2 = epsx2_pt / self.di.points_mm
        epsy2 = epsy2_pt / self.di.points_mm
        eps_width  = epsx2 - epsx1
        eps_height = epsy2 - epsy1
        s = s + "%% %s: bounding box mm = %s\n" % (self.__class__.__name__,
                                                   str( (epsx1, epsy1, epsx2, epsy2) ))

        # Sanity check.  We can't operate with width or height <= 0.
        if eps_width <= 0 or eps_height <= 0:
            print >>sys.stderr, "%s: Cannot work with this bounding box: %s (file: %s)" % \
                (sys.argv[0], str(boundingbox), self.epsfilepathname)
            s += "%% Cannot work with this BoundingBox: %s\n" % str(boundingbox)
            return s

        # Some space for layout.
        inset = self.pWidth / 200.0
        maxwidth = self.pWidth - inset # Yes, only one inset.
        maxheight = self.pHeight - 2*inset

        # Calculate the scale factor.  We want the EPS page to expand to the maximum it can
        # before hitting the top and bottom, or hitting the left and right.
        eps_xscale = maxwidth * 2.0 / eps_width
        eps_yscale = maxheight / eps_height
        if eps_xscale == eps_yscale:
            scale = eps_xscale
        elif eps_xscale < eps_yscale:
            # The X dimension of the EPS file takes up more of the available space than does
            # the Y dimension.  So maximise the EPS to the X scale, and centre the Y.
            eps_scale = eps_xscale
        else:
            # The reverse of the previous case.
            eps_scale = eps_yscale

        # The Y position does not depend on the page side.
        if eps_scale == eps_yscale:
            # The Y dimension takes up the whole page in this case.
            ypos = self.pBottom + inset
        else:
            ypos = self.pBottom + inset + (maxheight - (eps_height * eps_scale)) / 2.0

        # The X position does depend on the page side.
        if self.side == self.LEFT:
            xpos = self.pLeft + inset + maxwidth - (eps_width * eps_scale / 2.0)
        else:
            xpos = self.pLeft - (eps_width * eps_scale / 2.0)

        # Now draw a debugging box around that bit, if it's requested.
        if self.di.debugBoxes:
            s += '0 SLW %5.3f %5.3f %5.3f %5.3f debugboxLBWH\n' % \
                (xpos, ypos, eps_width * eps_scale, eps_height * eps_scale)

        # If we're not drawing the debug boxes, then create a clipping region, so that the EPS
        # does not flow outside where the user would expect it.
        if not self.di.debugBoxes:
            clipw = eps_width * eps_scale / 2.0
            cliph = eps_height * eps_scale
            clipy = ypos
            if self.side == self.LEFT:
                clipx = xpos
            else:
                clipx = self.pLeft
            #s += '0 SLW %5.3f %5.3f %5.3f %5.3f debugboxLBWH\n' % \
            #    (clipx, clipy, clipw, cliph)
            s += 'newpath %5.3f %5.3f %5.3f %5.3f rectclip\n' % \
                (clipx, clipy, clipw, cliph)

        # To draw the EPS, we move to the calculated spot, adjusted by the first pair of
        # coordinates in the bounding box.  And that adjustment must be scaled.
        s += '%5.3f %5.3f M CP TR\n' % (xpos - epsx1*eps_scale, ypos - epsy1*eps_scale)

        # Debugging smiley.
        if self.di.debugBoxes:
            s += 'SA\n' + self.smiley() + 'RE\n'

        # Scale the EPS page
        s += "%5.3f %5.3f SC\n" % (eps_scale,eps_scale)

        s += self.embedEPS(self.epsfilepathname, epsfile)
        epsfile.close()

        return s


# ############################################################################################

# Two pages whose content is made up of two halves of an EPS file.

class TwoEPSFilePages(EPSFilePage):

    def __init__(self, dinfo, epsfilename, title1=None, title2=None):
        self.dinfo = dinfo
        self.epsfilename = epsfilename
        self.title1 = title1
        self.title2 = title2


    def page(self):
        s = ''

        epsfilepathname = self.findEPSFile(self.epsfilename)
        if epsfilepathname is None:
            print >>sys.stderr, "cannot find %s" % self.epsfilename
            return "%% %s: cannot find %s\n" % (self.__class__.__name__, self.epsfilename)
        s = s + "%% %s: found %s at %s\n" % (self.__class__.__name__,
                                             self.epsfilename, epsfilepathname)

        title1 = self.title1
        if title1 is not None and (self.title2 is None or self.title2 == ''):
            # This single space is a bit of a hack to get a line across underneath where the
            # title would go, without putting a title there.
            title2 = ' '
        else:
            title2 = self.title2
        s = s + HalfEPSFilePage(self.dinfo, epsfilepathname,
                                title1, HalfEPSFilePage.LEFT).page() \
              + HalfEPSFilePage(self.dinfo, epsfilepathname,
                                title2, HalfEPSFilePage.RIGHT).page()
        return s


# ############################################################################################

# Pages that contain a printed man page.

class ManPagePages(PostscriptPage):
    def __init__(self, dinfo, manPageInfo ):
        self.dinfo = dinfo
        self.manPageInfo = manPageInfo

    def page(self):
        # Get the output from running man.
        try:
            if self.manPageInfo[1] is None:
                # No man section specified
                man_args = ('man', '-t', self.manPageInfo[0])
                man_par_name = self.manPageInfo[0]
                man_nonpar_name = self.manPageInfo[0]
            else:
                man_args = ('man', '-t', self.manPageInfo[1], self.manPageInfo[0])
                man_par_name = "%s(%s)" % (self.manPageInfo[0], self.manPageInfo[1])
                man_nonpar_name = "%s %s" % (self.manPageInfo[1], self.manPageInfo[0])
            man_process = subprocess.Popen(man_args,
                                           shell=False,
                                           stdin=open('/dev/null'),
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           close_fds=True)
            #print str(man_process)
            man_stdout, man_stderr = man_process.communicate()
            man_returncode = man_process.returncode
            if man_returncode:
                print >>sys.stderr, "%s: cannot get man page for %s: (%d):\n%s" % \
                      (sys.argv[0], man_par_name, man_returncode, man_stderr)
                return "%% -- Cannot run man -t %s\n" % man_nonpar_name
        except OSError, e:
            print >>sys.stderr, "%s: cannot run ``man -t %s'': (%d):\n%s" % \
                  (sys.argv[0], man_nonpar_name, e.errno, e.strerror)
            return "%% -- Cannot run man -t %s %s\n" % man_nonpar_name

        # Convert the man output into EPS.
        try:
            eps_process = subprocess.Popen(('ps2eps'),
                                           shell=False,
                                           stdin=subprocess.PIPE,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           close_fds=True)
            eps_stdout, eps_stderr = eps_process.communicate(man_stdout)
            eps_returncode = eps_process.returncode
            if eps_returncode:
                print >>sys.stderr, "%s: error running ps2eps: (%d):\n%s" % \
                      (sys.argv[0], eps_returncode, eps_stderr)
                return "% -- Cannot run ps2eps\n"
        except OSError, e:
            print >>sys.stderr, "%s: cannot run ps2eps: (%d):\n%s" % \
                  (sys.argv[0], e.errno, e.strerror)
            return "% -- Cannot run ps2eps\n"

        # We don't need these any more.
        man_stdout = None
        man_stderr = None
        eps_stderr = None

        # Prepare the return string.
        s = ''

        # Now for each page, add our page with the EPS in it.  We loop until psselect tells us
        # that it has reached the end.  It does that by returning a completely empty page,
        # rather than with an error or return code.
        pageNumber = 1
        while True:
            #print >>sys.stderr, "Getting page %d" % pageNumber
            try:
                pss_process = subprocess.Popen(('psselect', '-p%d'%pageNumber),
                                               shell=False,
                                               stdin=subprocess.PIPE,
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE,
                                               close_fds=True)
                pss_stdout, pss_stderr = pss_process.communicate(eps_stdout)
                pss_returncode = pss_process.returncode
                if pss_returncode:
                    print >>sys.stderr, "%s: cannot get page %d using psselect: (%d):\n%s" % \
                          (sys.argv[0], pageNumber, pss_returncode, pss_stderr)
                    s += "%% Cannot run psselect -p%d\n" % pageNumber
                    return s
            except OSError, e:
                print >>sys.stderr, "%s: cannot get page %d: (%d):\n%s" % \
                      (sys.argv[0], pageNumber, pss_returncode, pss_stderr)
                s += "%% Cannot get page %d" % pageNumber
                return s

            # Check to see if the page was extracted, or if psselect just gave us an empty
            # page, which is what it does when we ask for a page after the end of the document.
            if not re.search('''^%%Page:''', pss_stdout, re.MULTILINE):
                return s

            # Get our diary page, with the EPS page embedded.
            epsString = StringIO.StringIO(pss_stdout)
            s += EPSFilePage(self.dinfo, epsString).page()

            pageNumber += 1


        return "%% -- man %s(%s)\n" % self.manPageInfo


# ############################################################################################

# An empty page.

class EmptyPage(PostscriptPage):
    def body(self):
        return "% --- An empty page\n"

# ############################################################################################

# An almost empty page, with version information printed.

class VersionPage(PostscriptPage):
    def body(self):
        fontSize = 2.1*self.di.pageHeight/210.0
        linex = fontSize*6
        s=""
        versionString = self.postscriptEscape(versionNumber)
        dateString = self.postscriptEscape(DateTime.now() \
                                           .strftime("Generated at: %Y-%m-%dT%H:%M:%S%Z"))
        urlString = "http://adelie.cx/makediary/"
        s = s + "% --- Version page\n" \
            + "/Courier %5.3f selectfont " % fontSize \
            + "%5.3f %5.3f M (%s) SH\n" % (linex, fontSize*12, versionString) \
            + "%5.3f %5.3f M (%s) SH\n" % (linex, fontSize*10, dateString) \
            + "%5.3f %5.3f M (%s) SH\n" % (linex, fontSize*8, urlString)
        liney = self.di.pageHeight*0.9
        s = s + "%5.3f %5.3f M (Command:) SH\n" % (linex, liney)
        liney = liney - fontSize*1.25
        s = s + "%5.3f %5.3f M (   %s) SH\n" % (linex, liney, self.di.myname)
        liney = liney - fontSize*1.25
        for i in range(len(self.di.opts)):
            s = s + "%5.3f %5.3f M (   %s) SH\n" % (linex, liney,
                                                    self.postscriptEscape(self.di.opts[i]))
            liney = liney - fontSize*1.25
        liney = liney - fontSize*2.5
        for i in range(len(self.di.usageStrings)):
            s = s + "%5.3f %5.3f M (%s) SH\n" % (linex, liney,
                                                 self.postscriptEscape(self.di.usageStrings[i]))
            liney = liney - fontSize*1.25
        return s

# ############################################################################################

class NotSoEmptyPage(PostscriptPage):
    def body(self):
        return "% Not so empty\n" + self.title("Not So Empty")

# ############################################################################################

class CoverPage(PostscriptPage):
    def body(self):
        xleft = self.di.iMargin + self.di.iMargin
        xright = self.di.pageWidth - self.di.oMargin - self.di.iMargin
        ybottom = self.di.bMargin + self.di.iMargin
        ytop = self.di.pageHeight - self.di.tMargin - self.di.iMargin
        textheight = self.di.coverTitleFontSize
        picxprop = 0.8
        picyprop = 0.8
        textycentre = (ytop-ybottom) * 0.66 + ybottom - textheight/2
        textxcentre = (xright-xleft)/2 + xleft

        s = ''

        if self.di.coverPageImage is not None:
            l = self.pLeft
            b = self.pBottom
            w = self.pWidth
            h = self.pHeight
            s += "%% -- %s -- image is %s\n" % (self.__class__.__name__,
                                                self.postscriptEscape(self.di.coverPageImage))
            s += "%% l=%5.3f b=%5.3f w=%5.3f h=%5.3f\n" % (l, b, w, h)
            s += self.image(self.di.coverPageImage, l, b, w, h)
            return s

        if self.di.title is not None:
            title = self.di.title
        elif self.di.dtbegin.month==1 and self.di.dtbegin.day==1:
            title = "%d" % self.di.dtbegin.year
        else:
            title = "%04d-%02d" % (self.di.dtbegin.year, (self.di.dtbegin.year+1) % 100)

        s =   "% --- cover page\n" \
            + "10 dict begin /availablewidth %5.3f def /xleft %5.3f def /title (%s) def\n" % \
            (0.90*(xright - xleft), xleft, self.postscriptEscape(title.replace('\n','\\n'))) \
            + "/textheight %5.3f def /textxcentre %5.3f def /textycentre %5.3f def\n" % \
            (textheight, textxcentre, textycentre) \
            + "% border around the cover page\n" \
            + "%5.3f %5.3f %5.3f %5.3f %5.3f boxLBRT\n" % \
            (xleft,ybottom,xright,ytop,self.di.underlineThick)

        # Now we find out how wide the title is, and if it's wider than the box we reduce the
        # font to make it fit.
        titlestrings = title.split('\n')

        s = s + "/Times-Roman textheight selectfont\n" \
            + "% find the width of the title string\n" \
            + "/titlewidth 0\n"

        for ts in titlestrings:
            s = s + "(%s) SW pop max\n" % self.postscriptEscape(ts)
        s = s + "def\n"

        # If we have a wide title, print the title in a smaller font.
        s = s + "titlewidth availablewidth gt " \
            + "{ /textheight availablewidth titlewidth div textheight mul def } if\n" \
            + "/Times-Roman textheight selectfont\n"

        # If there is more than one line in the title, move up a bit and start there.
        if len(titlestrings) > 1:
            s = s + "/textycentre %5.3f %d textheight 2 div mul 1.1 mul add def\n" % \
                (textycentre, len(titlestrings))

        # Now print the titles.
        for ts in titlestrings:
            s = s + "(%s) dup textxcentre exch SW pop 2 div sub textycentre M SH\n" % \
                self.postscriptEscape(ts) \
                + "/textycentre textycentre textheight 1.1 mul sub def\n"

        s = s + "end\n"

        if self.di.coverImage==None:
            if self.di.smiley:
                smileysize = self.di.coverTitleFontSize
                smileyycentre = ((ytop-ybottom) * 0.33) + ybottom
                smileyxcentre = textxcentre
                s = s \
                    + "% a big smiley face\n" \
                    + ("%5.2f %5.2f M SA %5.2f dup SC\n" % \
                       (smileyxcentre,smileyycentre,smileysize)) \
                    + self.smiley() \
                    + "RE\n"
        else:
            picxsize = (xright-xleft) * picxprop
            picysize = (xright-xleft) * picyprop
            picleft = xleft + (xright-xleft) * (1-picxprop)/2.0
            picbottom = ybottom + (xright-xleft) * (1-picyprop)/2.0
            # Draw a faint line around the image square, for debugging
            #if self.di.debugBoxes:
            #    s = s + "% debugging box for image\n" \
            #        + "0 SLW %5.3f %5.3f %5.3f %5.3f 2 debugboxLBWHD\n" % \
            #        (picleft,picbottom,picxsize,picysize)
            s = s \
                + "%% cover image: %s bottom=%5.3f left=%5.3f xsize=%5.3f ysize=%5.3f\n" % \
                (self.di.coverImage,picbottom,picleft,picxsize,picysize) \
                + self.image(self.di.coverImage,picleft,picbottom,picxsize,picysize)
        #s = s + self.image("c2-small.bmp",60,30,20,20)
        return s


# ############################################################################################

class CalendarPage(PostscriptPage):
    def body(self):
        # Configurable variables
        mvprop = 0.92                   # proportion of month box that gets printed in
        mhprop = 0.90                   # proportion of month box that gets printed in
        # Calculated variables
        mvspacing = self.pHeight/(9.0+3.0*(1.0-mvprop)) # total height of a month box
        mhspacing = self.pWidth/4.0     # total width of a month box
        mvsize = mvspacing * mvprop     # vertical size of the printed part of the month box
        mhsize = mhspacing * mhprop     # horiz size of ...
        mvgap = mvspacing * (1.0-mvprop) # gap between months
        mhgap = mhspacing * (1.0-mhprop) # gap between months
        bottom = self.di.bMargin
        yheight = 3.0 * mvspacing       # height of a year
        yvgap = mvspacing * (1.0-mvprop) # extra gap between years (see above)
        s =   self.title("Calendars") + self.bottomline()
        if self.di.evenPage:
            left = self.di.oMargin
        else:
            left = self.di.iMargin
        # Box around the current (middle) year
        bleft = left
        bright = left + self.pWidth
        btop = bottom + yheight*2.0 + yvgap*2.0
        bbottom = bottom + yheight + yvgap
        bs =   ("0 SLW %5.3f %5.3f M %5.3f %5.3f L " % (bleft,bbottom,bleft,btop)) \
             + ("%5.3f %5.3f L %5.3f %5.3f L " % (bright,btop,bright,bbottom)) \
             + ("%5.3f %5.3f L " % (bleft,bbottom)) \
             + "gsave %5.3f setgray fill grestore S\n" % ((1.0+self.di.titleGray)/2.0,)
        s = s + bs
        yr = self.di.dtbegin.year
        for yd in ((yr-1, left, bottom + yheight*2.0 + yvgap*2.5 ),
                   (yr,   left, bottom + yheight + yvgap*1.5),
                   (yr+1, left, bottom + yvgap*0.5)):
            year = yd[0]
            x = yd[1]
            y = yd[2]

            for m in range(1,13):
                my = y + mvspacing * (2-int((m-1)/4)) + mvgap*0.5
                mx = x + ((m-1) % 4) * mhspacing + mhgap*0.5
                mname = self.di.getMonthCalendarPsFnCall(year,m)
                ms = "%5.3f %5.3f M SA %5.3f %5.3f SC %s RE\n" % \
                     (mx,my,mhsize,mvsize,mname)
                s = s + ms
        return s


# ############################################################################################

class HalfCalendarPage(PostscriptPage):

    def __init__(self,dinfo):
        PostscriptPage.__init__(self,dinfo)

    def body(self):
        # Configurable variables
        mvprop = 0.92                   # proportion of month box that gets printed in
        mhprop = 0.90                   # proportion of month box that gets printed in
        # Calculated variables
        mvspacing = self.pHeight/(6.0+3.0*(1.0-mvprop)) # total height of a month box
        mhspacing = self.pWidth/3.0     # total width of a month box
        mvsize = mvspacing * mvprop     # vertical size of the printed part of the month box
        mhsize = mhspacing * mhprop     # horiz size of ...
        mvgap = mvspacing * (1.0-mvprop) # gap between months
        mhgap = mhspacing * (1.0-mhprop) # gap between months
        bottom = self.di.bMargin
        yheight = 2.0 * mvspacing       # height of a year
        yvgap = mvspacing * (1.0-mvprop) # extra gap between years (see above)
        if self.di.evenPage:
            left = self.di.oMargin
        else:
            left = self.di.iMargin

        s = ''
        s = s + self.title("Calendars") + self.bottomline()
        if self.di.evenPage: ss = 'even'
        else:                ss = 'odd'
        s = s + '%% --- HalfCalendarPage, on an %s page\n' % ss


        # Box around the current (middle) year
        bleft = left
        bright = left + self.pWidth
        btop = bottom + yheight*2.0 + yvgap*2.0
        bbottom = bottom + yheight + yvgap
        # Leave the inside margin side of the box without a line
        if self.di.evenPage:
            bs = "%5.3f SLW " % self.di.underlineThick \
                 + "%5.3f %5.3f M %5.3f %5.3f L " % (bright,bbottom,bleft,bbottom) \
                 + "%5.3f %5.3f L %5.3f %5.3f L " % (bleft,btop,bright,btop) \
                 + "gsave %5.3f setgray fill grestore S\n" % ((1.0+self.di.titleGray)/2.0,)
        else:
            bs = "%5.3f SLW " % self.di.underlineThick \
                 + "%5.3f %5.3f M %5.3f %5.3f L " % (bleft,bbottom,bright,bbottom) \
                 + "%5.3f %5.3f L %5.3f %5.3f L " % (bright,btop,bleft,btop) \
                 + "gsave %5.3f setgray fill grestore S\n" % ((1.0+self.di.titleGray)/2.0,)
        s = s + bs

        # Make a list detailing where the months are to go.  The list contains tuples of (year,
        # month, row, column).
        y = self.di.dtbegin.year
        if self.di.evenPage:
            months = ( (y-1, 1, 0, 0), (y-1, 2, 0, 1), (y-1, 3, 0, 2),
                       (y-1, 7, 1, 0), (y-1, 8, 1, 1), (y-1, 9, 1, 2),
                       (y,   1, 2, 0), (y,   2, 2, 1), (y,   3, 2, 2),
                       (y,   7, 3, 0), (y,   8, 3, 1), (y,   9, 3, 2),
                       (y+1, 1, 4, 0), (y+1, 2, 4, 1), (y+1, 3, 4, 2),
                       (y+1, 7, 5, 0), (y+1, 8, 5, 1), (y+1, 9, 5, 2) )
        else:
            months = ( (y-1, 4,  0, 0), (y-1, 5,  0, 1), (y-1, 6,  0, 2),
                       (y-1, 10, 1, 0), (y-1, 11, 1, 1), (y-1, 12, 1, 2),
                       (y,   4,  2, 0), (y,   5,  2, 1), (y,   6,  2, 2),
                       (y,   10, 3, 0), (y,   11, 3, 1), (y,   12, 3, 2),
                       (y+1, 4,  4, 0), (y+1, 5,  4, 1), (y+1, 6,  4, 2),
                       (y+1, 10, 5, 0), (y+1, 11, 5, 1), (y+1, 12, 5, 2) )

        # Now print each month
        for month in months:
            thisy = month[0]
            thism = month[1]
            thisr = month[2]
            thisc = month[3]
            s = s + "%% year=%d month=%d row=%d column=%d\n" % (thisy,thism,thisr,thisc)
            mbottom = bottom + self.pHeight - (thisr+1)*mvspacing
            if thisr >=4 : mbottom = mbottom - 2.0*mvgap
            elif thisr >= 2: mbottom = mbottom - mvgap
            mleft = left + thisc*mhspacing + mhgap*0.5
            mname = self.di.getMonthCalendarPsFnCall(thisy,thism)
            s = s + "%5.3f %5.3f M SA %5.3f %5.3f SC %s RE\n" % \
                (mleft, mbottom, mhsize, mvsize, mname)

        return s


# ############################################################################################

class TwoCalendarPages:

    def __init__(self,dinfo):
        self.dinfo = dinfo

    def page(self):
        s = ''
        s = s + HalfCalendarPage(self.dinfo).page()
        s = s + HalfCalendarPage(self.dinfo).page()
        return s



# ############################################################################################

class PerpetualYear:
    """Hold all the information about particular year calendars.

    This class has static member dictionaries that are maps from (b,e)->c, c->years, and
    year->c, where b and e are the day of the week of the first and last days of the year, and
    c is a character from 'A' to 'N'.  It also contains a list of years that are to go on the
    perpetual calendars list.

    To add a year to the list, create an instance with PerpetualYear(year).  You don't have to
    hold on to that object, as all information goes into the class members.
    """
    d2c = {}                            # Map ((b,e)->titlechar)
    c2years = {}                        # Map (c->years)
    year2c = {}                         # Map (year->c)
    years = []
    for d in range(7):
        for leap in (0,1):
            be_dow = (d, (d+leap)%7)    # Beginning and end dow of a year.
            c = chr(ord('A')+d+(leap*7))
            d2c[be_dow] = c
            c2years[c] = []

    def __init__(self, year):
        d0 = DateTime.DateTime(year, 1, 1).day_of_week
        d9 = DateTime.DateTime(year,12,31).day_of_week
        be_dow = (d0,d9)
        c = PerpetualYear.d2c[be_dow]
        # Append this year to the relevant list.
        PerpetualYear.c2years[c].append(year)
        PerpetualYear.year2c[year] = c
        PerpetualYear.years.append(year)


# ############################################################################################

class FourPerpetualCalendarsPage(PostscriptPage):

    def __init__(self, dinfo, char, nchars):
        PostscriptPage.__init__(self, dinfo)
        self.char = char                # char to year
        self.nchars = nchars            # number of chars to use for calendars
        # Configurable variables
        self.mvprop = 0.92              # proportion of month box that gets printed in
        self.mhprop = 0.90              # proportion of month box that gets printed in

    def body(self):
        # Calculated stuff
        yboxh = (self.di.titleLineY - self.pBottom) / 4.0
        yboxw = self.pWidth
        s = '% ----- FourPerpetualCalendarsPage\n'
        s += self.title("Perpetual calendars")
        y = self.pBottom + 4.0 * yboxh
        if self.nchars < 4:
            s += self.perpetualYearLists(self.pLeft, self.pBottom + 2.0*yboxh,
                                         yboxw, yboxh*2.0)
            y -= 2.0*yboxh
        for i in range(self.nchars):
            y -= yboxh
            s += self.perpetualYear(self.pLeft, y, yboxw, yboxh - 1.0, chr(ord(self.char)+i))
        return s

    def perpetualYear(self, l, b, w, h, char):
        '''Create a whole calendar for a year identified by a title char.

        All other data for the calendar is got by interrogating the PerpetualYear class static
        members.
        '''
        years = PerpetualYear.c2years[char]
        s = '%% ---- A perpetual year calendar\n'
        s += "%% --- years[0]: %d\n" % years[0]
        if self.di.debugBoxes:
            s += "%5.3f %5.3f %5.3f %5.3f debugboxLBWH\n" % (l, b, w, h)
        titlefontsize = h / 10.0
        if self.di.evenPage:
            ml = l + 1.5*titlefontsize
        else:
            ml = l
        mwidth = (w - 1.5*titlefontsize) / 6.0
        mheight = h / 2.0
        # On an odd page, shift everything away from the gutter.  See the comment below.
        s += "/Helvetica findfont [%5.3f 0 0 %5.3f 0 0] makefont setfont\n" % \
             (titlefontsize, titlefontsize)
        if self.di.evenPage:
            s += "%5.3f %5.3f M (%s) SH\n" % (l, b+(h-titlefontsize)/2.0, char)
            s += "%5.3f SLW %5.3f %5.3f M %5.3f 0 RL 0 %5.3f RL %5.3f 0 RL S\n" % \
                 (self.di.underlineThick * 0.6,
                  ml-0.25*titlefontsize, b, -0.25*titlefontsize,
                  2.0*mheight, 0.25*titlefontsize)
        else:
            s += "%5.3f (%s) SW pop sub %5.3f M (%s) SH\n" % \
                (l+w, char, b+(h-titlefontsize)/2.0, char)
            s += "%5.3f SLW %5.3f %5.3f M %5.3f 0 RL 0 %5.3f RL %5.3f 0 RL S\n" % \
                 (self.di.underlineThick * 0.6,
                  ml+6.0*mwidth+0.25*titlefontsize, b, 0.25*titlefontsize,
                  2.0*mheight, -0.25*titlefontsize)
        mbottom = b + mheight
        for m in range(1,13):
            dt = DateTime.DateTime(years[0], m)
            mleft = ml + (((m-1) % 6) * mwidth)
            # Because we make the months slightly smaller than the available space, they seem
            # to be shifted left.  When we are printing on an odd (right side) page, make them
            # shift right, so we shift away from the gutter in both cases.
            if not self.di.evenPage:
                mleft += mwidth * (1.0 - self.mhprop)
            if m == 7:
                mbottom -= mheight
            s += "%5.3f %5.3f M SA %5.3f %5.3f SC %s RE\n" % \
                 (mleft, mbottom, mwidth*self.mhprop, mheight*self.mvprop,
                  self.di.getMonthCalendarPsFnCall(years[0], m, addyear=False))
        return s

    def perpetualYearLists(self, l, b, w, h):
        '''Create the lists of perpetual years on half of a page.
        '''
        s = ''
        fontsize = h / 45.0
        rowheight = fontsize * 1.3
        columnwidth = fontsize * 5.0
        columntextwidth = fontsize * 3.5 # Estimated width of text.
        columnpos = l + 1.0 + (columnwidth * 0.3)
        toprowpos = b + h - (2.0 * fontsize)
        rowpos = toprowpos
        bottomrowpos = b + rowheight
        s += "/Helvetica findfont [%5.3f 0 0 %5.3f 0 0] makefont setfont\n" % \
             (fontsize, fontsize)
        for year in PerpetualYear.years:
            c = PerpetualYear.year2c[year]
            s += "%5.3f %5.3f M (%d) SH %5.3f (%s) SWP2D sub %5.3f M (%s) SH\n" % \
                 (columnpos, rowpos, year, columnpos + 3.0*fontsize, c, rowpos, c)
            rowpos -= rowheight
            if rowpos <= bottomrowpos:
                rowpos = toprowpos
                columnpos += columnwidth
                if columnpos + columntextwidth > l + w:
                    break
        return s



# ############################################################################################

class PerpetualCalendarPages:

    def __init__(self,dinfo):
        self.di = dinfo
        # Generate the lists of years.
        year = self.di.dt.year - 301
        year -= year % 100
        # Do lots of years.  They don't take up much memory and the page will stop printing
        # years when the page area fills up.
        for i in range(year, year+451):
            # We don't have to keep this object.
            PerpetualYear(i)

    def page(self):
        s = ''
        s += FourPerpetualCalendarsPage(self.di, 'A', 2).page()
        s += FourPerpetualCalendarsPage(self.di, 'C', 4).page()
        s += FourPerpetualCalendarsPage(self.di, 'G', 4).page()
        s += FourPerpetualCalendarsPage(self.di, 'K', 4).page()
        return s



# ############################################################################################

class PersonalInformationPage(PostscriptPage):

    def __init__(self, dinfo):
        PostscriptPage.__init__(self, dinfo)
        self.linenum = 1                #
        self.linespacing = 0            #
        self.minlines = 20              # Required no of lines to fit in all our info

    def body(self):
        # These gymnastics with linespacing are to ensure we get an even spacing of lines
        # over the page.
        initiallinespacing = self.di.lineSpacing * 1.25
        nlines = int(self.pHeight / initiallinespacing)
        if nlines < self.minlines:
            nlines = self.minlines
        self.linespacing = float(self.pHeight) / float(nlines)
        s = ""
        s = s + "%--- Personal Information Page\n" \
            + "%% pheight=%5.3f nlines=%5.3f initial=%5.3f spacing=%5.3f\n" \
            % (self.pHeight,nlines,initiallinespacing,self.linespacing) \
            + self.title("Personal Information") \
            + self.bottomline()
        s = s + "SA %5.3f %5.3f TR\n" % (self.pLeft,self.pBottom)
        fontsize = self.linespacing * 0.5
        s = s + "/%s %5.3f selectfont\n" % (self.di.subtitleFontName,fontsize)

        co = self.di.configOptions
        if not co.has_section("Personal Information"):
            co.add_section("Personal Information")
        s = s \
            + self.do1line( co, [ ("Name"   , ("Name",),        ),        ] ,0) \
            + self.do1line( co, [ ("Phone"  , ("Phone",)        ),
                                  (("Mobile", "Cell"),
                                   ("Mobile", "Cell") ),                  ] ,0) \
            + self.do1line( co, [ ("Email"  , ("Email",
                                               "Email address") ),        ] ,0) \
            + self.do1line( co, [ ("Address", ("Address", )     ),        ] ,0) \
            + self.do1line( co, [                                         ] ,0) \
            + self.do1line( co, [                                         ] ,0) \
            + self.do1line( co, [ ("Work"   , (             )   ),        ] ,0) \
            + self.do1line( co, [ ("Phone"  , ("Work phone",)   ),
                                  (("Mobile", "Cell"),
                                   ("Work mobile", "Work cell") ),        ] ,0) \
            + self.do1line( co, [ ("Email"  , ("Work email",)   ),        ] ,0) \
            + self.do1line( co, [ ("Address", ("Work address",) ),        ] ,0) \
            + self.do1line( co, [                                         ] ,0) \
            + self.do1line( co, [                                         ] ,0) \
            + self.do1line( co, [ ("Emergency Contacts", ()     ),        ] ,0) \
            + self.do1line( co, [ ("", ("Emergency Contact 1",),),        ] ,0) \
            + self.do1line( co, [ ("", ("Emergency Contact 2",),),        ] ,0) \
            + self.do1line( co, [ ("", ("Emergency Contact 3",),),        ] ,0) \
            + self.do1line( co, [ ("", ("Emergency Contact 4",),),        ] ,0) \
            + self.do1line( co, [ ("Other Information" , ()     ),        ] ,0)

        while self.linenum < nlines:
            s = s + self.do1line( co, [ ] ,0)

        s = s + "RE\n"
        return s

    def do1line(self, config, title_info_pairs, linethick):
        """Do one line of the personal information page."""
        s = ""
        texty = self.pHeight - self.linenum*self.linespacing + 0.2*self.linespacing
        fontsize = self.linespacing * 0.5
        infofontsize = fontsize * 1.1 # Times font appears smaller than helvetica
        nelements = len(title_info_pairs)
        thiselement = 0
        nameindex = 0
        for title_info in title_info_pairs:
            titles = title_info[0]
            infos = title_info[1]
            info_index_count = 0
            info_index = 0
            info_string = None
            for info in infos:
                if config.has_option("Personal Information", info):
                    info_string = config.get("Personal Information", info)
                    info_index = info_index_count
                    break
                else:
                    info_index_count += 1
            if isinstance(titles, tuple):
                # If there is no info specified for this title, the index defaults to 0, so we
                # get the first of the possible titles when a tuple is supplied.
                title_string = titles[info_index]
            else:
                title_string = titles

            title = self.postscriptEscape(title_string)
            s = s + "/%s %5.3f selectfont\n" % (self.di.subtitleFontName,fontsize)
            s = s + "%5.3f %5.3f M (%s) SH \n" % (self.pWidth * thiselement / nelements, texty,
                                                  title)
            if info_string:
                info = self.postscriptEscape(info_string)
                # This is deliberately printed in the previous font.
                s = s + "( - ) SH\n"
                if "email" in title_string.lower():
                    s = s + "/%s %5.3f selectfont\n" % (self.di.personalinfoFixedFontName,
                                                        infofontsize)
                else:
                    s = s + "/%s %5.3f selectfont\n" % (self.di.personalinfoFontName,
                                                        infofontsize)
                s = s + "(%s) SH\n" % info
            thiselement += 1
        liney = self.pHeight - self.linenum * self.linespacing
        if linethick:
            s = s + "%5.2f SLW " % self.di.underlineThick
        else:
            s = s + "0   SLW "
        s = s + "0 %5.3f M %5.3f 0 RL S\n" % (liney,self.pWidth)
        self.linenum = self.linenum + 1
        return s


# ############################################################################################

class PlannerPage(PostscriptPage):
    year = 0                            # The planner year
    nlines = 31+6+2                     # Number of lines on page
    lineheight = 0                      # Height of each line (between baselines)
    daywidth = 11.0                     # Width of day titles column
    monthwidth = 0                      # Width of each month column
    fontsize = 0                        # Font size...
    textb = 0                           # Text bottom (within the box)
    top = 0                             # Page limits
    bottom = 0
    nondaygray = -1                     # Grey levels for day boxes
    weekendgray = -1

    def __init__(self, year, startingmonth, nmonths, dinfo, doEvents):
        PostscriptPage.__init__(self, dinfo)
        self.nondaygray = self.di.titleGray
        self.weekendgray = (1.0+self.di.titleGray)/2.0
        self.titlegray = self.weekendgray
        self.year = year
        self.startingmonth = startingmonth
        self.nmonths = nmonths
        self.top = self.pTop - 2.0 # was 5.0
        self.bottom = self.pBottom + 2.0 # was 5.0
        self.lineheight = float(self.top - self.bottom) / float(self.nlines)
        self.daywidth = self.lineheight * 2
        self.monthwidth = float(self.pWidth - self.daywidth) / nmonths
        self.fontsize = self.lineheight * 0.7
        self.textb = self.lineheight * 0.2
        self.titleboxThick = self.di.underlineThick / 2.0
        self.doEvents = doEvents


    def dayColumn(self,l,b):
        """Print one day title column at a certain place on the page."""
        s = ""
        s = s + "%% year=%d ptop=%5.3f top=%5.3f pbottom=%5.3f bottom=%5.3f\n" % \
            (self.year,self.pTop,self.top,self.pBottom,self.bottom)
        s = s + "SA %5.3f %5.3f TR\n" % (l,b)
        firstdayb = self.lineheight * (self.nlines - 2)
        s = s + "/%s %5.3f selectfont\n" % (self.di.subtitleFontName,self.fontsize)
        for i in range(0,self.nlines-2):
            # dayb is the bottom of this day box.
            dayb = firstdayb - (i * self.lineheight)
            # Draw the box and fill it with gray (or grey?)
            s = s + "0 %5.3f %5.3f %5.3f %5.3f %5.3f boxLBWHgray " % \
                (dayb,self.daywidth,self.lineheight,self.titleboxThick,self.titlegray)
            # Now assume MONDAY==0 etc.  FIXME: This needs locale stuff.  Mmmm, how?
            daynum = i % 7
            if   daynum==0: dayname="Mon"
            elif daynum==1: dayname="Tue"
            elif daynum==2: dayname="Wed"
            elif daynum==3: dayname="Thu"
            elif daynum==4: dayname="Fri"
            elif daynum==5: dayname="Sat"
            elif daynum==6: dayname="Sun"
            else:           dayname="Unknown day:%d" % daynum # Should never happen
            s = s + "(%s) dup %5.3f exch SW pop sub 2 div %5.3f M SH\n" \
                  % (dayname,self.daywidth,dayb+self.textb)
        s = s + "RE\n"
        return s

    def monthColumn(self,l,b,month):
        s = "SA %5.3f %5.3f TR\n" % (l,b)
        s = s + "/%s %5.3f selectfont 0 SLW\n" % (self.di.subtitleFontName,self.fontsize)
        dt = DateTime.DateTime(self.year, month)
        days = []
        # Add all the days into one flat list.
        for day in range(0,dt.day_of_week):
            days.append(0)
        for day in range(1, 1+dt.days_in_month):
            days.append(day)
        # Bottom of the highest day box
        firstdayb = self.lineheight * (self.nlines - 1)
        s = s + "%% Day boxes for month %d\n0 SLW\n" % month
        # Do boxes for the whole set of lines
        for n in range(self.nlines-2):
            eventlist = None
            isholiday = 0
            if n<len(days)  and  days[n]!=0:
                dd = DateTime.DateTime(self.year, month, days[n])
                if self.di.events.has_key(dd):
                    #sys.stderr.write("%s has events\n" % dd)
                    eventlist = self.di.events[dd]
                    for event in eventlist:
                        if event.has_key('holiday'):
                            #sys.stderr.write("%s is a holiday: %s\n" % (dd,str(event)))
                            isholiday = 1
            dayb = (self.nlines-n-2) * self.lineheight
            # If this is not a day of the month, fill it a bit darker
            if n>=len(days)  or  days[n]==0:
                s = s + "0 %5.3f %5.3f %5.3f 0 %5.3f boxLBWHgray " % \
                    (dayb,self.monthwidth,self.lineheight,self.nondaygray)
            else:
                # Fill the weekends and holidays slightly grey
                if (n%7==DateTime.Saturday)  or  (n%7==DateTime.Sunday) or isholiday:
                    s = s + "0 %5.3f %5.3f %5.3f %5.3f %5.3f boxLBWHgray " % \
                        (dayb,self.monthwidth,self.lineheight,self.titleboxThick,self.weekendgray)
                # All the other days are white
                else:
                    s = s + "0 %5.3f %5.3f %5.3f 0 boxLBWH\n" % \
                        (dayb,self.monthwidth,self.lineheight)
            if n<len(days)  and  days[n]!=0:
                # Now fill in the day number, if required
                s = s + "/%s %5.3f selectfont %5.3f %5.3f M (%d) SH\n" % \
                    (self.di.subtitleFontName, self.fontsize,
                     self.textb, dayb+self.textb, days[n])
                # Fill in the short calendar event names, if requested
                if self.doEvents:
                    if eventlist is not None:
                        #sys.stderr.write("planner: events for %s: %s\n" % (str(dd),eventlist))
                        se = ""             # event list string
                        for event in eventlist:
                            if event.has_key("short") and not event.has_key("_warning") \
                                and event["short"] != ' ':
                                if event.has_key("personal"):
                                    font = self.di.subtitleFontName + "-Oblique"
                                else:
                                    font = self.di.subtitleFontName
                                if event.has_key("small"):
                                    eventFontSize = self.fontsize*0.3
                                else:
                                    eventFontSize = self.fontsize*0.6
                                if len(se)==0:
                                    se = "/%s %5.3f selectfont (%s) SH " % \
                                         (font, eventFontSize,
                                          self.postscriptEscape(event["short"]))
                                else: se = se + \
                                           "/%s %5.3f selectfont (, ) SH " % \
                                           (self.di.subtitleFontName, self.fontsize*0.6) + \
                                           "/%s %5.3f selectfont (%s) SH " % \
                                           (font, eventFontSize,
                                            self.postscriptEscape(event["short"]))

                        if len(se) != 0:
                            s = s + "%% events for %s\n" % dd.strftime("%Y-%m-%d")
                            # Clip to the current day box to avoid events text spilling outside
                            # that box.
                            s = s + "gsave 0 %5.3f %5.3f %5.3f rectclip\n" % \
                                (dayb,self.monthwidth,self.lineheight)
                            se = "%5.3f %5.3f M " %(self.lineheight*1.1, dayb+self.textb) + \
                                 se + "\n"
                            s = s + se
                            s = s + "grestore\n"

        # Do the month titles (top and bottom). We attempt to make this localised, by using
        # strftime(), but that doesn't appear to work, even with LANG and LC_TIME set in the
        # environment.
        monthname = DateTime.DateTime(2000,month).strftime("%B")

        for monthtb in (0.0, (self.lineheight*(self.nlines-1))):
            s = s + "0 %5.3f %5.3f %5.3f %5.3f %5.3f boxLBWHgray " % \
                (monthtb,self.monthwidth,self.lineheight,self.titleboxThick,self.titlegray) \
                + "/%s %4.3f selectfont (%s) dup %5.3f exch SWP2D sub %5.3f M SH\n" % \
                (self.di.subtitleFontName,self.fontsize,
                 monthname,self.monthwidth/2,monthtb+self.textb)
        s = s + "RE\n"
        return s

    def body(self):
        s = ""
        s = s + ("%%--- Planner Page for %d\n" % self.year) \
            + self.title("%d Planner" % self.year) + self.bottomline()
        # Do six month columns
        for i in range(self.nmonths):
            month = i + self.startingmonth
            monthb = self.bottom
            if self.di.evenPage:
                monthl = self.di.oMargin + self.daywidth + i * self.monthwidth
            else:
                monthl = self.di.iMargin + i * self.monthwidth
            s = s + self.monthColumn(monthl,monthb,month)
        # Calculate where the day column will be.
        if self.di.evenPage:
            dayl = self.di.oMargin
        else:
            dayl = self.di.pageWidth - self.di.oMargin - self.daywidth
        dayb = self.bottom
        s = s + self.dayColumn(dayl,dayb) # Print the day column
        return s


# ############################################################################################

class TwoPlannerPages:
    """Print two planner pages for one year."""

    def __init__(self, year, dinfo):
        self.year = year
        self.dinfo = dinfo

    def page(self):
        return PlannerPage(self.year,1,6,self.dinfo,False).page() \
               + PlannerPage(self.year,7,6,self.dinfo,False).page()


# ############################################################################################

class FourPlannerPages:
    """Print four planner pages for one year."""

    def __init__(self, year, dinfo, doEventsOnPlanner=False):
        self.year = year
        self.dinfo = dinfo
        self.doEvents = doEventsOnPlanner

    def page(self):
        return PlannerPage(self.year,1,3,self.dinfo,self.doEvents).page() \
               + PlannerPage(self.year,4,3,self.dinfo,self.doEvents).page() \
               + PlannerPage(self.year,7,3,self.dinfo,self.doEvents).page() \
               + PlannerPage(self.year,10,3,self.dinfo,self.doEvents).page()


# ############################################################################################

class TwelvePlannerPages:
    """Print twelve planner pages (one for each month) for one year."""

    def __init__(self, year, dinfo, doEventsOnPlanner=False):
        self.year = year
        self.dinfo = dinfo
        self.doEvents = doEventsOnPlanner

    def page(self):
        page = ""
        for month in range(1,13): # month numbers are one based
            page += PlannerPage(self.year,month,1,self.dinfo,self.doEvents).page()
        return page

# ############################################################################################

class AddressPage(PostscriptPage):

    naddresses = 10                     # Per page
    nameprop = 0.25                     # Proportion of width in name field
    teleprop = 0.25                     # ditto for telephone field
    namewidth = -1                      # Actual width of the name field
    addrwidth = -1                      # ditto for address field
    telewidth = -1                      # ditto for telephone field
    left = -1
    fontsize = 4.0                      # For titles
    abheight = -1                       # Address block height
    tbheight = -1                       # Title block height

    def titleBlock(self):
        s = ""
        # Draw a line around the titles
        s = s + "%5.3f SLW %5.3f %5.3f M %5.3f 0 RL 0 %5.3f RL %5.3f 0 RL 0 %5.3f RL " % \
            (self.di.underlineThick, self.left, self.pTop, self.pWidth, -self.tbheight,
             -self.pWidth, self.tbheight)
        s = s + "gsave %5.3f setgray fill grestore S\n" % self.di.titleGray
        # Draw the separator lines between the titles
        s = s + "%5.3f %5.3f M 0 %5.3f RL S\n" % \
            (self.left+self.namewidth, self.pTop, -self.tbheight)
        s = s + "%5.3f %5.3f M 0 %5.3f RL S\n" % \
            (self.left+self.namewidth+self.addrwidth, self.pTop, -self.tbheight)
        # Now add the titles themselves
        s = s + "/%s %5.3f selectfont\n" % (self.di.subtitleFontName, self.fontsize)
        titley = self.pTop - self.tbheight + self.fontsize*0.5
        # A clever loop for the title text, so we don't have to write this code three times.
        for par in (("Name",self.left+self.namewidth/2.0),
                    ("Address",self.left+self.namewidth+self.addrwidth/2.0),
                    ("Telephone",self.left+self.namewidth+self.addrwidth+self.telewidth/2.0)):

            s = s + "(%s) dup exch SWP2D %5.3f exch sub %5.3f M SH\n" % \
                (par[0],par[1], titley)
        return s

    def addressBlock(self,b):
        s = ""
        s = s + "%5.3f %5.3f M SA CP TR 0 SLW\n" % (self.pLeft,b)
        s = s + "0 0 M 0 %5.3f RL %5.3f 0 RL 0 %5.3f RL %5.3f 0 RL S " % \
            (self.abheight,self.pWidth,-self.abheight,-self.pWidth) \
            + "%5.3f 0 M 0 %5.3f RL S " % (self.namewidth,self.abheight) \
            + "%5.3f 0 M 0 %5.3f RL S RE\n" % (self.namewidth+self.addrwidth, self.abheight)
        return s

    def body(self):
        # Calculate some sizes first
        self.tbheight = self.fontsize * 1.8
        self.abheight = (self.pHeight - self.tbheight) / self.naddresses
        if self.di.evenPage:
            self.left = self.di.oMargin
        else:
            self.left = self.di.iMargin
        self.namewidth = self.nameprop * self.pWidth
        self.telewidth = self.teleprop * self.pWidth
        self.addrwidth = self.pWidth - self.namewidth - self.telewidth
        s = ""
        s = s + "%--- Address Page\n"
        for i in range(self.naddresses):
            s = s + self.addressBlock(self.pBottom + i*self.abheight)
        s = s + self.titleBlock()
        # Box around the whole page.
        s = s + "%5.3f SLW %5.3f %5.3f M 0 %5.3f RL %5.3f 0 RL 0 %5.3f RL %5.3f 0 RL\n" % \
            (self.di.underlineThick, self.left, self.pBottom, self.pHeight, self.pWidth,
             -self.pHeight, -self.pWidth)
        s = s + self.title("Addresses") + self.bottomline()
        return s


# ############################################################################################

class NotesPage(PostscriptPage):
    def body(self):

        s = "%--- Notes Page\n" + self.title("Notes") + self.bottomline()
        s = s + "SA %5.3f %5.3f TR 0 SLW\n" % (self.pLeft,self.pBottom)

        if self.di.griddedNotesPages:

            llineSpacing = self.di.lineSpacing * 0.75
            hnlines = int(self.pHeight / llineSpacing)
            vnlines = int(self.pWidth / llineSpacing)
            # Recalculate line spacing to avoid dangling lines.
            hlinespacing = float(self.pHeight) / float(hnlines)
            vlinespacing = float(self.pWidth ) / float(vnlines)
            sbox = int (vnlines / 4)
            s = s + "%% -- hnlines=%s vnlines=%d sbox=%d\n" % (hnlines, vnlines, sbox)
            s = s + "[0.2 0.3] 0 setdash\n"
            # Print horizontal lines, but miss the top two.
            for n in range(2,hnlines+1):
                s = s + "0 %5.3f M %5.3f 0 RL S\n" % (self.pHeight-hlinespacing*n,
                                                      self.pWidth)
            s = s + "%5.3f %5.3f M\n" % (self.pLeft,self.pBottom)
            # Print vertical lines, missing lines that go all the way to the top of the page.
            s = s + "% vertical lines\n"
            for n in range(1,sbox)+range(sbox+1,vnlines-sbox)+range(vnlines-sbox+1,vnlines):
                s = s + "%5.3f 0 M 0 %5.3f RL S\n" % (self.pWidth - vlinespacing*n,
                                                      self.pHeight - 2 * hlinespacing)
            # Print the vertical lines that do go to the top of the page.
            s = s + "% longer vertical lines\n"
            for n in (0,sbox,vnlines-sbox,vnlines):
                s = s + "%5.3f 0 M 0 %5.3f RL S\n" % (self.pWidth - vlinespacing*n,
                                                      self.pHeight)

        else:

            nlines = int(self.pHeight / self.di.lineSpacing)
            # Recalculate line spacing to avoid dangling bottom lines.
            linespacing = float(self.pHeight) / float(nlines)
            for n in range(0,nlines):
                s = s + "0 %5.3f M %5.3f 0 RL S\n" % (self.pHeight-linespacing*(n+1),
                                                      self.pWidth)

        s = s + "RE\n"
        return s


# ############################################################################################

class ExpensePage(PostscriptPage):

    inoutcolumnwidths = 0.2

    def __init__(self,month1,nmonths,dinfo):
        PostscriptPage.__init__(self,dinfo)
        self.nmonths = nmonths
        self.month1 = month1
        self.fontsize = self.di.subtitleFontSize
        self.titleheight = self.fontsize * 2.0
        self.monthheight = float(self.pHeight) / float(self.nmonths)
        self.monthwidth = self.pWidth - self.titleheight
        self.column1x = self.monthwidth * (1.0 - 2.0*self.inoutcolumnwidths)
        self.column2x = self.monthwidth * (1.0 - self.inoutcolumnwidths)

    def titleblock(self,month,ypos):
        s = "%% title block: month=%d ypos=%5.3f\n" % (month,ypos)
        monthname = DateTime.DateTime(self.di.dtbegin.year,month).strftime("%B")
        if self.di.evenPage:
            titlex = self.pLeft + self.titleheight
            titley = ypos
            titlerot = 90
        else:
            titlex = self.pRight - self.titleheight
            titley = ypos + self.monthheight
            titlerot = -90
        # Translate and rotate to the bottom left of the title.
        s = s + "SA %5.3f %5.3f TR %5.3f rotate\n" % (titlex,titley,titlerot)
        # Fill the title with gray, and draw a box around it.
        #s = s + "0 0 M 0 %5.3f RL %5.3f 0 RL 0 %5.3f RL %5.3f 0 RL " % \
        #    (self.titleheight,self.monthheight,-self.titleheight,-self.monthheight) \
        #    + "gsave %5.3f setgray fill grestore S\n" % self.di.titleGray
        s = s + "0 0 %5.3f %5.3f %5.3f %5.3f boxLBRTgray\n" % \
            (self.monthheight,self.titleheight,self.di.underlineThick,self.di.titleGray)
        # Now put the text into the box.
        s = s + "/%s %5.3f selectfont (%s) dup SWP2D %5.3f exch sub %5.3f M SH " % \
            (self.di.subtitleFontName,self.fontsize,
             monthname, self.monthheight*0.5, self.titleheight*0.25)
        s = s + "RE\n"
        return s

    def block(self,ypos):
        s = ""
        if self.di.evenPage:
            blockl = self.pLeft + self.titleheight
        else:
            blockl = self.pLeft
        blockwidth = self.pWidth - self.titleheight
        s = s + "SA %5.3f %5.3f TR " % (blockl,ypos)
        s = s + "0 0 %5.3f %5.3f %5.3f boxLBRT\n" % \
            (blockwidth, self.monthheight, self.di.underlineThick)
        s = s + "% columns \n"
        s = s + "%5.3f 0 M 0 %5.3f RL S %5.3f 0 M 0 %5.3f RL S\n" % \
            (self.column1x,self.monthheight,self.column2x,self.monthheight)
        nlines = 1 + int(self.monthheight / self.di.lineSpacing)
        linespacing = self.monthheight / float(nlines)
        s = s + "0 SLW "
        for i in range(1,nlines):
            s = s + "0 %5.3f M %5.3f 0 RL S " % (i*linespacing,self.monthwidth)
        s = s + " RE\n"
        return s

    def body(self):
        s = "%--- Expenses Page\n" \
            + self.title("Expenses") \
            + self.bottomline()
        for i in range(self.nmonths):
            y = self.pTop - (i+1) * self.monthheight
            s = s + self.titleblock(self.month1+i,y) \
                + self.block(y)
        return s


# ############################################################################################

class FourExpensePages:
    def page(self,dinfo):
        s = ""
        s = s + ExpensePage(1,3,dinfo).page() \
            + ExpensePage(4,3,dinfo).page() \
            + ExpensePage(7,3,dinfo).page() \
            + ExpensePage(10,3,dinfo).page()
        return s


# ############################################################################################

class TwoExpensePages:
    def page(self,dinfo):
        s = ""
        s = s + ExpensePage(1,6,dinfo).page() \
            + ExpensePage(7,6,dinfo).page()
        return s


# ############################################################################################

class DiaryPage(PostscriptPage):

    mooncalc = Moon.MoonCalc()

    def __init__(self,dinfo):
        PostscriptPage.__init__(self,dinfo)
        self.otherdaygray = (1.0+self.di.titleGray)/2.0
        self.weekendgray = self.di.titleGray
        # When we print six month calendars across the bottom of a page, there will (obviously)
        # be 12 calendars across an opening.  We want the left page of the opening to have the
        # five months before the current month, and the current month, and the right page to
        # have the six months after the current month.  Because the current month can change in
        # the course of printing an opening (or even in the course of printing a page) we save
        # the date of the first day printed on the opening, and then we can refer to that when
        # printing month calendars on both the pages of the opening.  The first page of an
        # opening is always an even page.  Currently, we always start a year of diary pages on
        # an even page.  This will have to be revisited if that changes.
        if self.di.evenPage:
            self.di.openingCalendarsCurrentDate = self.di.dt

    def setMargins(self):
        """Override setMargins() specially for diary pages."""
        PostscriptPage.setMargins(self)
        di = self.di
        self.pTop_diary = di.pageHeight - di.tMargin
        self.pHeight_diary = self.pTop_diary - self.pBottom
        self.ptop_diary = 0
        self.pheight_diary = 0

        if di.layout == "week-to-opening":
            self.dheight = self.pHeight_diary/4.0
        elif di.layout == "day-to-page":
            self.dheight = self.pHeight_diary * 0.9
            self.bottomcalheight = self.pHeight_diary - self.dheight
        elif di.layout == "work":
            self.dheight = self.pHeight_diary * 0.45
            self.bottomcalheight = self.pHeight_diary - self.dheight * 2.0
            self.weekendDheight = self.dheight / 2.0
        else:
            self.dheight = self.pHeight_diary/2.0
        self.dwidth = self.pWidth

        # In here, "app" is short for appointment.
        if di.appointments:
            self.appProportion = self.di.appointmentWidth /100.0 # Proportion of page width
            self.appLeft = self.dwidth * (1.0 - self.appProportion)
            self.appRight = self.dwidth
            self.appWidth = self.appRight - self.appLeft
            self.dwidthLines = self.appLeft - 0.2*di.lineSpacing
        else:
            self.dwidthLines = self.pWidth

        # These are the settings that have the most effect on the layout of a day.
        if di.layout == "week-to-opening":
            # Smaller boxes when we cram a week into two pages
            self.titleboxsize = di.lineSpacing * 1.2
        else:
            self.titleboxsize = di.lineSpacing * 1.4
        self.titleboxy = self.dheight - self.titleboxsize
        self.titlefontsize = self.titleboxsize * 0.63
        self.titlefonty = self.dheight - self.titleboxsize * 0.7
        self.titlefontgap = self.titlefontsize * 0.5
        self.subtitlefontsize = self.titleboxsize * 0.35

        # Number of writing lines
        self.nlines = int(self.titleboxy / di.lineSpacing)


    def diaryDay(self, height=None):

        """Print a diary day in part of a page.  At the point this is called, the graphics
        state has already been translated so we can just draw straight into our patch."""

        di = self.di
        dt = di.dt

        # If a height has been specified, we adjust some of the layout parameters to make the
        # day fit within that space.  But we have to save and restore the old parameters as
        # this may not be the last day printed on this page.
        #
        # This is simulated dynamic scope.  Yuk.

        if height is not None:
            saved_dheight = self.dheight
            saved_titleboxy = self.titleboxy
            saved_titlefonty = self.titlefonty
            saved_nlines = self.nlines

            self.dheight = height
            self.titleboxy = self.dheight - self.titleboxsize
            self.titlefonty = self.dheight - self.titleboxsize * 0.7
            self.nlines = int(self.titleboxy / di.lineSpacing)

            s = self.diaryDay()

            self.dheight = saved_dheight
            self.nlines = saved_nlines
            self.titleboxy = saved_titleboxy
            self.titlefonty = saved_titlefonty

            return s

        s = "%%--- diary day for %d-%02d-%02d\n" % (dt.year,dt.month,dt.day)

        # Find out if this is a holiday.
        dd = DateTime.DateTime(dt.year, dt.month, dt.day)
        isholiday = 0
        if self.di.events.has_key(dd):
            #sys.stderr.write("%s has events\n" % dd)
            eventlist = self.di.events[dd]
            for event in eventlist:
                if event.has_key('holiday'):
                    #sys.stderr.write("%s is a holiday: %s\n" % (dd,str(event)))
                    isholiday = 1

        # Draw the box around the title
        if isholiday or dd.day_of_week==DateTime.Saturday or dd.day_of_week==DateTime.Sunday:
            gr = self.weekendgray
        else:
            gr = self.otherdaygray
        s = s + "0 %5.3f %5.3f %5.3f %5.3f %5.3f boxLBWHgray\n" % \
            (self.titleboxy, self.dwidth, self.titleboxsize, di.underlineThick, gr)

        # Print the day name as the diary day header.
        s = s + "10 10 M /%s %5.2f selectfont " % (di.titleFontName, self.titlefontsize)
        daynumber = dt.strftime("%d")
        if daynumber[0] == '0':
            daynumber = ' ' + daynumber[1]
        dtext = dt.strftime("%A, " + daynumber + " %B") # %e seems to be undocumented
        if di.evenPage:
            s = s + "%5.3f %5.3f M (%s) SH\n" % (self.titlefontgap,self.titlefonty,dtext)
        else:
            s = s + "(%s) dup %5.3f exch SW pop sub %5.3f M SH\n" % \
                (dtext,self.dwidth-self.titlefontgap,self.titlefonty)
        # And draw the julian day as well
        jtext = "%03d/%03d" % (dt.day_of_year, di.currentJDaysLeft)
        s = s + "/%s %5.3f selectfont " % (di.subtitleFontName, self.subtitlefontsize)
        if di.evenPage:
            s = s + "(%s) dup %5.3f exch SW pop sub %5.3f M SH\n" % \
                (jtext, self.dwidth-self.titlefontgap, self.titlefonty)
        else:
            s = s + "%5.3f %5.3f M (%s) SH\n" % (self.titlefontgap,self.titlefonty,jtext)

        # Draw all the writing lines, but if the appointments take up the whole width, don't
        # print the writing lines.
        if self.di.appointmentWidth != 100:
            s = s + "0 SLW "
            for lineno in range(self.nlines):
                liney = self.titleboxy-(1+lineno)*di.lineSpacing
                s = s + "0 %5.3f M %5.3f 0 RL S " % (liney,self.dwidthLines)
            s = s + "\n"

        # Put in the events for this day
        eventstr = self.drawEvents(0, self.titleboxy - di.lineSpacing, di.lineSpacing)
        if eventstr is not None:
            s = s + eventstr

        # Print the appointments box, if required.
        if di.appointments:
            s = s + self.drawAppointments()

        # Draw the moon phase, if required.
        if di.moon:
            if di.evenPage:
                moonx = self.dwidth * 0.68
            else:
                moonx = self.dwidth * 0.32
            s = s + self.drawMoon(moonx,
                                  self.titleboxy + self.titleboxsize * 0.5,
                                  di.lineSpacing*0.8)

        # Other bits of code rely on us going to the next day only at the end of printing a
        # diary day.  An example is the code that prints six months at the bottom of each page
        # in some layouts.  Don't change this without thinking hard, and testing harder.
        di.gotoNextDay()
        return s

    def drawAppointments(self):
        """Draw the appointments box on the diary day."""
        di = self.di
        s = ""
        # Adding and removing entries from this list will automatically adjust the number
        # of appointment lines, and the size of the lines.  Entries that are None result in
        # a line without a label.
        tempAppTimes = ["9","10","11","12","1","2","3","4","5","6","7"]
        appTimes = [ ]
        while len(appTimes) < self.nlines:
            if len(appTimes) < len(tempAppTimes):
                appTimes.append(tempAppTimes[len(appTimes)])
            else:
                appTimes.append(None)
        # Make the appointment lines end at the same spot as the diary lines.
        appheight = di.lineSpacing #(self.nlines * di.lineSpacing) / len(appTimes)
        s = s + '/%s %5.3f selectfont\n' % (di.subtitleFontName,
                                            appheight*0.5)
        # Line thicknesses
        leftTh = di.underlineThick * 0.5
        bottomTh = 0
        for lineno in range(len(appTimes)):
            s = s + "%5.3f SLW %5.3f %5.3f M 0 %5.3f RL CP S %5.3f SLW M %5.3f 0 RL S " % \
                (leftTh, self.appLeft, self.titleboxy-appheight*lineno,
                 -appheight, bottomTh, self.appWidth)
            if di.appointmentTimes and appTimes[lineno] is not None:
                appx = self.appLeft + appheight*0.2
                appy = self.titleboxy - appheight * (lineno+0.55)
                s = s + " %5.3f %5.3f M (%s) SH\n" % \
                    (appx,appy,self.postscriptEscape(appTimes[lineno]))
            else:
                s = s + "\n"
        return s


    def drawEvents(self, startx, starty, yspace):
        di = self.di
        date = di.dt
        #date = (dt.year, dt.month, dt.day)
        if not di.events.has_key(date):
            return
        eventlist = di.events[date]
        nevents = len(eventlist)
        textx = startx
        picx = startx
        y = starty
        s = ''
        s = s + '%% events for %s\n' % str(date)

        # First find out whether we are printing any images for this day.  If so, move all the
        # text to the right, out of the way of the images.
        if di.drawEventImages:
            for i in range(nevents):
                event = eventlist[i]
                if event.has_key('image') \
                        and not (event.has_key('_warning') and event['_warning']):
                    textx = textx + 2.2*yspace
                    break

        for i in range(nevents):
            event = eventlist[i]
            # Print an image, unless this is a warning event.
            if event.has_key('image') and di.drawEventImages \
                    and not (event.has_key('_warning') and event['_warning']):
                s = s + self.image(event['image'],
                                   picx + 0.1*di.lineSpacing, y - yspace + 0.1*di.lineSpacing,
                                   1.8*yspace, 1.8*yspace)
                imageDrawn = True
            else:
                imageDrawn = False
            if event.has_key('small'):
                eventFontSize = yspace*0.3
            else:
                eventFontSize = yspace*0.6
            if event.has_key('personal'):
                s = s + '/%s-Oblique %5.3f selectfont\n' % (di.subtitleFontName, eventFontSize)
            else:
                s = s + '/%s %5.3f selectfont\n' % (di.subtitleFontName, eventFontSize)

            if event.has_key('grey')  and  event['grey']:
                s = s + "0.5 setgray "
            else:
                s = s + "0 setgray "
            s = s + "%5.3f %5.3f M" % (textx, y+(yspace*0.25))
            st = self.postscriptEscape(event['text'])
            s = s + ' (%s) SH 0 setgray\n' % st
            if imageDrawn:
                y = y - 2*yspace
            else:
                y = y - yspace
        return s


    def topHalf(self):
        s = "%--- diary page TOP half\n" \
            + ("SA %5.3f %5.3f TR\n" % \
               (self.pLeft,self.pBottom+(self.pHeight_diary/2))) \
            + self.diaryDay() \
            + "RE\n"
        return s

    def bottomHalf(self):
        s = "%--- diary page BOTTOM half\n" \
            + ("SA %5.3f %5.3f TR\n" % (self.pLeft,self.pBottom)) \
            + self.diaryDay() \
            + "RE\n"
        return s

    def printMondayWTO(self):
        s = '% -- Monday\n' \
            + ("SA %5.3f %5.3f TR\n" % (self.pLeft, self.pBottom+(self.pHeight_diary*0.5))) \
            + self.diaryDay() \
            + "RE\n"
        return s

    def printTuesdayWTO(self):
        s = '% -- Tuesday\n' \
            + ("SA %5.3f %5.3f TR\n" % (self.pLeft, self.pBottom+(self.pHeight_diary*0.25))) \
            + self.diaryDay() \
            + "RE\n"
        return s

    def printWednesdayWTO(self):
        s = '% -- Wednesday\n' \
            + ("SA %5.3f %5.3f TR\n" % (self.pLeft, self.pBottom)) \
            + self.diaryDay() \
            + "RE\n"
        return s

    def printThursdayWTO(self):
        s = '% -- Thursday\n' \
            + ("SA %5.3f %5.3f TR\n" % (self.pLeft, self.pBottom+(self.pHeight_diary*0.75))) \
            + self.diaryDay() \
            + "RE\n"
        return s

    def printFridayWTO(self):
        s = '% -- Friday\n' \
            + ("SA %5.3f %5.3f TR\n" % (self.pLeft, self.pBottom+(self.pHeight_diary*0.5))) \
            + self.diaryDay() \
            + "RE\n"
        return s

    def printSaturdayWTO(self):
        s = '% -- Saturday\n' \
            + ("SA %5.3f %5.3f TR\n" % (self.pLeft, self.pBottom+(self.pHeight_diary*0.25))) \
            + self.diaryDay() \
            + "RE\n"
        return s

    def printSundayWTO(self):
        s = '% -- Sunday\n' \
            + ("SA %5.3f %5.3f TR\n" % (self.pLeft, self.pBottom)) \
            + self.diaryDay() \
            + "RE\n"
        return s

    def largeDayOnPage(self):
        s = "% -- Day\n" \
            + ("SA %5.3f %5.3f TR\n" % (self.pLeft, self.pBottom+self.bottomcalheight)) \
            + self.diaryDay() \
            + "RE\n"
        return s

    def workLayoutTopDay(self):
        s = "% -- top day\n"\
            + ("SA %5.3f %5.3f TR\n" % (self.pLeft, \
                                        self.pBottom+self.bottomcalheight+self.dheight)) \
            + self.diaryDay() \
            + "RE\n"
        return s

    def workLayoutBottomDay(self):
        s = "% -- bottom day\n"\
            + ("SA %5.3f %5.3f TR\n" % (self.pLeft, \
                                        self.pBottom+self.bottomcalheight)) \
            + self.diaryDay() \
            + "RE\n"
        return s

    def workLayoutSaturday(self):
        s = "% -- Saturday on a work layout\n" \
            + ("SA %5.3f %5.3f TR\n" % (self.pLeft,
                                        self.pBottom
                                        + self.bottomcalheight
                                        + self.weekendDheight)) \
            + self.diaryDay(self.weekendDheight) \
            + "RE\n"
        return s

    def workLayoutSunday(self):
        s = "% -- Sunday on a work layout\n" \
            + ("SA %5.3f %5.3f TR\n" % (self.pLeft,
                                        self.pBottom
                                        + self.bottomcalheight)) \
            + self.diaryDay(self.weekendDheight) \
            + "RE\n"
        return s

    def titleAndThreeMonthsAtTop(self):
        """Print three calendars on the top half of a page."""
        di = self.di
        s = "%--- three month calendars\n"
        # Page title.
        s = s + self.title(di.dt.strftime("%B %Y"),
                           "Week %d" % di.dt.iso_week[1])
        # Calculate the area we have for drawing.
        if di.layout == "week-to-opening" or di.layout == "day-to-page":
            b = di.bMargin + self.pHeight_diary*0.75
        else:
            b = di.bMargin + self.pHeight_diary*0.5
        l = self.pLeft
        w = self.pWidth
        h = self.pTop - b
        # Draw a really obvious box to see if the drawing space is correct.
        #s = s + "SA 4 SLW 2 setlinecap %5.3f %5.3f TR\n" % (l,b) \
        #      + "2 2 M 0 %5.3f RL %5.3f 0 RL 0 %5.3f RL %5.3f 0 RL S RE\n" % \
        #      (h-4,w-4,-(h-4),-(w-4))
        s = s + "SA %5.3f %5.3f TR\n" % (l,b)
        if di.layout == "week-to-opening":
            c_bottom = h * 0.45
            c_height = h * 0.49
            c_indent = w * 0.033
            c_width = c_height * 1.4
        else:
            c_bottom = h * 0.65             # The c_ prefix for these variables means "calendar"
            c_height = h * 0.3
            c_indent = w * 0.023
            c_width = c_height * 1.33
        c_totalwidth = w - 2*c_indent
        c_gutter = (c_totalwidth - 3*c_width) / 2
        c_boxborder = h * 0.02
        # Adjust for the maximum available width of a month.
        if c_gutter < 2*c_boxborder:
            c_width = (c_totalwidth - 4*c_boxborder)/3.0
            c_gutter = 2*c_boxborder
        s = s + "%% c_bottom=%5.3f c_height=%5.3f c_width=%5.3f c_totalwidth=%5.3f c_gutter=%5.3f\n" % \
              (c_bottom,c_height,c_width,c_totalwidth,c_gutter)
        for i in (-1,0,1):
            c_d = self.getOffsetMonth(self.di.dt, i)
            c_left = c_indent + (i+1)*(c_width+c_gutter)
            s = s +"%5.3f %5.3f M SA %5.3f %5.3f SC " % \
                (c_left,c_bottom,c_width,c_height) \
                + self.di.getMonthCalendarPsFnCall(c_d.year, c_d.month) \
                + " RE\n"
            # Draw a box around the current month
            if i == 0:
                s = s + "0 SLW %5.3f %5.3f M " % (c_left-c_boxborder,c_bottom-c_boxborder) \
                    + "0 %5.3f RL %5.3f 0 RL " % (c_height+2*c_boxborder,c_width+2*c_boxborder) \
                    + "0 %5.3f RL %5.3f 0 RL S\n" % (-c_height-2*c_boxborder,-c_width-2*c_boxborder)
        # Now draw the lines just below the month calendars.
        l_y = c_bottom - di.lineSpacing - 1.3
        s = s + "0 SLW\n"
        while l_y > (di.lineSpacing * 0.3):
            s = s + "%5.3f %5.3f M %5.2f 0 RL S\n" % (c_indent,l_y,c_totalwidth)
            l_y = l_y - di.lineSpacing

        s = s + "RE\n"
        return s


    def getOffsetMonth(self, dt, offset):
        '''Return a DateTime object corresponding to some time in the month indicated by the
        integer offset from the current month.'''

        if offset==0:
            return dt
        else:
            # Base this from the middle of the month, so we don't get strange month skip
            # effects when the current day is near the beginning or end of the month.
            return DateTime.DateTime(dt.year, dt.month, 15) + 30.5 * DateTime.oneDay * offset


    def sixMonthsAtBottom(self):
        '''Print six months at the bottom of the page, five months before the current month,
        and the current month, on the left (even) pages, and six months after the current month
        on the right (odd) pages.'''

        # If we start on the 15th day of the relevant month, we can add or subtract 30 days
        # several times without worrying about crossing a month boundary when we don't want to.
        date = DateTime.DateTime( self.di.openingCalendarsCurrentDate.year,
                                  self.di.openingCalendarsCurrentDate.month,
                                  15)
        if self.di.evenPage:
            date -= DateTime.oneDay * 30 * 5
        else:
            date += DateTime.oneDay * 30
        s = "%% -- Bottom calendars, starting at %s\n" % date.strftime("%Y %m")

        # Proportion of the month box to fill.
        monthprop = 0.90

        for i in range(0,6):
            s = s + "%5.3f %5.3f M SA %5.3f %5.3f SC %s RE\n" % \
                    (self.pLeft+(self.dwidth/6.0)*(i+((1.0-monthprop)/2.0)),
                     self.pBottom + self.bottomcalheight*(1.0-monthprop)/2.0,
                     (self.dwidth/6.0)*monthprop,
                     self.bottomcalheight*monthprop,
                     self.di.getMonthCalendarPsFnCall(date.year, date.month) )
            date += DateTime.oneDay * 30
        return s


    def drawMoon(self, x, y, size):

        """Draw a moon at (x,y), with the given size."""

        di = self.di
        if not di.moon:
            return ""

        # Calculate the current phase, and the previous and next day's phases
        dt = di.dt
        dty = di.dt - DateTime.oneDay
        dtt = di.dt + DateTime.oneDay
        currentPhase = self.mooncalc.calc_phase(dt.year, dt.month, dt.day)
        previousPhase = self.mooncalc.calc_phase(dty.year, dty.month, dty.day)
        nextPhase = self.mooncalc.calc_phase(dtt.year, dtt.month, dtt.day)
        quarter = self.mooncalc.is_quarter(previousPhase, currentPhase, nextPhase)
        if quarter == self.mooncalc.MOON_OTHER:
            return ""

        fontsize = size * 0.4
        radius = size/2.0
        linex = x + size * 0.65
        line1y = y + size * 0.1
        line2y = y - size * 0.4
        s = "%% Moon for %d-%d-%d\n" % (dt.year, dt.month, dt.day)
        s = s + "newpath 0 setgray 0.1 SLW /%s %5.3f selectfont " % \
            (di.subtitleFontName, fontsize)
        s = s + "%5.3f %5.3f %5.3f 0 360 arc S %% circle\n" % (x,y,radius)

        # In the southern hemisphere, a first quarter moon is light on the left, and a third
        # quarter moon is light on the right.

        if quarter == self.mooncalc.MOON_NM:
            s = s + "%5.3f %5.3f %5.3f 0 360 arc fill %% new moon\n" % (x,y,radius) \
                + "%5.3f %5.3f M (New) SH %5.3f %5.3f M (Moon) SH\n" % \
                (linex,line1y, linex,line2y)
        elif quarter == self.mooncalc.MOON_1Q:
            if self.di.northernHemisphereMoon:
                s = s + self.drawMoonRightWhite(x, y, radius, size)
            else:
                s = s + self.drawMoonLeftWhite(x, y, radius, size)
            s = s + "%5.3f %5.3f M (First) SH %5.3f %5.3f M (Quarter) SH\n" % \
                (linex,line1y, linex,line2y)
        elif quarter == self.mooncalc.MOON_FM:
            s = s + "%5.3f %5.3f M (Full) SH %5.3f %5.3f M (Moon) SH\n" % \
                (linex,line1y, linex,line2y)
        elif quarter == self.mooncalc.MOON_3Q:
            if self.di.northernHemisphereMoon:
                s = s + self.drawMoonLeftWhite(x, y, radius, size)
            else:
                s = s + self.drawMoonRightWhite(x, y, radius, size)
            s = s + "%5.3f %5.3f M (Third) SH %5.3f %5.3f M (Quarter) SH\n" % \
                (linex,line1y, linex,line2y)

        return s

    def drawMoonLeftWhite(self, x, y, radius, size):
        s = "%5.3f %5.3f %5.3f 270 90 arc 0 %5.3f RL fill %% white left, " % \
            (x,y,radius,-size)
        if self.di.northernHemisphereMoon:
            s = s + "third quarter in northern hemisphere\n"
        else:
            s = s + "first quarter in southern hemisphere\n"
        return s

    def drawMoonRightWhite(self, x, y, radius, size):
        s = "%5.3f %5.3f %5.3f 90 270 arc 0 %5.3f RL fill %% white right, " % \
            (x,y,radius,size)
        if self.di.northernHemisphereMoon:
            s = s + "first quarter in northern hemisphere\n"
        else:
            s = s + "third quarter in southern hemisphere\n"
        return s

    def body(self):
        s = ""
        if self.di.layout == "day-to-page":
            s = self.sixMonthsAtBottom() + self.largeDayOnPage()
        elif self.di.layout == "work":
            s = self.sixMonthsAtBottom() + self.workLayoutTopDay()
            if self.di.dt.day_of_week == DateTime.Saturday:
                s += self.workLayoutSaturday() + self.workLayoutSunday()
            else:
                s += self.workLayoutBottomDay()
        elif self.di.dt.day_of_week == DateTime.Monday:
            if self.di.layout == "week-to-opening":
                s = self.titleAndThreeMonthsAtTop() +  \
                    self.printMondayWTO() + \
                    self.printTuesdayWTO() + \
                    self.printWednesdayWTO()
            else:
                s = self.titleAndThreeMonthsAtTop() + self.bottomHalf();
        else:
            if self.di.layout == "week-to-opening":
                s = self.printThursdayWTO() + \
                    self.printFridayWTO() + \
                    self.printSaturdayWTO() + \
                    self.printSundayWTO()
            else:
                s = self.topHalf() + self.bottomHalf();
        return s


# ############################################################################################

class Diary:

    def __init__(self,diaryinfo):
        self.di = diaryinfo
        self.out = self.di.out

    def w(self,s):
        self.out.write(s)

    def preamble(self):
        """Return the document header as a string."""
        p =   "%!PS-Adobe-2.0\n" \
            + ("%% -- printed by %s %s, %s\n" % (self.di.myname, self.di.opts,
                                                 DateTime.now().strftime("%Y-%m-%dT%H%M%S%Z")))
        p = p + "%%%%Creator: %s, by Russell Steicke, version: %s\n" % \
            (self.di.myname,versionNumber) \
            + DateTime.now().strftime("%%%%CreationDate: %a, %d %b %Y %H:%M:%S %z\n") \
            + "%%%%BoundingBox: 0 0 %.0f %.0f\n" % \
            (self.di.paperWidth * self.di.points_mm, self.di.paperHeight * self.di.points_mm)
        p = p + "%%DocumentNeededResources: font Times-Roman\n" \
            "%%+ font Times-Bold\n" \
            "%%+ font Helvetica\n" \
            "%%+ font Helvetica-Oblique\n" \
            "%%+ font Courier\n" \
            "%%+ font Courier-Bold\n" \
            "%%Pages: (atend)\n" \
            "%%PageOrder: Ascend\n" \
            "%%Orientation: Portrait\n" \
            "%%EndComments\n" \
            "%%BeginProlog\n" \
            "%%BeginResource: MakediaryProcs\n" \
            "/CP {currentpoint} bind def " \
            "/M {moveto} bind def /RM {rmoveto} bind def " \
            "/L {lineto} bind def /RL {rlineto} bind def\n" \
            "/S {stroke} bind def /SH {show} bind def " \
            "/SP {showpage} bind def /SLW {setlinewidth} bind def\n" \
            "/SA {save} bind def /RE {restore} bind def " \
            "/TR {translate} bind def\n" \
            "/SW {stringwidth} bind def /SC {scale} bind def\n" \
            "/SWP2D {SW pop 2 div} bind def\n" \
            "/D {def} bind def /ED {exch def} bind def\n" \
            + "/MM {%8.6f %8.6f SC} bind def\n" % (self.di.points_mm,self.di.points_mm) \
            + "matrix currentmatrix 0 get /originalXscale ED " \
            "matrix currentmatrix 3 get /originalYscale ED\n"


        # Code for printing boxes around things.  The linewidth must be set before using either
        # of these.

        p = p + "% construct a path given <left bottom width height>\n" \
            "/pathLBWH { 4 dict begin /h ED /w ED /b ED /l ED\n" \
            "l b M w 0 RL 0 h RL w neg 0 RL 0 h neg RL end} def\n" \
            "% construct a path given <left bottom right top>\n" \
            "/pathLBRT { 4 dict begin /t ED /r ED /b ED /l ED\n" \
            "l b M r b L r t L l t L l b L end} def\n"

        p = p + "% print a box given <left bottom width height linethickness>\n" \
            "/boxLBWH { gsave SLW pathLBWH S grestore } def\n" \
            "% print a box given <left bottom right top linethickness>\n" \
            "/boxLBRT { gsave SLW pathLBRT S grestore } def\n"

        # Print a box with the current line width (in the current gray level), and fill it with
        # the specfied gray.

        p = p + "% print a box and fill it <l b w h linethick gray\n" \
            "/boxLBWHgray { gsave 2 dict begin /g ED /th ED 4 copy " \
            "pathLBWH currentgray g setgray fill setgray th boxLBWH end grestore } def\n" \
            "% print a box and fill it <l b r t linewidth gray\n" \
            "/boxLBRTgray { gsave 2 dict begin /g ED /th ED 4 copy " \
            "pathLBRT currentgray g setgray fill setgray th boxLBRT end grestore } def\n"

        # Code for printing dashed debugging boxes around things.  These defs need the dash
        # length supplied so that we can manually compensate for different scales.

        p = p + "% print a debug box given <left bottom right top dashlen>\n" \
            "/debugboxLBRTD {gsave 6 dict begin /len ED /t ED /r ED /b ED /l ED\n" \
            "[ len ] 0 setdash 0 SLW " \
            "l b M l t L S l t M r t L S r t M r b L S r b M l b L S\n" \
            "end grestore} def\n" \
            "% print a debug box given <left bottom width height dashlen>\n" \
            "/debugboxLBWHD {6 dict begin /len ED /h ED /w ED /b ED /l ED\n" \
            "l b l w add b h add len debugboxLBRTD end} def\n"

        # Additional defs for debug box printing.  These defs calculate the dash length from
        # the current transformation matrix.  This works, except that ghostscript changes the
        # current matrix depending on the zoom level, so the dash length changes when we zoom.
        # But at least we get the same dash length on everything, regardless of the scale in
        # use at that point.  The number just before "matrix currentmatrix" should the the
        # length of the dashes in postscript points.  There is also a test against divide by
        # zero in here.  It is possible to get a 0 in currentmatrix[0] or currentmatrix[3],
        # which will stop the job with an error on some printers.

        p = p + "% print a debug box given <left bottom right top>, guess the dash length\n" \
            "/debugboxLBRT {gsave 6 dict begin /t ED /r ED /b ED /l ED\n" \
            "10.0 matrix currentmatrix 0 get dup 0 eq { pop pop 5.0 } { div abs } ifelse /xl ED " \
            "10.0 matrix currentmatrix 3 get dup 0 eq { pop pop 5.0 } { div abs } ifelse /yl ED\n" \
            "[ xl ] 0 setdash l b M r b L S l t M r t L S\n" \
            "[ yl ] 0 setdash l b M l t L S r b M r t L S\n" \
            "end grestore} def\n" \
            "% print a debug box given <left bottom width height>, guess the dash length\n" \
            "/debugboxLBWH {6 dict begin /h ED /w ED /b ED /l ED\n" \
            "l b l w add b h add debugboxLBRT end} def\n"

        # This line is used in the middle of /debugboxLBRT to show the scale
            #+ "/Courier xl selectfont l b M xl 10 string cvs SH (  ) SH yl 10 string cvs SH\n" \

        # Debian GNU/Linux seems to have a problem here.  ghostview ignores the -media command
        # line option, and always sets the sizes in currentpagedevice to what is specified by
        # /etc/papersize.  The -media size is used to set the "paper" size of the ghostscript
        # window.

        p = p + "% --- code to find out the page size.\n" \
            "/pageIsA4 { currentpagedevice begin " \
            "  PageSize 0 get 595 sub abs 10 lt PageSize 1 get 842 sub abs 10 lt " \
            "  and end } bind def\n" \
            "/pageIsA5 { currentpagedevice begin " \
            "  PageSize 0 get 421 sub abs 10 lt PageSize 1 get 595 sub abs 10 lt " \
            "  and end } bind def\n" \
            "/pageIsLetter { currentpagedevice begin " \
            "  PageSize 0 get 612 sub abs 10 lt PageSize 1 get 792 sub abs 10 lt " \
            "  and end } bind def\n" \
            "% concatstr(ings) copied from http://en.wikibooks.org/wiki/PostScript_FAQ\n" \
            "/concatstr % (a) (b) -> (ab)\n" \
            "{ exch dup length\n" \
            "  2 index length add string\n" \
            "  dup dup 4 2 roll copy length\n" \
            "  4 -1 roll putinterval\n" \
            "} bind def\n" \
            + self.monthCalendars() \
            + "%%EndResource\n" \
            + "%%EndProlog\n"

        p = p + "%%BeginSetup\n" \
            "%%IncludeResource: font Times-Roman\n" \
            "%%IncludeResource: font Times-Bold\n" \
            "%%IncludeResource: font Helvetica\n" \
            "%%IncludeResource: font Helvetica-Oblique\n" \
            "%%IncludeResource: font Courier\n" \
            "%%IncludeResource: font Courier-Bold\n" \
            "%%IncludeResource: procset MakediaryProcs\n" \
            + "%%%%IncludeFeature: *PageSize %s\n" % self.di.paperSize.title() \
            + "%%EndSetup\n"
        return p

    def postamble(self):
        """Return the document trailer as a string."""
        p =   self.di.sectionSep \
            + "%%Trailer\n" \
            + ("%%%%Pages: %d\n" % self.di.pageNumber) \
            + "%%EOF\n"
        return p


    def monthCalendars(self):
        """ Print code that defines a postscript name for printing a calendar for the months of
        last year, this year and next year.  We will end up with a dictionary called
        'monthCalendars' that contains entries such as 'M_2000_12', 'M_2001_01' etc.  Calling
        those names will print the corresponding calendar with its bottom left corner at
        currentpoint.  The calendar will be 1 unit high and 1 unit wide.  Change the size of
        these calendars by calling scale before calling the calendar procedure"""

        p = self.di.sectionSep
        y = self.di.dtbegin.year
        a7 = 142.86                     # 1000/7
        a8 = 125.0                      # 1000/8
        p = p + "/monthCalendars 100 dict dup begin\n"
        # This list of years contains one instance of each of the 14 possible calendars.
        yearslist = [2000,2001,2002,2003,2004,2005,2006,2008,2009,2010,2012,2016,2020,2024]

        # Create 168 (14*12) month calendars, named M_mMM_bB_eE, where MM is a month number, B
        # is the day of week of 1jan, and E is day of week of 31dec (day of week is 0 to 6).
        # Callers need to call self.di.getMonthCalendarPsFnCall(y,m[,addyear=True]) when
        # printing a calendar.
        for year in yearslist:

            day_b = DateTime.DateTime(year,  1,  1).day_of_week
            day_e = DateTime.DateTime(year, 12, 31).day_of_week

            for month in range(1,13):
                mtime = DateTime.DateTime(year,month)
                # Work in a 1000-scaled world to make the numbers a bit easier.
                # "0 25 TR" here is to move things up very slightly, so that the
                # bottom line is not right on the bottom.  "25" should be calculated,
                # but at the moment it is measured and a static quantity.
                p = p + mtime.strftime("%%%%----\n/M_m%%02m_b%d_e%d{" % (day_b, day_e)) \
                    + " 5 dict begin /TT exch def\n" \
                    + " SA CP TR 0.001 0.001 scale 0 25 TR\n" \
                    + "/Helvetica-Bold findfont [80 0 0 100 0 0] makefont setfont\n"
                ts = mtime.strftime("%B")
                #p = p + "(%s) SWP2D 500 exch sub %d M " % (ts,a8*7) # Centred titles
                p = p + "%5.3f %5.3f M " % (20,a8*7) # Left titles
                p = p + "(%s) TT length 0 ne { (  ) concatstr TT concatstr} if SH\n" % (ts,)
                p = p + "/Helvetica findfont [80 0 0 100 0 0] makefont setfont " \
                    + "%5.3f (M) SWP2D sub %5.3f M (M) SH\n" % (a7*0.5,a8*6.0) \
                    + "%5.3f (T) SWP2D sub %5.3f M (T) SH\n" % (a7*1.5,a8*6.0) \
                    + "%5.3f (W) SWP2D sub %5.3f M (W) SH\n" % (a7*2.5,a8*6.0) \
                    + "%5.3f (T) SWP2D sub %5.3f M (T) SH\n" % (a7*3.5,a8*6.0) \
                    + "%5.3f (F) SWP2D sub %5.3f M (F) SH\n" % (a7*4.5,a8*6.0) \
                    + "%5.3f (S) SWP2D sub %5.3f M (S) SH\n" % (a7*5.5,a8*6.0) \
                    + "%5.3f (S) SWP2D sub %5.3f M (S) SH\n" % (a7*6.5,a8*6.0)
                thisweek = 0            # Used to calculate what line to print the week on
                ndays = mtime.days_in_month
                for day in range(1,ndays+1):
                    wday = DateTime.DateTime(year,month,day).day_of_week
                    p = p + "(%d) dup SWP2D %3.2f exch sub %5.3f M SH\n" \
                        % (day, wday*a7+a7/2, (5-thisweek)*a8 )
                    if wday==DateTime.Sunday:
                        thisweek = thisweek + 1
                p = p + "0 -25 TR "
                # Now draw a box around the month, just for boundary checking
                if self.di.debugBoxes:
                    #p = p + "0 SLW 0 0 999 999 50 debugboxLBRTD "
                    p = p + "0 SLW 0 0 999 999 debugboxLBRT "
                # End of the month definition
                p = p + "RE end } def\n"
        p = p + "end def\n"
        return p


    # print the whole diary
    def diary(self):
        di = self.di
        w = self.w
        w( self.preamble() )
        w( CoverPage(di).page() )
        #self.w( CalendarPage(di).page() )
        if di.debugVersion:
            w( VersionPage(di).page() )
        else:
            w( EmptyPage(di).page() )
        w( PersonalInformationPage(di).page() )

        # Print image pages, if there are any, and end on a new opening.
        for imagePage in di.imagePages:
            npages = imagePage["pages"]
            if npages == 1:
                w( ImageFilePage(di, imagePage["fileName"], imagePage["title"] ).page() )
            elif npages == 2:
                if di.evenPage:
                    self.w( NotesPage(di).page() )
                w( TwoImageFilePages(di, imagePage["fileName"], imagePage["title"]).page() )
            else:
                print >>sys.stderr, "makediary: internal error:"
                print >>sys.stderr, "-- image file (%s): imagePage['pages'] == %d" \
                      % (imagePage['fileName'], npages)
                sys.exit(1)
        if di.evenPage:
            self.w( EmptyPage(di).page() )

        w( TwoCalendarPages(di).page() )

        if di.perpetualCalendars:
            self.w( PerpetualCalendarPages(di).page() )

        # Ensure that the planner pages are on facing pages.
        if di.nPlannerYears > 0:
            if di.evenPage:
                self.w( EmptyPage(di).page() )
            # Decide whether to put short events on the planner pages.  If we are not using
            # pcal to generate the events, then yes.  If we are using pcal, only put short
            # events on if we have been told.
            doEventsOnPlanner = (not di.pcal or (di.pcal and di.pcalPlanner))
            if di.largePlanner:
                w( TwelvePlannerPages(di.dtbegin.year, di, doEventsOnPlanner).page() )
            else:
                w( FourPlannerPages(di.dtbegin.year, di, doEventsOnPlanner).page() )
            if di.dtbegin.month==1 and di.dtbegin.day==1:
                for i in range(1, di.nPlannerYears):
                    w( TwoPlannerPages(di.dtbegin.year+i, di).page() )
            else:
                w( FourPlannerPages(di.dtbegin.year+1, di).page() )
                for i in range(2, di.nPlannerYears):
                    w( TwoPlannerPages(di.dtbegin.year+i, di).page() )


        for i in range(di.nAddressPages):
            w( AddressPage(di).page() )

        # Ensure we start the expense pages on an even page
        if di.evenPage:
            if di.nAddressPages != 0:
                w( AddressPage(di).page() )
            else:
                w( EmptyPage(di).page() )

        if di.nExpensePages == 2:
            w( TwoExpensePages().page(di) )
        elif di.nExpensePages == 4:
            w( FourExpensePages().page(di) )

        for epsPage in di.epsPages:
            try:
                eps_pages = epsPage["pages"]
                eps_fileName = epsPage["fileName"]
                eps_title1 = epsPage["title1"]
                eps_title2 = epsPage["title2"]
            except KeyError, reason:
                print >>sys.stderr, "KeyError: missing key for EPS page (%s): %s" % \
                      (epsPage, str(reason))
                continue
            if eps_pages == 1:
                w( EPSFilePage(di, eps_fileName, eps_title1).page() )
            elif eps_pages == 2:
                # Ensure we start the two eps pages on an even page
                if di.evenPage:
                    w( EmptyPage(di).page() )
                w( TwoEPSFilePages(di, eps_fileName, eps_title1, eps_title2).page() )

        for manPageInfo in di.manPages:
            w( ManPagePages(di, manPageInfo).page() )

        for i in range(di.nNotesPages):
            w( NotesPage(di).page() )

        # Ensure we start the diary pages on a Monday
        while di.dt.day_of_week != DateTime.Monday: di.gotoPreviousDay()
        # Now get a multiple of whole weeks of the previous year
        for i in range(0,7*di.nWeeksBefore): di.gotoPreviousDay()

        # Print a blank page or an extra notes page to start the year on a left side page
        if di.evenPage:
            if di.nNotesPages > 0:
                w( NotesPage(di).page() )
            else:
                w( EmptyPage(di).page() )

        # Print diary pages until we see the end date
        while 1:
            if di.dt >= di.dtend:
                break
            w( DiaryPage(di).page() )

        # If specified, add a number of whole weeks after, probably in the next year.
        if di.nWeeksAfter:
            dw = di.dt + (7*di.nWeeksAfter)
            while di.dt < dw:
                w( DiaryPage(di).page() )
        # Finish at the end of a week
        while di.dt.day_of_week != DateTime.Monday:
            w( DiaryPage(di).page() )

        # Notes pages at the rear
        for i in range(di.nNotesPages):
            w( NotesPage(di).page() )
        # Print an extra notes page to finish on an even page.
        if not di.evenPage:
            if di.nNotesPages > 0:
                w( NotesPage(di).page() )

        w(self.postamble())



# ############################################################################################
# main()

def go(myname, opts):
    dinfo = DiaryInfo(myname, opts)
    dinfo.parseOptions()
    dinfo.readDotCalendar()
    #sys.stderr.write("%s\n" % dinfo.events)
    d = Diary(dinfo)
    d.diary()
    if dinfo.pdf:
        # If we don't close the pipe to the pdf2ps process, it waits forever for more input.
        dinfo.pdfProcess.stdin.close()
        dinfo.pdfProcess.wait()

if __name__=='__main__':
    try:
        go(sys.argv[0], sys.argv[1:])
    except IOError, reason:
        if reason.errno == EPIPE:
            sys.exit(1)
        else:
            raise


# This section is for emacs.
# Local variables: ***
# mode:python ***
# py-indent-offset:4 ***
# fill-column:95 ***
# End: ***
