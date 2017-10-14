import sys
import re

from DiaryInfo import DiaryInfo
from DSC import preamble, postamble


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
    print preamble(di)
    print bp.page()
    print postamble(di)

