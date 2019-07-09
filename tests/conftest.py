import pytest
import os

from tests.utils import (
    create_index,
    delete_index,
    get_connection,
)


@pytest.fixture(scope='function')
def connection():
    test_executor = get_connection()
    create_index(test_executor)

    yield test_executor
    delete_index(test_executor)


@pytest.fixture(scope="session", autouse=True)
def temp_config(tmpdir_factory):
    # this function runs on start of test session.
    # use temporary directory for config home so user config will not be used
    os.environ["XDG_CONFIG_HOME"] = str(tmpdir_factory.mktemp("data"))
