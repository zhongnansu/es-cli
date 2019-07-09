from __future__ import unicode_literals
from .__init__ import __version__
import click
import sys
import re
import itertools
import pyfiglet

from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.enums import DEFAULT_BUFFER, EditingMode
from prompt_toolkit.shortcuts import PromptSession, CompleteStyle
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

from collections import namedtuple
from pygments.lexers.sql import SqlLexer
from .executor import ESExecute, ConnectionFailException
from cli_helpers.tabular_output import TabularOutputFormatter
from cli_helpers.tabular_output.preprocessors import align_decimals, format_numbers
from .esbuffer import pg_is_multiline
from .pgstyle import style_factory, style_factory_output
from .encodingutils import text_type

# Ref: https://stackoverflow.com/questions/30425105/filter-special-chars-such-as-color-codes-from-shell-output
COLOR_CODE_REGEX = re.compile(r"\x1b(\[.*?[@-~]|\].*?(\x07|\x1b\\))")

click.disable_unicode_literals_warning = True

OutputSettings = namedtuple(
    "OutputSettings",
    "table_format is_vertical max_width style_output missingval",
)

OutputSettings.__new__.__defaults__ = (
    None,
    False,
    sys.maxsize,
    None,
    "null",
)

KEYWORDS = ['ACCESS', 'ADD', 'ALL', 'ALTER TABLE', 'AND', 'ANY', 'AS',
            'ASC', 'BEFORE', 'BEGIN', 'BETWEEN',
            'BIGINT', 'BINARY', 'BY', 'CASE', 'CHANGE MASTER TO', 'CHAR',
            'CHARACTER SET', 'CHECK', 'COLLATE', 'COLUMN', 'COMMENT',
            'COMMIT', 'CONSTRAINT', 'CREATE', 'CURRENT',
            'CURRENT_TIMESTAMP', 'DATABASE', 'DATE', 'DECIMAL', 'DEFAULT',
            'DELETE FROM', 'DELIMITER', 'DESC', 'DESCRIBE', 'DROP',
            'ELSE', 'END', 'ENGINE', 'ESCAPE', 'EXISTS', 'FILE', 'FLOAT',
            'FOR', 'FOREIGN KEY', 'FORMAT', 'FROM', 'FULL', 'FUNCTION',
            'GRANT', 'GROUP BY', 'HAVING', 'HOST', 'IDENTIFIED', 'IN',
            'INCREMENT', 'INDEX', 'INT', 'INTEGER',
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

FUNCTIONS = ['AVG', 'CONCAT', 'COUNT', 'DISTINCT', 'FIRST', 'FORMAT',
             'FROM_UNIXTIME', 'LAST', 'LCASE', 'LEN', 'MAX', 'MID',
             'MIN', 'NOW', 'ROUND', 'SUM', 'TOP', 'UCASE', 'UNIX_TIMESTAMP']


class ESCli:

    # TODO: Add index suggestion by using getIndex api

    def __init__(self,
                 esclirc_file=None,
                 esexecute=None):

        # Load config.
        config = self.config = get_config(esclirc_file)

        self.prompt_app = None

        self.esexecute = esexecute

        self.syntax_style = config["main"]["syntax_style"]
        self.cli_style = config["colors"]
        self.table_format = config["main"]["table_format"]

        self.style_output = style_factory_output(self.syntax_style, self.cli_style)

    def _build_cli(self):

        self.multiline_continuation_char = '.'
        self.multi_line = True
        self.multiline_mode = 'escli'

        sql_completer = WordCompleter(KEYWORDS + FUNCTIONS + self.esexecute.indices_list, ignore_case=True)

        def get_continuation(width, line_number, is_soft_wrap):
            continuation = self.multiline_continuation_char * (width - 1) + " "
            return [("class:continuation", continuation)]

        prompt_app = PromptSession(
            lexer=PygmentsLexer(SqlLexer),
            completer=sql_completer,
            # complete_while_typing=True,
            # completer=DynamicCompleter(lambda: self.completer),
            # history=history,
            style=style_factory(self.syntax_style, self.cli_style),
            prompt_continuation=get_continuation,
            multiline=pg_is_multiline(self),
            auto_suggest=AutoSuggestFromHistory(),
            input_processors=[ConditionalProcessor(
                processor=HighlightMatchingBracketProcessor(
                    chars='[](){}'),
                filter=HasFocus(DEFAULT_BUFFER) & ~IsDone()
            )],
            tempfile_suffix='.sql',
        )

        return prompt_app

    def run_cli(self):

        self.prompt_app = self._build_cli()

        settings = OutputSettings(
            max_width=self.prompt_app.output.get_size().columns,
            style_output=self.style_output,
            table_format=self.table_format,
        )

        # print Banner
        banner = pyfiglet.figlet_format("Open Distro", font="slant")
        print(banner)

        # print meta info
        print("Server: Open Distro for ES: %s" % self.esexecute.es_version)
        print("Version:", __version__)
        print("Endpoint: %s" % self.esexecute.endpoint)

        while True:
            try:
                text = self.prompt_app.prompt(message='escli' + '> ')
            except KeyboardInterrupt:
                continue  # Control-C pressed. Try again.
            except EOFError:
                break  # Control-D pressed.

            try:
                data = self.esexecute.execute_query(text)
                if data:

                    output = format_output(data, settings)
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

    def connect(self, endpoint, http_auth=None):

        try:
            self.esexecute = ESExecute(endpoint, http_auth)

        except ConnectionFailException as e:
            click.echo(e)
            sys.exit(0)


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
    help="Convert output from horizontal to vertical",
)
@click.option(
    "-U",
    "--username",
    help="Username to connect to the Elasticsearch",
)
@click.option(
    "-W",
    "--password",
    help="password of the username",
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
):
    """
    Provide endpoint for elasticsearch connection.
    By default, it uses http://localhost:9200 to connect
    """

    if username and password:
        http_auth = (username, password)
    else:
        http_auth = None

    # handle single query without more interaction with user
    if query:
        try:
            esexecutor = ESExecute(endpoint, http_auth)
            if explain:
                res = esexecutor.execute_query(query, explain=True)
            else:
                res = esexecutor.execute_query(query, output_format=result_format)
                if res and result_format == 'jdbc':
                    settings = OutputSettings(table_format='psql', is_vertical=is_vertical)
                    res = format_output(res, settings)
                    res = '\n'.join(res)

            click.echo(res)
            sys.exit(0)

        except ConnectionFailException as e:
            click.echo(e)
            sys.exit(0)

    escli = ESCli(esclirc_file=esclirc)
    escli.connect(endpoint, http_auth)
    escli.run_cli()


