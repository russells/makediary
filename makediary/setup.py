# Setup for cdp.


# $Id: setup.py 16 2002-12-22 16:46:53Z anonymous $

from distutils.core import setup

setup(name='cdp',
      description="""Make printed diaries.""",

      long_description="""
      Print diaries on a range of paper sizes.  The diaries can
      include a cover page, various types of front matter pages
      (planners, calendars, addresses etc), and a year's worth of day
      pages.""",

      author='Russell Steicke',
      author_email='russells@adelie.cx',
      url='http://adelie.cx/cdp',
      version='0.1',
      license="GPL",
      packages=['cdp'],
      scripts=['makediary'],
      data_files=[('man/man1', ['man/makediary.1'])])
