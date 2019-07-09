from elasticsearch import Elasticsearch, RequestsHttpConnection
from elasticsearch.exceptions import ConnectionError
import click
import sys
from elasticsearch.connection import create_ssl_context
import ssl
from requests_aws4auth import AWS4Auth
import boto3
import urllib3
import logging


class ConnectionFailException (Exception):
    pass


class ESExecute:

    def __init__(
        self,
        endpoint=None,
        http_auth=None,

    ):
        self.conn = None
        self.get_connection(endpoint, http_auth)
        self.es_version = None
        self.endpoint = endpoint

    def get_connection(self, endpoint, http_auth=None):

        urllib3.disable_warnings()
        logging.captureWarnings(True)

        def get_aes_client():
            service = 'es'
            session = boto3.Session()

            credentials = session.get_credentials()
            region = session.region_name
            awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service)

            aes_client = Elasticsearch(
                hosts=[{'host': str(endpoint), 'port': 443}],
                http_auth=awsauth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection
            )

            return aes_client

        def get_od_client():
            ssl_context = create_ssl_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            od_client = Elasticsearch([endpoint],
                                      http_auth=http_auth,
                                      verify_certs=False,
                                      ssl_context=ssl_context,
                                      )

            return od_client

        if http_auth:
            es = get_od_client()

        elif str(endpoint).endswith('es.amazonaws.com'):
            es = get_aes_client()

        else:
            es = Elasticsearch([endpoint], verify_certs=True)

        # check connection
        if es.ping():
            info = es.info()
            es_version = info['version']['number']

            self.conn = es
            self.es_version = es_version

            return es, es_version

        else:
            raise ConnectionFailException('Can not connect to endpoint: ' + endpoint)

    def _handle_server_closed_connection(self, endpoint):
        """Used during CLI execution."""
        try:
            click.secho("Reconnecting...", fg="green")
            self.get_connection(endpoint)
            click.secho("Reconnected! Please run query again", fg="green")

        except ConnectionFailException as e:
            click.secho("Connection Failed", fg="red")
            click.secho(str(e), err=True, fg="red")

    def execute_query(self, query, output_format='jdbc', explain=False):
        # deal with input
        final_query = query.strip().strip(';')
        es = self.conn

        if explain:
            try:
                data = es.transport.perform_request(url="/_opendistro/_sql/_explain", method="POST", body={
                    'query': final_query
                })
                return data
            except Exception as e:
                click.echo(e.info['error'])

        else:
            try:
                data = es.transport.perform_request(url="/_opendistro/_sql/", method="POST",
                                                    params={'format': output_format},
                                                    body={
                                                        'query': final_query
                                                    })
                return data

            except ConnectionError as e:
                self._handle_server_closed_connection(self.endpoint)

            except Exception as e:
                click.echo(e.info['error'])