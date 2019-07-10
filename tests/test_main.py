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
from collections import namedtuple


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
        "total": 1,
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
        "data retrieved / total hits = 1/1",
        "+--------+-------+",
        "| name   | age   |",
        "|--------+-------|",
        "| Tim    | 24    |",
        "+--------+-------+",
    ]
    assert list(results) == expected


def test_format_output_vertical():
    settings = OutputSettings(table_format="psql", max_width=1)
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
        "total": 1,
        "datarows": [
            [
                "Tim",
                24
            ]
        ],
        "size": 1,
        "status": 200
    }

    expanded = [
        "data retrieved / total hits = 1/1",
        "-[ RECORD 1 ]-------------------------",
        "name | Tim",
        "age  | 24",
    ]

    with mock.patch("escli.main.click.secho") as mock_secho, mock.patch("escli.main.click.confirm") as mock_confirm:
        expanded_results = format_output(
            data, settings
        )

    mock_secho.assert_called_with(
        message="Output longer than terminal width",
        fg="red"
    )
    mock_confirm.assert_called_with(
        "Do you want to display data vertically for better visual effect?"
    )

    assert "\n".join(expanded_results) == "\n".join(expanded)


@pytest.fixture
def pset_pager_mocks():
    cli = ESCli()
    with mock.patch("escli.main.click.echo") as mock_echo, mock.patch(
        "escli.main.click.echo_via_pager"
    ) as mock_echo_via_pager, mock.patch.object(cli, "prompt_app") as mock_app:

        yield cli, mock_echo, mock_echo_via_pager, mock_app


termsize = namedtuple("termsize", ["rows", "columns"])
test_line = "-" * 10
test_data = [
    (10, 10, "\n".join([test_line] * 7)),
    (10, 10, "\n".join([test_line] * 6)),
    (10, 10, "\n".join([test_line] * 5)),
    (10, 10, "-" * 11),
    (10, 10, "-" * 10),
    (10, 10, "-" * 9),
]


use_pager_when_on = [True, True, False, True, False, False]

test_ids = [
    "Output longer than terminal height",
    "Output equal to terminal height",
    "Output shorter than terminal height",
    "Output longer than terminal width",
    "Output equal to terminal width",
    "Output shorter than terminal width",
]

pager_test_data = [l + (r,) for l, r in zip(test_data, use_pager_when_on)]


@pytest.mark.parametrize(
    "term_height,term_width,text,use_pager", pager_test_data, ids=test_ids
)
def test_pager(term_height, term_width, text, use_pager, pset_pager_mocks):
    cli, mock_echo, mock_echo_via_pager, mock_cli = pset_pager_mocks
    mock_cli.output.get_size.return_value = termsize(
        rows=term_height, columns=term_width
    )

    cli.echo_via_pager(text)

    if use_pager:
        mock_echo.assert_not_called()
        mock_echo_via_pager.assert_called()
    else:
        mock_echo_via_pager.assert_not_called()
        mock_echo.assert_called()


@pytest.mark.parametrize(
    "text,expected_length",
    [
        (
            "22200K .......\u001b[0m\u001b[91m... .......... ...\u001b[0m\u001b[91m.\u001b[0m\u001b[91m...... .........\u001b[0m\u001b[91m.\u001b[0m\u001b[91m \u001b[0m\u001b[91m.\u001b[0m\u001b[91m.\u001b[0m\u001b[91m.\u001b[0m\u001b[91m.\u001b[0m\u001b[91m...... 50% 28.6K 12m55s",
            78,
        ),
        ("=\u001b[m=", 2),
        ("-\u001b]23\u0007-", 2),
    ],
)
def test_color_pattern(text, expected_length, pset_pager_mocks):
    cli = pset_pager_mocks[0]
    assert len(COLOR_CODE_REGEX.sub("", text)) == expected_length




