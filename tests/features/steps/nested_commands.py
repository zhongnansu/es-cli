# -*- coding: utf-8
"""
Steps for behavioral style tests are defined in this module.
Each step is defined by the string decorating it.
This string is used to call the step in "*.feature" file.
"""
from __future__ import unicode_literals, print_function

from behave import when, then
from textwrap import dedent
import tests.features.steps.wrappers as wrappers


@when("we launch escli using {arg}")
def step_run_cli_using_arg(context, arg):
    prompt_check = False
    if arg == "--query":
        # TODO: Set escli_test / endpoint / port as env
        arg = "--query={}".format("'SELECT * FROM escli_test'")

        prompt_check = False

    wrappers.run_cli(context, run_args=[arg], prompt_check=prompt_check)


@then("we see query output")
def step_see_output(context):
    wrappers.expect_exact(
        context,
        expected=dedent(
            """\
            fetched rows / total rows = 1/1\r
            +-----+\r
            | a   |\r
            |-----|\r
            | aws |\r
            +-----+\r
        """
        ),
        timeout=1,
    )
