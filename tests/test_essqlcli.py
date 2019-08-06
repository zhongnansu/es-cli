from utils import estest, load_data, run, get_connection, TEST_INDEX_NAME
from escli.essqlcli import ESSqlCli
from escli.executor import ESExecutor
from escli.esstyle import style_factory
from prompt_toolkit.shortcuts import PromptSession
from escli.esbuffer import es_is_multiline
from prompt_toolkit.input.defaults import create_pipe_input
import mock


INVALID_ENDPOINT = "http://invalid:9200"
OPEN_DISTRO_ENDPOINT = "https://opedistro:9200"
AES_ENDPOINT = "https://fake.es.amazonaws.com"
AUTH = None
ENDPOINT = "http://localhost:9200"
QUERY_WITH_CTRL_D = "select * from %s;\r\x04\r" % TEST_INDEX_NAME


def test_connect(default_config_location):
    escli = ESSqlCli(esclirc_file=default_config_location, always_use_pager=False)

    with mock.patch.object(
        ESExecutor, "__init__", return_value=None
    ) as mock_ESExecutor, mock.patch.object(
        ESExecutor, "set_connection"
    ) as mock_set_connectiuon:
        escli.connect(endpoint=ENDPOINT)

        mock_ESExecutor.assert_called_with(ENDPOINT, AUTH)
        mock_set_connectiuon.assert_called()


@estest
def test_run_cli(connection, default_config_location, capfd):
    doc = {"a": "aws"}
    load_data(connection, doc)

    escli = ESSqlCli(esclirc_file=default_config_location, always_use_pager=False)
    escli.connect(ENDPOINT)

    expected = "data retrieved / total hits = 1/1" \
               "\n+-----+\n| \x1b[38;5;47;01ma\x1b[39;00m   |\n|-----|\n| aws |\n+-----+"

    with mock.patch.object(ESSqlCli, "echo_via_pager") as mock_pager, mock.patch.object(
        escli, "build_cli"
    ) as mock_prompt:
        inp = create_pipe_input()
        inp.send_text(QUERY_WITH_CTRL_D)

        mock_prompt.return_value = PromptSession(
            input=inp,
            multiline=es_is_multiline(escli),
            style=style_factory(escli.syntax_style, escli.cli_style),
        )
        escli.run_cli()
        inp.close()

        mock_pager.assert_called_with(expected)
        out, err = capfd.readouterr()

        # TODO check the print messages
