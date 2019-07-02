# coding=utf-8
from __future__ import unicode_literals, print_function
import os
import platform
import mock

import pytest

from escli.main import (
    ESCli,
    format_output,
    COLOR_CODE_REGEX,
    OutputSettings
)


def test_format_output():
    settings = OutputSettings(table_format="psql")
    data = {
        "schema": [
            {
                "name": "name",
                "type": "text"
            },
            {
                "name": "age",
                "type": "long"
            }
        ],
        "total": 2,
        "datarows": [
            [
                "Tim",
                24
            ]
        ],
        "size": 1,
        "status": 200
    }
    results = format_output(
        data, settings
    )

    expected = [
        "+--------+-------+",
        "| name   | age   |",
        "|--------+-------|",
        "| Tim    | 24    |",
        "+--------+-------+",
    ]
    assert list(results) == expected
