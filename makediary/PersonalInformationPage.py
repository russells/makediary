import sys

from DSC import preamble, postamble
from DiaryInfo import DiaryInfo
from PostscriptPage import PostscriptPage


class PersonalInformationPage(PostscriptPage):

    def __init__(self, dinfo):
        PostscriptPage.__init__(self, dinfo)
        self.linenum = 1                #
        self.linespacing = 0            #
        self.minlines = 20              # Required no of lines to fit in all our info

    def body(self):
        # These gymnastics with linespacing are to ensure we get an even spacing of lines
        # over the page.
        initiallinespacing = self.di.lineSpacing * 1.25
        nlines = int(self.pHeight / initiallinespacing)
        if nlines < self.minlines:
            nlines = self.minlines
        self.linespacing = float(self.pHeight) / float(nlines)
        s = ""
        s = s + "%--- Personal Information Page\n" \
            + "%% pheight=%5.3f nlines=%5.3f initial=%5.3f spacing=%5.3f\n" \
            % (self.pHeight,nlines,initiallinespacing,self.linespacing) \
            + self.title("Personal Information") \
            + self.bottomline()
        s = s + "SA %5.3f %5.3f TR\n" % (self.pLeft,self.pBottom)
        fontsize = self.linespacing * 0.5
        s = s + "/%s %5.3f selectfont\n" % (self.di.subtitleFontName,fontsize)

        co = self.di.configOptions
        if not co.has_section("Personal Information"):
            co.add_section("Personal Information")
        s = s \
            + self.do1line( co, [ ("Name"   , ("Name",),        ),        ] ,0) \
            + self.do1line( co, [ ("Phone"  , ("Phone",)        ),
                                  (("Mobile", "Cell"),
                                   ("Mobile", "Cell") ),                  ] ,0) \
            + self.do1line( co, [ ("Email"  , ("Email",
                                               "Email address") ),        ] ,0) \
            + self.do1line( co, [ ("Address", ("Address", )     ),        ] ,0) \
            + self.do1line( co, [                                         ] ,0) \
            + self.do1line( co, [                                         ] ,0) \
            + self.do1line( co, [ ("Work"   , (             )   ),        ] ,0) \
            + self.do1line( co, [ ("Phone"  , ("Work phone",)   ),
                                  (("Mobile", "Cell"),
                                   ("Work mobile", "Work cell") ),        ] ,0) \
            + self.do1line( co, [ ("Email"  , ("Work email",)   ),        ] ,0) \
            + self.do1line( co, [ ("Address", ("Work address",) ),        ] ,0) \
            + self.do1line( co, [                                         ] ,0) \
            + self.do1line( co, [                                         ] ,0) \
            + self.do1line( co, [ ("Emergency Contacts", ()     ),        ] ,0) \
            + self.do1line( co, [ ("", ("Emergency Contact 1",),),        ] ,0) \
            + self.do1line( co, [ ("", ("Emergency Contact 2",),),        ] ,0) \
            + self.do1line( co, [ ("", ("Emergency Contact 3",),),        ] ,0) \
            + self.do1line( co, [ ("", ("Emergency Contact 4",),),        ] ,0) \
            + self.do1line( co, [ ("Other Information" , ()     ),        ] ,0)

        while self.linenum < nlines:
            s = s + self.do1line( co, [ ] ,0)

        s = s + "RE\n"
        return s

    def do1line(self, config, title_info_pairs, linethick):
        """Do one line of the personal information page."""
        s = ""
        texty = self.pHeight - self.linenum*self.linespacing + 0.2*self.linespacing
        fontsize = self.linespacing * 0.5
        infofontsize = fontsize * 1.1 # Times font appears smaller than helvetica
        nelements = len(title_info_pairs)
        thiselement = 0
        nameindex = 0
        for title_info in title_info_pairs:
            titles = title_info[0]
            infos = title_info[1]
            info_index_count = 0
            info_index = 0
            info_string = None
            for info in infos:
                if config.has_option("Personal Information", info):
                    info_string = config.get("Personal Information", info)
                    info_index = info_index_count
                    break
                else:
                    info_index_count += 1
            if isinstance(titles, tuple):
                # If there is no info specified for this title, the index defaults to 0, so we
                # get the first of the possible titles when a tuple is supplied.
                title_string = titles[info_index]
            else:
                title_string = titles

            title = self.postscriptEscape(title_string)
            s = s + "/%s %5.3f selectfont\n" % (self.di.subtitleFontName,fontsize)
            s = s + "%5.3f %5.3f M (%s) SH \n" % (self.pWidth * thiselement / nelements, texty,
                                                  title)
            if info_string:
                info = self.postscriptEscape(info_string)
                # This is deliberately printed in the previous font.
                s = s + "( - ) SH\n"
                if "email" in title_string.lower():
                    s = s + "/%s %5.3f selectfont\n" % (self.di.personalinfoFixedFontName,
                                                        infofontsize)
                else:
                    s = s + "/%s %5.3f selectfont\n" % (self.di.personalinfoFontName,
                                                        infofontsize)
                s = s + "(%s) gsave 0 setgray SH grestore\n" % info
            thiselement += 1
        liney = self.pHeight - self.linenum * self.linespacing
        if linethick:
            s = s + "%5.2f SLW " % self.di.underlineThick
        else:
            s = s + "0   SLW "
        s = s + "0 %5.3f M %5.3f 0 RL S\n" % (liney,self.pWidth)
        self.linenum = self.linenum + 1
        return s


if __name__ == '__main__':
    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    pip = PersonalInformationPage(di)
    print preamble(di)
    print pip.page()
    print postamble(di)
