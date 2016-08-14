# coding=utf-8
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import csv
import sys


def coroutine(func):
    def wrapped(*args, **kwargs):
        routine = func(*args, **kwargs)
        routine.next()
        return routine

    return wrapped


@coroutine
def stdout_sink(formatter):
    while True:
        value = (yield)
        sys.stdout.write(formatter(value))


@coroutine
def csv_file_sink(filepath, header=None):
    with open(filepath, 'w') as f:
        writer = csv.writer(f)
        if header:
            writer.writerow(header)
        while True:
            values = (yield)
            writer.writerow(values)
