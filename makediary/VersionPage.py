import sys

from makediary.DT             import DT
from makediary.DiaryInfo      import DiaryInfo
from makediary.DSC            import preamble, postamble
from makediary.PostscriptPage import PostscriptPage
from makediary.versionNumber  import versionNumber


class VersionPage(PostscriptPage):
    """A page with version number, command arguments, and usage information."""

    def body(self):
        fontSize = 2.1*self.di.pageHeight/210.0
        linex = fontSize*6
        s=""
        versionString = self.postscriptEscape(versionNumber)
        dateString = self.postscriptEscape(DT.now() \
                                           .strftime("Generated at: %Y-%m-%dT%H:%M:%S%Z"))
        urlString = "http://adelie.cx/makediary/"
        s = s + "% --- Version page\n" \
            + "/Courier %5.3f selectfont " % fontSize \
            + "%5.3f %5.3f M (%s) SH\n" % (linex, fontSize*12, versionString) \
            + "%5.3f %5.3f M (%s) SH\n" % (linex, fontSize*10, dateString) \
            + "%5.3f %5.3f M (%s) SH\n" % (linex, fontSize*8, urlString)
        liney = self.di.pageHeight*0.9
        s = s + "%5.3f %5.3f M (Command:) SH\n" % (linex, liney)
        liney = liney - fontSize*1.25
        s = s + "%5.3f %5.3f M (   %s) SH\n" % (linex, liney, self.di.myname)
        liney = liney - fontSize*1.25
        for i in range(len(self.di.opts)):
            s = s + "%5.3f %5.3f M (   %s) SH\n" % (linex, liney,
                                                    self.postscriptEscape(self.di.opts[i]))
            liney = liney - fontSize*1.25
        liney = liney - fontSize*2.5
        for i in range(len(self.di.usageStrings)):
            s = s + "%5.3f %5.3f M (%s) SH\n" % (linex, liney,
                                                 self.postscriptEscape(self.di.usageStrings[i]))
            liney = liney - fontSize*1.25
        return s


if __name__ == '__main__':
    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    vp = VersionPage(di)
    print(preamble(di))
    print(vp.page())
    print(postamble(di))
