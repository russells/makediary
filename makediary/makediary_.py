#!/usr/bin/env python3

# vim: set shiftwidth=4 expandtab smartindent textwidth=95:

# Print a year diary.

from makediary.versionNumber import versionNumber

import sys
import makediary.Moon
from makediary.DiaryInfo import DiaryInfo
from errno import EPIPE

from makediary                         import DSC
from makediary.DT                      import DT
from makediary.BasicPostscriptPage     import BasicPostscriptPage
from makediary.PostscriptPage          import PostscriptPage
from makediary.EmptyPage               import EmptyPage
from makediary.CoverPage               import CoverPage
from makediary.VersionPage             import VersionPage
from makediary.PersonalInformationPage import PersonalInformationPage
from makediary.ImageFilePages          import ImageFilePage, TwoImageFilePages
from makediary.EPSFilePages            import EPSFilePage, TwoEPSFilePages
from makediary.CalendarPages           import TwoCalendarPages
from makediary.ManPagePages            import ManPagePages
from makediary.PerpetualCalendarPages  import PerpetualCalendarPages
from makediary.PlannerPages            import TwoPlannerPages, FourPlannerPages, TwelvePlannerPages
from makediary.AddressPage             import AddressPage
from makediary.NotesPage               import NotesPage
from makediary.ExpensePages            import TwoExpensePages, FourExpensePages
from makediary.DiaryPage               import DiaryPage
from makediary.LogbookPage             import LogbookPage


# ############################################################################################

