#!/usr/bin/python

# vim: set shiftwidth=4 expandtab smartindent textwidth=95:

# Print a year diary.

# $Id: makediary.py 94 2003-12-18 16:06:58Z anonymous $

versionNumber = "0.1.2pre"

import sys
import getopt
import re
import StringIO
import Image
import EpsImagePlugin
import DotCalendar
import PaperSize
import Moon
from mx import DateTime #import *
from math import pow

# ############################################################################################

class DiaryInfo:
    
    """ This class holds configuration information for the rest of the program, parses command
    line args, prints the usage message."""

    points_mm = 2.8346457               # Do all our work in millimetres

    sectionSep = "%-----------------\n" # Separator inside the postscript

    options = ["year=",
               "output-file=",
               "cover-image=",
               "images",
               "colour",
               "address-pages=",
               "notes-pages=",
               "planner-years=",
               "line-spacing=",
               "page-size=",
               "page-x-offset=",
               "page-y-offset=",
               "paper-size=",
               "weeks-before=",
               "weeks-after=",
               "debug-boxes",
               "debug-version",
               "debug-whole-page-boxes",
               "page-registration-marks",
               "appointments",
               "appointment-width=",
               "no-appointment-times",
               "week-to-opening",
               "moon",
               "margins-multiplier=",
               "help",
               "version"]

    usageStrings = \
                 ["Usage: %s [--year=year] [--output-file=file]\n",
                  "  [--cover-image=file] [--address-pages=n] [--notes-pages=n]\n",
                  "  [--planner-years=n] [--line-spacing=mm] [--appointments]\n",
                  "  [--appointment-width=w] [--images] [--weeks-before=n] [--weeks-after=n]\n",
                  "  [--week-to-opening] [--margins-multiplier=f]\n",
                  "  [--no-appointment-times]\n",
                  "  [--debug-boxes] [--debug-whole-page-boxes] [--debug-version]\n",
                  "  [--page-registration-marks] [--colour] [--moon]\n",
                  "  [--page-x-offset=Xmm] [--page-y-offset=Ymm]\n",
                  "  [--help] [--version]\n"]
    sizes = PaperSize.getPaperSizeNames()
    sizesString = ''
    for n in range(len(sizes)):
        s = sizes[n]
        if n == len(sizes)-1: sizesString = sizesString+s
        else:                 sizesString = sizesString+s+'|'
    usageStrings.append("  [--page-size=%s]\n" % sizesString)
    usageStrings.append("  [--paper-size=%s]\n" % sizesString)

    def usage(self, f=sys.stderr):
        for i in range(len(self.usageStrings)):
            f.write(self.usageStrings[i])
        sys.exit(1)

    def __init__(self, myname, opts):

        self.myname = myname
        self.opts = opts
        self.usageStrings[0] = self.usageStrings[0] % myname

        # first init the instance variables.
        self.pageNumber = 0             # Page number count
        self.currentJDaysLeft = -1      # Days left in year
        self.dt = DateTime.DateTime(DateTime.now().year+1) # Adjusted time (next year)
        self.year = self.dt.year        # Calendar year
        wh = PaperSize.getPaperSize('a5') # Page sizes.  Default to a5.
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
        self.titleY = -1                # Distance from bottom to title, calc from page size
        self.titleLineY = -1            # 
        self.titleGray = 0.8            # Background for titles on some pages
        self.underlineThick = 0.2       # Thickness of title lines etc
        self.lineSpacing = 6.0          # Spacing for writing lines
        self.evenPage = 0               # even and odd pages
        self.out = sys.stdout           # Output file
        self.nAddressPages = 6          # Default
        self.nNotesPages = 6            # 
        self.nPlannerYears = 2          # 
        self.coverImage = None          # Pic for the cover page.
        self.appointments = 0           # Different "styles" for different people.
        self.appointmentTimes = 1       # Print appointment times or not
        self.appointmentWidth = 0.35    # Width of appointments (as proportion)
        self.colour = 0                 # If true, print images in colour
        self.moon = 0                   # If true, print moon phases
        self.weekToOpening = 0          #
        self.debugBoxes = 0             # If true, draw faint boxes around things for debugging
        self.debugVersion = 0           # If true, print version info on inside cover.
        self.debugWholePageBoxes = 0    # If true, draw faint boxes around all pages.
        self.pageRegistrationMarks = 0  # Print marks to show where to cut.
        self.events = {}                # Events to draw on each page, from .calendar file.
        self.drawImages = 0             # If true, draw event images
        self.nWeeksBefore = 0           # Print this number of weeks before the current year.
        self.nWeeksAfter = 0

    def parseOptions(self):
        args = self.opts
        # The first week day should be settable by command line option.
        #calendar.setfirstweekday(MONDAY)
        try:
            optlist,args = getopt.getopt(args,'',self.options)
        except getopt.error, reason:
            sys.stderr.write( "Error parsing options: " + str(reason) + "\n")
            self.usage()
        if len(args) != 0:
            sys.stderr.write("Unknown arg: %s\n" % args[0] )
            self.usage()
        for opt in optlist:
            if opt[0] == '--year':
                self.year = self.integerOption("year",opt[1])
                self.dt = DateTime.DateTime(self.year)
            elif opt[0] == '--output-file':
                try:
                    self.out = open(opt[1],'w')
                except IOError, reason:
                    sys.stderr.write(("Error opening '%s': " % opt[1]) \
                                     + str(reason) + "\n")
                    self.usage()
            elif opt[0] == "--address-pages":
                self.nAddressPages = self.integerOption("address-pages",opt[1])
            elif opt[0] == "--notes-pages":
                self.nNotesPages = self.integerOption("notes-pages",opt[1])
            elif opt[0] == "--planner-years":
                self.nPlannerYears = self.integerOption("planner-years",opt[1])
            elif opt[0] == "--line-spacing":
                self.lineSpacing = self.floatOption("line-spacing",opt[1])
            elif opt[0] == "--page-size":
                self.setPageSize(opt[1])
            elif opt[0] == "--paper-size":
                self.setPaperSize(opt[1])
            elif opt[0] == "--page-x-offset":
                self.pageXOffset = self.floatOption("page-x-offset", opt[1])
            elif opt[0] == "--page-y-offset":
                self.pageYOffset = self.floatOption("page-y-offset", opt[1])
            elif opt[0] == "--cover-image":
                self.coverImage = opt[1]
            elif opt[0] == "--debug-boxes":
                self.debugBoxes = 1
            elif opt[0] == "--debug-whole-page-boxes":
                self.debugWholePageBoxes = 1
            elif opt[0] == "--debug-version":
                self.debugVersion = 1
            elif opt[0] == "--page-registration-marks":
                self.pageRegistrationMarks = 1
            elif opt[0] == "--appointments":
                self.appointments = 1
            elif opt[0] == "--no-appointment-times":
                self.appointmentTimes = 0
            elif opt[0] == "--appointment-width":
                self.appointments = 1
                self.appointmentWidth = self.floatOption("appointment-width",opt[1])
            elif opt[0] == "--week-to-opening":
                self.weekToOpening = 1
            elif opt[0] == "--images":
                self.drawImages = 1
            elif opt[0] == "--colour":
                self.colour = 1
            elif opt[0] == "--moon":
                self.moon = 1
            elif opt[0] == "--weeks-before":
                self.nWeeksBefore = self.integerOption("weeks-before",opt[1])
            elif opt[0] == "--weeks-after":
                self.nWeeksAfter = self.integerOption("weeks-after",opt[1])
            elif opt[0] == "--margins-multiplier":
                multiplier = self.floatOption("margins-multiplier",opt[1])
                self.tMargin = self.tMargin * multiplier
                self.bMargin = self.bMargin * multiplier
                self.iMargin = self.iMargin * multiplier
                self.oMargin = self.oMargin * multiplier
            elif opt[0] == "--help":
                self.usage(sys.stdout)
            elif opt[0] == "--version":
                print "makediary, version " + versionNumber
                print "$Id: makediary.py 94 2003-12-18 16:06:58Z anonymous $"
                sys.exit(0)
            else:
                print >>sys.stderr, "Unknown option: %s" % opt[0]
                self.usage()
        self.calcPageLayout()
        self.calcDateStuff()


    def integerOption(self,name,s):
        """Convert an arg to an int."""
        try:
            return int(s)
        except ValueError,reason:
            sys.stderr.write("Error converting integer: " + str(reason) + "\n")
            self.usage()

    def floatOption(self,name,s):
        """Convert an arg to a float."""
        try:
            return float(s)
        except ValueError,reason:
            sys.stderr.write("Error converting float: " + str(reason) + "\n")
            self.usage()

    def setPageSize(self,s):
        """Set the page size to a known size."""
        sizes = PaperSize.getPaperSize(s)
        if sizes is None:
            print >>sys.stderr, "Unknown page size: %s" % s
            self.usage()
        self.pageWidth = sizes[0]
        self.pageHeight = sizes[1]
        # Adjust font sizes with respect to A5, on a square root scale.
        self.adjustSizesForPageSize()

    def setPaperSize(self,s):
        """Set the paper size to a known size."""
        sizes = PaperSize.getPaperSize(s)
        if sizes is None:
            print >>sys.stderr, "Unknown paper size: %s" % s
            self.usage()
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
        dc = DotCalendar.DotCalendar()
        years = []
        for i in range(self.nPlannerYears+2):
            years.append(self.year-1+i)
        dc.setYears(years)
        dc.readCalendarFile()
        self.events = dc.datelist


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
                        + "%%BeginPageSetup\n" \
                        + "SA MM\n"
        if self.di.translatePage:
            self.preamble = self.preamble \
                            + "%5.3f %5.3f TR\n" % (self.di.translateXOffset,
                                                    self.di.translateYOffset)
        self.preamble = self.preamble \
                        + "calendars begin\n" \
                        + "%%EndPageSetup\n" \
                        + "%% This is for year %d, " % self.di.dt.year
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
    """Basic PostScript page with images."""

    def image(self,file,x,y,xmaxsize,ymaxsize):
        
        """Print an image on the page.  The image will be scaled so it will fit within a box at
        (x,y), with size (xmaxsize,ymaxsize), and centred inside that box."""

        s = ""
        im = Image.open(file,"r")
        xsize,ysize = im.size
        if not self.di.colour:
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


