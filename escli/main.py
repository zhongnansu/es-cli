from __future__ import unicode_literals
from .__init__ import __version__
import click
import sys



from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import DynamicCompleter, ThreadedCompleter
from prompt_toolkit.enums import DEFAULT_BUFFER, EditingMode
from prompt_toolkit.shortcuts import PromptSession, CompleteStyle
from prompt_toolkit.document import Document
from prompt_toolkit.filters import HasFocus, IsDone
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.layout.processors import (
    ConditionalProcessor,
    HighlightMatchingBracketProcessor,
    TabsProcessor,
)
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory


from pygments.lexers.sql import SqlLexer
from .connection import get_connection, execute_query
from cli_helpers.tabular_output import TabularOutputFormatter
from cli_helpers.tabular_output.preprocessors import align_decimals, format_numbers
from .esbuffer import pg_is_multiline
from .pgstyle import style_factory, style_factory_output

from .encodingutils import text_type

class ESCli:

    keywords = ['ACCESS', 'ADD', 'ALL', 'ALTER TABLE', 'AND', 'ANY', 'AS',
                'ASC', 'AUTO_INCREMENT', 'BEFORE', 'BEGIN', 'BETWEEN',
                'BIGINT', 'BINARY', 'BY', 'CASE', 'CHANGE MASTER TO', 'CHAR',
                'CHARACTER SET', 'CHECK', 'COLLATE', 'COLUMN', 'COMMENT',
                'COMMIT', 'CONSTRAINT', 'CREATE', 'CURRENT',
                'CURRENT_TIMESTAMP', 'DATABASE', 'DATE', 'DECIMAL', 'DEFAULT',
                'DELETE FROM', 'DELIMITER', 'DESC', 'DESCRIBE', 'DROP',
                'ELSE', 'END', 'ENGINE', 'ESCAPE', 'EXISTS', 'FILE', 'FLOAT',
                'FOR', 'FOREIGN KEY', 'FORMAT', 'FROM', 'FULL', 'FUNCTION',
                'GRANT', 'GROUP BY', 'HAVING', 'HOST', 'IDENTIFIED', 'IN',
                'INCREMENT', 'INDEX', 'INSERT INTO', 'INT', 'INTEGER',
                'INTERVAL', 'INTO', 'IS', 'JOIN', 'KEY', 'LEFT', 'LEVEL',
                'LIKE', 'LIMIT', 'LOCK', 'LOGS', 'LONG', 'MASTER',
                'MEDIUMINT', 'MODE', 'MODIFY', 'NOT', 'NULL', 'NUMBER',
                'OFFSET', 'ON', 'OPTION', 'OR', 'ORDER BY', 'OUTER', 'OWNER',
                'PASSWORD', 'PORT', 'PRIMARY', 'PRIVILEGES', 'PROCESSLIST',
                'PURGE', 'REFERENCES', 'REGEXP', 'RENAME', 'REPAIR', 'RESET',
                'REVOKE', 'RIGHT', 'ROLLBACK', 'ROW', 'ROWS', 'ROW_FORMAT',
                'SAVEPOINT', 'SELECT', 'SESSION', 'SET', 'SHARE', 'SHOW',
                'SLAVE', 'SMALLINT', 'SMALLINT', 'START', 'STOP', 'TABLE',
                'THEN', 'TINYINT', 'TO', 'TRANSACTION', 'TRIGGER', 'TRUNCATE',
                'UNION', 'UNIQUE', 'UNSIGNED', 'UPDATE', 'USE', 'USER',
                'USING', 'VALUES', 'VARCHAR', 'VIEW', 'WHEN', 'WHERE', 'WITH']

    functions = ['AVG', 'CONCAT', 'COUNT', 'DISTINCT', 'FIRST', 'FORMAT',
                 'FROM_UNIXTIME', 'LAST', 'LCASE', 'LEN', 'MAX', 'MID',
                 'MIN', 'NOW', 'ROUND', 'SUM', 'TOP', 'UCASE', 'UNIX_TIMESTAMP']

    # old lowercase keywords
    # keywords = [
    #     'abort', 'action', 'add', 'after', 'all', 'alter', 'analyze', 'and',
    #     'as', 'asc', 'attach', 'autoincrement', 'before', 'begin', 'between',
    #     'by', 'cascade', 'case', 'cast', 'check', 'collate', 'column',
    #     'commit', 'conflict', 'constraint', 'create', 'cross', 'current_date',
    #     'current_time', 'current_timestamp', 'database', 'default',
    #     'deferrable', 'deferred', 'delete', 'desc', 'detach', 'distinct',
    #     'drop', 'each', 'else', 'end', 'escape', 'except', 'exclusive',
    #     'exists', 'explain', 'fail', 'for', 'foreign', 'from', 'full', 'glob',
    #     'group', 'having', 'if', 'ignore', 'immediate', 'in', 'index',
    #     'indexed', 'initially', 'inner', 'insert', 'instead', 'intersect',
    #     'into', 'is', 'isnull', 'join', 'key', 'left', 'like', 'limit',
    #     'match', 'natural', 'no', 'not', 'notnull', 'null', 'of', 'offset',
    #     'on', 'or', 'order', 'outer', 'plan', 'pragma', 'primary', 'query',
    #     'raise', 'recursive', 'references', 'regexp', 'reindex', 'release',
    #     'rename', 'replace', 'restrict', 'right', 'rollback', 'row',
    #     'savepoint', 'SELECT', 'set', 'table', 'temp', 'temporary', 'then',
    #     'to', 'transaction', 'trigger', 'union', 'unique', 'update', 'using',
    #     'vacuum', 'values', 'view', 'virtual', 'when', 'where', 'with',
    #     'without']

    sql_completer = WordCompleter(keywords + functions, ignore_case=True)

    cli_style = {
        'completion-menu.completion': 'bg:#008888 #ffffff',
        'completion-menu.completion.current': 'bg:#00aaaa #000000',
        # 'scrollbar.background': 'bg:#88aaaa',
        # 'scrollbar.button': 'bg:#222222',
        'scrollbar.arrow' : 'bg:#003333',
        'scrollbar': 'bg:#00aaaa',
        'output.header': "#00ff5f bold",
        'output.odd-row': "",
        'output.even-row': ""
    }

    def __init__(self):
        self.prompt_app = None
        self.connection = None
        self.setting = None
        self.syntax_style = 'default'
        self.style_output = style_factory_output(self.syntax_style, self.cli_style)


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
            complete_while_typing=True,
            # completer=DynamicCompleter(lambda: self.completer),
            # history=history,
            style=style_factory(self.syntax_style, self.cli_style),
            prompt_continuation=get_continuation,
            multiline=pg_is_multiline(self),
            # style=self.style,
            auto_suggest=AutoSuggestFromHistory(),
            input_processors=[ConditionalProcessor(
                processor=HighlightMatchingBracketProcessor(
                    chars='[](){}'),
                filter=HasFocus(DEFAULT_BUFFER) & ~IsDone()
            )],
            tempfile_suffix='.sql',
        )

        return prompt_app

    def run_cli(self, endpoint):

        self.connection, es_version = get_connection(endpoint)
        self.prompt_app = self._build_cli()
        self.setting = {
            "max_width": self.prompt_app.output.get_size().columns,
            "style_output": self.style_output,
        }

        print("Server: ES Open Distro: %s" % es_version)
        print("Version:", __version__)
        print("Home: https://opendistro.github.io/for-elasticsearch-docs/")

        while True:
            if self.connection:
                try:
                    text = self.prompt_app.prompt(message='escli@' + endpoint + '> ')
                except KeyboardInterrupt:
                    continue  # Control-C pressed. Try again.
                except EOFError:
                    break  # Control-D pressed.


            # TODO: handle case that connection lost during the cli is sill running. _handle_server_closed_connection(text)
                try:
                    data = execute_query(self.connection, text)
                    output = format_output(data, self.setting)

                    click.echo('\n'.join(output))
                except Exception as e:
                    print(repr(e))

        print('GoodElasticBye!')


