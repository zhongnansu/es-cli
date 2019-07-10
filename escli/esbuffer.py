from __future__ import unicode_literals

from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.filters import Condition
from prompt_toolkit.application import get_app


def es_is_multiline(escli):
    @Condition
    def cond():
        doc = get_app().layout.get_buffer_by_name(DEFAULT_BUFFER).document

        if not escli.multi_line:
            return False
        if escli.multiline_mode == "safe":
            return True
        else:
            return not _multiline_exception(doc.text)

    return cond


def _is_complete(sql):
    # A complete command is an sql statement that ends with a semicolon
    return sql.endswith(";")


def _multiline_exception(text):
    text = text.strip()
    return _is_complete(text)
