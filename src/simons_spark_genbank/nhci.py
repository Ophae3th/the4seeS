# coding=utf-8
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from functools import partial
import re
import requests
import sys
from xml import sax

from .util import tsv_sink
from .xmltools import XMLStreamTransformer, BufferHandler

NHCI_URL_TEMPLATE = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db={db}&id={id}&retmode=xml&rettype=fasta"


def nhci_url(db, dbid):
    return NHCI_URL_TEMPLATE.format(db=db, id=dbid)


def xml_re_filter(tag_regexp, content_regexp, tag, content):
    if not tag_regexp.search(tag):
        return None

    results = []
    content_matches = content_regexp.finditer(content)
    for match in content_matches:
        # Append the hit, start, and end positions.
        # Add 1 to the first offset of the matching string.
        # Bioinformatics convention is to index sequence offsets starting at 1.
        # Do not add one to the second offset, as the specification requires
        # that both indices be inclusive, in contrast to python convention, so
        # this noop is actually equivalent to "plus one, minus one".
        results.append((match.group(0), match.start(0) + 1, match.end(0)))

    return results


def prepare_filter(tag_regexp, content_regexp, tag, content):
    return xml_re_filter(re.compile(tag_regexp),
                         re.compile(r"(" + content_regexp + r")"),
                         tag,
                         content)


def query_async(db, dbid, tag_regexp, content_regexp, output_streams=None, stream_chunk_size=8192):
    if output_streams is None:
        output_streams = [tsv_sink(sys.stdout)]
    else:
        output_streams = map(tsv_sink, output_streams)
    transformer = partial(prepare_filter, tag_regexp, content_regexp)

    input_stream = requests.get(nhci_url(db, dbid), stream=True)
    transformer = XMLStreamTransformer(input_stream.iter_content(chunk_size=stream_chunk_size),
                                       transformer, output_streams)
    transformer.run()


def query(db, dbid, tag_regexp, content_regexp):
    transformer = partial(prepare_filter, tag_regexp, content_regexp)
    xml = requests.get(nhci_url(db, dbid)).content
    handler = BufferHandler(transformer)
    sax.parseString(xml, handler)

    return handler.buffer

