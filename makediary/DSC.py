import sys
from mx import DateTime

from DiaryInfo import DiaryInfo
from versionNumber import versionNumber


def preamble(di):
    """Return the document header as a string."""
    p =   "%!PS-Adobe-2.0\n" \
        + ("%% -- printed by %s %s, %s\n" % (di.myname, di.opts,
                                             DateTime.now().strftime("%Y-%m-%dT%H%M%S%Z")))
    p = p + "%%%%Creator: %s, by Russell Steicke, version: %s\n" % \
        (di.myname,versionNumber) \
        + DateTime.now().strftime("%%%%CreationDate: %a, %d %b %Y %H:%M:%S %z\n") \
        + "%%%%BoundingBox: 0 0 %.0f %.0f\n" % \
        (di.paperWidth * di.points_mm, di.paperHeight * di.points_mm)
    p = p + "%%DocumentNeededResources: font Times-Roman\n" \
        "%%+ font Times-Bold\n" \
        "%%+ font Helvetica\n" \
        "%%+ font Helvetica-Oblique\n" \
        "%%+ font Courier\n" \
        "%%+ font Courier-Bold\n" \
        "%%Pages: (atend)\n" \
        "%%PageOrder: Ascend\n" \
        "%%Orientation: Portrait\n" \
        "%%EndComments\n" \
        "%%BeginProlog\n" \
        "%%BeginResource: MakediaryProcs\n" \
        "/CP {currentpoint} bind def " \
        "/M {moveto} bind def /RM {rmoveto} bind def " \
        "/L {lineto} bind def /RL {rlineto} bind def\n" \
        "/S {stroke} bind def /SH {show} bind def " \
        "/SP {showpage} bind def /SLW {setlinewidth} bind def\n" \
        "/SA {save} bind def /RE {restore} bind def " \
        "/TR {translate} bind def\n" \
        "/SW {stringwidth} bind def /SC {scale} bind def\n" \
        "/SWP2D {SW pop 2 div} bind def\n" \
        "/D {def} bind def /ED {exch def} bind def\n" \
        + "/MM {%8.6f %8.6f SC} bind def\n" % (di.points_mm,di.points_mm) \
        + "matrix currentmatrix 0 get /originalXscale ED " \
        "matrix currentmatrix 3 get /originalYscale ED\n"


    # Code for printing boxes around things.  The linewidth must be set before using either
    # of these.

    p = p + "% construct a path given <left bottom width height>\n" \
        "/pathLBWH { 4 dict begin /h ED /w ED /b ED /l ED\n" \
        "l b M w 0 RL 0 h RL w neg 0 RL 0 h neg RL end} def\n" \
        "% construct a path given <left bottom right top>\n" \
        "/pathLBRT { 4 dict begin /t ED /r ED /b ED /l ED\n" \
        "l b M r b L r t L l t L l b L end} def\n"

    p = p + "% print a box given <left bottom width height linethickness>\n" \
        "/boxLBWH { gsave SLW pathLBWH S grestore } def\n" \
        "% print a box given <left bottom right top linethickness>\n" \
        "/boxLBRT { gsave SLW pathLBRT S grestore } def\n"

    # Print a box with the current line width (in the current gray level), and fill it with
    # the specfied gray.

    p = p + "% print a box and fill it <l b w h linethick gray\n" \
        "/boxLBWHgray { gsave 2 dict begin /g ED /th ED 4 copy " \
        "pathLBWH currentgray g setgray fill setgray th boxLBWH end grestore } def\n" \
        "% print a box and fill it <l b r t linewidth gray\n" \
        "/boxLBRTgray { gsave 2 dict begin /g ED /th ED 4 copy " \
        "pathLBRT currentgray g setgray fill setgray th boxLBRT end grestore } def\n"

    # Code for printing dashed debugging boxes around things.  These defs need the dash
    # length supplied so that we can manually compensate for different scales.

    p = p + "% print a debug box given <left bottom right top dashlen>\n" \
        "/debugboxLBRTD {gsave 6 dict begin /len ED /t ED /r ED /b ED /l ED\n" \
        "[ len ] 0 setdash 0 SLW " \
        "l b M l t L S l t M r t L S r t M r b L S r b M l b L S\n" \
        "end grestore} def\n" \
        "% print a debug box given <left bottom width height dashlen>\n" \
        "/debugboxLBWHD {6 dict begin /len ED /h ED /w ED /b ED /l ED\n" \
        "l b l w add b h add len debugboxLBRTD end} def\n"

    # Additional defs for debug box printing.  These defs calculate the dash length from
    # the current transformation matrix.  This works, except that ghostscript changes the
    # current matrix depending on the zoom level, so the dash length changes when we zoom.
    # But at least we get the same dash length on everything, regardless of the scale in
    # use at that point.  The number just before "matrix currentmatrix" should the the
    # length of the dashes in postscript points.  There is also a test against divide by
    # zero in here.  It is possible to get a 0 in currentmatrix[0] or currentmatrix[3],
    # which will stop the job with an error on some printers.

    p = p + "% print a debug box given <left bottom right top>, guess the dash length\n" \
        "/debugboxLBRT {gsave 6 dict begin /t ED /r ED /b ED /l ED\n" \
        "10.0 matrix currentmatrix 0 get dup 0 eq { pop pop 5.0 } { div abs } ifelse /xl ED " \
        "10.0 matrix currentmatrix 3 get dup 0 eq { pop pop 5.0 } { div abs } ifelse /yl ED\n" \
        "[ xl ] 0 setdash l b M r b L S l t M r t L S\n" \
        "[ yl ] 0 setdash l b M l t L S r b M r t L S\n" \
        "end grestore} def\n" \
        "% print a debug box given <left bottom width height>, guess the dash length\n" \
        "/debugboxLBWH {6 dict begin /h ED /w ED /b ED /l ED\n" \
        "l b l w add b h add debugboxLBRT end} def\n"

    # This line is used in the middle of /debugboxLBRT to show the scale
        #+ "/Courier xl selectfont l b M xl 10 string cvs SH (  ) SH yl 10 string cvs SH\n" \

    # Debian GNU/Linux seems to have a problem here.  ghostview ignores the -media command
    # line option, and always sets the sizes in currentpagedevice to what is specified by
    # /etc/papersize.  The -media size is used to set the "paper" size of the ghostscript
    # window.

    p = p + "% --- code to find out the page size.\n" \
        "/pageIsA4 { currentpagedevice begin " \
        "  PageSize 0 get 595 sub abs 10 lt PageSize 1 get 842 sub abs 10 lt " \
        "  and end } bind def\n" \
        "/pageIsA5 { currentpagedevice begin " \
        "  PageSize 0 get 421 sub abs 10 lt PageSize 1 get 595 sub abs 10 lt " \
        "  and end } bind def\n" \
        "/pageIsLetter { currentpagedevice begin " \
        "  PageSize 0 get 612 sub abs 10 lt PageSize 1 get 792 sub abs 10 lt " \
        "  and end } bind def\n" \
        "% concatstr(ings) copied from http://en.wikibooks.org/wiki/PostScript_FAQ\n" \
        "/concatstr % (a) (b) -> (ab)\n" \
        "{ exch dup length\n" \
        "  2 index length add string\n" \
        "  dup dup 4 2 roll copy length\n" \
        "  4 -1 roll putinterval\n" \
        "} bind def\n" \
        + monthCalendars(di) \
        + "%%EndResource\n" \
        + "%%EndProlog\n"

    p = p + "%%BeginSetup\n" \
        "%%IncludeResource: font Times-Roman\n" \
        "%%IncludeResource: font Times-Bold\n" \
        "%%IncludeResource: font Helvetica\n" \
        "%%IncludeResource: font Helvetica-Oblique\n" \
        "%%IncludeResource: font Courier\n" \
        "%%IncludeResource: font Courier-Bold\n" \
        "%%IncludeResource: procset MakediaryProcs\n" \
        + "%%%%IncludeFeature: *PageSize %s\n" % di.paperSize.title() \
        + "%%EndSetup\n"
    return p


