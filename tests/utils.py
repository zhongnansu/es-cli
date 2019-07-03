from elasticsearch import Elasticsearch, helpers
import json


def create_index(client, index_name):

    client.indices.create(index=index_name)


def delete_index(client, index_name):

    client.indices.delete(index=index_name)


def load_data(es, index_name, filename='accounts.json'):

    filepath = './test_data/' + filename

    # generate iterable data
    def load_json():
        with open(filepath, 'r') as f:
            for line in f:
                yield json.loads(line)

    helpers.bulk(es, load_json(), index=index_name)


def get_connection():
    endpoint = 'http://localhost:9200'

    client = Elasticsearch([endpoint], verify_certs=True)

    return client


es = get_connection()
create_index(es, 'bank')
load_data(es, 'bank')