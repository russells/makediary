#!/usr/bin/python

"""A package for printing book style diaries."""


__version__ = '0.3.0'

from DiaryInfo import DiaryInfo
from BasicPostscriptPage import BasicPostscriptPage

__all__ = ['makediary',
           'BasicPostscriptPage',
           'DiaryInfo',
           'DotCalendar',
           'Moon',
           'PaperSize']
