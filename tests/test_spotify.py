import os
import sys
from datetime import datetime, timedelta

import pytest

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))

from src.spotify import (
    get_artist_albums,
    get_spotify_tokens,
    get_token,
    get_user_followed_artists,
    save_spotify_tokens,
)

TEST_TOKEN = "test_token"


class TestToken:
    @pytest.mark.order(3)
    def test_save_false_spotify_tokens(self):
        expires_in_seconds = 3600
        expires_in = datetime.now() + timedelta(seconds=expires_in_seconds)
        save_spotify_tokens(TEST_TOKEN, TEST_TOKEN, expires_in)

    @pytest.mark.order(4)
    def test_get_false_spotify_tokens(self):
        token, refresh_token, _ = get_spotify_tokens()
        assert token == TEST_TOKEN
        assert refresh_token == TEST_TOKEN

    @pytest.mark.order(5)
    def test_get_token(self):
        token = get_token()
        assert token

    @pytest.mark.order(6)
    def test_get_user_followed_artists(self, token):
        artists = get_user_followed_artists(token)
        assert len(artists) > 0
        for artist in artists:
            assert "id" in artist
            assert "external_urls" in artist
            assert "spotify" in artist["external_urls"]
            assert "images" in artist
            assert "name" in artist

    @pytest.mark.order(7)
    def test_get_artist_albums(self, token):
        albums = get_artist_albums(token, "3fMbdgg4jU18AjLCKBhRSm")
        assert len(albums) > 0
        for album in albums:
            assert "id" in album
            assert "external_urls" in album
            assert "spotify" in album["external_urls"]
            assert "images" in album
            assert "release_date" in album
            assert "type" in album
