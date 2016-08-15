# coding=utf-8
"""
Custom exceptions to make errors more meaningful and
limit possible exceptions that clients must handle.
"""


class GenbankException(Exception):
    pass


class NCBIWebRequestError(GenbankException):
    pass


class RegexpError(GenbankException):
    pass