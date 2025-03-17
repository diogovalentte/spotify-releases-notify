import uuid
from datetime import datetime, timedelta
from time import sleep

from flask import Flask, jsonify, redirect, request, session
from pytfy import NtfyPublisher

from src.spotify import (
    _get_token,
    get_artist_albums,
    get_token,
    get_user_followed_artists,
    save_spotify_tokens,
)
from src.utils import get_configs, get_logger

app = Flask(__name__)
configs = get_configs()
app.secret_key = configs["encryption_key"]


@app.route("/health")
def health():
    return "OK"


@app.route("/spotify/login")
def login():
    scope = "user-follow-read"
    state = str(uuid.uuid4())
    session["oauth_state"] = state

    return redirect(
        f"https://accounts.spotify.com/authorize?client_id={configs['client_id']}&response_type=code&redirect_uri={configs['redirect_uri']}&scope={scope}&state={state}&show_dialog=true"
    )


@app.route("/spotify/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")
    if not state:
        return jsonify({"error": "missing state"}), 400
    if state != session.pop("oauth_state", None):
        return jsonify({"error": "invalid state"}), 400
    if error:
        return jsonify({"error": error}), 400
    if not code:
        return jsonify({"error": "missing code"}), 400

    try:
        token, refresh_token, expires_in_seconds = _get_token(
            configs["client_id"],
            configs["client_secret"],
            code=code,
            redirect_uri=configs["redirect_uri"],
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    expires_in = datetime.now() + timedelta(seconds=expires_in_seconds - 5)
    save_spotify_tokens(token, refresh_token, expires_in)

    return "OK"


@app.route("/spotify/notify")
def spotify_notify():
    include_groups = request.args.get("include_groups")
    if not include_groups:
        include_groups = "album,single,appears_on"

    today_str = datetime.now().strftime("%Y-%m-%d")
    today_releases = []
    logger = get_logger()
    start = datetime.now()
    try:
        token = get_token()
        artists = get_user_followed_artists(token)

        for artist in artists:
            try:
                albums = get_artist_albums(token, artist["id"], include_groups)
                for album in albums:
                    if album["release_date"] == today_str:
                        album["og_artist"] = artist["name"]
                        today_releases.append(album)
            except Exception as e:
                logger.error(f"Error getting albums for {artist['name']}: {e}")
                try:
                    albums = get_artist_albums(token, artist["id"], include_groups)
                    for album in albums:
                        if album["release_date"] == today_str:
                            album["og_artist"] = artist["name"]
                            today_releases.append(album)
                except Exception as e:
                    logger.error(f"Error getting albums for {artist['name']}: {e}")
                    logger.warning(
                        f"Max retries reached for {artist['name']}, skipping artist..."
                    )
            finally:
                sleep(2)
        end = datetime.now()
        diff = end - start

        if len(today_releases) > 0:
            send_release_notifications(today_releases)

        return {
            "releases": today_releases,
            "start_time": start,
            "end_time": end,
            "took_seconds": diff.total_seconds(),
        }
    except Exception as e:
        send_error_notifications(e)
        return jsonify({"error": str(e)}), 500


def send_release_notifications(releases):
    ntfy = NtfyPublisher(
        configs["ntfy_url"], configs["ntfy_topic"], configs["ntfy_token"]
    )
    message = "\n".join(
        [
            f"{album.get('name', 'No Name')} ({album.get('album_group', 'Unknown')}) - {album['og_artist']}: {album['external_urls'].get('spotify', 'No URL')}"
            for album in releases
        ]
    )
    ntfy.post(message, title="New Spotify Releases")


def send_error_notifications(e):
    ntfy = NtfyPublisher(
        configs["ntfy_url"], configs["ntfy_topic"], configs["ntfy_token"]
    )
    ntfy.post(f"An error occurred:\n{e}", title="New Spotify Releases")
