import sys

from DiaryInfo import DiaryInfo
from DSC import preamble, postamble
from PostscriptPage import PostscriptPage


class TitledPage(PostscriptPage):
    def __init__(self, di, thetitle):
        PostscriptPage.__init__(self, di)
        self.thetitle = thetitle
    def body(self):
        return "% Titled page\n" + self.title(self.thetitle)


if __name__ == '__main__':
    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    tp = TitledPage(di, "Titled page")
    print preamble(di)
    print tp.page()
    print postamble(di)
