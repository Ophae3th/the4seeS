# coding=utf-8
"""
Utilities and helper functions.
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import csv
import sys


class Counter(object):
    """
    Simple as it looks. Avoid using collections.Counter in case py2.6 compatibility needed.
    """
    def __init__(self):
        self._count = 0

    def count(self, val):
        self._count += val

    @property
    def value(self):
        return self._count


def coroutine(func):
    """
    Ensures generator execution is advanced to a state where
     it can accept values via .send()
    :param func: a generator
    :return: a generator
    """
    def wrapped(*args, **kwargs):
        routine = func(*args, **kwargs)
        routine.next()
        return routine

    return wrapped


@coroutine
def stdout_sink(formatter):
    """
    A generator which applies a formatter function to an object
    before writing it to stdout.
    :param formatter: a function of the values expected to be passed
        to this generator via .send()
    :return: None
    """
    while True:
        value = (yield)
        sys.stdout.write(formatter(value))


@coroutine
def csv_file_sink(filepath, header=None):
    """
    A generator which writes values to a CSV file.
    :param filepath: the filesystem path to the file to be written
    :param header: an iterable of column names
    :return: None
    """
    with open(filepath, 'w') as f:
        writer = csv.writer(f)
        if header:
            writer.writerow(header)
        while True:
            values = (yield)
            writer.writerow(values)
