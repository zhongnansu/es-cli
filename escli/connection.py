from elasticsearch import Elasticsearch
import click
import sys


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
        es_version = info['version']['number']

        return es, es_version

    else:
        click.echo('Can not connect to endpoint: ' + endpoint)
        sys.exit(0)


def execute_query(es, query, output_format='jdbc', explain=False):
    # deal with input
    final_query = query.strip().strip(';')

    data = es.transport.perform_request(url="/_opendistro/_sql/", method="POST", params={'format': output_format},
                                        body={
                                            'query': final_query
                                        })

    # todo this is not flexible at all, change to use setting to config params, use only one perform_request at the end
    if explain:
        data = es.transport.perform_request(url="/_opendistro/_sql/_explain", method="POST", body={
            'query': final_query
        })

    return data

# endpoint = "http://localhost:9200"
# s = "select * from es_1,es_2"
# es = get_connection(endpoint)
# data, header = query(es, s)
#
# format_output(data, header)
