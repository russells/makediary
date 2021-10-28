import sys

from makediary.DiaryInfo      import DiaryInfo
from makediary.DSC            import preamble, postamble
from makediary.PostscriptPage import PostscriptPage


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
             + ("%5.3f %5.3f L " % (bleft,bbottom))
        if self.di.shading:
            sh = "gsave %5.3f setgray fill grestore S\n" % ((1.0+self.di.titleGray)/2.0,)
        else:
            sh = "\n"
        s = s + bs + sh
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
            bs = \
                "%5.3f %5.3f %5.3f %5.3f %5.3f boxLBRTgraynoborder " % \
                (bleft,bbottom,bright,btop,self.di.titleGray) \
                + "%5.3f SLW " % self.di.underlineThick \
                + "%5.3f %5.3f M %5.3f %5.3f L " % (bright,bbottom,bleft,bbottom) \
                + "%5.3f %5.3f L %5.3f %5.3f L S\n" % (bleft,btop,bright,btop)
        else:
            bs = \
                "%5.3f %5.3f %5.3f %5.3f %5.3f boxLBRTgraynoborder " % \
                (bleft,bbottom,bright,btop,self.di.titleGray) \
                + "%5.3f SLW " % self.di.underlineThick \
                + "%5.3f %5.3f M %5.3f %5.3f L " % (bleft,bbottom,bright,bbottom) \
                + "%5.3f %5.3f L %5.3f %5.3f L S\n" % (bright,btop,bleft,btop)
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


class TwoCalendarPages:

    def __init__(self,dinfo):
        self.dinfo = dinfo

    def page(self):
        s = ''
        s = s + HalfCalendarPage(self.dinfo).page()
        s = s + HalfCalendarPage(self.dinfo).page()
        return s



if __name__ == '__main__':

    from TitledPage import TitledPage

    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    tcp = TwoCalendarPages(di)
    print(preamble(di))
    print(TitledPage(di, sys.argv[0]).page())
    print(tcp.page())
    print(postamble(di))
