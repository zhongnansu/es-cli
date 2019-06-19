from datetime import datetime
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch_dsl import search
from elasticsearch import Transport
from elasticsearch import ConnectionPool
import json

# es = Elasticsearch({'host': 'localhost', 'url_prefix': '_opendistro/_sql/'})
# es = Elasticsearch(
#     [
#         'http://localhost:9200/_opendistro/_sql/'
#     ]
# )
# res = es.search(body={"query": "SELECT * FROM test1 LIMIT 50"})



def get_connection(endpoint):
    es = Elasticsearch([endpoint], verify_certs=True)

    if es.ping():

        info = es.info()
        version = info['version']['number']
        print("ES version: %s" % version)
        return es

    else:
        return None


def query(es, query):
    data = es.transport.perform_request(url="/_opendistro/_sql", method="POST", params={'format': 'jdbc'}, body={
        'query': query
    })

    return data



# endpoint = "http://localhost:9200"
# query = "select * from test1 limit 50"
# get_connection(endpoint)