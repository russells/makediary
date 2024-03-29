#!/usr/bin/env python3

# Maintain a dictionary of paper sizes.


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
    "filofax": ( 96.0, 172.0          ),
    "letter" : ( 215.9,     279.4     ),
    "half-letter" : ( 139.7, 215.9    ),
    }

def getPaperSize(name):
    """Return a tuple (width,height), given a size name."""
    try:
        return _paperSizes[name]
    except KeyError:
        return None

def getPaperSizeNames():

    """Return a list of the names of all the paper sizes."""

    # FIXME - there is probably a more pythonic way of taking this copy.

    sizes = list(_paperSizes.keys())
    sizes_copy = [ ]
    for size in sizes:
        sizes_copy.append(size)
    sizes_copy.sort()
    return sizes_copy


# This section is for emacs.
# Local variables: ***
# mode:python ***
# py-indent-offset:4 ***
# fill-column:95 ***
# End: ***
