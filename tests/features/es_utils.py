from elasticsearch import ConnectionError, helpers, ConnectionPool
import json
import pytest
import sys

from escli.executor import ESExecute
from escli.main import OutputSettings, format_output

TEST_INDEX_NAME = 'escli_test'
HOST = 'http://localhost:9200'


def create_index(test_executor):
    es = test_executor.conn
    es.indices.create(index=TEST_INDEX_NAME)


def delete_index(test_executor):
    es = test_executor.conn
    es.indices.delete(index=TEST_INDEX_NAME)


def close_connection(es):
    ConnectionPool.close(es)


def load_file(test_executor, filename='accounts.json'):
    es = test_executor.conn

    filepath = './test_data/' + filename

    # generate iterable data
    def load_json():
        with open(filepath, 'r') as f:
            for line in f:
                yield json.loads(line)

    helpers.bulk(es, load_json(), index=TEST_INDEX_NAME)


def load_data(test_executor, doc):
    es = test_executor.conn
    es.index(index=TEST_INDEX_NAME, body=doc)
    es.indices.refresh(index=TEST_INDEX_NAME)


def get_connection():

    test_executor = ESExecute(endpoint=HOST)

    return test_executor


try:
    conn = get_connection()
    CAN_CONNECT_TO_ES = True

except ConnectionError:
    CAN_CONNECT_TO_ES = False


estest = pytest.mark.skipif(
    not CAN_CONNECT_TO_ES,
    reason="Need a Elasticsearch node running at localhost PORT 9200 accessible",
)


def run(test_executor, query):

    data = test_executor.execute_query(query=query)

    if data:
        settings = OutputSettings(
            table_format='psql'
        )

        res = format_output(data, settings)
        res = '\n'.join(res)

        return res