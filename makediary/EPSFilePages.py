#!/usr/bin/env python3
import sys

from makediary.DiaryInfo      import DiaryInfo
from makediary.DSC            import preamble, postamble
from makediary.PostscriptPage import PostscriptPage


class EPSFilePage(PostscriptPage):
    """A page whose content is made up of an EPS file."""

    def __init__(self, dinfo, epsfilename, epstitle=None):
        PostscriptPage.__init__(self, dinfo)
        self.epsfilename = epsfilename
        self.epstitle = epstitle


    def findEPSFile(self, epsfilename):
        epsfilepathname = None
        # If we are given a full or relative-to-pwd path to the file, use that.
        if self.epsfilename.startswith('/') or self.epsfilename.startswith('./') \
               or self.epsfilename.startswith('../'):
            epsfilepathname = self.epsfilename
        else:
            # Otherwise, construct the full path to the file.  If we are running from the
            # development directory, or otherwise not from a full path name, look at relative
            # locations first.  In any case, we search the current directory first.
            if sys.argv[0].startswith('.'):
                searchpath = ['.', '..', '../..']
            else:
                searchpath = ['.']
            for p in sys.path:
                searchpath.append(p)
            #print >>sys.stderr, "searchpath is %s" % str(searchpath)
            for path in searchpath:
                epsfilepathname = self.searchfor(path, 'eps', self.epsfilename)
                if epsfilepathname:
                    break
        return epsfilepathname


    # FIXME this method is intended to factor out the bounding box, scaling and translation
    # stuff for both EPSFilePage and HalfEPSFilePage.  It is not used (yet).
    def calculateEPSStuff(self, boundingbox, maxwidth, maxheight):
        epsx1_pt, epsy1_pt, epsx2_pt, epsy2_pt = boundingbox
        epsx1 = epsx1_pt/self.di.points_mm
        epsy1 = epsy1_pt/self.di.points_mm
        epsx2 = epsx2_pt/self.di.points_mm
        epsy2 = epsy2_pt/self.di.points_mm
        epswidth  = epsx2 - epsx1
        epsheight = epsy2 - epsy1

        # Some space for layout.
        inset = self.pWidth / 200.0


    def body(self):
        s = ''

        # Ensure we start with black.
        s = s + "0 setgray\n"

        # If we were supplied a string, it's a file name, otherwise we assume it's a file like
        # object.
        if isinstance(self.epsfilename, ''.__class__):
            try:
                epsfile = open(self.epsfilename, 'r')
            except IOError as reason:
                print("Can't open %s: %s" % (self.epsfilename, str(reason)), file=sys.stderr)
                return "%% +++ Error opening %s: %s\n" % (self.epsfilename, str(reason))
        else:
            epsfile = self.epsfilename

        errmsg, boundingbox = self.findBoundingBoxInEPS(self.epsfilename, epsfile)
        if errmsg:
            print("%s: %s" % (sys.argv[0], errmsg), file=sys.stderr)
            return "%% +++ %s\n" % self.postscriptEscape(errmsg)

        if self.epstitle:
            s = s + self.title(self.epstitle)

        epsx1_pt, epsy1_pt, epsx2_pt, epsy2_pt = boundingbox
        epsx1 = epsx1_pt/self.di.points_mm
        epsy1 = epsy1_pt/self.di.points_mm
        epsx2 = epsx2_pt/self.di.points_mm
        epsy2 = epsy2_pt/self.di.points_mm
        epswidth  = epsx2 - epsx1
        epsheight = epsy2 - epsy1

        # Some space for layout.
        inset = self.pWidth / 200.0

        x = self.pLeft+inset
        y = self.pBottom+inset
        maxwidth = self.pWidth-2*inset
        maxheight = self.pHeight-2*inset

        s = s + self.di.sectionSep + "%% Beginning embedded PS file: %s\n" % self.epsfilename
        s = s + "%% x=%5.3f y=%5.3f maxwidth=%5.3f maxheight=%5.3f\n" % \
                (x,y,maxwidth,maxheight)
        s = s + "%% epsx1_pt=%7.3f   epsy1_pt=%7.3f   epsx2_pt=%7.3f   epsy2_pt=%7.3f\n" % \
                (epsx1_pt, epsy1_pt, epsx2_pt, epsy2_pt)
        s = s + "%% epsx1   =%7.3f   epsy1   =%7.3f   epsx2   =%7.3f   epsy2   =%7.3f\n" % \
                (epsx1, epsy1, epsx2, epsy2)

        # Make a clipping region.
        #s = s + "% Clipping path to contain the EPS file.\n"
        #s = s + "gsave newpath %.3f %.3f %.3f %.3f rectclip\n" % (x, y, maxwidth, maxheight)

        # Move to the required origin for the EPS
        s = s + "%5.3f %5.3f M\n" % (x, y) #(x+xoffset,y+yoffset)

        # Find out which of the x or y axes has to be adjusted.
        rawxscale = maxwidth / epswidth
        rawyscale = maxheight / epsheight
        if rawxscale == rawyscale:
            scale = rawxscale
            xadj = 0
            yadj = 0
        elif rawxscale < rawyscale:
            scale = rawxscale
            xadj = 0
            yadj = (maxheight - (epsheight * scale))/2.0
        else:
            scale = rawyscale
            xadj = (maxwidth - (epswidth * scale))/2.0
            yadj = 0

        s = s + "% Results from scaling:\n"
        s = s + "%% rawxscale=%5.3f rawyscale=%5.3f scale=%5.3f xadj=%5.3f yadj=%5.3f\n" % \
                (rawxscale,rawyscale,scale,xadj,yadj)
        xadj -= epsx1*scale
        yadj -= epsy1*scale
        s = s + "%% Then, xadj=%5.3f yadj=%5.3f\n" % (xadj,yadj)
        # Now go there
        s = s + "SA %5.3f %5.3f RM %5.3f %5.3f SC CP TR\n" % (xadj,yadj,scale,scale)

        epsp = self.embedEPS(self.epsfilename, epsfile)
        epsfile.close()
        return s + epsp + "RE\n"


