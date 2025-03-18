import os
import sys

import pytest
from flask.testing import FlaskClient

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))


class TestAPI:
    @pytest.mark.order(8)
    def test_health(self, client: FlaskClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.data == b"OK"

    @pytest.mark.order(9)
    def test_login(self, client: FlaskClient):
        response = client.get("/spotify/login")
        assert response.status_code == 302

    @pytest.mark.order(10)
    def test_callback_validations(self, client: FlaskClient):
        response = client.get("/spotify/callback")
        assert response.status_code == 400
        assert response.json and response.json["error"] == "missing state"

        response = client.get("/spotify/callback?state=123")
        assert response.status_code == 400
        assert response.json and response.json["error"] == "invalid state"

        with client.session_transaction() as session:
            session["oauth_state"] = "123"

        response = client.get("/spotify/callback?state=123")
        assert response.status_code == 400
        assert response.json and response.json["error"] == "missing code"

        with client.session_transaction() as session:
            # do again because the callback will pop the state
            session["oauth_state"] = "123"

        response = client.get("/spotify/callback?state=123&error=random_error")
        assert response.status_code == 400
        assert response.json and response.json["error"] == "random_error"

    @pytest.mark.order(12)
    def test_spotify_notify(self, client):
        response = client.get("/spotify/notify?notify_error=false")
        assert response.status_code == 200
        assert response.json["took_seconds"] > 0
