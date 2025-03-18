import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))

from src.db import create_db, get_db_conn


@pytest.mark.not_logged
class TestDB:
    @pytest.mark.order(1)
    def test_create_db(self):
        create_db()

    @pytest.mark.order(2)
    def test_get_db_conn(self):
        conn = get_db_conn()
        assert conn is not None