def postamble(di):
    """Return the document trailer as a string."""
    p =   di.sectionSep \
        + "%%Trailer\n" \
        + ("%%%%Pages: %d\n" % di.pageNumber) \
        + "%%EOF\n"
    return p


def monthCalendars(di):
    """ Print code that defines a postscript name for printing a calendar for the months of
    last year, this year and next year.  We will end up with a dictionary called
    'monthCalendars' that contains entries such as 'M_2000_12', 'M_2001_01' etc.  Calling
    those names will print the corresponding calendar with its bottom left corner at
    currentpoint.  The calendar will be 1 unit high and 1 unit wide.  Change the size of
    these calendars by calling scale before calling the calendar procedure"""

    p = di.sectionSep
    y = di.dtbegin.year
    a7 = 142.86                     # 1000/7
    a8 = 125.0                      # 1000/8
    p = p + "/monthCalendars 100 dict dup begin\n"
    # This list of years contains one instance of each of the 14 possible calendars.
    yearslist = [2000,2001,2002,2003,2004,2005,2006,2008,2009,2010,2012,2016,2020,2024]

    # Create 168 (14*12) month calendars, named M_mMM_bB_eE, where MM is a month number, B
    # is the day of week of 1jan, and E is day of week of 31dec (day of week is 0 to 6).
    # Callers need to call di.getMonthCalendarPsFnCall(y,m[,addyear=True]) when
    # printing a calendar.
    for year in yearslist:

        day_b = DateTime.DateTime(year,  1,  1).day_of_week
        day_e = DateTime.DateTime(year, 12, 31).day_of_week

        for month in range(1,13):
            mtime = DateTime.DateTime(year,month)
            # Work in a 1000-scaled world to make the numbers a bit easier.
            # "0 25 TR" here is to move things up very slightly, so that the
            # bottom line is not right on the bottom.  "25" should be calculated,
            # but at the moment it is measured and a static quantity.
            p = p + mtime.strftime("%%%%----\n/M_m%%02m_b%d_e%d{" % (day_b, day_e)) \
                + " 5 dict begin /TT exch def\n" \
                + " SA CP TR 0.001 0.001 scale 0 25 TR\n" \
                + "/Helvetica-Bold findfont [80 0 0 100 0 0] makefont setfont\n"
            ts = mtime.strftime("%B")
            #p = p + "(%s) SWP2D 500 exch sub %d M " % (ts,a8*7) # Centred titles
            p = p + "%5.3f %5.3f M " % (20,a8*7) # Left titles
            p = p + "(%s) TT length 0 ne { (  ) concatstr TT concatstr} if SH\n" % (ts,)
            p = p + "/Helvetica findfont [80 0 0 100 0 0] makefont setfont " \
                + "%5.3f (M) SWP2D sub %5.3f M (M) SH\n" % (a7*0.5,a8*6.0) \
                + "%5.3f (T) SWP2D sub %5.3f M (T) SH\n" % (a7*1.5,a8*6.0) \
                + "%5.3f (W) SWP2D sub %5.3f M (W) SH\n" % (a7*2.5,a8*6.0) \
                + "%5.3f (T) SWP2D sub %5.3f M (T) SH\n" % (a7*3.5,a8*6.0) \
                + "%5.3f (F) SWP2D sub %5.3f M (F) SH\n" % (a7*4.5,a8*6.0) \
                + "%5.3f (S) SWP2D sub %5.3f M (S) SH\n" % (a7*5.5,a8*6.0) \
                + "%5.3f (S) SWP2D sub %5.3f M (S) SH\n" % (a7*6.5,a8*6.0)
            thisweek = 0            # Used to calculate what line to print the week on
            ndays = mtime.days_in_month
            for day in range(1,ndays+1):
                wday = DateTime.DateTime(year,month,day).day_of_week
                p = p + "(%d) dup SWP2D %3.2f exch sub %5.3f M SH\n" \
                    % (day, wday*a7+a7/2, (5-thisweek)*a8 )
                if wday==DateTime.Sunday:
                    thisweek = thisweek + 1
            p = p + "0 -25 TR "
            # Now draw a box around the month, just for boundary checking
            if di.debugBoxes:
                #p = p + "0 SLW 0 0 999 999 50 debugboxLBRTD "
                p = p + "0 SLW 0 0 999 999 debugboxLBRT "
            # End of the month definition
            p = p + "RE end } def\n"
    p = p + "end def\n"
    return p


if __name__ == '__main__':
    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    print preamble(di)
    print postamble(di)
