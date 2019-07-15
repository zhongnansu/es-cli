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


@when("we select from table")
def step_select_from_table(context):
    """
    Send select from table.
    """
    context.cli.sendline("select * from escli_test;")


@then("we see data selected")
def step_see_data_selected(context):
    """
    Wait to see select output.
    """
    wrappers.expect_pager(
        context,
        expected=dedent(
            """\
            data retrieved / total hits = 1/1\r
            +-----+\r
            | a   |\r
            |-----|\r
            | aws |\r
            +-----+\r
        """
        ),
        timeout=1,
    )