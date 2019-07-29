from __future__ import unicode_literals

import click
import re
import pyfiglet
import sys

from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.filters import HasFocus, IsDone
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.layout.processors import (
    ConditionalProcessor,
    HighlightMatchingBracketProcessor,
)
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from pygments.lexers.sql import SqlLexer
from elasticsearch.exceptions import ConnectionError

from .config import get_config
from .executor import ESExecute
from .esbuffer import es_is_multiline
from .esstyle import style_factory, style_factory_output
from .esliterals.main import get_literals
from .formatter import Formatter
from .utils import OutputSettings
from .__init__ import __version__


# Ref: https://stackoverflow.com/questions/30425105/filter-special-chars-such-as-color-codes-from-shell-output
COLOR_CODE_REGEX = re.compile(r"\x1b(\[.*?[@-~]|\].*?(\x07|\x1b\\))")

click.disable_unicode_literals_warning = True


class ESCli:
    """ESCli instance is used to build and run the ES SQL CLI."""

    def __init__(self, esclirc_file=None, esexecute=None, always_use_pager=False):
        # Load conf file
        config = self.config = get_config(esclirc_file)

        self.prompt_app = None
        self.esexecute = esexecute
        self.always_use_pager = always_use_pager
        self.syntax_style = config["main"]["syntax_style"]
        self.cli_style = config["colors"]
        self.table_format = config["main"]["table_format"]
        self.multiline_continuation_char = config["main"]["multiline_continuation_char"]
        self.multi_line = config["main"].as_bool("multi_line")
        self.multiline_mode = config["main"].get("multi_line_mode", "escli")
        self.null_string = config["main"].get("null_string", "null")
        self.style_output = style_factory_output(self.syntax_style, self.cli_style)

    def _build_cli(self):
        # TODO: Optimize index suggestion to serve indices options only at the needed position, such as 'from'
        keywords_list = get_literals("keywords")
        functions_list = get_literals("functions")
        indices_list = self.esexecute.indices_list

        sql_completer = WordCompleter(
            keywords_list + functions_list + indices_list, ignore_case=True
        )

        # https://stackoverflow.com/a/13726418 denote multiple unused arguments of callback in Python
        def get_continuation(width, *_):
            continuation = self.multiline_continuation_char * (width - 1) + " "
            return [("class:continuation", continuation)]

        prompt_app = PromptSession(
            lexer=PygmentsLexer(SqlLexer),
            completer=sql_completer,
            complete_while_typing=True,
            # TODO: add history, refer to pgcli approach
            # history=history,
            style=style_factory(self.syntax_style, self.cli_style),
            prompt_continuation=get_continuation,
            multiline=es_is_multiline(self),
            auto_suggest=AutoSuggestFromHistory(),
            input_processors=[
                ConditionalProcessor(
                    processor=HighlightMatchingBracketProcessor(chars="[](){}"),
                    filter=HasFocus(DEFAULT_BUFFER) & ~IsDone(),
                )
            ],
            tempfile_suffix=".sql",
        )

        return prompt_app

    def run_cli(self):
        """
        Print welcome page, goodbye message.

        Run the CLI and keep listening to user's input.
        """
        self.prompt_app = self._build_cli()

        settings = OutputSettings(
            max_width=self.prompt_app.output.get_size().columns,
            style_output=self.style_output,
            table_format=self.table_format,
            missingval=self.null_string,
        )

        # print Banner
        banner = pyfiglet.figlet_format("Open Distro", font="slant")
        print(banner)

        # print info on the welcome page
        print("Server: Open Distro for ES %s" % self.esexecute.es_version)
        print("Version: %s" % __version__)
        print("Endpoint: %s" % self.esexecute.endpoint)

        while True:
            try:
                text = self.prompt_app.prompt(message="escli" + "> ")
            except KeyboardInterrupt:
                continue  # Control-C pressed. Try again.
            except EOFError:
                break  # Control-D pressed.

            try:
                output = self.esexecute.execute_query(text)
                if output:
                    formatter = Formatter(settings)
                    formatted_output = formatter.format_output(output)
                    self.echo_via_pager("\n".join(formatted_output))

            except Exception as e:
                print(repr(e))

        print("See you next search!")

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
        if self.always_use_pager:
            click.echo_via_pager(text, color=color)

        elif self.is_too_tall(lines) or any(self.is_too_wide(l) for l in lines):
            click.echo_via_pager(text, color=color)
        else:
            click.echo(text, color=color)

    def connect(self, endpoint, http_auth=None):
        try:
            self.esexecute = ESExecute(endpoint, http_auth)

        except ConnectionError as e:
            click.secho("Can not connect to endpoint %s" % endpoint, fg="red")
            click.echo(repr(e))
            sys.exit(0)
