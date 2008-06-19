#!/usr/bin/python

# Calculate moon phases.  This code is copied from moonphas.c in the pcal source, and
# translated from C into python.  I don't understand it at all.  This code generates the same
# answers (days and phases) as the original C code, so that's good.


import sys
import math
import time
from string import atoi

class MoonCalc:

    MOON_NM = 0
    MOON_1Q = 1
    MOON_FM = 2
    MOON_3Q = 3
    MOON_OTHER = -1

    epoch = 2444238.5                   # 1980 January 0.0 
    elonge = 278.833540                 # ecliptic longitude of the Sun at epoch 1980.0
    elongp = 282.596403                 # ecliptic longitude of the Sun at perigee
    eccent = 0.016718                   # eccentricity of Earth's orbit
    mmlong = 64.975464                  # moon's mean lonigitude at the epoch
    mmlongp = 349.383063                # mean longitude of the perigee at the epoch
    mlnode = 151.950429                 # mean longitude of the node at the epoch
    synmonth = 29.53058868              # synodic month (new Moon to new Moon)
    PI = 3.14159265358979323846         # assume not near black hole nor in Tennessee ;)
    
    utc_offset = math.fmod(time.timezone, 86400.0) / 86400.0
    if utc_offset < 0.0:
        utc_offset = utc_offset + 1.0
    if utc_offset > 0.5:
        utc_offset = utc_offset - 0.5


    def FNITG(self, x):
        if x < 0: sign = -1
        else:     sign = 1
        return sign * math.floor(math.fabs(x))

    def fixangle(self, a):
        return a - 360.0 * math.floor(a / 360.0)

    def torad(self, d):
        return d * self.PI / 180.0
    
    def todeg(self, d):
        return d * 180.0 / self.PI

    def julday(self, year, month, day):
        mn1 = month
        yr1 = year
        if yr1 < 0: yr1 = yr1 + 1
        if month<3:
            mn1 = month + 12
            yr1 = yr1 - 1
        if (year<1582) \
               or (year==1582 and month<10) \
               or (year==1582 and month==10 and day<15):
            b = 0
        else:
            a = math.floor(yr1 / 100.0)
            b = 2 - a + math.floor(a/4)
        if yr1 >= 0:
            c = math.floor(365.25 * yr1) - 694025
        else:
            c = self.FNITG ((365.25 * yr1) - 0.75) - 694025
        d = math.floor (30.6001 * (mn1 + 1))
        djd = b + c + d + day + 2415020.0
        return djd

    def kepler(self, m, ecc):
        EPSILON= 1E-6
        e = m = self.torad(m)
        delta = 100
        while math.fabs(delta) > EPSILON:
            delta = e - ecc * math.sin(e) - m
            e = e - delta / (1 - ecc*math.cos(e))
        return e

    def calc_phase(self, year, month, day):

        """Copied directly from moonphas.c.  I don't understand this at all."""
        
        pdate = self.julday(year, month, day) + self.utc_offset
        
        Day = pdate - self.epoch
        N = self.fixangle((360 / 365.2422) * Day)
        M = self.fixangle(N + self.elonge - self.elongp)
        Ec = self.kepler(M, self.eccent)
        Ec = math.sqrt((1+self.eccent) / (1-self.eccent)) * math.tan(Ec/2)
        Ec = 2 * self.todeg(math.atan(Ec))
        Lambdasun = self.fixangle(Ec + self.elongp)

        ml = self.fixangle(13.1763966 * Day + self.mmlong)

        MM = self.fixangle(ml - 0.1114041 * Day - self.mmlongp)

        Ev = 1.2739 * math.sin(self.torad(2 * (ml - Lambdasun) - MM))

        Ae = 0.1858 * math.sin(self.torad(M))

        A3 = 0.37 * math.sin(self.torad(M))

        MmP = MM + Ev - Ae - A3

        mEc = 6.2886 * math.sin(self.torad(MmP))

        A4 = 0.214 * math.sin(self.torad(2 * MmP))

        lP = ml + Ev + mEc - Ae + A4

        V = 0.6583 * math.sin(self.torad(2 * (lP - Lambdasun)))

        lPP = lP + V

        MoonAge = lPP - Lambdasun

        phase = self.fixangle(MoonAge) / 360.0

        if phase < 0.0:
            phase = phase + 1.0

        return phase

    def is_quarter(self, prev, curr, next):

        """Given the moon phases of three successive days, decide if the centre day (curr) is
        on a quarter moon, and which one it is.

        Returns MOON_NM, MOON_1Q, MOON_FM, MOON_3Q or MOON_OTHER."""
        
        if curr < prev:
            curr = curr + 1
        if next < prev:
            next = next + 1

        for quarter in (1,2,3,4):
            phase = quarter / 4.0
            if (prev < phase) and (next > phase):
                diff = math.fabs(curr-phase)
                if (diff < (phase - prev)) and (diff < (next - phase)):
                    # This return value must correspond with MOON_1Q etc
                    return quarter % 4
        return self.MOON_OTHER
               

if __name__=='__main__':
    mc = MoonCalc()
    y = atoi(sys.argv[1])
    m = atoi(sys.argv[2])
    d = atoi(sys.argv[3])
    phase = mc.calc_phase(y, m, d)
    quarter = mc.is_quarter(mc.calc_phase(y,m,d-1), phase, mc.calc_phase(y,m,d+1))
    print "day = %04d-%02d-%02d, phase = %6.5f, quarter = %d" % \
          (y,m,d, phase, quarter)


# This section is for emacs.
# Local variables: ***
# mode:python ***
# py-indent-offset:4 ***
# fill-column:95 ***
# End: ***
