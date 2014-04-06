import sys

from DiaryInfo import DiaryInfo
from DSC import preamble, postamble
from PostscriptPage import PostscriptPage

# ############################################################################################

class AddressPage(PostscriptPage):

    naddresses = 10                     # Per page
    nameprop = 0.25                     # Proportion of width in name field
    teleprop = 0.25                     # ditto for telephone field
    namewidth = -1                      # Actual width of the name field
    addrwidth = -1                      # ditto for address field
    telewidth = -1                      # ditto for telephone field
    left = -1
    fontsize = 4.0                      # For titles
    abheight = -1                       # Address block height
    tbheight = -1                       # Title block height

    def titleBlock(self):
        s = ""
        # Draw a line around the titles
        s = s + "%5.3f SLW %5.3f %5.3f M %5.3f 0 RL 0 %5.3f RL %5.3f 0 RL 0 %5.3f RL " % \
            (self.di.underlineThick, self.left, self.pTop, self.pWidth, -self.tbheight,
             -self.pWidth, self.tbheight)
        s = s + "gsave %5.3f setgray fill grestore S\n" % self.di.titleGray
        # Draw the separator lines between the titles
        s = s + "%5.3f %5.3f M 0 %5.3f RL S\n" % \
            (self.left+self.namewidth, self.pTop, -self.tbheight)
        s = s + "%5.3f %5.3f M 0 %5.3f RL S\n" % \
            (self.left+self.namewidth+self.addrwidth, self.pTop, -self.tbheight)
        # Now add the titles themselves
        s = s + "/%s %5.3f selectfont\n" % (self.di.subtitleFontName, self.fontsize)
        titley = self.pTop - self.tbheight + self.fontsize*0.5
        # A clever loop for the title text, so we don't have to write this code three times.
        for par in (("Name",self.left+self.namewidth/2.0),
                    ("Address",self.left+self.namewidth+self.addrwidth/2.0),
                    ("Telephone",self.left+self.namewidth+self.addrwidth+self.telewidth/2.0)):

            s = s + "(%s) dup exch SWP2D %5.3f exch sub %5.3f M SH\n" % \
                (par[0],par[1], titley)
        return s

    def addressBlock(self,b):
        s = ""
        s = s + "%5.3f %5.3f M SA CP TR 0 SLW\n" % (self.pLeft,b)
        s = s + "0 0 M 0 %5.3f RL %5.3f 0 RL 0 %5.3f RL %5.3f 0 RL S " % \
            (self.abheight,self.pWidth,-self.abheight,-self.pWidth) \
            + "%5.3f 0 M 0 %5.3f RL S " % (self.namewidth,self.abheight) \
            + "%5.3f 0 M 0 %5.3f RL S RE\n" % (self.namewidth+self.addrwidth, self.abheight)
        return s

    def body(self):
        # Calculate some sizes first
        self.tbheight = self.fontsize * 1.8
        self.abheight = (self.pHeight - self.tbheight) / self.naddresses
        if self.di.evenPage:
            self.left = self.di.oMargin
        else:
            self.left = self.di.iMargin
        self.namewidth = self.nameprop * self.pWidth
        self.telewidth = self.teleprop * self.pWidth
        self.addrwidth = self.pWidth - self.namewidth - self.telewidth
        s = ""
        s = s + "%--- Address Page\n"
        for i in range(self.naddresses):
            s = s + self.addressBlock(self.pBottom + i*self.abheight)
        s = s + self.titleBlock()
        # Box around the whole page.
        s = s + "%5.3f SLW %5.3f %5.3f M 0 %5.3f RL %5.3f 0 RL 0 %5.3f RL %5.3f 0 RL\n" % \
            (self.di.underlineThick, self.left, self.pBottom, self.pHeight, self.pWidth,
             -self.pHeight, -self.pWidth)
        s = s + self.title("Addresses") + self.bottomline()
        return s


if __name__ == '__main__':
    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    ap = AddressPage(di)
    print preamble(di)
    print ap.page()
    print postamble(di)