class Diary(object):

    def __init__(self,diaryinfo):
        self.di = diaryinfo
        self.out = self.di.out
        self.convert_to_bytes = False

    def _generate_cover_pages(self):
        di = self.di
        self.out.write( CoverPage(di).page() )
        #self.w( CalendarPage(di).page() )
        if di.debugVersion:
            self.out.write( VersionPage(di).page() )
        else:
            self.out.write( EmptyPage(di).page() )
        self.out.write( PersonalInformationPage(di).page() )

    def _generate_image_pages(self):
        di = self.di
        # Print image pages, if there are any, and end on a new opening.
        for imagePage in di.imagePages:
            npages = imagePage["pages"]
            if npages == 1:
                self.out.write( ImageFilePage(di, imagePage["fileName"], imagePage["title"] ).page() )
            elif npages == 2:
                if di.evenPage:
                    self.out.write( NotesPage(di).page() )
                self.out.write( TwoImageFilePages(di, imagePage["fileName"], imagePage["title"],
                                     imagePage["coverage"]).page() )
            else:
                print(f"makediary: internal error:", file=sys.stderr)
                print(f"-- image file ({imagePage['fileName']}): imagePage['pages'] == {npages}", file=sys.stderr)
                sys.exit(1)
        if di.evenPage:
            self.out.write( EmptyPage(di).page() )

    def _generate_calendar_and_planner_pages(self):
        di = self.di
        if di.calendarPages:
            self.out.write( TwoCalendarPages(di).page() )

        if di.perpetualCalendars:
            self.out.write( PerpetualCalendarPages(di).page() )

        # Ensure that the planner pages are on facing pages.
        if di.nPlannerYears > 0:
            if di.evenPage:
                self.out.write( EmptyPage(di).page() )
            # Decide whether to put short events on the planner pages.  If we are not using
            # pcal to generate the events, then yes.  If we are using pcal, only put short
            # events on if we have been told.
            doEventsOnPlanner = (not di.pcal or (di.pcal and di.pcalPlanner))
            if di.largePlanner:
                self.out.write( TwelvePlannerPages(di.dtbegin.year, di, doEventsOnPlanner).page() )
            else:
                self.out.write( FourPlannerPages(di.dtbegin.year, di, doEventsOnPlanner).page() )
            if di.dtbegin.month==1 and di.dtbegin.day==1:
                for i in range(1, di.nPlannerYears):
                    self.out.write( TwoPlannerPages(di.dtbegin.year+i, di).page() )
            else:
                self.out.write( FourPlannerPages(di.dtbegin.year+1, di).page() )
                for i in range(2, di.nPlannerYears):
                    self.out.write( TwoPlannerPages(di.dtbegin.year+i, di).page() )

    def _generate_address_and_expense_pages(self):
        di = self.di
        for i in range(di.nAddressPages):
            self.out.write( AddressPage(di).page() )

        # Ensure we start the expense pages on an even page
        if di.evenPage:
            if di.nAddressPages != 0:
                self.out.write( AddressPage(di).page() )
            else:
                self.out.write( EmptyPage(di).page() )

        if di.nExpensePages == 2:
            self.out.write( TwoExpensePages().page(di) )
        elif di.nExpensePages == 4:
            self.out.write( FourExpensePages().page(di) )

    def _generate_eps_and_man_pages(self):
        di = self.di
        for epsPage in di.epsPages:
            try:
                eps_pages = epsPage["pages"]
                eps_fileName = epsPage["fileName"]
                eps_title1 = epsPage["title1"]
                eps_title2 = epsPage["title2"]
            except KeyError as reason:
                print(f"KeyError: missing key for EPS page ({epsPage}): {reason}", file=sys.stderr)
                continue
            if eps_pages == 1:
                self.out.write( EPSFilePage(di, eps_fileName, eps_title1).page() )
            elif eps_pages == 2:
                # Ensure we start the two eps pages on an even page
                if di.evenPage:
                    self.out.write( EmptyPage(di).page() )
                self.out.write( TwoEPSFilePages(di, eps_fileName, eps_title1, eps_title2).page() )

        for manPageInfo in di.manPages:
            self.out.write( ManPagePages(di, manPageInfo).page() )

    def _generate_diary_pages(self):
        di = self.di
        for i in range(di.nNotesPages):
            self.out.write( NotesPage(di).page() )

        # Ensure we start the diary pages on a Monday
        while di.dt.day_of_week() != DT.Monday: di.gotoPreviousDay()
        # Now get a multiple of whole weeks of the previous year
        for i in range(0,7*di.nWeeksBefore): di.gotoPreviousDay()

        # Print a blank page or an extra notes page to start the year on a left side page
        if di.evenPage:
            if di.nNotesPages > 0:
                self.out.write( NotesPage(di).page() )
            else:
                self.out.write( EmptyPage(di).page() )


        # Set the title for notes pages in the week-with-notes layout.  If we start at the
        # start of a year, set it to the year.  Otherwise, empty.
        if di.layout == "week-with-notes":
            if di.dtbegin.month==1 and di.dtbegin.day==1:
                wwnNotesTitle = f"{di.dtbegin.year}"
            else:
                wwnNotesTitle = ""


        if di.layout == "logbook":
            # The logbook layout is handled differently to other layouts.  For others,
            # DiaryPage inspects the layout and changes its behaviour, but for logbook we use
            # the layout directly here.
            for n in range(di.nLogbookPages):
                self.out.write( LogbookPage(di).page() )
        else:
            # Print diary pages until we see the end date
            while True:
                if di.dt >= di.dtend:
                    break
                y1 = di.dt.year
                self.out.write( DiaryPage(di).page() )
                if di.layout == "week-with-notes":
                    self.out.write( self.weekWithNotesNotesPage() )

            # If specified, add a number of whole weeks after, probably in the next year.
            if di.nWeeksAfter:
                dw = di.dt + DT.delta(7*di.nWeeksAfter)
                while di.dt < dw:
                    self.out.write( DiaryPage(di).page() )
                    if di.layout == "week-with-notes":
                        self.out.write( self.weekWithNotesNotesPage() )

            # Finish at the end of a week
            while di.dt.day_of_week() != DT.Monday:
                self.out.write( DiaryPage(di).page() )

        # Notes pages at the rear
        for i in range(di.nNotesPages):
            self.out.write( NotesPage(di).page() )
        # Print an extra notes page to finish on an even page.
        if not di.evenPage:
            if di.nNotesPages > 0:
                self.out.write( NotesPage(di).page() )

    # print the whole diary
    def diary(self):
        di = self.di

        self.out.write( DSC.preamble(self.di) )
        self._generate_cover_pages()
        self._generate_image_pages()
        self._generate_calendar_and_planner_pages()
        self._generate_address_and_expense_pages()
        self._generate_eps_and_man_pages()
        self._generate_diary_pages()
        self.out.write( DSC.postamble(self.di) )

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
            return NotesPage(self.di, f"{y-1} - {y}").page()
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
    except IOError as reason:
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