# ############################################################################################

# An empty page.

class EmptyPage(PostscriptPage):
    def body(self):
        return "% --- An empty page\n"

# ############################################################################################

# An almost empty page, with version information printed.

class VersionPage(PostscriptPage):
    def body(self):
        fontSize = 2.4*self.di.pageHeight/210.0
        linex = fontSize*6
        s=""
        versionString = self.postscriptEscape(
            "Version: $Id: makediary.py 94 2003-12-18 16:06:58Z anonymous $")
        dateString = self.postscriptEscape(DateTime.now() \
                                           .strftime("Generated at: %Y-%m-%dT%H:%M:%S%Z"))
        s = s + "% --- Version page\n" \
            + "/Courier %5.3f selectfont " % fontSize \
            + "%5.3f %5.3f M (%s) SH\n" % (linex, fontSize*12, versionString) \
            + "%5.3f %5.3f M (%s) SH\n" % (linex, fontSize*10, dateString)
        liney = self.di.pageHeight*0.8
        s = s + "%5.3f %5.3f M (Command:) SH\n" % (linex, liney)
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
        
        s =   "% --- cover page\n" \
            + "% border around the cover page\n" \
            + "%5.3f %5.3f %5.3f %5.3f %5.3f boxLBRT\n" % \
            (xleft,ybottom,xright,ytop,self.di.underlineThick) \
            + "/Times-Roman %d selectfont\n" % textheight \
            + "% find half of the width of the year string\n" \
            + "(%d) dup SW pop 2 div\n" % self.di.year \
            + "% move that far left of the centre\n" \
            + "%5.2f exch sub %5.2f M SH\n" % (textxcentre,textycentre)
        if self.di.coverImage==None:
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
        yr = self.di.dt.year
        for yd in ((yr-1, left, bottom + yheight*2.0 + yvgap*2.5 ),
                   (yr,   left, bottom + yheight + yvgap*1.5),
                   (yr+1, left, bottom + yvgap*0.5)):
            year = yd[0]
            x = yd[1]
            y = yd[2]

            for m in range(1,13):
                my = y + mvspacing * (2-int((m-1)/4)) + mvgap*0.5
                mx = x + ((m-1) % 4) * mhspacing + mhgap*0.5
                mname = DateTime.DateTime(year,m).strftime("%b%Y")
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
        y = self.di.dt.year
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
            mname = DateTime.DateTime(thisy,thism).strftime("%b%Y")
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
        
        s = s \
            + self.do1line("Name"              ,None       ,0) \
            + self.do1line("Phone"             ,"Mobile"   ,0) \
            + self.do1line("Email"             ,None       ,0) \
            + self.do1line("Address"           ,None       ,0) \
            + self.do1line(None                ,None       ,0) \
            + self.do1line(None                ,None       ,1) \
            + self.do1line("Work"              ,None       ,0) \
            + self.do1line("Phone"             ,"Fax"      ,0) \
            + self.do1line("Email"             ,None       ,0) \
            + self.do1line("Address"           ,None       ,0) \
            + self.do1line(None                ,None       ,0) \
            + self.do1line(None                ,None       ,1) \
            + self.do1line("Emergency Contacts",None       ,0) \
            + self.do1line(None                ,None       ,0) \
            + self.do1line(None                ,None       ,0) \
            + self.do1line(None                ,None       ,0) \
            + self.do1line(None                ,None       ,1) \
            + self.do1line("Other Information" ,None       ,0)

        while self.linenum < nlines:
            s = s + self.do1line(None,None,0)
        
        s = s + "RE\n"
        return s

    def do1line(self,title1,title2,linethick):
        """Do one line of the personal information page."""
        s = ""
        texty = self.pHeight - self.linenum*self.linespacing + 0.2*self.linespacing
        if title1 is not None:
            title1 = self.postscriptEscape(title1)
            s = s + "0 %5.3f M (%s) SH\n" % (texty,title1)
        if title2 is not None:
            title2 = self.postscriptEscape(title2)
            s = s + "%5.3f %5.3f M (%s) SH\n" % (self.pWidth/2,texty,title2)
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

    def __init__(self,year, startingmonth, nmonths, dinfo):
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
        self.monthwidth = float(self.pWidth - self.daywidth) / nmonths
        self.fontsize = self.lineheight * 0.7
        self.textb = self.lineheight * 0.2
        self.titleboxThick = self.di.underlineThick / 2.0


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
                    s = s + "0 %5.3f %5.3f %5.3f 0 %5.3f boxLBWHgray " % \
                        (dayb,self.monthwidth,self.lineheight,self.weekendgray)
                # All the other days are white
                else:
                    s = s + "0 %5.3f %5.3f %5.3f 0 boxLBWH\n" % \
                        (dayb,self.monthwidth,self.lineheight)
            if n<len(days)  and  days[n]!=0:
                # Now fill in the day number, if required
                s = s + "/%s %5.3f selectfont %5.3f %5.3f M (%d) SH\n" % \
                    (self.di.subtitleFontName, self.fontsize,
                     self.textb, dayb+self.textb, days[n])
                # Fill in the short calendar event names, for the current year only
                if self.year == self.di.year:
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
                                if len(se)==0:
                                    se = "/%s %5.3f selectfont (%s) SH " % \
                                         (font, self.fontsize*0.6,
                                          self.postscriptEscape(event["short"]))
                                else: se = se + \
                                           "/%s %5.3f selectfont (, ) SH " % \
                                           (self.di.subtitleFontName, self.fontsize*0.6) + \
                                           "/%s %5.3f selectfont (%s) SH " % \
                                           (font, self.fontsize*0.6,
                                            self.postscriptEscape(event["short"]))
                            
                        if len(se) != 0:
                            se = "%5.3f %5.3f M " %(self.lineheight*1.1, dayb+self.textb) + \
                                 se + "\n"
                            s = s + se 

        # Do the month titles (top and bottom)
        # Month name.  Needs to use locales.
        if   month==1:  monthname="January"
        elif month==2:  monthname="February"
        elif month==3:  monthname="March"
        elif month==4:  monthname="April"
        elif month==5:  monthname="May"
        elif month==6:  monthname="June"
        elif month==7:  monthname="July"
        elif month==8:  monthname="August"
        elif month==9:  monthname="September"
        elif month==10: monthname="October"
        elif month==11: monthname="November"
        elif month==12: monthname="December"
        else:           monthname="Mon %d" % month
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
        return PlannerPage(self.year,1,6,self.dinfo).page() \
               + PlannerPage(self.year,7,6,self.dinfo).page()


