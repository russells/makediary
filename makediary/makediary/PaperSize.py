#!/usr/bin/python2.2

# Maintain a dictionary of paper sizes.

# $Id: PaperSize.py 48 2002-12-31 17:19:45Z anonymous $

__revision__ = """$Id: PaperSize.py 48 2002-12-31 17:19:45Z anonymous $"""


_paperSizes = {
    "a8"     : ( 52.211111, 74.083333 ),
    "a7"     : ( 74.083333, 104.775   ),
    "a6"     : ( 104.775,  148.16667  ),
    "a5"     : ( 148.1667, 209.90278  ),
    "a4"     : ( 209.90278, 297.03889 ),
    "a3"     : ( 297.03889, 420.15833 ),
    "a2"     : ( 420.15833, 594.07778 ),
    "a1"     : ( 594.07778, 841.02222 ),
    "a0"     : ( 841.02222, 1188.8611 ),
    "b5"     : ( 176.03611, 250.11944 ),
    "b5j"    : ( 182.03333, 257.175   ),
    "letter" : ( 215.9,     279.4     ),
    "half-letter" : ( 139.7, 215.9    )
    }

def getPaperSize(name):
    """Return a tuple (width,height), given a size name."""
    try:
        return _paperSizes[name]
    except KeyError:
        return None

def getPaperSizeNames():

    """Return a list of the names of all the paper sizes."""

    sizes = _paperSizes.keys()
    sizes.sort()
    return sizes


# This section is for emacs, God's Own Text Editor.
# Local variables: ***
# mode:python ***
# py-indent-offset:4 ***
# fill-column:95 ***
# End: ***
