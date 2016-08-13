# coding=utf-8
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals


def coroutine(func):
    def wrapped(*args, **kwargs):
        routine = func(*args, **kwargs)
        routine.next()
        return routine

    return wrapped


@coroutine
def tsv_sink(stream):
    while True:
        values = (yield)
        stream.write("\t".join(map(unicode, values)) + "\n")


@coroutine
def file_sync(writer):
    while True:
        values = (yield)
        writer.writerow(values)