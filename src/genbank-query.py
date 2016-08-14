# coding=utf-8
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import argparse

from simons_spark_genbank import nhci, util

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
    csv_handler = util.csv_file_sink(args.output_file,
                                     header=('matched_sequence', 'start_pos', 'end_pos'))
    if args.stream:
        nhci.query_async(args.database, args.id, args.tag_regexp, args.regexp,
                         output_handlers=(stdout_handler, csv_handler),
                         stream_chunk_size=args.stream_chunk_size)
    else:
        out = nhci.query(args.database, args.id, args.tag_regexp, args.regexp)
        for row in out:
            for handler in (stdout_handler, csv_handler):
                handler.send(row)
