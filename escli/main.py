from __future__ import unicode_literals

import click
import sys

from elasticsearch.exceptions import ConnectionError

from .config import config_location
from .executor import ESExecutor
from .utils import OutputSettings
from .escli import ESCli
from .formatter import Formatter

click.disable_unicode_literals_warning = True


@click.command()
@click.argument("endpoint", default="http://localhost:9200")
@click.option(
    "-q",
    "--query",
    "query",
    type=click.STRING,
    help="Run single query without getting in to the console",
)
@click.option("-e", "--explain", "explain", is_flag=True, help="Explain sql to DSL")
@click.option(
    "--esclirc",
    default=config_location() + "conf",
    envvar="ESCLIRC",
    help="Location of esclirc file.",
    type=click.Path(dir_okay=False),
)
@click.option(
    "-f",
    "--format",
    "result_format",
    type=click.STRING,
    default="jdbc",
    help="Specify format of output, jdbc/raw/csv. By default, it's jdbc.",
)
@click.option(
    "-v",
    "--vertical",
    "is_vertical",
    is_flag=True,
    default=False,
    help="Convert output from horizontal to vertical. Only used for single query not getting into console",
)
@click.option("-U", "--username", help="Username to connect to the Elasticsearch")
@click.option("-W", "--password", help="password of the username")
@click.option(
    "-p",
    "--pager",
    "always_use_pager",
    is_flag=True,
    default=False,
    help="Always use pager to display output. If not specified, smart pager mode will be used according to the \
         length/width of output",
)
def cli(
    endpoint,
    query,
    explain,
    esclirc,
    result_format,
    is_vertical,
    username,
    password,
    always_use_pager,
):
    """
    Provide endpoint for Elasticsearch connection.
    By default, it uses http://localhost:9200 to connect.
    """

    if username and password:
        http_auth = (username, password)
    else:
        http_auth = None

    is_single_query = query is not None

    # TODO add validation for endpoint to avoid the cost of connecting to some obviously invalid endpoint

    # handle single query without more interaction with user
    if is_single_query:
        try:
            es_executor = ESExecutor(endpoint, http_auth)
            es_executor.set_connection()
            if explain:
                output = es_executor.execute_query(
                    query, explain=True, use_console=False
                )
            else:
                output = es_executor.execute_query(
                    query, output_format=result_format, use_console=False
                )
                if output and result_format == "jdbc":
                    settings = OutputSettings(
                        table_format="psql", is_vertical=is_vertical
                    )

                    formatter = Formatter(settings)
                    output = formatter.format_output(output)
                    output = "\n".join(output)

            click.echo(output)
            sys.exit(0)

        except ConnectionError as e:
            click.secho("Can not connect to endpoint %s" % endpoint, fg="red")
            click.echo(repr(e))
            sys.exit(0)

    # use console to interact with user
    escli = ESCli(esclirc_file=esclirc, always_use_pager=always_use_pager)
    escli.connect(endpoint, http_auth)
    escli.run_cli()


if __name__ == "__main__":
    cli()
