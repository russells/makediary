import sys

from makediary.DiaryInfo      import DiaryInfo
from makediary.DSC            import preamble, postamble
from makediary.PostscriptPage import PostscriptPage


class ImageFilePage(PostscriptPage):
    """A page whose content is made up of an image file."""


    def __init__(self, dinfo, imgfilename, imagetitle=None, left=0.0, right=1.0):
        PostscriptPage.__init__(self, dinfo)
        self.imgfilename = imgfilename
        self.imagetitle = imagetitle
        assert left >= 0.0
        assert right > 0.0
        assert left < 1.0
        assert right <= 1.0
        assert left < right
        assert (right - left) > 0.1
        self.left = left
        self.right = right


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
            sclip = "newpath %5.3f %5.3f %5.3f %5.3f rectclip\n" % \
                    (self.pLeft, self.pBottom, self.pWidth, self.pHeight)
            # Calculate the bounds of the entire image.  The image will be clipped to the page
            # layout boundaries.
            w = self.pWidth / (self.right - self.left) - 2*inset
            x = self.pLeft      - w * self.left + inset
            y = self.pBottom    + inset
            h = self.pHeight    - 2*inset


            imgp = self.image(imgfilepathname, x, y, w, h)
            if self.imagetitle:
                return self.title(self.imagetitle) + sclip + imgp
            else:
                return sclip + imgp
        else:
            print("Can't find %s" % self.imgfilename, file=sys.stderr)
            return "%% -- Can't find %s\n" % self.imgfilename


class TwoImageFilePages:
    """Two pages whose content is made up of two halves of one image file."""

    def __init__(self, dinfo, imgfilename, imagetitle=None, coverage=0.5):
        self.dinfo = dinfo
        self.imgfilename = imgfilename
        self.imagetitle = imagetitle
        self.coverage = coverage


    def page(self):
        s = ''
        s = s + ImageFilePage(self.dinfo, self.imgfilename, self.imagetitle,
                              0.0, self.coverage).page()
        s = s + ImageFilePage(self.dinfo, self.imgfilename, self.imagetitle,
                              1.0-self.coverage, 1.0).page()
        return s


if __name__ == '__main__':
    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    print(preamble(di))
    print(ImageFilePage(di, './makediary-qrcode.png', './makediary-qrcode.png').page())
    print(TwoImageFilePages(di, './makediary-qrcode.png', './makediary-qrcode.png').page())
    print(postamble(di))
