import sys

from makediary.DT             import DT
from makediary.DiaryInfo      import DiaryInfo
from makediary.DSC            import preamble, postamble
from makediary.PostscriptPage import PostscriptPage
from makediary.TitledPage     import TitledPage


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
        monthname = DT(self.di.dtbegin.year,month,1).strftime("%B")
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
            (self.monthheight,self.titleheight,
             max(self.di.underlineThick,self.di.lineThickness),self.di.titleGray)
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
            (blockwidth, self.monthheight, max(self.di.underlineThick,self.di.lineThickness))
        s = s + "% columns \n"
        s = s + "%5.3f SLW %5.3f 0 M 0 %5.3f RL S %5.3f 0 M 0 %5.3f RL S 0 SLW\n" % \
            (self.di.lineThickness,
             self.column1x,self.monthheight,self.column2x,self.monthheight)
        nlines = 1 + int(self.monthheight / self.di.lineSpacing)
        linespacing = self.monthheight / float(nlines)
        s = s + "%5.3f SLW " % self.di.lineThickness
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


class FourExpensePages:
    def page(self,dinfo):
        s = ""
        s = s + ExpensePage(1,3,dinfo).page() \
            + ExpensePage(4,3,dinfo).page() \
            + ExpensePage(7,3,dinfo).page() \
            + ExpensePage(10,3,dinfo).page()
        return s


class TwoExpensePages:
    def page(self,dinfo):
        s = ""
        s = s + ExpensePage(1,6,dinfo).page() \
            + ExpensePage(7,6,dinfo).page()
        return s


if __name__ == '__main__':
    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    print(preamble(di))
    print(TitledPage(di, sys.argv[0]).page())
    print(TwoExpensePages().page(di))
    print(FourExpensePages().page(di))
    print(postamble(di))
