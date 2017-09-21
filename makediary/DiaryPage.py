import sys
from mx import DateTime

from DiaryInfo import DiaryInfo
from DSC import preamble, postamble
from PostscriptPage import PostscriptPage
from TitledPage import TitledPage
import Moon


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

        isweekend = dd.day_of_week==DateTime.Saturday or dd.day_of_week==DateTime.Sunday

        # Draw the box around the title.  Fill in the box with the appropriate shading, which
        # is determined from the type of day and a user option.
        if self.di.dayTitleShading == "all":
            if isholiday or isweekend:
                gr = self.weekendgray
            else:
                gr = self.otherdaygray
        elif self.di.dayTitleShading == "holidays":
            if isholiday or isweekend:
                gr = self.otherdaygray
            else:
                gr = 0
        elif self.di.dayTitleShading == "none":
            gr = 0
        else:
            print >>sys.stderr, "Unknown day title shading: \"%s\"" % self.di.dayTitleShading
            sys.exit(1)

        if gr:
            s = s + "0 %5.3f %5.3f %5.3f %5.3f %5.3f boxLBWHgray\n" % \
                (self.titleboxy, self.dwidth, self.titleboxsize, di.underlineThick, gr)
        else:
            s = s + "0 %5.3f %5.3f %5.3f %5.3f boxLBWH\n" % \
                (self.titleboxy, self.dwidth, self.titleboxsize, di.underlineThick)

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
        s = s + "%% events for %s\ngsave\n" % str(date)

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
        s = s + "grestore\n"
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
            if self.di.evenPage and i == 5:
                # Draw a box around the current month.  Make the box just inside the area set
                # aside for the month.
                s = s + "%5.3f %5.3f %5.3f %5.3f %5.3f boxLBWH\n" % \
                    (self.pLeft+self.dwidth*5.02/6.0,
                     self.pBottom+self.bottomcalheight*0.02,
                     self.dwidth*0.96/6.0,
                     self.bottomcalheight*0.96,
                     0)
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
        # Make sure the colour is right.
        s = s + "gsave %5.3f %5.3f %5.3f SRC\n" % \
            (self.di.lineColour[0], self.di.lineColour[1], self.di.lineColour[2])
        s = s + "newpath 0.1 SLW /%s %5.3f selectfont " % \
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
        s = s + "grestore\n"

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


if __name__ == '__main__':
    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    print preamble(di)
    print TitledPage(di, sys.argv[0]).page()
    for i in range(4):
        dp = DiaryPage(di)
        print dp.page()
    print postamble(di)
