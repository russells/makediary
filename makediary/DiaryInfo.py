#!/usr/bin/env python3
import sys
import getopt
import re
from os.path import join as path_join
from os.path import exists as path_exists
from glob import glob
from iniparse import SafeConfigParser as ConfigParser
from os.path import expanduser
from math import pow
import subprocess
from makediary.DT            import DT
from makediary.versionNumber import versionNumber

from makediary import PaperSize


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
               "calendar-pages=",
               "colour",
               "colour-images",
               "conversions-ref",
               "cover-image=",
               "cover-page-image=",
               "day-title-shading=",
               "debug-boxes",
               "debug-version",
               "debug-whole-page-boxes",
               "eps-page=",
               "eps-2page=",
               "event-images",
               "expense-pages=",
               "gridded-logbook",
               "gridded-notes",
               "gridded",
               "help",
               "image-page=",
               "image-2page=",
               "large-planner",
               "layout=",
               "line-colour=",
               "line-spacing=",
               "line-thickness=",
               "logbook-pages=",
               "man-page=",
               "margins-multiplier=",
               "moon",
               "northern-hemisphere-moon",
               "no-appointment-times",
               "no-smiley",
               "notes-pages=",
               "output-file=",
               "page-numbers",
               "page-registration-marks",
               "page-size=",
               "page-x-offset=",
               "page-y-offset=",
               "paper-size=",
               "pcal",
               "pcal-planner",
               "pdf",
               "perpetual-calendars",
               "personal-info-no-work",
               "planner-years=",
               "ref=",
               "sed-ref",
               "sh-ref",
               "shading=",
               "start-date=",
               "title=",
               "units-ref",
               "unix-ref",
               "vi-ref",
               "vim-ref",
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
                  "    [--calendar-pages=yes|no]\n",
                  "    [--colour | --colour-images] [--line-colour=COLOUR]\n",
                  "    [--cover-image=IMAGE] [--cover-page-image=IMAGE]\n",
                  "    [--day-title-shading=all|holidays|none] [--shading=yes|no]\n",
                  "    [--debug-boxes] [--debug-whole-page-boxes] [--debug-version]\n",
                  "    [--eps-page=epsfile[|title]] [--eps-2page=epsfile[|title1[|title2]]]\n",
                  "    [--event-images] [--expense-pages=0|2|4] [--gridded-notes]\n",
                  "    [--image-page=IMGFILE[,title]] [--image-2page=IMGFILE[,title][,coverage]]\n",
                  "    [--large-planner] [--layout=LAYOUT] [--line-spacing=mm]\n",
                  "    [--line-thickness=mm] [--margins-multiplier=f] [--moon]\n",
                  "    [--layout=LAYOUT] [--logbook-pages=N] [--man-page=MANPAGE]\n",
                  "    [--northern-hemisphere-moon] [--no-appointment-times] [--no-smiley]\n",
                  "    [--notes-pages=n] [--page-numbers]\n",
                  "    [--page-registration-marks] [--page-x-offset=Xmm]\n",
                  "    [--page-y-offset=Ymm] [--pdf] [--planner-years=n] \n",
                  "    [--pcal] [--pcal-planner] [--perpetual-calendars]\n",
                  "    [--personal-info-no-work]\n",
                  "    [--ref=<refname>] [--awk-ref] [--conversions-ref]\n",
                  "    [--sed-ref] [--sh-ref] [--units-ref] [--unix-ref] [--vi[m]-ref]\n",
                  "    [--weeks-before=n] [--weeks-after=n]\n",
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

    layouts = ( "day-to-page", "logbook", "week-to-opening", "week-to-2-openings",
                "week-to-page", "week-with-notes", "work" )
    defaultLayout = "week-to-2-openings"
    usageStrings.append("  Layouts: " + ", ".join(layouts) + "\n")
    usageStrings.append("  Default layout: " + defaultLayout + "\n")

    def usage(self, f=sys.stderr, code=1):
        for i in range(len(self.usageStrings)):
            f.write(self.usageStrings[i])
        sys.exit(code)

    def shortUsage(self, f=sys.stderr):
        print("%s --help for usage" % self.myname, file=f)
        sys.exit(1)

    def __init__(self, myname, opts):

        self.myname = myname
        self.opts = opts
        self.usageStrings[0] = self.usageStrings[0] % myname

        # first init the instance variables.
        self.pageNumber = 0             # Page number count
        self.currentJDaysLeft = -1      # Days left in year
        dt = DT.now()
        self.setStartDate(DT(dt.year+1, 1, 1)) # Adjusted time, next year
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
        self.titleFontNoBoldName = "Times" #
        self.subtitleFontSize = 4.0     #
        self.subtitleFontName = "Helvetica" #
        self.subtitleFontNoBoldName = "Helvetica" #
        self.personalinfoFontName = "Times-Bold" #
        self.personalinfoFixedFontName = "Courier-Bold" #
        self.titleY = -1                # Distance from bottom to title, calc from page size
        self.titleLineY = -1            #
        self.titleGray = 0.8            # Background for titles on some pages
        self.underlineThick = 0.2       # Thickness of title lines etc
        self.lineSpacing = 6.0          # Spacing for writing lines
        self.lineThickness = 0          # Thickness of writing and other lines
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
        self.pageNumbers = False        # Print page numbers. where to cut.
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
        self.calendarPages = True
        self.nExpensePages = 2
        self.griddedLogbookPages = False
        self.griddedNotesPages = False
        self.griddedLogbookPages = False
        self.dayTitleBoxes = True
        self.dayTitleShading = "all"
        self.shading = True
        self.nLogbookPages = 100
        self.lineColour = [0,0,0]
        self.personalInfoNoWork = False

        self.configOptions = ConfigParser()
        self.configOptions.read( (expanduser("~/.makediaryrc"), ".makediaryrc", "makediaryrc") )

        self.createMonthCalendars()

        self.parseOptions()
        self.readDotCalendar()


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
        dow_begin = DT(year,  1,  1).day_of_week()
        dow_end   = DT(year, 12, 31).day_of_week()
        k = (month, dow_begin, dow_end)
        if not k in self.monthCalendarList:
            print("makediary: internal error:", file=sys.stderr)
            print("-- No month calendar for year=%s month=%s" % (str(year),str(month)),
                  file=sys.stderr)
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

        # Save the command line opts in here, and process them all at the end.
        c = {}

        try:
            optlist,args = getopt.getopt(args,'',self.options)
        except getopt.error as reason:
            sys.stderr.write( "Error parsing options: " + str(reason) + "\n")
            self.shortUsage()
        if len(args) != 0:
            sys.stderr.write("Unknown arg: %s\n" % args[0] )
            self.shortUsage()
        # Gather all the command line options into a list so we can process them later.
        for opt in optlist:
            assert len(opt) == 2
            if 0:
                pass
            elif opt[0] == "--help":
                # The help option bypasses all the others.
                self.usage(sys.stdout, 0)
            elif opt[0] == "--man-page":
                # --man-page can be specified multiple times.
                self.manPageOption(opt[1])
            elif opt[0] == "--ref":
                # --ref can be specified multiple times.
                name_and_titles = opt[1].split('|')
                self.standardEPSRef(name_and_titles[0], name_and_titles[1:])
            # Now all the standard args.
            elif len(opt[1]) == 0:
                # No argument, so just save the setting.
                c[opt[0]] = True
            else:
                # Save the setting and the argument.
                c[opt[0]] = opt[1]

        # Now process all the gathered options.  Look at the layout option first, so we can set
        # things needed by the layout, and potentially change them later.
        if "--layout" in c:
            l = c["--layout"]
            if l in self.layouts:
                self.layout = l
                if self.layout == "logbook":
                    self.calendarPages = False
                    self.nPlannerYears = 0
                elif self.layout == "week-to-page" or self.layout == "week-with-notes":
                    self.dayTitleBoxes = False
                    self.dayTitleShading = "none"
            else:
                print("%s: Unknown layout %s" % (self.myname, l), file=sys.stderr)
                self.shortUsage()
        if "--address-pages" in c:
            self.nAddressPages = self.integerOption("address-pages",c["--address-pages"])
        if "--appointment-width" in c:
            self.appointments = True
            aw = c["--appointment-width"]
            if aw[-1] == '%':
                optstr = aw[0:-1] # Strip an optional trailing '%'
            else:
                optstr = aw
            self.appointmentWidth = self.floatOption("appointment-width",optstr)
            if self.appointmentWidth < 0 or self.appointmentWidth > 100:
                sys.stderr.write("%s: appointment width must be >=0 and <=100\n" %
                                 self.myname)
                sys.exit(1)
        if "--appointments" in c:
            self.appointments = True
        if "--awk-ref" in c:
            self.standardEPSRef( 'awk', ['Awk reference'] )
        if "--calendar-pages" in c:
            self.calendarPages = self.boolOption("calendar-pages", c["--calendar-pages"])
        if "--colour" in c or "--colour-images" in c:
            self.colour = True
        if "--line-colour" in c:
            self.setLineColour(c["--line-colour"])
            self.dayTitleShading = "none"
            self.shading = False
        if "--shading" in c:
            self.shading = self.boolOption("shading", c["--shading"])
        if "--conversions-ref" in c:
            self.standardEPSRef( 'conversions', ['Double conversion tables'] )
        if "--cover-image" in c:
            self.coverImage = c["--cover-image"]
        if "--cover-page-image" in c:
            self.coverPageImage = c["--cover-page-image"]
        if "--day-title-shading" in c:
            dts = c["--day-title-shading"]
            if dts in ("all", "holidays", "none"):
                self.dayTitleShading = dts
            else:
                print("day-title-shading must be all or holidays or none" \
                      + " (not \"%s\")" % dts, file=sys.stderr)
                self.shortUsage();
        if "--debug-boxes" in c:
            self.debugBoxes = 1
        if "--debug-whole-page-boxes" in c:
            self.debugWholePageBoxes = 1
        if "--debug-version" in c:
            self.debugVersion = True
        if "--eps-page" in c:
            self.epsFilePageOption(c["--eps-page"], 1)
        if "--eps-2page" in c:
            self.epsFilePageOption(c["--eps-2page"], 2)
        if "--expense-pages" in c:
            ep = c["--expense-pages"]
            if ep == '0' or ep == '2' or ep == '4':
                self.nExpensePages = int(ep)
            else:
                print("%s: number of expense pages must be 0, 2, or 4 (not \"%s\")." % \
                      (sys.argv[0], ep), file=sys.stderr)
                self.shortUsage()
        if "--perpetual-calendars" in c:
            self.perpetualCalendars = True
        if "--event-images" in c:
            self.drawEventImages = True
        if "--gridded" in c:
            self.griddedLogbookPages = True
            self.griddedNotesPages = True
        if "--gridded-logbook" in c:
            self.griddedLogbookPages = True
        if "--gridded-notes" in c:
            self.griddedNotesPages = True
        if "--image-page" in c:
            self.imagePageOption(c["--image-page"], 1)
        if "--image-2page" in c:
            self.imagePageOption(c["--image-2page"], 2)
        if "--large-planner" in c:
            self.largePlanner = True
        if "--line-spacing" in c:
            self.lineSpacing = self.floatOption("line-spacing",c["--line-spacing"])
        if "--line-thickness" in c:
            self.lineThickness = self.floatOption("line-thickness",c["--line-thickness"])
        if "--logbook-pages" in c:
            self.nLogbookPages = self.integerOption("logbook-pages",c["--logbook-pages"])
        if "--margins-multiplier" in c:
            multiplier = self.floatOption("margins-multiplier",c["--margins-multiplier"])
            self.tMargin = self.tMargin * multiplier
            self.bMargin = self.bMargin * multiplier
            self.iMargin = self.iMargin * multiplier
            self.oMargin = self.oMargin * multiplier
        if "--moon" in c:
            self.moon = True
        if "--northern-hemisphere-moon" in c:
            self.moon = True
            self.northernHemisphereMoon = True
        if "--no-appointment-times" in c:
            self.appointmentTimes = False
        if "--no-smiley" in c:
            self.smiley = False
        if "--notes-pages" in c:
            self.nNotesPages = self.integerOption("notes-pages",c["--notes-pages"])
        if "--output-file" in c:
            self.outName = c["--output-file"]
            self.outNameSet = True
        if "--page-numbers" in c:
            self.pageNumbers = True
        if "--page-registration-marks" in c:
            self.pageRegistrationMarks = True
        if "--page-size" in c:
            self.pageSize = c["--page-size"]
            self.setPageSize(self.pageSize)
        if "--page-x-offset" in c:
            self.pageXOffset = self.floatOption("page-x-offset", c["--page-x-offset"])
        if "--page-y-offset" in c:
            self.pageYOffset = self.floatOption("page-y-offset", c["--page-y-offset"])
        if "--pdf" in c:
            self.pdf = True
        if "--paper-size" in c:
            self.paperSize = c["--paper-size"]
            self.setPaperSize(self.paperSize)
        if "--pcal" in c:
            self.pcal = True
        if "--pcal-planner" in c:
            self.pcal = True
            self.pcalPlanner = True
        if "--personal-info-no-work" in c:
            self.personalInfoNoWork = True
        if "--planner-years" in c:
            self.nPlannerYears = self.integerOption("planner-years",c["--planner-years"])
        if "--version" in c:
            print("makediary, version " + versionNumber)
            sys.exit(0)
        if "--sed-ref" in c:
            self.standardEPSRef( 'sed', ['sed reference'] )
        if "--sh-ref" in c:
            self.standardEPSRef( 'sh', ['Shell and utility reference'] )
        if "--start-date" in c:
            self.setStartDate(DT.strptime(c["--start-date"], '%Y-%m-%d'))
        if "--title" in c:
            self.title = c["--title"]
        if "--units-ref" in c:
            self.standardEPSRef( 'units', ['Units'] )
        if "--unix-ref" in c:
            self.standardEPSRef( 'unix', ['Unix reference',] )
        if "--vim-ref" in c or "--vi-ref" in c:
            self.standardEPSRef( 'vi', ['Vi reference', 'Vim extensions'] )
        if "--weeks-after" in c:
            self.nWeeksAfter = self.integerOption("weeks-after",c["--weeks-after"])
        if "--weeks-before" in c:
            self.nWeeksBefore = self.integerOption("weeks-before",c["--weeks-before"])
        if "--year" in c:
            self.setStartDate(DT(self.integerOption("year",c["--year"]), 1, 1))

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
            #print("Running "+str(pdfArgs), file=sys.stderr)
            self.pdfProcess = subprocess.Popen(pdfArgs, stdin=subprocess.PIPE)
            self.out = self.pdfProcess.stdin
        else:
            if self.outName == '-':
                self.out = sys.stdout
            else:
                try:
                    self.out = open(self.outName,'w')
                except IOError as reason:
                    sys.stderr.write(("Error opening '%s': " % self.outName) \
                                     + str(reason) + "\n")
                    #self.usage()
                    sys.exit(1)
        try:
            self.setPageSize(self.pageSize)
        except:
            self.setPageSize(self.paperSize)
        self.calcPageLayout()
        self.calcDateStuff()


    def setLineColour(self, c):
        if c == "red":
            self.lineColour = [1,0,0]
        elif c == "green":
            self.lineColour = [0,1,0]
        elif c == "blue":
            self.lineColour = [0,0,1]
        else:
            try:
                cols = c.split(',')
                if len(cols) != 3:
                    raise Exception("need three numbers")
                r = float(cols[0])
                if r < 0.0 or r > 1.0:
                    raise Exception("red out of range")
                g = float(cols[1])
                if g < 0.0 or g > 1.0:
                    raise Exception("green out of range")
                b = float(cols[2])
                if b < 0.0 or b > 1.0:
                    raise Exception("blue out of range")
                self.lineColour = (r,g,b)
            except Exception as e:
                print("line colour wacky: %s: %s" % (c, e.message), file=sys.stderr)
                sys.exit(1)


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
            print("Strange number of pages for eps-page: %d" % npages, file=sys.stderr)
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
            print("%s: cannot find ref files for \"%s\"" % \
                  (sys.argv[0], name), file=sys.stderr)
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
        except ValueError as reason:
            sys.stderr.write("Error converting integer: " + str(reason) + "\n")
            self.shortUsage()


    def boolOption(self, name, s):
        if s in ('0', 'false', 'False', 'FALSE', 'no', 'NO'):
            return False
        if s in ('1', 'true', 'True', 'TRUE', 'yes', 'YES'):
            return True
        sys.stderr.write("Error converting bool for %s: %s\n" % (name, s))
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

        print("%s: unknown man page: %s" % (sys.argv[0], opt), file=sys.stderr)


    def setStartDate(self,date):
        self.dtbegin = DT(date.year, date.month, date.day)
        self.dt = DT(date.year, date.month, date.day)
        #self.dtend = self.dt + DateTime.RelativeDateTime(years=1)
        self.dtend = DT(date.year+1, date.month, date.day)


    def imagePageOption(self, option, npages):
        assert npages==1 or npages==2
        commaparts = option.split(",", npages)
        if len(commaparts) == 1:
            self.imagePages.append( { "fileName" : commaparts[0],
                                      "title"    : "",
                                      # npages can be 1 here, in which case the coverage option
                                      # will be ignored by the ImageFilePages class.  It's just
                                      # simpler to put it in here.
                                      "coverage" : 0.5,
                                      "pages"    : npages } )
        elif len(commaparts) == 2:
            self.imagePages.append( { "fileName" : commaparts[0],
                                      "title"    : commaparts[1],
                                      # npages can also be 1 here.
                                      "coverage" : 0.5,
                                      "pages"    : npages } )
        elif len(commaparts) == 3:
            coverage = self.floatOption(option, commaparts[2])
            # Check the coverage for sanity.  It can be from 50% to 90%, and we allow it to be
            # specified as in the ranges 0.5 to 0.9 or 50 to 90.
            if not ((coverage >= 0.5 and coverage <= 0.9) \
                    or (coverage >= 50 and coverage <= 90)):
                sys.stderr.write("coverage of a 2 page image must be between 0.5 and 0.9" +
                                 " (or 50 and 90) - I got %.2f\n" % coverage)
                self.shortUsage()
            if coverage > 1.0:
                coverage = coverage / 100.0
            self.imagePages.append( { "fileName" : commaparts[0],
                                      "title"    : commaparts[1],
                                      "coverage" : coverage,
                                      "pages"    : npages } )


    def floatOption(self,name,s):
        """Convert an arg to a float."""
        try:
            return float(s)
        except ValueError as reason:
            sys.stderr.write("Error converting float: " + str(reason) + \
                             ", from " + str(name) + "\n")
            self.shortUsage()

    def setPageSize(self,s):
        """Set the page size to a known size."""
        sizes = PaperSize.getPaperSize(s)
        if sizes is None:
            print("Unknown page size: %s" % s, file=sys.stderr)
            self.shortUsage()
        self.pageWidth = sizes[0]
        self.pageHeight = sizes[1]
        # Adjust font sizes with respect to A5, on a square root scale.
        self.adjustSizesForPageSize()

    def setPaperSize(self,s):
        """Set the paper size to a known size."""
        sizes = PaperSize.getPaperSize(s)
        if sizes is None:
            print("Unknown paper size: %s" % s, file=sys.stderr)
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
        self.dt = self.dt + DT.delta(1)
        self.calcDateStuff()

    def gotoPreviousDay(self):
        self.dt = self.dt - DT.delta(1)
        self.calcDateStuff()

    def calcDateStuff(self):
        # Call this every time the day changes.
        def is_leapyear(y):
            return ((y%4) == 0) and (((y%400) == 0) or ((y%100) != 0))
        def jday(dt):
            return dt.timetuple().tm_yday
        if is_leapyear(self.dt.year):
            self.currentJDaysLeft = 366 - jday(self.dt)
        else:
            self.currentJDaysLeft = 365 - jday(self.dt)
        #sys.stderr.write("calcDateStuff: currentsec = %d\n" % self.currentSecond )


    def readDotCalendar(self):
        if self.pcal:
            from makediary import DotCalendarPcal as DotCalendar
        else:
            from makediary import DotCalendar
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
            #print("searchpath is %s" % str(searchpath), file=sys.stderr)
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