class HalfEPSFilePage(EPSFilePage):
    """One page whose content is made up of a half of an EPS file."""

    # Sides
    LEFT = "Left"
    RIGHT = "Right"


    def __init__(self, dinfo, epsfilepathname, epstitle=None, side=LEFT):
        EPSFilePage.__init__(self, dinfo, None, epstitle)
        self.epsfilepathname = epsfilepathname
        self.side = side


    def body(self):
        '''New body() method.'''
        pe = self.postscriptEscape
        s = ''
        s += '%% %s: file=%s side=%s\n' % (self.__class__.__name__,
                                           pe(self.epsfilepathname),
                                           pe(self.side))

        if self.epstitle:
            s = s + self.title(self.epstitle)

        if self.di.debugBoxes:
            # This is a bit of an abuse of the --debug-boxes flag, but I think that's ok since
            # we would not normally want to print the file name info like this unless we're
            # drawing the debug boxes.
            fontSize = 2.2*self.di.pageHeight/210.0
            s += "/Courier %5.3f selectfont " % fontSize
            s += '%5.3f %5.3f M (%s, %s, %s) SH\n' % (self.pLeft+1, self.pBottom+1,
                                                      pe(self.__class__.__name__),
                                                      pe(self.side),
                                                      pe(self.epsfilepathname))

        try:
            epsfile = open(self.epsfilepathname, 'r')
        except IOError as reason:
            print("%s: Can't open %s: %s" % (sys.argv[0],
                                                           self.epsfilepathname,
                                                           str(reason)), file=sys.stderr)
            return "%% +++ Error opening %s: %s\n" % (pe(self.epsfilepathname),
                                                      pe(str(reason)))

        errmsg, boundingbox = self.findBoundingBoxInEPS(self.epsfilepathname, epsfile)
        if errmsg:
            print("%s: %s" % (sys.argv[0], errmsg), file=sys.stderr)
            return "%% +++ %s\n" % self.postscriptEscape(errmsg)
        s = s + "%% %s: bounding box = %s\n" % (self.__class__.__name__, str(boundingbox))

        # Now find out how big the bounding box will be on the page.
        epsx1_pt, epsy1_pt, epsx2_pt, epsy2_pt = boundingbox
        epsx1 = epsx1_pt / self.di.points_mm
        epsy1 = epsy1_pt / self.di.points_mm
        epsx2 = epsx2_pt / self.di.points_mm
        epsy2 = epsy2_pt / self.di.points_mm
        eps_width  = epsx2 - epsx1
        eps_height = epsy2 - epsy1
        s = s + "%% %s: bounding box mm = %s\n" % (self.__class__.__name__,
                                                   str( (epsx1, epsy1, epsx2, epsy2) ))

        # Sanity check.  We can't operate with width or height <= 0.
        if eps_width <= 0 or eps_height <= 0:
            print("%s: Cannot work with this bounding box: %s (file: %s)" % \
                (sys.argv[0], str(boundingbox), self.epsfilepathname), file=sys.stderr)
            s += "%% Cannot work with this BoundingBox: %s\n" % str(boundingbox)
            return s

        # Some space for layout.
        inset = self.pWidth / 200.0
        maxwidth = self.pWidth - inset # Yes, only one inset.
        maxheight = self.pHeight - 2*inset

        # Calculate the scale factor.  We want the EPS page to expand to the maximum it can
        # before hitting the top and bottom, or hitting the left and right.
        eps_xscale = maxwidth * 2.0 / eps_width
        eps_yscale = maxheight / eps_height
        if eps_xscale == eps_yscale:
            scale = eps_xscale
        elif eps_xscale < eps_yscale:
            # The X dimension of the EPS file takes up more of the available space than does
            # the Y dimension.  So maximise the EPS to the X scale, and centre the Y.
            eps_scale = eps_xscale
        else:
            # The reverse of the previous case.
            eps_scale = eps_yscale

        # The Y position does not depend on the page side.
        if eps_scale == eps_yscale:
            # The Y dimension takes up the whole page in this case.
            ypos = self.pBottom + inset
        else:
            ypos = self.pBottom + inset + (maxheight - (eps_height * eps_scale)) / 2.0

        # The X position does depend on the page side.
        if self.side == self.LEFT:
            xpos = self.pLeft + inset + maxwidth - (eps_width * eps_scale / 2.0)
        else:
            xpos = self.pLeft - (eps_width * eps_scale / 2.0)

        # Now draw a debugging box around that bit, if it's requested.
        if self.di.debugBoxes:
            s += '0 SLW %5.3f %5.3f %5.3f %5.3f debugboxLBWH\n' % \
                (xpos, ypos, eps_width * eps_scale, eps_height * eps_scale)

        # If we're not drawing the debug boxes, then create a clipping region, so that the EPS
        # does not flow outside where the user would expect it.
        if not self.di.debugBoxes:
            clipw = eps_width * eps_scale / 2.0
            cliph = eps_height * eps_scale
            clipy = ypos
            if self.side == self.LEFT:
                clipx = xpos
            else:
                clipx = self.pLeft
            #s += '0 SLW %5.3f %5.3f %5.3f %5.3f debugboxLBWH\n' % \
            #    (clipx, clipy, clipw, cliph)
            s += 'newpath %5.3f %5.3f %5.3f %5.3f rectclip\n' % \
                (clipx, clipy, clipw, cliph)

        # To draw the EPS, we move to the calculated spot, adjusted by the first pair of
        # coordinates in the bounding box.  And that adjustment must be scaled.
        s += '%5.3f %5.3f M CP TR\n' % (xpos - epsx1*eps_scale, ypos - epsy1*eps_scale)

        # Debugging smiley.
        if self.di.debugBoxes:
            s += 'SA\n' + self.smiley() + 'RE\n'

        # Scale the EPS page
        s += "%5.3f %5.3f SC\n" % (eps_scale,eps_scale)

        s += self.embedEPS(self.epsfilepathname, epsfile)
        epsfile.close()

        return s


