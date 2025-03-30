import os
import sys
from datetime import datetime, timedelta

import pytest

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))

from src.spotify import SpotifyClient

TEST_TOKEN = "test_token"


class TestToken:
    @pytest.mark.not_logged
    @pytest.mark.order(3)
    def test_save_false_spotify_tokens(self):
        spotify = SpotifyClient()
        expires_in = datetime.now() + timedelta(seconds=3600)
        spotify.save_spotify_tokens(TEST_TOKEN, TEST_TOKEN, expires_in)

    @pytest.mark.not_logged
    @pytest.mark.order(4)
    def test_get_tokens_from_db(self):
        spotify = SpotifyClient()
        token, refresh_token, _ = spotify._get_tokens_from_db()
        assert token == TEST_TOKEN
        assert refresh_token == TEST_TOKEN

    @pytest.mark.not_logged
    @pytest.mark.order(5)
    def test_get_token(self):
        spotify = SpotifyClient()
        token = spotify._get_token()
        assert token == TEST_TOKEN

    @pytest.mark.logged
    @pytest.mark.order(6)
    def test_get_user_followed_artists(self):
        spotify = SpotifyClient()
        artists = spotify.get_user_followed_artists()
        assert len(artists) > 0
        for artist in artists:
            assert "id" in artist
            assert "external_urls" in artist
            assert "spotify" in artist["external_urls"]
            assert "images" in artist
            assert "name" in artist

    @pytest.mark.logged
    @pytest.mark.order(7)
    def test_get_artist_albums(self):
        spotify = SpotifyClient()
        albums = spotify.get_artist_albums("3fMbdgg4jU18AjLCKBhRSm")
        assert len(albums) > 0
        for album in albums:
            assert "id" in album
            assert "external_urls" in album
            assert "spotify" in album["external_urls"]
            assert "images" in album
            assert "release_date" in album
            assert "type" in album
