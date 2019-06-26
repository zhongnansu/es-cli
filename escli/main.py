from __future__ import unicode_literals
from .__init__ import __version__
import click
import sys
import re

import pyfiglet

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
from .config import (
    get_casing_file,
    load_config,
    config_location,
    ensure_dir_exists,
    get_config,
)

from pygments.lexers.sql import SqlLexer
from .connection import get_connection, execute_query
from cli_helpers.tabular_output import TabularOutputFormatter
from cli_helpers.tabular_output.preprocessors import align_decimals, format_numbers
from .esbuffer import pg_is_multiline
from .pgstyle import style_factory, style_factory_output
from .encodingutils import text_type

# Ref: https://stackoverflow.com/questions/30425105/filter-special-chars-such-as-color-codes-from-shell-output
COLOR_CODE_REGEX = re.compile(r"\x1b(\[.*?[@-~]|\].*?(\x07|\x1b\\))")


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

    sql_completer = WordCompleter(keywords + functions, ignore_case=True)
    # TODO: Add index suggestion by using getIndex api

    def __init__(self,
                 esclirc_file=None):

        # Load config.
        config = self.config = get_config(esclirc_file)

        self.prompt_app = None
        self.connection = None
        self.setting = None

        self.syntax_style = config["main"]["syntax_style"]
        self.cli_style = config["colors"]
        self.table_format = config["main"]["table_format"]

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
            "table_format": self.table_format,
        }
        # print Banner
        banner = pyfiglet.figlet_format("ES SQL", font="slant")
        print(banner)

        # print info data
        print("Server: Open Distro for ES: %s" % es_version)
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
            # TODO: handle case that connection lost during the cli is sill running.
            #  _handle_server_closed_connection(text)
                try:
                    data = execute_query(self.connection, text)

                    if data:

                        output = format_output(data, self.setting)
                        self.echo_via_pager('\n'.join(output))
                    else:
                        continue
                except Exception as e:
                    print(repr(e))

        print('GoodElasticBye!')

    def is_too_wide(self, line):
        """Will this line be too wide to fit into terminal?"""
        if not self.prompt_app:
            return False
        return (
            len(COLOR_CODE_REGEX.sub("", line))
            > self.prompt_app.output.get_size().columns
        )

    def is_too_tall(self, lines):
        """Are there too many lines to fit into terminal?"""
        if not self.prompt_app:
            return False
        return len(lines) >= (self.prompt_app.output.get_size().rows - 4)

    def echo_via_pager(self, text, color=None):
        lines = text.split("\n")

        if self.is_too_tall(lines) or any(self.is_too_wide(l) for l in lines):
            click.echo_via_pager(text, color=color)
        else:
            click.echo(text, color=color)


@click.command()
@click.argument('endpoint', default="http://localhost:9200")
@click.option(
    "-q",
    "--query",
    "query",
    type=click.STRING,
    help="Run single query without getting in to the console",
)
@click.option(
    "-e",
    "--explain",
    "explain",
    is_flag=True,
    help="Explain sql to DSL",
)
@click.option(
    "--esclirc",
    default=config_location() + "config",
    envvar="ESCLIRC",
    help="Location of esclirc file.",
    type=click.Path(dir_okay=False),
)
@click.option(
    "-f",
    "--format",
    "format",
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
    help="Convert output from horizontal to vertical",
)
def cli(endpoint, query, explain, esclirc, format, is_vertical):
    """
    Provide endpoint for elasticsearch connection.
    By Default, it uses http://localhost:9200 to connect
    """

    # TODO: echo or print more info of server and cli here

    # handle single query without interaction with user
    if query:
        es, es_version = get_connection(endpoint)
        if explain:
            res = execute_query(es, query, explain=True)
        else:
            res = execute_query(es, query, output_format=format)
            if res and format == 'jdbc':
                res = format_output(res, settings={'table_format': 'psql',
                                                   'format_name': 'vertical' if is_vertical else None})
                res = '\n'.join(res)

        click.echo(res)
        sys.exit(0)

    escli = ESCli(esclirc_file=esclirc)

    escli.run_cli(endpoint)


def format_output(data, settings):

    formatter = TabularOutputFormatter(format_name=settings['table_format'])

    max_width = settings.get('max_width', sys.maxsize)

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
        # todo encapsulate to a OutputSetting object, refer to pgcli source code
        # "missing_value": settings.missingval,
        # "integer_format": settings.dcmlfmt,
        # "float_format": settings.floatfmt,
        "preprocessors": (format_numbers, format_arrays),
        "disable_numparse": True,
        "preserve_whitespace": True,
        "style": settings.get('style_output', None)
    }

    fields = []
    types = []

    # get header and type as list
    for i in schema:
        fields.append(i['name'])
        types.append(i['type'])

    format_name = settings.get('format_name', None)
    output = formatter.format_output(datarows, fields, format_name=format_name, **output_kwargs)


    # check width overflow, change format_name for better visual effect
    first_line = next(output)

    if len(first_line) > max_width:
        click.secho("Output longer than terminal width", fg="red")
        if click.confirm("Do you want to convert to vertical for better visual effect?"):
            output = formatter.format_output(datarows, fields, format_name='vertical', **output_kwargs)

    return output


if __name__ == "__main__":
    cli()