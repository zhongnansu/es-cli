from __future__ import unicode_literals
import click

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
from .connection import get_connection, query
from cli_helpers.tabular_output import TabularOutputFormatter
from .esbuffer import pg_is_multiline


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

    style = Style.from_dict({
        'completion-menu.completion': 'bg:#008888 #ffffff',
        'completion-menu.completion.current': 'bg:#00aaaa #000000',
        'scrollbar.background': 'bg:#88aaaa',
        'scrollbar.button': 'bg:#222222',
    })

    def __init__(self):
        self.prompt_app = None
        self.connection = None
        self.setting = None


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
            prompt_continuation=get_continuation,
            multiline=pg_is_multiline(self),
            style=self.style,
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

        self.connection = get_connection(endpoint)
        self.prompt_app = self._build_cli()
        self.setting = {
            "max_width": self.prompt_app.output.get_size().columns
        }

        while True:
            if self.connection:
                try:
                    text = self.prompt_app.prompt(message='escli@' + endpoint + '> ')
                except KeyboardInterrupt:
                    continue  # Control-C pressed. Try again.
                except EOFError:
                    break  # Control-D pressed.
            else:
                click.echo('Can not connect to endpoint: ' + endpoint)
                break

            # TODO: handle case that connection lost during the cli is sill running. _handle_server_closed_connection(text)
            try:
                data = query(self.connection, text)
                output = format_output(data, self.setting)

                click.echo('\n'.join(output))
            except Exception as e:
                print(repr(e))

        print('GoodElasticBye!')


@click.command()
@click.argument('endpoint', default="http://localhost:9200")
def cli(endpoint):
    """Provide endpoint for connection"""

    # TODO: echo or print more info of server and cli


    escli = ESCli()

    escli.run_cli(endpoint)


def format_output(data, settings):

    formatter = TabularOutputFormatter(format_name='psql')

    max_width = settings['max_width']

    datarows = data['datarows']
    schema = data['schema']

    fields = []
    types = []

    # get header and type as list
    for i in schema:
        fields.append(i['name'])
        types.append(i['type'])

    output = formatter.format_output(datarows, fields)
    first_line = next(output)

    # check width overflow, change format_name for better visual effect
    if len(first_line) > max_width:
        output = formatter.format_output(datarows, fields, format_name='vertical')

    return output

if __name__ == "__main__":
    cli()