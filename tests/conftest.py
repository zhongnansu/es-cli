import pytest
import os

from tests.utils import (
    create_index,
    delete_index,
    get_connection,
)


@pytest.fixture(scope='function')
def connection():
    es = get_connection()
    create_index(es)

    yield es
    delete_index(es)


@pytest.fixture(scope="session", autouse=True)
def temp_config(tmpdir_factory):
    # this function runs on start of test session.
    # use temporary directory for config home so user config will not be used
    os.environ["XDG_CONFIG_HOME"] = str(tmpdir_factory.mktemp("data"))
