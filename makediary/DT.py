#!/usr/bin/env python3
# Date/time class for makediary.

import datetime

class DT(datetime.datetime):

    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6

    # This is 9999 in the current implementation.  It needs to be a year that we won't generate
    # a diary for, and also an acceptable year for the constructor.
    ANYYEAR = datetime.MAXYEAR

    def is_leapyear(self):
        y = self.year
        return ((y%4) == 0) and (((y%400) == 0) or ((y%100) != 0))

    def jday(self):
        return self.timetuple().tm_yday

    def day_of_week(self):
        return self.timetuple().tm_wday

    def days_in_month(self):
        if self.month in (1, 3, 5, 7, 8, 10, 12):
            return 31
        elif self.month == 2:
            if self.is_leapyear():
                return 29
            else:
                return 28
        else:
            return 30

    @classmethod
    def delta(cls, n):
        return datetime.timedelta(n)
