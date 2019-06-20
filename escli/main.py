from __future__ import unicode_literals
import click

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers.sql import SqlLexer
from .connection import get_connection, query
from cli_helpers.tabular_output import TabularOutputFormatter
from .esbuffer import pg_is_multiline


class ESCli:
    sql_completer = WordCompleter([
        'abort', 'action', 'add', 'after', 'all', 'alter', 'analyze', 'and',
        'as', 'asc', 'attach', 'autoincrement', 'before', 'begin', 'between',
        'by', 'cascade', 'case', 'cast', 'check', 'collate', 'column',
        'commit', 'conflict', 'constraint', 'create', 'cross', 'current_date',
        'current_time', 'current_timestamp', 'database', 'default',
        'deferrable', 'deferred', 'delete', 'desc', 'detach', 'distinct',
        'drop', 'each', 'else', 'end', 'escape', 'except', 'exclusive',
        'exists', 'explain', 'fail', 'for', 'foreign', 'from', 'full', 'glob',
        'group', 'having', 'if', 'ignore', 'immediate', 'in', 'index',
        'indexed', 'initially', 'inner', 'insert', 'instead', 'intersect',
        'into', 'is', 'isnull', 'join', 'key', 'left', 'like', 'limit',
        'match', 'natural', 'no', 'not', 'notnull', 'null', 'of', 'offset',
        'on', 'or', 'order', 'outer', 'plan', 'pragma', 'primary', 'query',
        'raise', 'recursive', 'references', 'regexp', 'reindex', 'release',
        'rename', 'replace', 'restrict', 'right', 'rollback', 'row',
        'savepoint', 'select', 'set', 'table', 'temp', 'temporary', 'then',
        'to', 'transaction', 'trigger', 'union', 'unique', 'update', 'using',
        'vacuum', 'values', 'view', 'virtual', 'when', 'where', 'with',
        'without'], ignore_case=True)

    style = Style.from_dict({
        'completion-menu.completion': 'bg:#008888 #ffffff',
        'completion-menu.completion.current': 'bg:#00aaaa #000000',
        'scrollbar.background': 'bg:#88aaaa',
        'scrollbar.button': 'bg:#222222',
    })

    def __init__(self):
        self.prompt_app = None
        self.connection = None

    def _build_cli(self):

        self.multiline_continuation_char = '.'
        self.multi_line = True
        self.multiline_mode = 'escli'

        def get_continuation(width, line_number, is_soft_wrap):
            continuation = self.multiline_continuation_char * (width - 1) + " "
            return [("class:continuation", continuation)]

        prompt_app = PromptSession(
            lexer=PygmentsLexer(SqlLexer),
            completer=self.sql_completer,
            prompt_continuation=get_continuation,
            multiline=pg_is_multiline(self),
            style=self.style)

        return prompt_app

    def run_cli(self, endpoint):

        self.connection = get_connection(endpoint)
        self.prompt_app = self._build_cli()

        while True:
            try:
                text = self.prompt_app.prompt('escli > ')
            except KeyboardInterrupt:
                continue  # Control-C pressed. Try again.
            except EOFError:
                break  # Control-D pressed.

            if self.connection:
                try:
                    data = query(self.connection, text)
                    output = format_output(data)

                    click.echo('\n'.join(output))
                except Exception as e:
                    print(repr(e))
            # TODO: handle case that connection lost during the cli is sill running. _handle_server_closed_connection(text)

        print('GoodElasticBye!')


@click.command()
@click.argument('endpoint', default="http://localhost:9200")
def cli(endpoint):
    """Provide endpoint for connection"""
    click.echo("Hi %s" % endpoint)

    # TODO: echo or print more info of server and cli
    #   print("Server: PostgreSQL", self.pgexecute.server_version)
    #   print("Version:", __version__)
    #   print("Chat: https://gitter.im/dbcli/pgcli")
    #   print("Mail: https://groups.google.com/forum/#!forum/pgcli")
    #   print("Home: http://pgcli.com")


    escli = ESCli()

    escli.run_cli(endpoint)


def format_output(data):

    formatter = TabularOutputFormatter(format_name='simple')

    datarows = data['datarows']
    schema = data['schema']

    field = []
    type = []

    # get header and type as list
    for i in schema:
        field.append(i['name'])
        type.append(i['type'])

    output = formatter.format_output(datarows, field)

    return output


if __name__ == "__main__":
    cli()