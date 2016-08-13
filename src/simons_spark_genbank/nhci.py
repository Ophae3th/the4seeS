# coding=utf-8

import re
import requests
import sys
from xml import sax

NHCI_URL_TEMPLATE = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db={db}&id={id}&retmode=xml&rettype=fasta"

output_streams = [sys.stdout]


def nhci_url(db, dbid):
    return NHCI_URL_TEMPLATE.format(db=db, id=dbid)


def coroutine(func):
    def wrapped(*args, **kwargs):
        routine = func(*args, **kwargs)
        routine.next()
        return routine

    return wrapped


@coroutine
def make_sink(stream):
    while True:
        value = (yield)
        stream.write(value[0])


class BufferHandler(sax.handler.ContentHandler):
    def __init__(self, filter_func):
        sax.handler.ContentHandler.__init__(self)
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
    def __init__(self, filter_func, outstreams):
        sax.handler.ContentHandler.__init__(self)   # Base class is old-style
        self._tag_name = None
        self._outstreams = outstreams
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
                    for outstream in self._outstreams:
                        outstream.send(out)


class XMLStreamTransformer(object):
    def __init__(self, instream, extractor, outstreams):
        self._stream = instream
        self._parser = sax.make_parser(['xml.sax.IncrementalParser'])

        self._transformer = StreamHandler(extractor, outstreams)
        self._parser.setContentHandler(self._transformer)

    def run(self):
        for item in self._stream:
            self._parser.feed(item)


def xml_re_filter(tag_regexp, content_regexp, tag, content):
    if not tag_regexp.search(tag):
        return None

    results = []
    content_matches = content_regexp.finditer(content)
    for match in content_matches:
        # Add 1 to the offsets of the matching string.
        # Bioinformatics convention is to index sequence offsets starting at 1
        indices = [i + 1 for i in match.span(0)]
        results.append((match.group(0), indices[0], indices[1]))

    return results


def query(db, dbid, tag_regexp, content_regexp, stream=False):

    def transform_func(tag, content):
        return xml_re_filter(re.compile(tag_regexp),
                             re.compile(r"(" + content_regexp + r")", re.UNICODE),
                             tag,
                             content)

    if stream:
        instream = requests.get(nhci_url(db, dbid), stream=True)
        outstreams = map(make_sink, output_streams)
        transformer = XMLStreamTransformer(instream.iter_content(chunk_size=4096),
                                           transform_func, outstreams)
        transformer.run()
    else:
        xml = requests.get(nhci_url(db, dbid)).content
        handler = BufferHandler(transform_func)
        sax.parseString(xml, handler)

        return handler.buffer

