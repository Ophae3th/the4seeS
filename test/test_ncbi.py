# coding=utf-8
"""
To be run one way or another with 'nose', http://nose.readthedocs.io/en/latest/
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))
from simons_spark_genbank import ncbi
from simons_spark_genbank.errors import NCBIWebRequestError, RegexpError

from nose.tools import raises


@raises(NCBIWebRequestError)
def test_bad_db():
    ncbi.query("foobar", 30271926, r"^TSeq_sequence$", ".*")


@raises(NCBIWebRequestError)
def test_bad_id_format():
    ncbi.query("nucleotide", "foobar", r"^TSeq_sequence$", ".*")


@raises(NCBIWebRequestError)
def test_invalid_id():
    ncbi.query("nucleotide", 10000000000000000000101, r"^TSeq_sequence$", ".*")


@raises(NCBIWebRequestError)
def test_empty_id():
    ncbi.query("nucleotide", 1, r"^TSeq_sequence$", ".*")


@raises(RegexpError)
def test_bad_tagre():
    ncbi.query("nucleotide", 30271926, r"[", r".*")


@raises(RegexpError)
def test_bad_contentre():
    ncbi.query("nucleotide", 30271926, r".*", r"[")