def format_output(data, settings):
    table_format = "vertical" if settings.is_vertical else settings.table_format

    formatter = TabularOutputFormatter(format_name=table_format)

    max_width = settings.max_width

    datarows = data['datarows']
    schema = data['schema']
    total_hits = data['total']
    cur_size = data['size']

    # TODO: Display fraction of number of rows / total hits

    fields = []
    types = []

    def format_array(val):
        if val is None:
            return settings.missingval
        if not isinstance(val, list):
            return val
        return "[" + ",".join(text_type(format_array(e)) for e in val) + "]"

    def format_arrays(field_data, headers, **_):
        field_data = list(field_data)
        for row in field_data:
            row[:] = [
                format_array(val) if isinstance(val, list) else val for val in row
            ]

        return field_data, headers

    output_kwargs = {
        "sep_title": "RECORD {n}",
        "sep_character": "-",
        "sep_length": (1, 25),
        "missing_value": settings.missingval,
        "preprocessors": (format_numbers, format_arrays),
        "disable_numparse": True,
        "preserve_whitespace": True,
        "style": settings.style_output
    }

    # get header and type as lists, not sure if we need this info
    for i in schema:
        fields.append(i['name'])
        types.append(i['type'])

    output = formatter.format_output(datarows, fields, **output_kwargs)

    # check width overflow, change format_name for better visual effect
    first_line = next(output)
    output = itertools.chain([first_line], output)

    if len(first_line) > max_width:
        click.secho(message="Output longer than terminal width", fg="red")
        if click.confirm("Do you want to display data vertically for better visual effect?"):
            output = formatter.format_output(datarows, fields, format_name='vertical', **output_kwargs)

    # TODO: Add row limit. Refer to pgcli -> main -> line 866

    return output


if __name__ == "__main__":
    cli()
