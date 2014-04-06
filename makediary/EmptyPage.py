import sys

from DiaryInfo import DiaryInfo
from DSC import preamble, postamble
from PostscriptPage import PostscriptPage


class EmptyPage(PostscriptPage):
    """An empty page."""
    def body(self):
        return "% --- An empty page\n"


if __name__ == '__main__':
    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    ep = EmptyPage(di)
    print preamble(di)
    print ep.page()
    print postamble(di)
