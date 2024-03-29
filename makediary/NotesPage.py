#!/usr/bin/env python3
import sys

from makediary.DiaryInfo      import DiaryInfo
from makediary.DSC            import preamble, postamble
from makediary.PostscriptPage import PostscriptPage


class NotesPage(PostscriptPage):

    def __init__(self, dinfo, notesTitle="Notes"):
        self.notesTitle = notesTitle
        PostscriptPage.__init__(self, dinfo)


    def body(self):

        s = "%--- Notes Page\n" + self.title(self.notesTitle) + self.bottomline()
        s = s + "SA %5.3f %5.3f TR %5.3f SLW\n" % \
            (self.pLeft,self.pBottom,self.di.lineThickness)

        if self.di.griddedNotesPages:
            s = s + self.grid()
        else:
            s = s + self.lines()

        s = s + "RE\n"
        return s


    def lines(self):
        s = ''
        nlines = int(self.pHeight / self.di.lineSpacing)
        # Recalculate line spacing to avoid dangling bottom lines.
        linespacing = float(self.pHeight) / float(nlines)
        for n in range(0,nlines):
            s = s + "%5.3f SLW " % self.di.lineThickness
            s = s + "0 %5.3f M %5.3f 0 RL S\n" % (self.pHeight-linespacing*(n+1),
                                                  self.pWidth)
        return s


    def grid(self):
        s = ''
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
        for n in list(range(1,sbox)) + \
                 list(range(sbox+1,vnlines-sbox)) + \
                 list(range(vnlines-sbox+1,vnlines)):
            s = s + "%5.3f 0 M 0 %5.3f RL S\n" % (self.pWidth - vlinespacing*n,
                                                  self.pHeight - 2 * hlinespacing)
        # Print the vertical lines that do go to the top of the page.
        s = s + "% longer vertical lines\n"
        for n in (0,sbox,vnlines-sbox,vnlines):
            s = s + "%5.3f 0 M 0 %5.3f RL S\n" % (self.pWidth - vlinespacing*n,
                                                  self.pHeight)
        return s



if __name__ == '__main__':
    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    np = NotesPage(di)
    print(preamble(di))
    print(np.page())
    print(postamble(di))
