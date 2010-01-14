# Setup for makediary.


from distutils.core import setup

# This version number must match the version number in VERSION.

_makeDiaryVersion = '0.2.96'

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
      package_dir={'makediary' : 'makediary' },
      package_data={'makediary': ['eps/*/*.tex', 'eps/*/*.eps'] },
      scripts=['bin/makediary'],
      data_files=[('share/man/man1', ['man/makediary.1.gz']) ])

