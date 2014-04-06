import sys
from mx import DateTime

from DiaryInfo import DiaryInfo
from DSC import preamble, postamble
from PostscriptPage import PostscriptPage


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



if __name__ == '__main__':

    from TitledPage import TitledPage

    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    pps = PerpetualCalendarPages(di)
    print preamble(di)
    print TitledPage(di, sys.argv[0]).page()
    print pps.page()
    print postamble(di)
