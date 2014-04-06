import sys

from DiaryInfo import DiaryInfo
from DSC import preamble, postamble
from PostscriptPage import PostscriptPage


class ImageFilePage(PostscriptPage):
    """A page whose content is made up of an image file."""

    class Side:
        full  = "FULL"
        left  = "LEFT"
        right = "RIGHT"

    def __init__(self, dinfo, imgfilename, imagetitle=None, side=Side.full):
        PostscriptPage.__init__(self, dinfo)
        self.imgfilename = imgfilename
        self.imagetitle = imagetitle
        self.side = side


    def body(self):
        imgfilepathname = None
        # If we are given a full or relative-to-pwd path to the file, use that.
        if self.imgfilename.startswith('/') or self.imgfilename.startswith('./') \
               or self.imgfilename.startswith('../'):
            imgfilepathname = self.imgfilename
        else:
            # Otherwise, construct the full path to the file.  If we are running from the
            # development directory, or otherwise not from a full path name, look at relative
            # locations first.
            if self.di.myname.startswith('.'):
                searchpath = ['.', '..', '../..']
                for p in sys.path:
                    searchpath.append(p)
            else:
                searchpath = sys.path
            #print >>sys.stderr, "searchpath is %s" % str(searchpath)
            for path in searchpath:
                imgfilepathname = self.searchfor(path, 'image', self.imgfilename)
                if imgfilepathname:
                    break
        if imgfilepathname:
            inset = self.pWidth / 200.0
            if self.side == self.Side.full:
                sclip = ''
            elif self.side == self.Side.left or self.side == self.Side.right:
                sclip = "newpath %5.3f %5.3f %5.3f %5.3f rectclip\n" % \
                        (self.pLeft, self.pBottom, self.pWidth, self.pHeight)
            if self.side == self.Side.full:
                x = self.pLeft + inset
                y = self.pBottom + inset
                w = self.pWidth - 2*inset
                h = self.pHeight - 2*inset
            elif self.side == self.Side.left:
                x = self.pLeft    + inset
                y = self.pBottom  + inset
                w = self.pWidth*2 - 2*inset
                h = self.pHeight  - 2*inset
            elif self.side == self.Side.right:
                x = self.pLeft - self.pWidth + inset
                y = self.pBottom             + inset
                w = self.pWidth*2            - 2*inset
                h = self.pHeight             - 2*inset

            imgp = self.image(imgfilepathname, x, y, w, h)
            if self.imagetitle:
                return self.title(self.imagetitle) + sclip + imgp
            else:
                return sclip + imgp
        else:
            print >>sys.stderr, "Can't find %s" % self.imgfilename
            return "%% -- Can't find %s\n" % self.imgfilename


class TwoImageFilePages:
    """Two pages whose content is made up of two halves of one image file."""

    def __init__(self, dinfo, imgfilename, imagetitle=None):
        self.dinfo = dinfo
        self.imgfilename = imgfilename
        self.imagetitle = imagetitle


    def page(self):
        s = ''
        s = s + ImageFilePage(self.dinfo, self.imgfilename, self.imagetitle,
                              ImageFilePage.Side.left).page()
        s = s + ImageFilePage(self.dinfo, self.imgfilename, self.imagetitle,
                              ImageFilePage.Side.right).page()
        return s


if __name__ == '__main__':
    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    print preamble(di)
    print ImageFilePage(di, './makediary-qrcode.png', './makediary-qrcode.png').page()
    print TwoImageFilePages(di, './makediary-qrcode.png', './makediary-qrcode.png').page()
    print postamble(di)
