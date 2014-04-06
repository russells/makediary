import sys
import subprocess
import re

import StringIO
from DiaryInfo import DiaryInfo
from DSC import preamble, postamble
from PostscriptPage import PostscriptPage
from EPSFilePages import EPSFilePage



class ManPagePages(PostscriptPage):
    """Pages that contain a printed man page."""

    def __init__(self, dinfo, manPageInfo ):
        self.dinfo = dinfo
        self.manPageInfo = manPageInfo

    def page(self):
        # Get the output from running man.
        try:
            if self.manPageInfo[1] is None:
                # No man section specified
                man_args = ('man', '-t', self.manPageInfo[0])
                man_par_name = self.manPageInfo[0]
                man_nonpar_name = self.manPageInfo[0]
            else:
                man_args = ('man', '-t', self.manPageInfo[1], self.manPageInfo[0])
                man_par_name = "%s(%s)" % (self.manPageInfo[0], self.manPageInfo[1])
                man_nonpar_name = "%s %s" % (self.manPageInfo[1], self.manPageInfo[0])
            man_process = subprocess.Popen(man_args,
                                           shell=False,
                                           stdin=open('/dev/null'),
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           close_fds=True)
            #print str(man_process)
            man_stdout, man_stderr = man_process.communicate()
            man_returncode = man_process.returncode
            if man_returncode:
                print >>sys.stderr, "%s: cannot get man page for %s: (%d):\n%s" % \
                      (sys.argv[0], man_par_name, man_returncode, man_stderr)
                return "%% -- Cannot run man -t %s\n" % man_nonpar_name
        except OSError, e:
            print >>sys.stderr, "%s: cannot run ``man -t %s'': (%d):\n%s" % \
                  (sys.argv[0], man_nonpar_name, e.errno, e.strerror)
            return "%% -- Cannot run man -t %s %s\n" % man_nonpar_name

        # Convert the man output into EPS.
        try:
            eps_process = subprocess.Popen(('ps2eps'),
                                           shell=False,
                                           stdin=subprocess.PIPE,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           close_fds=True)
            eps_stdout, eps_stderr = eps_process.communicate(man_stdout)
            eps_returncode = eps_process.returncode
            if eps_returncode:
                print >>sys.stderr, "%s: error running ps2eps: (%d):\n%s" % \
                      (sys.argv[0], eps_returncode, eps_stderr)
                return "% -- Cannot run ps2eps\n"
        except OSError, e:
            print >>sys.stderr, "%s: cannot run ps2eps: (%d):\n%s" % \
                  (sys.argv[0], e.errno, e.strerror)
            return "% -- Cannot run ps2eps\n"

        # We don't need these any more.
        man_stdout = None
        man_stderr = None
        eps_stderr = None

        # Prepare the return string.
        s = ''

        # Now for each page, add our page with the EPS in it.  We loop until psselect tells us
        # that it has reached the end.  It does that by returning a completely empty page,
        # rather than with an error or return code.
        pageNumber = 1
        while True:
            #print >>sys.stderr, "Getting page %d" % pageNumber
            try:
                pss_process = subprocess.Popen(('psselect', '-p%d'%pageNumber),
                                               shell=False,
                                               stdin=subprocess.PIPE,
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE,
                                               close_fds=True)
                pss_stdout, pss_stderr = pss_process.communicate(eps_stdout)
                pss_returncode = pss_process.returncode
                if pss_returncode:
                    print >>sys.stderr, "%s: cannot get page %d using psselect: (%d):\n%s" % \
                          (sys.argv[0], pageNumber, pss_returncode, pss_stderr)
                    s += "%% Cannot run psselect -p%d\n" % pageNumber
                    return s
            except OSError, e:
                print >>sys.stderr, "%s: cannot get page %d: (%d):\n%s" % \
                      (sys.argv[0], pageNumber, pss_returncode, pss_stderr)
                s += "%% Cannot get page %d" % pageNumber
                return s

            # Check to see if the page was extracted, or if psselect just gave us an empty
            # page, which is what it does when we ask for a page after the end of the document.
            if not re.search('''^%%Page:''', pss_stdout, re.MULTILINE):
                return s

            # Get our diary page, with the EPS page embedded.
            epsString = StringIO.StringIO(pss_stdout)
            s += EPSFilePage(self.dinfo, epsString).page()

            pageNumber += 1


        return "%% -- man %s(%s)\n" % self.manPageInfo


if __name__ == '__main__':
    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    di.manPageOption('ls(1)')
    di.manPageOption('mkdir')
    di.manPageOption('umount,8')
    print preamble(di)
    for manPageInfo in di.manPages:
        print ManPagePages(di, manPageInfo).page()
    print postamble(di)
