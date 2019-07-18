import boto3
import click
import logging
import ssl
import urllib3

from elasticsearch import Elasticsearch, RequestsHttpConnection
from elasticsearch.exceptions import ConnectionError, RequestError
from elasticsearch.connection import create_ssl_context
from requests_aws4auth import AWS4Auth

from .encodingutils import unicode2utf8


class ESExecute:
    """ESExecute instances are used to set up and maintain connection to Elasticsearch cluster,
    as well as send user's SQL query to Elasticsearch.
    """

    def __init__(self, endpoint=None, http_auth=None):
        """Initialize an ESExecute instance.

        Set up connection and get indices list.

        :param endpoint: an url in the format of "http:localhost:9200"
        :param http_auth: a tuple in the format of (username, password)
        """
        self.conn = None
        self.es_version = None
        self._set_connection(endpoint, http_auth)
        self.indices_list = self._get_indices()
        self.endpoint = endpoint

    def _get_indices(self):
        client = self.conn
        res = client.indices.get_alias().keys()

        return list(res)

    def _set_connection(self, endpoint, http_auth=None):
        urllib3.disable_warnings()
        logging.captureWarnings(True)

        def _get_aes_client():
            service = "es"
            session = boto3.Session()

            credentials = session.get_credentials()
            region = session.region_name
            awsauth = AWS4Auth(
                credentials.access_key, credentials.secret_key, region, service
            )

            aes_client = Elasticsearch(
                hosts=[{"host": str(endpoint), "port": 443}],
                http_auth=awsauth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
            )

            return aes_client

        def _get_open_distro_client():
            ssl_context = create_ssl_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            open_distro_client = Elasticsearch(
                [endpoint],
                http_auth=http_auth,
                verify_certs=False,
                ssl_context=ssl_context,
            )

            return open_distro_client

        if http_auth:
            es = _get_open_distro_client()

        elif str(endpoint).endswith("es.amazonaws.com"):
            es = _get_aes_client()

        else:
            es = Elasticsearch([endpoint], verify_certs=True)

        # check connection
        try:
            info = es.info()
            es_version = info["version"]["number"]

            self.conn = es
            self.es_version = es_version
        except ConnectionError as err:
            raise err

    def _handle_server_closed_connection(self):
        """Used during CLI execution."""
        endpoint = self.endpoint

        try:
            click.secho("Reconnecting...", fg="green")
            self._set_connection(endpoint)
            click.secho("Reconnected! Please run query again", fg="green")

        except ConnectionError as e:
            click.secho("Connection Failed", fg="red")
            click.secho(str(e), err=True, fg="red")

    def execute_query(self, query, output_format="jdbc", explain=False):
        """
        Handle user input, send SQL query and get response.

        :param query: SQL query
        :param output_format: jdbc/raw/csv
        :param explain: if True, use _explain API.
        :return: raw http response
        """
        # deal with input
        # TODO: consider add evaluator/handler to filter obviously-invalid input,
        #  to save cost of http connection.
        final_query = query.strip().strip(";")
        es = self.conn

        def _error_printer(error):
            """Used to print RequestError."""
            error_dict = error.info["error"]
            error_message = dict(
                [(unicode2utf8(k), unicode2utf8(v)) for k, v in error_dict.items()]
            )

            click.secho(message=str(error_message), fg="red")

        if explain:
            try:
                data = es.transport.perform_request(
                    url="/_opendistro/_sql/_explain",
                    method="POST",
                    body={"query": final_query},
                )
                return data

            except RequestError as e:
                _error_printer(e)

        else:
            try:
                data = es.transport.perform_request(
                    url="/_opendistro/_sql/",
                    method="POST",
                    params={"format": output_format},
                    body={"query": final_query},
                )
                return data

            # connection lost during execution
            except ConnectionError:
                self._handle_server_closed_connection()

            except RequestError as e:
                _error_printer(e)
