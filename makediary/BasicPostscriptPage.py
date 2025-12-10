#!/usr/bin/env python3
import sys
import re

from makediary.DiaryInfo import DiaryInfo
from makediary.DSC import preamble, postamble


class BasicPostscriptPage(object):
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
                        + "%%%%PageBoundingBox: 0 0 %.0f %.0f\n" % \
                        (self.di.paperWidth * self.di.points_mm,
                         self.di.paperHeight * self.di.points_mm) \
                        + "%%BeginPageSetup\n" \
                        + "SA MM\n"
        if self.di.lineColour:
            self.preamble = self.preamble \
              + "%5.3f %5.3f %5.3f SRC\n" % (self.di.lineColour[0], self.di.lineColour[1], self.di.lineColour[2])
        if self.di.translatePage:
            self.preamble = self.preamble \
                            + "%5.3f %5.3f TR\n" % (self.di.translateXOffset,
                                                    self.di.translateYOffset)
        self.preamble = self.preamble \
                        + "monthCalendars begin\n" \
                        + "%%EndPageSetup\n" \
                        + "%% This is for year beginning %04d-%02d-%02d, " % \
                        (self.di.dtbegin.year, self.di.dtbegin.month, self.di.dtbegin.day)
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
            return self.preamble + self.debugPageBox() + self.body() + self.pageNumber() + self.postamble
        else:
            return self.preamble + self.body() + self.pageNumber() + self.postamble

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
        thickness = max(self.di.underlineThick, self.di.lineThickness)
        s = ""
        s = s + "%5.3f SLW 1 setlinecap %5.3f %5.3f M %5.3f %5.3f L S\n" \
            % (thickness,self.pLeft,self.di.titleLineY,self.pRight,self.di.titleLineY)
        return s

    def bottomline(self):
        s = ""
        s = s + "%5.3f SLW 1 setlinecap %5.3f %5.3f M %5.3f %5.3f L S\n" \
            % (self.di.underlineThick,self.pLeft,self.di.bMargin,self.pRight,self.di.bMargin)
        return s


    def pageNumber(self):
        '''Blank out a section of the page, and put the page number in there.'''
        if self.di.pageNumbers:

            # Finding out the size of a string on the screen is harder than it
            # sounds.  stringwidth gives a width and a zero, because the
            # current point has not moved vertically.  As well as that, the
            # characters are printed with the base at 0, and some of them
            # project below 0.
            #
            # For the same reasons, finding the size of a white box to print
            # behind the number is difficult.  We have to find out the size of
            # a box with spaces at each end, and then guess how far above and
            # below the text to make the y dimension.

            fontsize = self.di.subtitleFontSize * 0.7
            fontsizemultiplier = 1.5
            s = ""
            s += "%% Page number %d\n" % self.di.pageNumber
            s += "5 dict begin\n"
            s += "/%s %5.3f selectfont " % (self.di.subtitleFontName, fontsize)
            s += "/pn (%d) def " % self.di.pageNumber
            # Find out the width of the string, and the string with spaces at each end.
            s += "pn SW pop /w ED ( ) SW pop 2 mul w add /bw ED "
            s += "/h %5.3f def /bh %5.3f def\n" % (fontsize,
                                                   fontsize*fontsizemultiplier)
            if self.di.evenPage:
                # On an even page, the number is on the left, to the right of the outer margin.
                x = self.di.oMargin
            else:
                # On an odd page, the number is on the right, to the left of the outer margin.
                x = self.di.pageWidth - self.di.oMargin
            s += "/y %5.3f def " % (self.di.bMargin/2.0)
            if self.di.evenPage:
                # For even pages, we can print the page number starting at the x,y.
                s += "/x %5.3f def " % x
            else:
                # For odd pages, we need to move the number left.
                s += "/x %5.3f w sub def " % x
            s += "\n"
            s += "/bx bw w sub 2 div x exch sub def\n"
            s += "/by bh h sub 1.4 div y exch sub def\n"
            # Now we have the dictionary with x,y,w,h,bx,by,bh,bw,pn defined.

            s += "1 1 1 SRC bx by bw bh pathLBWH fill\n"
            #s += "0 0 0 SRC bx by bw bh 0 boxLBWH\n"
            s += "0 0 0 SRC x y M pn SH\n"
            s += "end\n"
            return s
        else:
            return ""


    def title(self,text1,text2="",bold=True):
        if bold:
            titleFontName = self.di.titleFontName
            subtitleFontName = self.di.subtitleFontName
        else:
            titleFontName = self.di.titleFontNoBoldName
            subtitleFontName = self.di.subtitleFontNoBoldName
        text1e = self.postscriptEscape(text1)
        s = self.topline()
        s = s + "/%s %5.3f selectfont " % (titleFontName,self.di.titleFontSize)
        if self.di.evenPage:
            s = s + ("%5.3f %5.3f M (%s) SH\n" % (self.pLeft,self.di.titleY,text1e))
        else:
            s = s + ("(%s) dup %5.3f exch SW pop sub %5.3f M SH\n" % \
                     (text1e,self.pRight,self.di.titleY))
        if text2 != "":
            text2e = self.postscriptEscape(text2)
            s = s + "/%s %5.3f selectfont " % (subtitleFontName, self.di.subtitleFontSize)
            if self.di.evenPage:
                s = s + "(%s) dup %5.3f exch SW pop sub %5.3f M SH\n" % \
                    (text2e,self.pRight,self.di.titleY)
            else:
                s = s + "%5.3f %5.3f M (%s) SH\n" % (self.pLeft,self.di.titleY,text2e)
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


if __name__ == '__main__':
    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    bp = BasicPostscriptPage(di)
    print(preamble(di))
    print(bp.page())
    print(postamble(di))