class TwoEPSFilePages(EPSFilePage):
    """Two pages whose content is made up of two halves of an EPS file."""

    def __init__(self, dinfo, epsfilename, title1=None, title2=None):
        self.dinfo = dinfo
        self.epsfilename = epsfilename
        self.title1 = title1
        self.title2 = title2


    def page(self):
        s = ''

        epsfilepathname = self.findEPSFile(self.epsfilename)
        if epsfilepathname is None:
            print("cannot find %s" % self.epsfilename, file=sys.stderr)
            return "%% %s: cannot find %s\n" % (self.__class__.__name__, self.epsfilename)
        s = s + "%% %s: found %s at %s\n" % (self.__class__.__name__,
                                             self.epsfilename, epsfilepathname)

        title1 = self.title1
        if title1 is not None and (self.title2 is None or self.title2 == ''):
            # This single space is a bit of a hack to get a line across underneath where the
            # title would go, without putting a title there.
            title2 = ' '
        else:
            title2 = self.title2
        s = s + HalfEPSFilePage(self.dinfo, epsfilepathname,
                                title1, HalfEPSFilePage.LEFT).page() \
              + HalfEPSFilePage(self.dinfo, epsfilepathname,
                                title2, HalfEPSFilePage.RIGHT).page()
        return s


if __name__ == '__main__':
    di = DiaryInfo(sys.argv[0], sys.argv[1:])
    #di.epsFilePageOption('eps/units/units.eps|EPS file units.eps', 1)
    #di.epsFilePageOption('eps/units/units.eps', 2)
    print(preamble(di))
    print(EPSFilePage(di, 'makediary-qrcode.eps').page())
    print(TwoEPSFilePages(di, 'makediary-qrcode.eps').page())
    print(postamble(di))
