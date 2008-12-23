# Setup for makediary.


from distutils.core import setup

# This version number must match the version number in VERSION.

_makeDiaryVersion = '0.2.3'

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
                  ('lib/site-python/makediary/eps/vi-ref',
                   ['eps/vi-ref/vi-ref.tex',
                    'eps/vi-ref/vi-ref.eps',
                    'eps/vi-ref/vi-back.tex',
                    'eps/vi-ref/vi-back.eps',
                   ]
                  ),
                  ('lib/site-python/makediary/eps/units-ref',
                   ['eps/units-ref/units-ref.tex',
                    'eps/units-ref/units-ref.eps',
                   ]
                  ),
                  ('lib/site-python/makediary/eps',
                   ['eps/unix-ref.tex',
                    'eps/unix-ref.eps',
                    'eps/sh-ref.tex',
                    'eps/sh-ref.eps',
                   ]
                  )
                 ])

