import pytest
import mock
from textwrap import dedent
from elasticsearch.exceptions import ConnectionError

from utils import (
    estest,
    load_data,
    run,
    TEST_INDEX_NAME,
)

from escli.executor import ESExecute



@estest
def test_conn_and_query(connection):

    doc = {
        'a': 'aws'
    }

    load_data(connection, doc)

    assert run(connection, 'select * from %s' % TEST_INDEX_NAME) == dedent(
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

    with mock.patch('escli.executor.click.secho') as mock_secho:
        run(connection, 'select * from non-existed')

    mock_secho.assert_called_with(
        message=str(expected),
        fg='red'
    )


def test_connection_fail_exception():
    """test that exception is raised when connect to invalid endpoint"""

    invalid_endpoint = 'http://invalid:9200'

    with pytest.raises(ConnectionError) as e:
        assert ESExecute(endpoint=invalid_endpoint)













