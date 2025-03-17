import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))

from src.utils import (
    get_configs,
)


@pytest.mark.order(0)
def test_get_configs():
    configs = get_configs()
    assert "client_id" in configs
    assert "client_secret" in configs
    assert "redirect_uri" in configs
    assert "ntfy_token" in configs
    assert "ntfy_topic" in configs
    assert "ntfy_url" in configs
    assert "encryption_key" in configs
    assert "db_path" in configs
