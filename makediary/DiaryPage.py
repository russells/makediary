#!/usr/bin/env python3
import sys

from makediary.DT             import DT
from makediary.DiaryInfo      import DiaryInfo
from makediary.DSC            import preamble, postamble
from makediary.PostscriptPage import PostscriptPage
from makediary.TitledPage     import TitledPage
from makediary import Moon


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
        elif di.layout == "week-to-page" or di.layout == "week-with-notes":
            self.dheight = self.pHeight_diary/7.0
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
        if di.layout == "week-to-opening" or di.layout == "week-to-page":
            # Smaller boxes when we cram a week into one or two pages
            self.titleboxsize = di.lineSpacing * 1.2
        else:
            self.titleboxsize = di.lineSpacing * 1.4
        self.titleboxy = self.dheight - self.titleboxsize
        self.titlefontsize = self.titleboxsize * 0.63
        self.titlefonty = self.dheight - self.titleboxsize * 0.7
        if self.di.dayTitleBoxes:
            # If we're printing boxes around the title, move the title text in slightly so it's
            # inside the box.
            self.titlefontgap = self.titlefontsize * 0.5
        else:
            # No boxes, so put the title text at the edge.
            self.titlefontgap = 0
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

        s = f"%%--- diary day for {dt.year}-{dt.month:02d}-{dt.day:02d}\n"

        # Find out if this is a holiday.
        dd = DT(dt.year, dt.month, dt.day)
        isholiday = 0
        if dd in self.di.events:
            #sys.stderr.write("%s has events\n" % dd)
            eventlist = self.di.events[dd]
            for event in eventlist:
                if 'holiday' in event:
                    #sys.stderr.write("%s is a holiday: %s\n" % (dd,str(event)))
                    isholiday = 1

        isweekend = dd.day_of_week()==DT.Saturday or dd.day_of_week()==DT.Sunday

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
            print(f'Unknown day title shading: "{self.di.dayTitleShading}"', file=sys.stderr)
            sys.exit(1)

        if self.di.dayTitleBoxes:
            if gr:
                s = s + f"0 {self.titleboxy:5.3f} {self.dwidth:5.3f} {self.titleboxsize:5.3f} {di.underlineThick:5.3f} {gr:5.3f} boxLBWHgray\n"
            else:
                s = s + f"0 {self.titleboxy:5.3f} {self.dwidth:5.3f} {self.titleboxsize:5.3f} {di.underlineThick:5.3f} boxLBWH\n"

        # Print the day name as the diary day header.
        s = s + f"10 10 M /{di.titleFontName} {self.titlefontsize:5.2f} selectfont "
        daynumber = dt.strftime("%d")
        if daynumber[0] == '0':
            daynumber = ' ' + daynumber[1]
        dtext = dt.strftime("%A, " + daynumber + " %B") # %e seems to be undocumented
        if di.evenPage:
            s = s + f"{self.titlefontgap:5.3f} {self.titlefonty:5.3f} M ({dtext}) SH\n"
        else:
            s = s + f"({dtext}) dup {self.dwidth-self.titlefontgap:5.3f} exch SW pop sub {self.titlefonty:5.3f} M SH\n"
        # And draw the julian day as well
        jtext = f"{dt.jday():03d}/{di.currentJDaysLeft:03d}"
        s = s + f"/{di.subtitleFontName} {self.subtitlefontsize:5.3f} selectfont "
        if di.evenPage:
            s = s + f"({jtext}) dup {self.dwidth-self.titlefontgap:5.3f} exch SW pop sub {self.titlefonty:5.3f} M SH\n"
        else:
            s = s + f"{self.titlefontgap:5.3f} {self.titlefonty:5.3f} M ({jtext}) SH\n"

        # Draw all the writing lines, but if the appointments take up the whole width, don't
        # print the writing lines.
        if self.di.appointmentWidth != 100:
            s = s + f"{self.di.lineThickness:5.3f} SLW "
            for lineno in range(self.nlines):
                liney = self.titleboxy-(1+lineno)*di.lineSpacing
                s = s + f"0 {liney:5.3f} M {self.dwidthLines:5.3f} 0 RL S "
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
        s = s + f'/{di.subtitleFontName} {appheight*0.5:5.3f} selectfont\n'
        # Line thicknesses
        leftTh = di.underlineThick * 0.5
        bottomTh = 0
        for lineno in range(len(appTimes)):
            s = s + f"{leftTh:5.3f} SLW {self.appLeft:5.3f} {self.titleboxy-appheight*lineno:5.3f} M 0 {-appheight:5.3f} RL CP S {bottomTh:5.3f} SLW M {self.appWidth:5.3f} 0 RL S "
            if di.appointmentTimes and appTimes[lineno] is not None:
                appx = self.appLeft + appheight*0.2
                appy = self.titleboxy - appheight * (lineno+0.55)
                s = s + f" {appx:5.3f} {appy:5.3f} M ({self.postscriptEscape(appTimes[lineno])}) SH\n"
            else:
                s = s + "\n"
        return s


    def drawEvents(self, startx, starty, yspace):
        di = self.di
        date = di.dt
        #date = (dt.year, dt.month, dt.day)
        if not date in di.events:
            return
        eventlist = di.events[date]
        nevents = len(eventlist)
        textx = startx
        picx = startx
        y = starty
        s = ''
        s = f"%% events for {date}\ngsave\n"

        # First find out whether we are printing any images for this day.  If so, move all the
        # text to the right, out of the way of the images.
        if di.drawEventImages:
            for i in range(nevents):
                event = eventlist[i]
                if 'image' in event \
                        and not ('_warning' in event and event['_warning']):
                    textx = textx + 2.2*yspace
                    break

        for i in range(nevents):
            event = eventlist[i]
            # Print an image, unless this is a warning event.
            if 'image' in event and di.drawEventImages \
                    and not ('_warning' in event and event['_warning']):
                s = s + self.image(event['image'],
                                   picx + 0.1*di.lineSpacing, y - yspace + 0.1*di.lineSpacing,
                                   1.8*yspace, 1.8*yspace)
                imageDrawn = True
            else:
                imageDrawn = False
            if 'small' in event:
                eventFontSize = yspace*0.3
            else:
                eventFontSize = yspace*0.6
            if 'personal' in event:
                s = s + f'/{di.subtitleFontName}-Oblique {eventFontSize:5.3f} selectfont\n'
            else:
                s = s + f'/{di.subtitleFontName} {eventFontSize:5.3f} selectfont\n'

            if 'grey' in event  and  event['grey']:
                s = s + "0.5 setgray "
            else:
                s = s + "0 setgray "
            s = s + f"{textx:5.3f} {y+(yspace*0.25):5.3f} M"
            st = self.postscriptEscape(event['text'])
            s = s + f' ({st}) SH 0 setgray\n'
            if imageDrawn:
                y = y - 2*yspace
            else:
                y = y - yspace
        s = s + "grestore\n"
        return s


    def topHalf(self):
        s = "%--- diary page TOP half\n" \
            + (f"SA {self.pLeft:5.3f} {self.pBottom+(self.pHeight_diary/2):5.3f} TR\n") \
            + self.diaryDay() \
            + "RE\n"
        return s

    def bottomHalf(self):
        s = "%--- diary page BOTTOM half\n" \
            + (f"SA {self.pLeft:5.3f} {self.pBottom:5.3f} TR\n") \
            + self.diaryDay() \
            + "RE\n"
        return s

    def printMondayWTO(self):
        s = '% -- Monday\n' \
            + (f"SA {self.pLeft:5.3f} {self.pBottom+(self.pHeight_diary*0.5):5.3f} TR\n") \
            + self.diaryDay() \
            + "RE\n"
        return s

    def printTuesdayWTO(self):
        s = '% -- Tuesday\n' \
            + (f"SA {self.pLeft:5.3f} {self.pBottom+(self.pHeight_diary*0.25):5.3f} TR\n") \
            + self.diaryDay() \
            + "RE\n"
        return s

    def printWednesdayWTO(self):
        s = '% -- Wednesday\n' \
            + (f"SA {self.pLeft:5.3f} {self.pBottom:5.3f} TR\n") \
            + self.diaryDay() \
            + "RE\n"
        return s

    def printThursdayWTO(self):
        s = '% -- Thursday\n' \
            + (f"SA {self.pLeft:5.3f} {self.pBottom+(self.pHeight_diary*0.75):5.3f} TR\n") \
            + self.diaryDay() \
            + "RE\n"
        return s

    def printFridayWTO(self):
        s = '% -- Friday\n' \
            + (f"SA {self.pLeft:5.3f} {self.pBottom+(self.pHeight_diary*0.5):5.3f} TR\n") \
            + self.diaryDay() \
            + "RE\n"
        return s

    def printSaturdayWTO(self):
        s = '% -- Saturday\n' \
            + (f"SA {self.pLeft:5.3f} {self.pBottom+(self.pHeight_diary*0.25):5.3f} TR\n") \
            + self.diaryDay() \
            + "RE\n"
        return s

    def printSundayWTO(self):
        s = '% -- Sunday\n' \
            + (f"SA {self.pLeft:5.3f} {self.pBottom:5.3f} TR\n") \
            + self.diaryDay() \
            + "RE\n"
        return s


    def printMondayWTP(self):
        s = '% -- Monday (WTP\n' \
            + (f"SA {self.pLeft:5.3f} {self.pBottom+(self.pHeight_diary*6.0/7.0):5.3f} TR\n") \
            + self.diaryDay() \
            + "RE\n"
        return s

    def printTuesdayWTP(self):
        s = '% -- Tuesday (WTP\n' \
            + (f"SA {self.pLeft:5.3f} {self.pBottom+(self.pHeight_diary*5.0/7.0):5.3f} TR\n") \
            + self.diaryDay() \
            + "RE\n"
        return s

    def printWednesdayWTP(self):
        s = '% -- Wednesday (WTP\n' \
            + (f"SA {self.pLeft:5.3f} {self.pBottom+(self.pHeight_diary*4.0/7.0):5.3f} TR\n") \
            + self.diaryDay() \
            + "RE\n"
        return s

    def printThursdayWTP(self):
        s = '% -- Thursday (WTP\n' \
            + (f"SA {self.pLeft:5.3f} {self.pBottom+(self.pHeight_diary*3.0/7.0):5.3f} TR\n") \
            + self.diaryDay() \
            + "RE\n"
        return s

    def printFridayWTP(self):
        s = '% -- Friday (WTP\n' \
            + (f"SA {self.pLeft:5.3f} {self.pBottom+(self.pHeight_diary*2.0/7.0):5.3f} TR\n") \
            + self.diaryDay() \
            + "RE\n"
        return s

    def printSaturdayWTP(self):
        s = '% -- Saturday (WTP\n' \
            + (f"SA {self.pLeft:5.3f} {self.pBottom+(self.pHeight_diary*1.0/7.0):5.3f} TR\n") \
            + self.diaryDay() \
            + "RE\n"
        return s

    def printSundayWTP(self):
        s = '% -- Sunday (WTP\n' \
            + (f"SA {self.pLeft:5.3f} {self.pBottom:5.3f} TR\n") \
            + self.diaryDay() \
            + "RE\n"
        return s


    def largeDayOnPage(self):
        s = "% -- Day\n" \
            + (f"SA {self.pLeft:5.3f} {self.pBottom+self.bottomcalheight:5.3f} TR\n") \
            + self.diaryDay() \
            + "RE\n"
        return s

    def workLayoutTopDay(self):
        s = "% -- top day\n"\
            + (f"SA {self.pLeft:5.3f} {self.pBottom+self.bottomcalheight+self.dheight:5.3f} TR\n") \
            + self.diaryDay() \
            + "RE\n"
        return s

    def workLayoutBottomDay(self):
        s = "% -- bottom day\n"\
            + (f"SA {self.pLeft:5.3f} {self.pBottom+self.bottomcalheight:5.3f} TR\n") \
            + self.diaryDay() \
            + "RE\n"
        return s

    def workLayoutSaturday(self):
        s = "% -- Saturday on a work layout\n" \
            + (f"SA {self.pLeft:5.3f} {self.pBottom + self.bottomcalheight + self.weekendDheight:5.3f} TR\n") \
            + self.diaryDay(self.weekendDheight) \
            + "RE\n"
        return s

    def workLayoutSunday(self):
        s = "% -- Sunday on a work layout\n" \
            + (f"SA {self.pLeft:5.3f} {self.pBottom + self.bottomcalheight:5.3f} TR\n") \
            + self.diaryDay(self.weekendDheight) \
            + "RE\n"
        return s

    def titleAndThreeMonthsAtTop(self):
        """Print three calendars on the top half of a page."""
        di = self.di
        s = "%--- three month calendars\n"
        # Page title.
        s = s + self.title(di.dt.strftime("%B %Y"),
                           "Week %d" % di.dt.isocalendar()[1])
        # Calculate the area we have for drawing.
        if di.layout == "week-to-opening" or di.layout == "day-to-page":
            b = di.bMargin + self.pHeight_diary*0.75
        else:
            b = di.bMargin + self.pHeight_diary*0.5
        l = self.pLeft
        w = self.pWidth
        h = self.pTop - b
        # Draw a really obvious box to see if the drawing space is correct.
        #s = s + f"SA 4 SLW 2 setlinecap {l:5.3f} {b:5.3f} TR\n" \
        #      + f"2 2 M 0 {h-4:5.3f} RL {w-4:5.3f} 0 RL 0 {-(h-4):5.3f} RL {-(w-4):5.3f} 0 RL S RE\n"
        s = s + f"SA {l:5.3f} {b:5.3f} TR\n"
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
        s = s + f"%% c_bottom={c_bottom:5.3f} c_height={c_height:5.3f} c_width={c_width:5.3f} c_totalwidth={c_totalwidth:5.3f} c_gutter={c_gutter:5.3f}\n"
        for i in (-1,0,1):
            c_d = self.getOffsetMonth(self.di.dt, i)
            c_left = c_indent + (i+1)*(c_width+c_gutter)
            s = s +f"{c_left:5.3f} {c_bottom:5.3f} M SA {c_width:5.3f} {c_height:5.3f} SC " \
                + self.di.getMonthCalendarPsFnCall(c_d.year, c_d.month) \
                + " RE\n"
            # Draw a box around the current month
            if i == 0:
                s = s + f"{self.di.lineThickness:5.3f} SLW " \
                    + f"{c_left-c_boxborder:5.3f} {c_bottom-c_boxborder:5.3f} M " \
                    + f"0 {c_height+2*c_boxborder:5.3f} RL {c_width+2*c_boxborder:5.3f} 0 RL " \
                    + f"0 {-(c_height+2*c_boxborder):5.3f} RL {-(c_width+2*c_boxborder):5.3f} 0 RL S\n"
        # Now draw the lines just below the month calendars.
        l_y = c_bottom - di.lineSpacing - 1.3
        s = s + f"{self.di.lineThickness:5.3f} SLW\n"
        while l_y > (di.lineSpacing * 0.3):
            s = s + f"{c_indent:5.3f} {l_y:5.3f} M {c_totalwidth:5.2f} 0 RL S\n"
            l_y = l_y - di.lineSpacing

        s = s + "RE\n"
        return s


    def getOffsetMonth(self, dt, offset):
        '''Return a DT object corresponding to some time in the month indicated by the
        integer offset from the current month.'''

        if offset==0:
            return dt
        else:
            # Base this from the middle of the month, so we don't get strange month skip
            # effects when the current day is near the beginning or end of the month.
            return DT(dt.year, dt.month, 15) + 30.5 * DT.delta(1) * offset


    def sixMonthsAtBottom(self):
        '''Print six months at the bottom of the page, five months before the current month,
        and the current month, on the left (even) pages, and six months after the current month
        on the right (odd) pages.'''

        # If we start on the 15th day of the relevant month, we can add or subtract 30 days
        # several times without worrying about crossing a month boundary when we don't want to.
        date = DT( self.di.openingCalendarsCurrentDate.year,
                   self.di.openingCalendarsCurrentDate.month,
                   15)
        if self.di.evenPage:
            date -= DT.delta(1) * 30 * 5
        else:
            date += DT.delta(1) * 30
        s = f"%% -- Bottom calendars, starting at {date.strftime('%Y %m')}\n"

        # Proportion of the month box to fill.
        monthprop = 0.90

        for i in range(0,6):
            s = s + f"{self.pLeft+(self.dwidth/6.0)*(i+((1.0-monthprop)/2.0)):5.3f} {self.pBottom + self.bottomcalheight*(1.0-monthprop)/2.0:5.3f} M SA {self.dwidth/6.0*monthprop:5.3f} {self.bottomcalheight*monthprop:5.3f} SC {self.di.getMonthCalendarPsFnCall(date.year, date.month)} RE\n"
            if self.di.evenPage and i == 5:
                # Draw a box around the current month.  Make the box just inside the area set
                # aside for the month.
                s = s + f"{self.pLeft+self.dwidth*5.02/6.0:5.3f} {self.pBottom+self.bottomcalheight*0.02:5.3f} {self.dwidth*0.96/6.0:5.3f} {self.bottomcalheight*0.96:5.3f} {0} boxLBWH\n"
            date += DT.delta(1) * 30
        return s


    def drawMoon(self, x, y, size):

        """Draw a moon at (x,y), with the given size."""

        di = self.di
        if not di.moon:
            return ""

        # Calculate the current phase, and the previous and next day's phases
        dt = di.dt
        dty = di.dt - DT.delta(1)
        dtt = di.dt + DT.delta(1)
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
        s = f"%% Moon for {dt.year}-{dt.month}-{dt.day}\n"
        # Make sure the colour is right.
        s = s + f"gsave {self.di.lineColour[0]:5.3f} {self.di.lineColour[1]:5.3f} {self.di.lineColour[2]:5.3f} SRC\n"
        s = s + f"newpath 0.1 SLW /{di.subtitleFontName} {fontsize:5.3f} selectfont "
        s = s + f"{x:5.3f} {y:5.3f} {radius:5.3f} 0 360 arc S %% circle\n"

        # In the southern hemisphere, a first quarter moon is light on the left, and a third
        # quarter moon is light on the right.

        if quarter == self.mooncalc.MOON_NM:
            s = s + f"{x:5.3f} {y:5.3f} {radius:5.3f} 0 360 arc fill %% new moon\n" \
                + f"{linex:5.3f} {line1y:5.3f} M (New) SH {linex:5.3f} {line2y:5.3f} M (Moon) SH\n"
        elif quarter == self.mooncalc.MOON_1Q:
            if self.di.northernHemisphereMoon:
                s = s + self.drawMoonRightWhite(x, y, radius, size)
            else:
                s = s + self.drawMoonLeftWhite(x, y, radius, size)
            s = s + f"{linex:5.3f} {line1y:5.3f} M (First) SH {linex:5.3f} {line2y:5.3f} M (Quarter) SH\n"
        elif quarter == self.mooncalc.MOON_FM:
            s = s + f"{linex:5.3f} {line1y:5.3f} M (Full) SH {linex:5.3f} {line2y:5.3f} M (Moon) SH\n"
        elif quarter == self.mooncalc.MOON_3Q:
            if self.di.northernHemisphereMoon:
                s = s + self.drawMoonLeftWhite(x, y, radius, size)
            else:
                s = s + self.drawMoonRightWhite(x, y, radius, size)
            s = s + f"{linex:5.3f} {line1y:5.3f} M (Third) SH {linex:5.3f} {line2y:5.3f} M (Quarter) SH\n"
        s = s + "grestore\n"

        return s

    def drawMoonLeftWhite(self, x, y, radius, size):
        s = f"{x:5.3f} {y:5.3f} {radius:5.3f} 270 90 arc 0 {-size:5.3f} RL fill %% white left, "
        if self.di.northernHemisphereMoon:
            s = s + "third quarter in northern hemisphere\n"
        else:
            s = s + "first quarter in southern hemisphere\n"
        return s

    def drawMoonRightWhite(self, x, y, radius, size):
        s = f"{x:5.3f} {y:5.3f} {radius:5.3f} 90 270 arc 0 {size:5.3f} RL fill %% white right, "
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
            if self.di.dt.day_of_week() == DT.Saturday:
                s += self.workLayoutSaturday() + self.workLayoutSunday()
            else:
                s += self.workLayoutBottomDay()
        elif self.di.dt.day_of_week() == DT.Monday:
            if self.di.layout == "week-to-opening":
                s = self.titleAndThreeMonthsAtTop() +  \
                    self.printMondayWTO() + \
                    self.printTuesdayWTO() + \
                    self.printWednesdayWTO()
            elif self.di.layout == "week-to-page" or self.di.layout == "week-with-notes":
                s = self.printMondayWTP() + \
                    self.printTuesdayWTP() + \
                    self.printWednesdayWTP() + \
                    self.printThursdayWTP() + \
                    self.printFridayWTP() + \
                    self.printSaturdayWTP() + \
                    self.printSundayWTP()
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
    print(preamble(di))
    print(TitledPage(di, sys.argv[0]).page())
    for i in range(4):
        dp = DiaryPage(di)
        print(dp.page())
    print(postamble(di))