@click.command()
@click.argument('endpoint', default="http://localhost:9200")
@click.option(
    "-q",
    "--query",
    "query",
    type=click.STRING,
    help="run single query without getting in to the console",
)
@click.option(
    "-e",
    "--explain",
    "explain",
    is_flag=True,
    help="run single query without getting in to the console",
)
def cli(endpoint, query, explain):
    """Provide endpoint for elasticsearch connection"""

    # TODO: echo or print more info of server and cli here

    # handle single query without more interaction with user
    if query:
        es, es_version = get_connection(endpoint)
        if explain:
            res = execute_query(es, query, explain=True)
        else:
            res = execute_query(es, query, 'raw')

        click.echo(res)
        sys.exit(0)


    escli = ESCli()

    escli.run_cli(endpoint)


def format_output(data, settings):

    formatter = TabularOutputFormatter(format_name='psql')

    max_width = settings['max_width']

    datarows = data['datarows']
    schema = data['schema']

    def format_array(val):
        if val is None:
            return settings.missingval
        if not isinstance(val, list):
            return val
        return "{" + ",".join(text_type(format_array(e)) for e in val) + "}"

    def format_arrays(data, headers, **_):
        data = list(data)
        for row in data:
            row[:] = [
                format_array(val) if isinstance(val, list) else val for val in row
            ]

        return data, headers

    output_kwargs = {
        "sep_title": "RECORD {n}",
        "sep_character": "-",
        "sep_length": (1, 25),
        # todo think about using config at the end
        # "missing_value": settings.missingval,
        # "integer_format": settings.dcmlfmt,
        # "float_format": settings.floatfmt,
        "preprocessors": (format_numbers, format_arrays),
        "disable_numparse": True,
        "preserve_whitespace": True,
        "style": settings["style_output"],
    }

    fields = []
    types = []

    # get header and type as list
    for i in schema:
        fields.append(i['name'])
        types.append(i['type'])

    output = formatter.format_output(datarows, fields, **output_kwargs)
    first_line = next(output)

    # check width overflow, change format_name for better visual effect
    if len(first_line) > max_width:
        click.secho("The result set has field length more than %s" % max_width, fg="red")
        if click.confirm("Do you want to convert to vertical?"):
            output = formatter.format_output(datarows, fields, format_name='vertical', **output_kwargs)

    return output


if __name__ == "__main__":
    cli()