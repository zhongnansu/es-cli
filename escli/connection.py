from elasticsearch import Elasticsearch

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

    # deal with input
    final_query = query.strip().strip(';')

    data = es.transport.perform_request(url="/_opendistro/_sql", method="POST", params={'format': 'jdbc'}, body={
        'query': final_query
    })

    return data





# endpoint = "http://localhost:9200"
# s = "select * from es_1,es_2"
# es = get_connection(endpoint)
# data, header = query(es, s)
#
# format_output(data, header)