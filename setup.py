# Setup for makediary.


# $Id: setup.py 75 2003-07-17 08:31:34Z  $

from distutils.core import setup

# This version number must match the version number in VERSION.

_makeDiaryVersion = '0.1.2pre'

setup(name='makediary',
      description="""Make printed diaries.""",

      long_description="""
      Print diaries on a range of paper sizes.  The diaries can
      include a cover page, various types of front matter pages
      (planners, calendars, addresses etc), and a year's worth of day
      pages.""",

      author='Russell Steicke',
      author_email='russells@adelie.cx',
      url='http://6u.adelie.cx/makediary',
      version=_makeDiaryVersion,
      license="GPL",
      packages=['makediary'],
      scripts=['bin/makediary'],
      data_files=[('man/man1', ['man/makediary.1'])])
