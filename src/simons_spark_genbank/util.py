# coding=utf-8
"""
Utilities and helper functions.
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import curses
import csv
import sys

from collections import defaultdict


class Accumulator(object):
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
def aggregating_curses_sink():
    """
    A generator which both aggregates (counts) sequence match input
    and uses the curses library to provide live updates of sequence
    counts for use in stream processing very large data.

    The aggregation should probably be factored out of this,
    leaving the sole responsibility here the display logic, but
    this application is already pushing overengineered.

    :return: None
    """
    try:
        stdscr = curses.initscr()
        # Turn off echoing of keys, and enter cbreak mode,
        # where no buffering is performed on keyboard input
        curses.noecho()
        curses.cbreak()
        # In keypad mode, escape sequences for special keys
        # (like the cursor keys) will be interpreted and
        # a special value like curses.KEY_LEFT will be returned
        stdscr.keypad(1)

        height, width = stdscr.getmaxyx()

        pad_height = int(height / 2)
        pad = curses.newpad(pad_height, width);
        pad.scrollok(True)
        pad.nodelay(1)
        pad.refresh(0, 0, 0, 0, height, width)

        pad.addstr(0, 0, "Counting sequence matches.\n")
        pad.addstr(1, 0, "\n")
        pad.addstr(2, 0, "Seq\tCount\n", curses.A_STANDOUT)
        matches = defaultdict(int)
        while True:
            values = (yield)
            sequence = values[0]
            matches[sequence] += 1
            # Super inefficient to resort this frequently if the list becomes
            # very large, but we get away with this for the most likely case
            # where unique sequence matches will be few.
            sorted_keys = sorted(matches, key=matches.__getitem__, reverse=True)
            for i, k in enumerate(sorted_keys):
                pad.addstr(i + 3, 0, "{0}\t{1}\n".format(k, matches[k]))
            pad.addstr(i + 4, 0, "\n")
            pad.addstr(i + 5, 0, "Press Ctrl-C or 'q' to exit.\n")
            pad.refresh(0, 0, 0, 0, height, width)

            # Must be non-blocking; pad.nodelay(1) set earlier.
            ch = pad.getch()
            if ch != curses.ERR and ch < 256 and chr(ch) == 'q':
                break

    finally:
        # Always clean up.
        # Write the current pad contents to stdout as usual after
        # the window has been closed so that final output will remain visible.
        mypad_contents = []
        for i in range(pad_height):
            mypad_contents.append(pad.instr(i, 0))
        stdscr.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
        # Exclude "counting sequence matches" header from final frame.
        for line in mypad_contents[1:]:
            sys.stdout.write(line + "\n")


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
