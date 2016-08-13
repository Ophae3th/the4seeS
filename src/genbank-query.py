# coding=utf-8
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import csv

from simons_spark_genbank import nhci

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

    if args.stream:
        nhci.query_async(args.database, args.id, args.tag_regexp, args.regexp,
                         stream_chunk_size=args.stream_chunk_size)
    else:
        out = nhci.query(args.database, args.id, args.tag_regexp, args.regexp)
        with open(args.output_file, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(('matched_sequence', 'start_pos', 'end_pos'))
            for row in out:
                # matched_sequence, start_pos, end_pos = row
                writer.writerow(row)
                print("\t".join(map(str, row)))
