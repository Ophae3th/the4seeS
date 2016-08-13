# coding=utf-8
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from xml import sax

from .util import coroutine


class BufferHandler(sax.handler.ContentHandler):
    def __init__(self, filter_func):
        sax.handler.ContentHandler.__init__(self)   # Base class is old-style
        self._tag_name = None
        self._filter_func = filter_func
        self._buffer = []

    def startElement(self, name, attrs):
        self._tag_name = name

    def characters(self, content):
        out = self._filter_func(self._tag_name, content)
        if out:
            self._buffer.extend(out)

    @property
    def buffer(self):
        return self._buffer


class StreamHandler(sax.handler.ContentHandler):
    def __init__(self, filter_func, output_streams):
        sax.handler.ContentHandler.__init__(self)   # Base class is old-style
        self._tag_name = None
        self._output_streams = output_streams
        self._distributor = self._stream_sink(filter_func)

    def startElement(self, name, attrs):
        self._tag_name = name

    def characters(self, content):
        self._distributor.send(content)

    @coroutine
    def _stream_sink(self, filter_func):
        while True:
            content = (yield)
            if content:
                out = filter_func(self._tag_name, content)
                if out:
                    for outstream in self._output_streams:
                        for match in out:
                            outstream.send(match)


class XMLStreamTransformer(object):
    def __init__(self, instream, extractor, outstreams):
        self._stream = instream
        self._parser = sax.make_parser(['xml.sax.IncrementalParser'])

        self._transformer = StreamHandler(extractor, outstreams)
        self._parser.setContentHandler(self._transformer)

    def run(self):
        for item in self._stream:
            self._parser.feed(item)