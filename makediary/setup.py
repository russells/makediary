# Setup for makediary.


# $Id: setup.py 31 2002-12-29 05:20:26Z anonymous $

from distutils.core import setup

# This version number must match the version number in VERSION.

_makeDiaryVersion = '0.1'

setup(name='makediary',
      description="""Make printed diaries.""",

      long_description="""
      Print diaries on a range of paper sizes.  The diaries can
      include a cover page, various types of front matter pages
      (planners, calendars, addresses etc), and a year's worth of day
      pages.""",

      author='Russell Steicke',
      author_email='russells@adelie.cx',
      url='http://adelie.cx/makediary',
      version=_makeDiaryVersion,
      license="GPL",
      packages=['makediary'],
      scripts=['bin/makediary'],
      data_files=[('man/man1', ['man/makediary.1'])])