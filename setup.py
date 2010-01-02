# Setup for makediary.


from distutils.core import setup

# This version number must match the version number in VERSION.

_makeDiaryVersion = '0.2.96'

from glob import glob


def globEPSFiles(base):
    files = []
    for f in glob('eps/%s/%s*.tex' % (base, base)):
        files.append(f)
    for f in glob('eps/%s/%s*.eps' % (base, base)):
        files.append(f)
    return files


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
      data_files=[('share/man/man1', ['man/makediary.1.gz']),
                  ('lib/site-python/makediary/eps/vi',
                   globEPSFiles('vi')
                  ),
                  ('lib/site-python/makediary/eps/unix',
                   ['eps/unix/unix.tex',
                    'eps/unix/unix.eps',
		   ]
		  ),
                  ('lib/site-python/makediary/eps/sh',
                   ['eps/sh/sh.tex',
                    'eps/sh/sh.eps',
                   ]
                  ),
                  ('lib/site-python/makediary/eps/units',
                   ['eps/units/units.tex',
                    'eps/units/units.eps',
                   ]
                  ),
                  ('lib/site-python/makediary/eps/sed',
                   globEPSFiles('sed')
                  ),
                 ])

