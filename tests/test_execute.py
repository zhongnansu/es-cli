import pytest

from textwrap import dedent

from tests.utils import (
    estest,
    load_data,
    load_file,
    create_index,
    delete_index,
    run,
    TEST_INDEX_NAME,
)


@estest
def test_query(connection):

    doc = {
        'a': 'aws'
    }

    load_data(connection, doc)

    assert run(connection, f'select * from {TEST_INDEX_NAME}') == dedent(
        """\
        +-----+
        | a   |
        |-----|
        | aws |
        +-----+"""
    )


