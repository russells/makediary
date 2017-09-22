#!/usr/bin/python

# vim: set shiftwidth=4 expandtab smartindent textwidth=95:

# Print a year diary.

from versionNumber import versionNumber

import sys
import Moon
from DiaryInfo import DiaryInfo
from mx import DateTime
from errno import EPIPE

import DSC
from BasicPostscriptPage     import BasicPostscriptPage
from PostscriptPage          import PostscriptPage
from EmptyPage               import EmptyPage
from CoverPage               import CoverPage
from VersionPage             import VersionPage
from PersonalInformationPage import PersonalInformationPage
from ImageFilePages          import ImageFilePage, TwoImageFilePages
from EPSFilePages            import EPSFilePage, TwoEPSFilePages
from CalendarPages           import TwoCalendarPages
from ManPagePages            import ManPagePages
from PerpetualCalendarPages  import PerpetualCalendarPages
from PlannerPages            import TwoPlannerPages, FourPlannerPages, TwelvePlannerPages
from AddressPage             import AddressPage
from NotesPage               import NotesPage
from ExpensePages            import TwoExpensePages, FourExpensePages
from DiaryPage               import DiaryPage
from LogbookPage             import LogbookPage


# ############################################################################################

class Diary:

    def __init__(self,diaryinfo):
        self.di = diaryinfo
        self.out = self.di.out

    def w(self,s):
        self.out.write(s)

    # print the whole diary
    def diary(self):
        di = self.di
        w = self.w
        w( DSC.preamble(self.di) )
        w( CoverPage(di).page() )
        #self.w( CalendarPage(di).page() )
        if di.debugVersion:
            w( VersionPage(di).page() )
        else:
            w( EmptyPage(di).page() )
        w( PersonalInformationPage(di).page() )

        # Print image pages, if there are any, and end on a new opening.
        for imagePage in di.imagePages:
            npages = imagePage["pages"]
            if npages == 1:
                w( ImageFilePage(di, imagePage["fileName"], imagePage["title"] ).page() )
            elif npages == 2:
                if di.evenPage:
                    self.w( NotesPage(di).page() )
                w( TwoImageFilePages(di, imagePage["fileName"], imagePage["title"],
                                     imagePage["coverage"]).page() )
            else:
                print >>sys.stderr, "makediary: internal error:"
                print >>sys.stderr, "-- image file (%s): imagePage['pages'] == %d" \
                      % (imagePage['fileName'], npages)
                sys.exit(1)
        if di.evenPage:
            self.w( EmptyPage(di).page() )

        if di.calendarPages:
            w( TwoCalendarPages(di).page() )

        if di.perpetualCalendars:
            self.w( PerpetualCalendarPages(di).page() )

        # Ensure that the planner pages are on facing pages.
        if di.nPlannerYears > 0:
            if di.evenPage:
                self.w( EmptyPage(di).page() )
            # Decide whether to put short events on the planner pages.  If we are not using
            # pcal to generate the events, then yes.  If we are using pcal, only put short
            # events on if we have been told.
            doEventsOnPlanner = (not di.pcal or (di.pcal and di.pcalPlanner))
            if di.largePlanner:
                w( TwelvePlannerPages(di.dtbegin.year, di, doEventsOnPlanner).page() )
            else:
                w( FourPlannerPages(di.dtbegin.year, di, doEventsOnPlanner).page() )
            if di.dtbegin.month==1 and di.dtbegin.day==1:
                for i in range(1, di.nPlannerYears):
                    w( TwoPlannerPages(di.dtbegin.year+i, di).page() )
            else:
                w( FourPlannerPages(di.dtbegin.year+1, di).page() )
                for i in range(2, di.nPlannerYears):
                    w( TwoPlannerPages(di.dtbegin.year+i, di).page() )


        for i in range(di.nAddressPages):
            w( AddressPage(di).page() )

        # Ensure we start the expense pages on an even page
        if di.evenPage:
            if di.nAddressPages != 0:
                w( AddressPage(di).page() )
            else:
                w( EmptyPage(di).page() )

        if di.nExpensePages == 2:
            w( TwoExpensePages().page(di) )
        elif di.nExpensePages == 4:
            w( FourExpensePages().page(di) )

        for epsPage in di.epsPages:
            try:
                eps_pages = epsPage["pages"]
                eps_fileName = epsPage["fileName"]
                eps_title1 = epsPage["title1"]
                eps_title2 = epsPage["title2"]
            except KeyError, reason:
                print >>sys.stderr, "KeyError: missing key for EPS page (%s): %s" % \
                      (epsPage, str(reason))
                continue
            if eps_pages == 1:
                w( EPSFilePage(di, eps_fileName, eps_title1).page() )
            elif eps_pages == 2:
                # Ensure we start the two eps pages on an even page
                if di.evenPage:
                    w( EmptyPage(di).page() )
                w( TwoEPSFilePages(di, eps_fileName, eps_title1, eps_title2).page() )

        for manPageInfo in di.manPages:
            w( ManPagePages(di, manPageInfo).page() )

        for i in range(di.nNotesPages):
            w( NotesPage(di).page() )

        # Ensure we start the diary pages on a Monday
        while di.dt.day_of_week != DateTime.Monday: di.gotoPreviousDay()
        # Now get a multiple of whole weeks of the previous year
        for i in range(0,7*di.nWeeksBefore): di.gotoPreviousDay()

        # Print a blank page or an extra notes page to start the year on a left side page
        if di.evenPage:
            if di.nNotesPages > 0:
                w( NotesPage(di).page() )
            else:
                w( EmptyPage(di).page() )


        # Set the title for notes pages in the week-with-notes layout.  If we start at the
        # start of a year, set it to the year.  Otherwise, empty.
        if di.layout == "week-with-notes":
            if di.dtbegin.month==1 and di.dtbegin.day==1:
                wwnNotesTitle = "%d" % di.dtbegin.year
            else:
                wwnNotesTitle = ""


        if di.layout == "logbook":
            # The logbook layout is handled differently to other layouts.  For others,
            # DiaryPage inspects the layout and changes its behaviour, but for logbook we use
            # the layout directly here.
            for n in range(di.nLogbookPages):
                w( LogbookPage(di).page() )
        else:
            # Print diary pages until we see the end date
            while 1:
                if di.dt >= di.dtend:
                    break
                y1 = di.dt.year
                w( DiaryPage(di).page() )
                if di.layout == "week-with-notes":
                    w( self.weekWithNotesNotesPage() )

            # If specified, add a number of whole weeks after, probably in the next year.
            if di.nWeeksAfter:
                dw = di.dt + (7*di.nWeeksAfter)
                while di.dt < dw:
                    w( DiaryPage(di).page() )
                    if di.layout == "week-with-notes":
                        w( self.weekWithNotesNotesPage() )

            # Finish at the end of a week
            while di.dt.day_of_week != DateTime.Monday:
                w( DiaryPage(di).page() )

        # Notes pages at the rear
        for i in range(di.nNotesPages):
            w( NotesPage(di).page() )
        # Print an extra notes page to finish on an even page.
        if not di.evenPage:
            if di.nNotesPages > 0:
                w( NotesPage(di).page() )

        w( DSC.postamble(self.di) )

    def weekWithNotesNotesPage(self):
        '''Return a Notes page with a year title.'''
        # If we're in January and the date now is before the seventh, then the last
        # week-to-page page crossed a year.  So print both years as our title.
        y = self.di.dt.year
        m = self.di.dt.month
        d = self.di.dt.day
        if m == 1 and d == 1:
            # If the current day is 1 Jan, then the last page contained the last week of the
            # year, and none of this year.  So the title should be last year.
            return NotesPage(self.di, str(y-1)).page()
        elif m == 1 and d <= 7 and d >= 2:
            # From the 2nd to the 7th of Jan, the previous page must have had days from this
            # year and last year.  So the title reflects that.
            return NotesPage(self.di, str(y-1)+" - "+str(y)).page()
        else:
            return NotesPage(self.di, str(y)).page()


# ############################################################################################
# main()

def go(myname, opts):
    dinfo = DiaryInfo(myname, opts)
    #dinfo.parseOptions()
    #dinfo.readDotCalendar()
    #sys.stderr.write("%s\n" % dinfo.events)
    d = Diary(dinfo)
    d.diary()
    if dinfo.pdf:
        # If we don't close the pipe to the pdf2ps process, it waits forever for more input.
        dinfo.pdfProcess.stdin.close()
        dinfo.pdfProcess.wait()

if __name__=='__main__':
    try:
        go(sys.argv[0], sys.argv[1:])
    except IOError, reason:
        if reason.errno == EPIPE:
            sys.exit(1)
        else:
            raise


# This section is for emacs.
# Local variables: ***
# mode:python ***
# py-indent-offset:4 ***
# fill-column:95 ***
# End: ***
