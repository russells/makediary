#!/usr/bin/env python3
import sys
import subprocess
import re

from io import StringIO
from makediary.DiaryInfo      import DiaryInfo
from makediary.DSC            import preamble, postamble
from makediary.PostscriptPage import PostscriptPage
from makediary.EPSFilePages   import EPSFilePage


class NamedStringIO(StringIO):
    """A string IO class that holds an informative name.

    The informative name is returned by __str__(), instead of
    <StringIO.StringIO instance at 0xdeadbee>
    """

    def __init__(self, s, name):
        self.name = name
        StringIO.__init__(self, s)

    def __str__(self):
        return self.name


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
                                           text=True, encoding='utf-8',
                                           close_fds=True)
            #print str(man_process)
            man_stdout, man_stderr = man_process.communicate()
            man_returncode = man_process.returncode
            if man_returncode:
                print("%s: cannot get man page for %s: (%d):\n%s" % \
                      (sys.argv[0], man_par_name, man_returncode, man_stderr), file=sys.stderr)
                return "%% -- Cannot run man -t %s\n" % man_nonpar_name
        except OSError as e:
            print("%s: cannot run ``man -t %s'': (%d):\n%s" % \
                  (sys.argv[0], man_nonpar_name, e.errno, e.strerror), file=sys.stderr)
            return "%% -- Cannot run man -t %s %s\n" % man_nonpar_name

        # Convert the man output into EPS.
        try:
            eps_process = subprocess.Popen(('ps2eps'),
                                           shell=False,
                                           stdin=subprocess.PIPE,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           text=True, encoding='utf-8',
                                           close_fds=True)
            eps_stdout, eps_stderr = eps_process.communicate(input=man_stdout)
            eps_returncode = eps_process.returncode
            if eps_returncode:
                print("%s: error running ps2eps: (%d):\n%s" % \
                      (sys.argv[0], eps_returncode, eps_stderr), file=sys.stderr)
                return "% -- Cannot run ps2eps\n"
        except OSError as e:
            print("%s: cannot run ps2eps: (%d):\n%s" % \
                  (sys.argv[0], e.errno, e.strerror), file=sys.stderr)
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
                                               text=True, encoding='utf-8',
                                               close_fds=True)
                pss_stdout, pss_stderr = pss_process.communicate(input=eps_stdout)
                pss_returncode = pss_process.returncode
                if pss_returncode and not pss_stdout:
                    # A non-zero return code with an empty stdout means we've
                    # gone past the end of the document.  This is not an error.
                    return s
                if pss_returncode:
                    print("%s: cannot get page %d using psselect: (%d):\n%s" % \
                          (sys.argv[0], pageNumber, pss_returncode, pss_stderr), file=sys.stderr)
                    s += "%% Cannot run psselect -p%d\n" % pageNumber
                    return s
            except OSError as e:
                print("%s: cannot get page %d: (%d):\n%s" % \
                      (sys.argv[0], pageNumber, pss_returncode, pss_stderr), file=sys.stderr)
                s += "%% Cannot get page %d" % pageNumber
                return s

            # Check to see if the page was extracted.  If we got an empty page,
            # it means we have reached the end.
            if not re.search('''^%%Page:''', pss_stdout, re.MULTILINE):
                break

            # Make up a name for the embedded document.
            if self.manPageInfo[1] is None:
                documentname = "man %s # page %d" % (self.manPageInfo[0], pageNumber)
            else:
                documentname = "man %s %s # page %d" % \
                               (self.manPageInfo[1], self.manPageInfo[0], pageNumber)
            # Get our diary page, with the EPS page embedded.
            epsString = NamedStringIO(pss_stdout, documentname)
            s += EPSFilePage(self.dinfo, epsString).page()

            pageNumber += 1


        return "%% -- man %s(%s)\n" % self.manPageInfo


if __name__ == '__main__':
    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    di.manPageOption('ls(1)')
    di.manPageOption('mkdir')
    di.manPageOption('umount,8')
    print(preamble(di))
    for manPageInfo in di.manPages:
        print(ManPagePages(di, manPageInfo).page())
    print(postamble(di))