# ############################################################################################

class FourPlannerPages:
    """Print four planner pages for one year."""

    def __init__(self, year, dinfo):
        self.year = year
        self.dinfo = dinfo

    def page(self):
        return PlannerPage(self.year,1,3,self.dinfo).page() \
               + PlannerPage(self.year,4,3,self.dinfo).page() \
               + PlannerPage(self.year,7,3,self.dinfo).page() \
               + PlannerPage(self.year,10,3,self.dinfo).page()


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

    monthnames = [ "January","February","March","April","May","June",
                   "July","August","September","October","November","December"]

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
        monthname = DateTime.DateTime(self.di.year,month).strftime("%B")
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


    def setMargins(self):
        """Override setMargins() specially for diary pages."""
        PostscriptPage.setMargins(self)
        di = self.di
        self.pTop_diary = di.pageHeight - di.tMargin
        self.pHeight_diary = self.pTop_diary - self.pBottom
        self.ptop_diary = 0
        self.pheight_diary = 0

        if di.weekToOpening:
            self.dheight = self.pHeight_diary/4.0
        else:
            self.dheight = self.pHeight_diary/2.0
        self.dwidth = self.pWidth

        self.appProportion = self.di.appointmentWidth # Proportion of width in appointments
        self.appLeft = self.dwidth * (1.0 - self.appProportion)
        self.appRight = self.dwidth
        self.appWidth = self.appRight - self.appLeft
        if di.appointments:
            self.dwidthLines = self.appLeft - 0.2*di.lineSpacing
        else:
            self.dwidthLines = self.pWidth

        # These are the settings that have the most effect on the layout of a day.
        if di.weekToOpening:
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


    def diaryDay(self):
        
        """Print a diary day in half a page.  At the point this is called, the graphics state
        has already been translated so we can just draw straight into our patch."""

        di = self.di
        dt = di.dt

        s = "%%--- diary page half for %d-%02d-%02d\n" % (dt.year,dt.month,dt.day)
        # Print the day name as the half page header.
        s = s + "10 10 M /%s %5.2f selectfont " % (di.titleFontName, self.titlefontsize)
        dtext = dt.strftime("%A, %e %B") # %e seems to be undocumented
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

        # Draw the box around the title
        s = s + "0 %5.3f %5.3f %5.3f %5.3f boxLBWH\n" % \
            (self.titleboxy, self.dwidth, self.titleboxsize, di.underlineThick)

        # Draw all the writing lines.
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

        di.gotoNextDay()
        return s

    def drawAppointments(self):
        """Draw the appointments box on the diary half-page."""
        di = self.di
        s = ""
        # Adding and removing entries from this list will automatically adjust the number
        # of appointment lines, and the size of the lines.  Entries that are None result in
        # a line without a label.
        tempAppTimes = ["7","8","9","10","11","12","1","2","3","4","5","6","7"]
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
        x = startx
        y = starty
        s = ''
        s = s + '%% events for %s\n' % str(date)
        for i in range(nevents):
            xx = x
            event = eventlist[i]
            # Print an image, unless this is a warning event.
            if event.has_key('image') and di.drawImages \
                    and not (event.has_key('_warning') and event['_warning']):
                s = s + self.image(event['image'],
                                   x + 0.1*di.lineSpacing, y - yspace + 0.1*di.lineSpacing,
                                   1.8*yspace, 1.8*yspace)
                xx = x + 2.2*yspace
            if event.has_key('personal'):
                s = s + '/%s-Oblique %5.3f selectfont\n' % (di.subtitleFontName, yspace*0.6)
            else:
                s = s + '/%s %5.3f selectfont\n' % (di.subtitleFontName, yspace*0.6)

            if event.has_key('grey')  and  event['grey']:
                s = s + "0.5 setgray "
            else:
                s = s + "0 setgray "
            s = s + "%5.3f %5.3f M" % (xx, y+(yspace*0.25))
            st = self.postscriptEscape(event['text'])
            s = s + ' (%s) SH 0 setgray\n' % st
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

    def calendarsAtTop(self):
        """Print three calendars on the top half of a page."""
        di = self.di
        s = "%--- three calendars\n"
        # Page title.
        s = s + self.title(di.dt.strftime("%B %Y"),
                           "Week %d" % di.dt.iso_week[1])
        # Calculate the area we have for drawing.
        if di.weekToOpening:
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
        if di.weekToOpening:
            c_bottom = h * 0.50
            c_height = h * 0.44
            c_indent = w * 0.033
            c_width = c_height * 1.7
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
            # We hack around with the number of days we add or subtract to get into the next
            # month depending on how far into the month we are.  The problem is that any fixed
            # offset in days is going to be wrong for some day in some month.  Consider the
            # case where Jan 31 is on a Monday, and therefore the calendars are being printed
            # at the point where di.dt==Jan 31.  If we subtract less than a whole month's worth
            # of days we will still be in January and will not print December's calendar, but
            # if we add a whole month's worth of days, we will be in March.  So with a fixed
            # number of days we have the choice of printing (Dec,Jan,Mar) or (Jan,Jan,Feb).
            # Therefore we need to adjust the number of days for printing calendars at
            # different parts of the month.
            if di.dt.day < 10:
                if    i==-1: c_d = di.dt - 15 * DateTime.oneDay
                elif  i== 1: c_d = di.dt + 45 * DateTime.oneDay
                else:        c_d = di.dt
            elif di.dt.day < 20:
                c_d = di.dt + 30 * DateTime.oneDay * i
            else: # di.dt.day >= 20
                if    i==-1: c_d = di.dt - 45 * DateTime.oneDay
                elif  i== 1: c_d = di.dt + 15 * DateTime.oneDay
                else:        c_d = di.dt
            c_left = c_indent + (i+1)*(c_width+c_gutter)
            s = s +"%5.3f %5.3f M SA %5.3f %5.3f SC " % \
                (c_left,c_bottom,c_width,c_height) \
                + c_d.strftime("%b%Y") \
                + " RE\n"
            # Draw a box around the current month
            if i == 0:
                s = s + "0 SLW %5.3f %5.3f M " % (c_left-c_boxborder,c_bottom-c_boxborder) \
                    + "0 %5.3f RL %5.3f 0 RL " % (c_height+2*c_boxborder,c_width+2*c_boxborder) \
                    + "0 %5.3f RL %5.3f 0 RL S\n" % (-c_height-2*c_boxborder,-c_width-2*c_boxborder)
        # Now draw the lines just below the month calendars.
        l_y = c_bottom - di.lineSpacing - 2
        s = s + "0 SLW\n"
        while l_y > (di.lineSpacing * 0.7):
            s = s + "%5.3f %5.3f M %5.2f 0 RL S\n" % (c_indent,l_y,c_totalwidth)
            l_y = l_y - di.lineSpacing

        s = s + "RE\n"
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
            s = s + "%5.3f %5.3f %5.3f 270 90 arc 0 %5.3f RL fill %% 1st q\n" % \
                (x,y,radius,-size) \
                + "%5.3f %5.3f M (First) SH %5.3f %5.3f M (Quarter) SH\n" % \
                (linex,line1y, linex,line2y)
        elif quarter == self.mooncalc.MOON_FM:
            s = s + "%5.3f %5.3f M (Full) SH %5.3f %5.3f M (Moon) SH\n" % \
                (linex,line1y, linex,line2y)
        elif quarter == self.mooncalc.MOON_3Q:
            s = s + "%5.3f %5.3f %5.3f 90 270 arc 0 %5.3f RL fill %% 3rd q\n" % \
                (x,y,radius,size) \
                + "%5.3f %5.3f M (Third) SH %5.3f %5.3f M (Quarter) SH\n" % \
                (linex,line1y, linex,line2y)

        return s

    def body(self):
        s = ""
        if self.di.dt.day_of_week == DateTime.Monday:
            if self.di.weekToOpening:
                s = self.calendarsAtTop() +  \
                    self.printMondayWTO() + \
                    self.printTuesdayWTO() + \
                    self.printWednesdayWTO()
            else:
                s = self.calendarsAtTop() + self.bottomHalf();
        else:
            if self.di.weekToOpening:
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
        p = p + "%%BeginProlog\n" \
            + "%%%%Creator: %s, by Russell Steicke, version: %s\n" % \
            (self.di.myname,"$Id: makediary.py 94 2003-12-18 16:06:58Z anonymous $") \
            + DateTime.now().strftime("%%%%CreationDate: %a, %d %b %Y %H:%M:%S %z\n")
        p = p + "%%DocumentNeededResources: font Times-Roman\n" \
            "%%+ font Times-Bold\n%%+ font Helvetica\n%%+ font Helvetica-Oblique\n" \
            "%%Pages: (atend)\n%%PageOrder: Ascend\n%%Orientation: Portrait\n" \
            "%%EndComments\n" \
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
            + self.calendars() \
            + "%%EndProlog\n"
        return p

    def postamble(self):
        """Return the document trailer as a string."""
        p =   self.di.sectionSep \
            + "%%Trailer\n" \
            + ("%%%%Pages: %d\n" % self.di.pageNumber) \
            + "%%EOF\n"
        return p


    def calendars(self):
        """ Print code that defines a postscript name for printing a calendar for the months of
        last year, this year and next year.  We will end up with a dictionary called
        'calendars' that contains entries such as 'Dec2000', 'Jan2001' etc.  Calling those
        names will print the corresponding calendar with its bottom left corner at
        currentpoint.  The calendar will be 1 unit high and 1 unit wide.  Change the size of
        these calendars by calling scale before calling the calendar procedure"""
        
        p = self.di.sectionSep
        y = self.di.year
        a7 = 142.86                     # 1000/7
        a8 = 125.0                      # 1000/8
        p = p + "/calendars 100 dict dup begin\n"
        for year in y-1,y,y+1:
            for month in range(1,13):
                mtime = DateTime.DateTime(year,month)
                # Work in a 1000-scaled world to make the numbers a bit easier.
                # "0 25 TR" here is to move things up very slightly, so that the
                # bottom line is not right on the bottom.  "25" should be calculated,
                # but at the moment it is measured and a static quantity.
                p = p + mtime.strftime("%%----\n/%b%Y{") \
                    + " SA CP TR 0.001 0.001 scale 0 25 TR\n" \
                    + "/Helvetica-Bold findfont [80 0 0 100 0 0] makefont setfont\n"
                ts = mtime.strftime("%B  %Y")
                #p = p + "(%s) SWP2D 500 exch sub %d M " % (ts,a8*7) # Centred titles
                p = p + "%5.3f %5.3f M " % (20,a8*7) # Left titles
                p = p + "(%s) SH\n" % (ts,)
                p = p + "/Helvetica findfont [80 0 0 100 0 0] makefont setfont " \
                    + "%5.3f (S) SWP2D sub %5.3f M (S) SH\n" % (a7*0.5,a8*6.0) \
                    + "%5.3f (M) SWP2D sub %5.3f M (M) SH\n" % (a7*1.5,a8*6.0) \
                    + "%5.3f (T) SWP2D sub %5.3f M (T) SH\n" % (a7*2.5,a8*6.0) \
                    + "%5.3f (W) SWP2D sub %5.3f M (W) SH\n" % (a7*3.5,a8*6.0) \
                    + "%5.3f (T) SWP2D sub %5.3f M (T) SH\n" % (a7*4.5,a8*6.0) \
                    + "%5.3f (F) SWP2D sub %5.3f M (F) SH\n" % (a7*5.5,a8*6.0) \
                    + "%5.3f (S) SWP2D sub %5.3f M (S) SH\n"% (a7*6.5,a8*6.0)
                thisweek = 0            # Used to calculate what line to print the week on
                ndays = mtime.days_in_month
                for day in range(1,ndays+1):
                    wday = DateTime.DateTime(year,month,day).day_of_week
                    wday = (wday + 1) % 7 # Make Sunday first
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
                p = p + "RE} def\n"
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
        w( TwoCalendarPages(di).page() )
        # Ensure that the planner pages are on facing pages.
        if di.nPlannerYears > 0:
            if di.evenPage:
                self.w( EmptyPage(di).page() )
            w( FourPlannerPages(di.year, di).page() )
            for i in range(1, di.nPlannerYears):
                w( TwoPlannerPages(di.year+i, di).page() )

        for i in range(di.nAddressPages):
            w( AddressPage(di).page() )

        # Ensure we start the expense pages on an even page
        if di.evenPage:
            if di.nAddressPages != 0:
                w( AddressPAge(di).page() )
            else:
                w( EmptyPage(di).page() )

        w( TwoExpensePages().page(di) )
        #self.w( FourExpensePages().page(di) )
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

        # Print diary pages until we see the next year
        while 1:
            if di.dt.year == di.year+1:
                break
            w( DiaryPage(di).page() )

        # Finish at the end of a week
        while di.dt.day_of_week != DateTime.Monday:
            w( DiaryPage(di).page() )
        # And get a multiple of whole weeks in the next year
        for i in range(0,di.nWeeksAfter):
            for j in range(0,4):        # 4 pages per week
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

if __name__=='__main__':
    go(sys.argv[0], sys.argv[1:])

# This section is for emacs, God's Own Text Editor.
# Local variables: ***
# mode:python ***
# py-indent-offset:4 ***
# fill-column:95 ***
# End: ***
