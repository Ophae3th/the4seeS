# coding=utf-8
"""
A command line query tool for Genbank sequences.
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import logging
import os
import sys

from simons_spark_genbank import ncbi, util
from simons_spark_genbank.errors import NCBIWebRequestError, RegexpError


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--database", required=True)
    parser.add_argument("-i", "--id", required=True)
    parser.add_argument("-r", "--regexp", required=True)
    parser.add_argument("-o", "--output-file", required=True, help="Name of CSV file to be output.")
    parser.add_argument("-tr", "--tag-regexp", default=r"^TSeq_sequence$")
    parser.add_argument("--stream", action="store_true", default=False)
    parser.add_argument("--stream-chunk-size", default=8192)
    args = parser.parse_args()

    stdout_handler = util.stdout_sink(lambda vals: "\t".join(map(unicode, vals)) + "\n")
    try:
        csv_handler = util.csv_file_sink(args.output_file,
                                         header=('matched_sequence', 'start_pos', 'end_pos'))
    except IOError as e:
        logging.fatal(e)
        if not os.path.exists(os.path.join(args.output_file, os.pardir)):
            logging.fatal("Please create all directories in path '{0}'. "
                          "The file will be created for you.".format(args.output_file))
        sys.exit(1)

    try:
        if args.stream:
            ncbi.query_async(args.database, args.id, args.tag_regexp, args.regexp,
                             output_handlers=(stdout_handler, csv_handler),
                             stream_chunk_size=args.stream_chunk_size)
        else:
            out = ncbi.query(args.database, args.id, args.tag_regexp, args.regexp)
            for row in out:
                for handler in (stdout_handler, csv_handler):
                    handler.send(row)
    except NCBIWebRequestError as e:
        logging.fatal(e)
        sys.exit(1)
    except RegexpError as e:
        logging.fatal(e)
        sys.exit(1)
