import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

text_type = unicode if PY2 else str


def unicode2utf8(arg):
    """
    Only in Python 2. It needs manual conversion from unicode to utf-8
    """

    if PY2 and isinstance(arg, unicode):
        return arg.encode("utf-8")
    return arg
