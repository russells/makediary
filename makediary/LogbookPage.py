import sys

from makediary.DiaryInfo import DiaryInfo
from makediary.DSC       import preamble, postamble
from makediary.NotesPage import NotesPage


class LogbookPage(NotesPage):
    def body(self):

        s = "%--- Logbook Page\n" + self.title("20__ /__ /__", bold=False) + self.bottomline()
        s = s + "SA %5.3f %5.3f TR 0 SLW\n" % (self.pLeft,self.pBottom)

        if self.di.griddedLogbookPages:
            s = s + self.grid()
        else:
            s = s + self.lines()

        s = s + "RE\n"
        return s


if __name__ == '__main__':
    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    np = LogbookPage(di)
    print(preamble(di))
    print(np.page())
    print(postamble(di))
