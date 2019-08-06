import pytest
import mock
from textwrap import dedent
from elasticsearch.exceptions import ConnectionError
from elasticsearch import Elasticsearch, RequestsHttpConnection

from utils import estest, load_data, run, get_connection, TEST_INDEX_NAME

from escli.executor import ESExecutor

INVALID_ENDPOINT = "http://invalid:9200"
OPEN_DISTRO_ENDPOINT = "https://opedistro:9200"
AES_ENDPOINT = "https://fake.es.amazonaws.com"
AUTH = ("username", "password")


@estest
def test_conn_and_query(connection):
    doc = {"a": "aws"}

    load_data(connection, doc)

    assert run(connection, "select * from %s" % TEST_INDEX_NAME) == dedent(
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
    doc = {"a": "aws"}

    load_data(connection, doc)
    expected = {
        "reason": "Invalid SQL query",
        "details": "no such index [non-existed]",
        "type": "IndexNotFoundException",
    }

    with mock.patch("escli.executor.click.secho") as mock_secho:
        run(connection, "select * from non-existed")

    mock_secho.assert_called_with(message=str(expected), fg="red")


def test_connection_fail():
    err_message = "Can not connect to endpoint %s" % INVALID_ENDPOINT
    test_executor = ESExecutor(endpoint=INVALID_ENDPOINT)

    with mock.patch("sys.exit") as mock_sys_exit, mock.patch(
        "escli.executor.click.secho"
    ) as mock_secho:
        test_executor.set_connection()

    mock_sys_exit.assert_called()
    mock_secho.assert_called_with(message=err_message, fg="red")


def side_effect_set_connection(is_reconnected):
    if is_reconnected:
        pass
    else:
        return ConnectionError()


def test_connection_lost():
    test_esexecutor = ESExecutor(endpoint=INVALID_ENDPOINT)

    with mock.patch("escli.executor.click.secho") as mock_secho, mock.patch.object(
        test_esexecutor, "set_connection"
    ) as mock_set_connection:
        mock_set_connection.side_effect = side_effect_set_connection(
            is_reconnected=True
        )
        test_esexecutor.handle_server_close_connection()

        mock_secho.assert_any_call("Reconnecting...", fg="green")
        mock_secho.assert_any_call("Reconnected! Please run query again", fg="green")

        mock_set_connection.side_effect = side_effect_set_connection(
            is_reconnected=False
        )
        test_esexecutor.handle_server_close_connection()

        mock_secho.assert_any_call("Reconnecting...", fg="green")
        mock_secho.assert_any_call(
            "Connection Failed. Check your ES is running and then come back", fg="red"
        )


def test_reconnection_exception():
    test_executor = ESExecutor(endpoint=INVALID_ENDPOINT)

    with pytest.raises(ConnectionError) as error:
        assert test_executor.set_connection(True)


def test_other_connection():
    od_test_executor = ESExecutor(endpoint=OPEN_DISTRO_ENDPOINT, http_auth=AUTH)
    aes_test_executor = ESExecutor(endpoint=AES_ENDPOINT)

    with mock.patch.object(
        od_test_executor, "get_open_distro_client"
    ) as mock_od_client:
        od_test_executor.set_connection()
        mock_od_client.assert_called()

    with mock.patch.object(aes_test_executor, "get_aes_client") as mock_aes_client:
        aes_test_executor.set_connection()
        mock_aes_client.assert_called()


def test_get_od_client():
    od_test_executor = ESExecutor(endpoint=OPEN_DISTRO_ENDPOINT, http_auth=AUTH)

    with mock.patch.object(Elasticsearch, "__init__", return_value=None) as mock_es:
        od_test_executor.get_open_distro_client()

        mock_es.assert_called_with(
            [OPEN_DISTRO_ENDPOINT],
            http_auth=AUTH,
            verify_certs=False,
            ssl_context=od_test_executor.ssl_context,
        )


def test_get_aes_client():
    aes_test_executor = ESExecutor(endpoint=AES_ENDPOINT)

    with mock.patch.object(Elasticsearch, "__init__", return_value=None) as mock_es:
        aes_test_executor.get_aes_client()

        mock_es.assert_called_with(
            hosts=[{"host": str(AES_ENDPOINT), "port": 443}],
            http_auth=aes_test_executor.aws_auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
        )
