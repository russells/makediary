#!/usr/bin/env python3
import sys
import io
import imageio as Image
try:
    #print("EpsImagePlugin")
    import EpsImagePlugin
except:
    try:
        #print("PIL.EpsImagePlugin")
        from PIL import EpsImagePlugin
    except:
        #print("PILcompat.EpsImagePlugin")
        from PILcompat import EpsImagePlugin
from os import getcwd
from os.path import join as path_join
from os.path import exists as path_exists

from makediary.DiaryInfo           import DiaryInfo
from makediary.DSC                 import preamble, postamble
from makediary.BasicPostscriptPage import BasicPostscriptPage


class PostscriptPage(BasicPostscriptPage):
    """Basic PostScript page with images and embedded Postscript objects."""

    def image(self,file,x,y,xmaxsize,ymaxsize):

        """Print an image on the page.  The image will be scaled so it will fit within a box at
        (x,y), with size (xmaxsize,ymaxsize), and centred inside that box."""

        s = ""
        im = Image.open(file,"r")
        xsize,ysize = im.size
        if self.di.colour:
            if im.mode not in ("L", "RGB", "CMYK"):
                im = im.convert("RGB")
        else:
            im = im.convert("L")
        epsfile = io.StringIO()

        rawxscale = float(xmaxsize)/xsize
        rawyscale = float(ymaxsize)/ysize
        if rawxscale == rawyscale:
            scale = rawxscale
            xpos = x
            ypos = y
        else:
            if rawxscale > rawyscale:
                scale = rawyscale
                ypos = y
                xpos = x + (xmaxsize - (xsize * scale))/2.0
            else:
                scale = rawxscale
                xpos = x
                ypos = y + (ymaxsize - (ysize * scale))/2.0

        s = s + self.di.sectionSep + "% Begin EPS image:\n"
        if self.di.debugBoxes:
            if rawxscale > rawyscale:
                dashlen = ymaxsize / 9.0
            else:
                dashlen = xmaxsize / 9.0
            s = s + "%% debug box\n%5.3f %5.3f %5.3f %5.3f debugboxLBWH\n" % \
                (x,y,xmaxsize,ymaxsize)
        s = s + "%% rawxscale=%5.3f rawyscale=%5.3f\n" % (rawxscale,rawyscale)
        s = s + "%% file=%s x=%5.3f y=%5.3f xmaxsize=%5.3f ymaxsize=%5.3f\n" % \
            (file,x,y,xmaxsize,ymaxsize)
        s = s + "%% xsize=%5.3f ysize=%5.3f rawxscale=%5.3f rawyscale=%5.3f\n" % \
            (xsize,ysize,rawxscale,rawyscale)
        s = s + "%% scale=%5.3f xpos=%5.3f ypos=%5.3f\n" % \
            (scale,xpos,ypos)
        s = s + "%% xmaxsize*scale=%5.3f ymaxsize*scale=%5.3f\n" % \
            (xmaxsize*scale,ymaxsize*scale)
        s = s + "5 dict begin /showpage { } bind def SA %5.3f %5.3f TR\n" % (xpos,ypos)
        s = s + "%5.3f %5.3f scale\n" % (scale, scale)
        s = s + "%%%%BeginDocument: %s\n" % file
        EpsImagePlugin._save(im,epsfile,None,1)
        eps = epsfile.getvalue()
        epsfile.close()
        #im.close()
        s = s + eps
        s = s + "\n%%EndDocument\n"
        s = s + "RE end\n" \
            + "% End EPS image\n" + self.di.sectionSep
        return s


    def findBoundingBoxInEPS(self, epsfilename, epsfile):
        '''Search for the BoundingBox comment, must be in the first 20 lines.'''

        filepos = epsfile.tell()

        boundingboxfound  = False
        for i in range(0,20):
            line = epsfile.readline()
            if line.startswith("%%BoundingBox:"):
                list = line.split()
                if len(list) != 5:
                    msg = "EPS file %s: can't split \"%s\"" % (epsfilename, line.strip())
                    return (msg, None)
                epsx1_pt = float(list[1])
                epsy1_pt = float(list[2])
                epsx2_pt = float(list[3])
                epsy2_pt = float(list[4])
                boundingboxfound = True
                break

        # Return the file to where we found it.
        epsfile.seek(filepos)

        if boundingboxfound:
            return (None, (epsx1_pt, epsy1_pt, epsx2_pt, epsy2_pt))
        else:
            return ("EPS file %s: no %%%%BoundingBox in first 20 lines" % epsfilename,
                    None)


    def embedEPS(self, filename, epsfile):
        '''Embed an EPS file within the diary.

        filename - name of file we are embedding, for error messages
        epsfile - file-like object that contains EPS
        '''

        s = ''

        # Redefine showpage so the EPS file doesn't muck up our page count, save the graphics
        # state, and scale so the EPS measurements in points are the correct size in our world
        # of millimetres.
        s = s + "5 dict begin /showpage { } bind def SA %5.6f %5.6f SC\n" % \
                (1.0/self.di.points_mm, 1.0/self.di.points_mm)
        s = s + "%%%%BeginDocument: %s\n" % filename

        for line in epsfile.readlines():
            s = s + line

        #s = s + "\n%%EndDocument\nRE end RE\n"
        s = s + "\n%%EndDocument\nRE end\n"

        # Remove the clipping region
        #s = s + "grestore\n"

        # Now draw a box so we can see where the image should be.
        #s = s + "%5.3f %5.3f %5.3f %5.3f 0 boxLBWH\n" % (x,y,maxwidth,maxheight)
        return s


    def searchfor(self, path, type, filename):
        '''Look for a file in the python search path, with a couple of optional prefixes.'''
        #print >>sys.stderr, "searchfor  (%s, %s)" % (path,filename)
        p = path_join(path, filename)
        pe = path_join(path, type, filename)
        pme = path_join(path, 'makediary', type, filename)
        #print >>sys.stderr, "Looking for %s, cwd is %s" % (p, getcwd())
        if path_exists(pme):
            #print "Found %s" % pme
            return pme
        elif path_exists(pe):
            #print "Found %s" % pe
            return pe
        elif path_exists(p):
            #print "Found %s" % p
            return p
        else:
            return None


if __name__ == '__main__':
    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    print(preamble(di))
    print(PostscriptPage(di).page())
    print(postamble(di))
