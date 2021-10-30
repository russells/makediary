#!/usr/bin/env python3
import sys

from makediary.DiaryInfo      import DiaryInfo
from makediary.DSC            import preamble, postamble
from makediary.PostscriptPage import PostscriptPage


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
        align = 'centre'

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

        if self.di.layout=="logbook":
            # Spaces at the start of these lines move all the lines to the right, and serve to
            # set the font size from the longest string.  Spaces at the end move the lines off
            # the right margin.
            title = \
                  '             Start date: 20___ /__ /__      \n' + \
                  '\n' + \
                  '     End date: 20___ /__ /__      '
            align = 'right'
        elif self.di.title is not None:
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
            if align=='centre':
                s = s + "(%s) dup textxcentre exch SW pop 2 div sub textycentre M SH\n" % \
                    self.postscriptEscape(ts)
            elif align=='right':
                s = s + "(%s) dup %5.3f exch SW pop sub textycentre M SH\n" % \
                    (self.postscriptEscape(ts), xright)
            s = s + "/textycentre textycentre textheight 1.1 mul sub def\n"

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


if __name__ == '__main__':
    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    cp = CoverPage(di)
    print(preamble(di))
    print(cp.page())
    print(postamble(di))
