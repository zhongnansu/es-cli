import pytest
import mock
from textwrap import dedent

from tests.utils import (
    estest,
    load_data,
    load_file,
    create_index,
    delete_index,
    close_connection,
    run,
    TEST_INDEX_NAME,
)

from escli.executor import ESExecute, ConnectionFailException


@estest
def test_conn_and_query(connection):

    doc = {
        'a': 'aws'
    }

    load_data(connection, doc)

    assert run(connection, f'select * from {TEST_INDEX_NAME}') == dedent(
        """\
        data retrieved / total hits = 1/1
        +-----+
        | a   |
        |-----|
        | aws |
        +-----+"""
    )


@estest
def test_nonexistent_index(connection):

    doc = {
        'a': 'aws'
    }

    load_data(connection, doc)
    expected = {'reason': 'Invalid SQL query', 'details': 'no such index [non-existed]', 'type': 'IndexNotFoundException'}

    with mock.patch('escli.executor.click.echo') as mock_echo:
        run(connection, f'select * from non-existed')

    mock_echo.assert_called_with(
        expected
    )


def test_connection_fail_exception():
    """test that exception is raised for invalid endpoint"""

    invalid_endpoint = 'http://invalid:9200'

    with pytest.raises(ConnectionFailException) as e:
        assert ESExecute(endpoint=invalid_endpoint)

    assert str(e.value) == f'Can not connect to endpoint: {invalid_endpoint}'












