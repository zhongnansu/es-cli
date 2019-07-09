from elasticsearch import Elasticsearch, helpers
import json
import pytest
from escli.connection import execute_query
from escli.main import OutputSettings, format_output

TEST_INDEX_NAME = 'escli_test'
HOST = 'http://localhost:9200'


def create_index(client):

    client.indices.create(index=TEST_INDEX_NAME)


def delete_index(client):

    client.indices.delete(index=TEST_INDEX_NAME)


def load_file(es, filename='accounts.json'):

    filepath = './test_data/' + filename

    # generate iterable data
    def load_json():
        with open(filepath, 'r') as f:
            for line in f:
                yield json.loads(line)

    helpers.bulk(es, load_json(), index=TEST_INDEX_NAME)


def load_data(es, doc):
    es.index(index=TEST_INDEX_NAME, body=doc)
    es.indices.refresh(index=TEST_INDEX_NAME)


def get_connection():

    client = Elasticsearch([HOST], verify_certs=True)

    return client


try:
    conn = get_connection()
    CAN_CONNECT_TO_ES = True

except:
    CAN_CONNECT_TO_ES = False


estest = pytest.mark.skipif(
    not CAN_CONNECT_TO_ES,
    reason="Need a Elasticsearch node running at localhost PORT 9200 accessible",
)


def run(es, query):

    data = execute_query(es, query)
    if data:
        settings = OutputSettings(
            table_format='psql'
        )

        res = format_output(data, settings)
        res = '\n'.join(res)

        return res


# es = get_connection()
# create_index(es)
#
# doc = {
#         'name': 'David',
#         'age': 23,
#     }
#
# query = f'select * from {TEST_INDEX_NAME}'
#
# load_data(es, doc)
# run(es, query)
#
#
# delete_index(es)













