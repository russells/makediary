
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
      version='1.0',
      license="GPL",
      packages=['cdp'],
      scripts=['cdp/makediary.py'])
