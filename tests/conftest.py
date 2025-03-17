import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))

from src.api import app
from src.spotify import get_token


@pytest.fixture()
def client():
    app.config.update({"TESTING": True})

    return app.test_client()


@pytest.fixture()
def token():
    return get_token()
