#!/bin/sh

set -e -x

sudo rm -rf cdp-1.0
rm -f MANIFEST

python2.2 setup.py sdist --formats=bztar
tar xvfj dist/cdp-1.0.tar.bz2
cd cdp-1.0
sudo python2.2 setup.py install

