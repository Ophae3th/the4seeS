# coding=utf-8
"""
Functions for use in querying NCBI sequence data.
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import sre_constants
from functools import partial
import re
import requests
from xml import sax
from xml.etree import ElementTree

from .errors import NCBIWebRequestError, RegexpError
from .util import stdout_sink, Counter
from .xmltools import XMLStreamTransformer, BufferHandler

NCBI_URL_TEMPLATE = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db={db}&id={id}&retmode=xml&rettype=fasta"


def ncbi_url(db, dbid):
    """
    Gets an NCBI query URL
    :param db: a database identifier
    :param dbid: an ID key within the database
    :return: an NCBI query URL
    """
    return NCBI_URL_TEMPLATE.format(db=db, id=dbid)


def prepare_filter(tag_pattern, content_pattern, offset_counter, tag, content):
    """
    Obtain a filter function for content search.
    :param tag_regexp: a string pattern to match XML tags against
    :param content_regexp: a string pattern to match content against
    :param offset_counter: a .util.Counter object to track the position in the stream
    :param tag: a specific string tag to be matched
    :param content: a specific string of content to be matched
    :return: a function
    """
    try:
        tag_regexp = re.compile(tag_pattern)
        content_regexp = re.compile(r"(" + content_pattern + r")")
    except sre_constants.error as e:
        raise RegexpError("Invalid python regexp: {0}".format(e.message))
    def xml_re_filter(tag, content):
        """
        Finds groups matching a regexp within a string, and the offsets of those groups
            in the content stream.
        :param tag: the specific string tag name being matched against tag_regexp
        :param content: the specific string content being scanned with content_regexp
        :return: a list of tuples, where each tuple is a (sequence, 1st offset, 2nd offset)
        """
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
            results.append((match.group(0),
                            match.start(0) + 1 + offset_counter.value,
                            match.end(0) + offset_counter.value))

        offset_counter.count(len(content))

        return results

    return xml_re_filter(tag, content)


def make_web_request(db, dbid, stream):
    """
    Executes an NCBI web request, with error checking.
    :param db: the name of an NCBI database
    :param dbid: an identifier of a record within the database
    :param stream: a boolean indicating whether to stream the response
    :return: a requests response object
    """
    res = requests.get(ncbi_url(db, dbid), stream=stream)
    if res.status_code == 200:
        # NCBI will return XML containing an error tag, but 200 status code in cases
        # where the ID is not in the database.
        # Use a heuristic to decide whether to search for this. A better way would be to
        # look for error tags during normal parsing.
        if not stream and len(res.content) < 1024:     # Content-Length header not always available
            parsed = ElementTree.fromstring(res.content)
            err = parsed.find("Error")
            if err is not None:
                raise NCBIWebRequestError("Error in NCBI response: {0}".format(err.text))
            else:
                seq = parsed.find("TSeq_sequence")
                if not seq or (seq and not seq.text):
                    raise NCBIWebRequestError("No sequence data returned by NCBI for this DB and ID")
    else:
        errtag = ElementTree.fromstring(res.content).findall("ERROR")
        if errtag:
            ncbierr = "Message: {0}".format(errtag[0].text)
        else:
            ncbierr = ""
        exc = NCBIWebRequestError("Received {0} HTTP status code from NCBI. "
                                  "{1}".format(res.status_code, ncbierr))
        raise exc

    return res


def query_async(db, dbid, tag_regexp, content_regexp, output_handlers=None, stream_chunk_size=8192):
    """
    Execute an NCBI query whose results are returned asynchronously, via output handlers.
    :param db: an NCBI database name
    :param dbid: an identifier within the database
    :param tag_regexp: a string pattern to match XML tags against
    :param content_regexp: a string pattern to match content against
    :param output_handlers: a list of generators in which output will be sent
    :param stream_chunk_size: an integer indicating how much of the response should be searched
        with the regexp at a time.
    :return: None
    """
    if output_handlers is None:
        output_handlers = (stdout_sink(lambda vals: "\t".join(map(unicode, vals)) + "\n"),)
    transformer = partial(prepare_filter, tag_regexp, content_regexp, Counter())
    input_stream = make_web_request(db, dbid, stream=True)
    transformer = XMLStreamTransformer(input_stream.iter_content(chunk_size=stream_chunk_size),
                                       transformer, output_handlers)
    transformer.run()


def query(db, dbid, tag_regexp, content_regexp):
    """
    Execute an NCBI query.
    :param db: an NCBI database name
    :param dbid: an identifier within the database
    :param tag_regexp: a string pattern to match XML tags against
    :param content_regexp: a string pattern to match content against
    :return: a list of tuples: (matched sequence, start offset, end offset)
    """
    transformer = partial(prepare_filter, tag_regexp, content_regexp, Counter())
    res = make_web_request(db, dbid, stream=False)
    xml = res.content
    handler = BufferHandler(transformer)
    sax.parseString(xml, handler)

    return handler.buffer
