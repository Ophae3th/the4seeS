# coding=utf-8

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
    args = parser.parse_args()

    out = nhci.query(args.database, args.id, args.tag_regexp, args.regexp, stream=args.stream)
    if out:
        with open(args.output_file, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(('matched_sequence', 'start_pos', 'end_pos'))
            for row in out:
                # matched_sequence, start_pos, end_pos = row
                writer.writerow(row)
                print("\t".join(map(str, row)))
