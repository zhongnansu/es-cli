import pytest

from .utils import (
    create_index,
    delete_index,
    get_connection,
)


@pytest.fixture(scope='function')
def connection():
    es = get_connection()
    create_index(es, '_test')

    yield es

    delete_index(es, '_test')



