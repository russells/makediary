import sys
from mx import DateTime

from DiaryInfo import DiaryInfo
from DSC import preamble, postamble
from PostscriptPage import PostscriptPage


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


class TwoPlannerPages:
    """Print two planner pages for one year."""

    def __init__(self, year, dinfo):
        self.year = year
        self.dinfo = dinfo

    def page(self):
        return PlannerPage(self.year,1,6,self.dinfo,False).page() \
               + PlannerPage(self.year,7,6,self.dinfo,False).page()


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


if __name__ == '__main__':

    from TitledPage import TitledPage

    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    y = DateTime.now().year+1
    print preamble(di)
    print TitledPage(di, sys.argv[0]).page()
    print TwoPlannerPages(y, di).page()
    print FourPlannerPages(y, di).page()
    print TwelvePlannerPages(y, di).page()
    print postamble(di)
