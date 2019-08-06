from elasticsearch import ConnectionError, helpers, ConnectionPool
import json
import pytest

from escli.executor import ESExecutor
from escli.utils import OutputSettings
from escli.formatter import Formatter

TEST_INDEX_NAME = "escli_test"
HOST = "http://localhost:9200"


def create_index(test_executor):
    es = test_executor.connection
    es.indices.create(index=TEST_INDEX_NAME)


def delete_index(test_executor):
    es = test_executor.connection
    es.indices.delete(index=TEST_INDEX_NAME)


def close_connection(es):
    ConnectionPool.close(es)


def load_file(test_executor, filename="accounts.json"):
    es = test_executor.connection

    filepath = "./test_data/" + filename

    # generate iterable data
    def load_json():
        with open(filepath, "r") as f:
            for line in f:
                yield json.loads(line)

    helpers.bulk(es, load_json(), index=TEST_INDEX_NAME)


def load_data(test_executor, doc):
    es = test_executor.connection
    es.index(index=TEST_INDEX_NAME, body=doc)
    es.indices.refresh(index=TEST_INDEX_NAME)


def get_connection():
    test_executor = ESExecutor(endpoint=HOST)
    test_executor.set_connection()

    return test_executor


try:
    connection = get_connection()
    CAN_CONNECT_TO_ES = True

except ConnectionError:
    CAN_CONNECT_TO_ES = False


estest = pytest.mark.skipif(
    not CAN_CONNECT_TO_ES,
    reason="Need a Elasticsearch server running at localhost PORT 9200 accessible",
)


def run(test_executor, query, use_console=True):
    data = test_executor.execute_query(query=query, use_console=use_console)
    settings = OutputSettings(table_format="psql")
    formatter = Formatter(settings)

    if data:
        res = formatter.format_output(data)
        res = "\n".join(res)

        return res
