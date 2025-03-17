import base64
from datetime import datetime, timedelta
from time import sleep

import requests

from src.db import create_db, get_db_conn
from src.utils import decrypt_str, encrypt_str, get_configs, get_logger


def check_response(response: requests.Response):
    logger = get_logger()
    if response.status_code == 429:
        retry_after_str = response.headers.get("retry-after")
        if retry_after_str:
            retry_after = 0
            try:
                retry_after = int(retry_after_str)
            except ValueError as e:
                logger.error(f"Error converting retry-after header to int: {e}")
                return response.text
            if retry_after >= 86400:
                err = f"Rate limit exceeded. Retry-after header found ({retry_after_str}) but it's greater or equal than 86400 (24 hours). Will not wait and retry"
                logger.error(err)
                return err
            logger.warning(
                f"Rate limit exceeded. Retry-after header found ({retry_after_str}), waiting for {retry_after} + 10 seconds"
            )
            sleep(retry_after + 10)
            return
        err = "Rate limit exceeded. Not retry-after header found"
        logger.error(err)
        return err
    logger.error(f"Error: {response.status_code} - {response.text}")
    return response.text


def check_for_rate_limit(func):

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            res = check_response(e.response)
            if res is not None:
                raise Exception(res)
            return func(*args, **kwargs)
        except Exception as e:
            raise e

    return wrapper


@check_for_rate_limit
def _get_token(
    client_id,
    client_secret,
    code: str | None = None,
    redirect_uri: str | None = None,
    refresh_token: str | None = None,
):
    """Get a token from the Spotify API.

    If code is provided, it will be used to get a new token and refresh token. In this case, redirect_uri is required.

    If refresh_token is provided, it will be used to get a new token. In this case, code and redirect_uri are not required and the returned refresh token is this arg's value.

    Args:
        client_id: Spotify client ID.
        client_secret: Spotify client secret.
        code (str | None, optional): Code got from callback after user log in. Defaults to None.
        redirect_uri (str | None, optional): Callback URI. Defaults to None.
        refresh_token (str | None, optional): Refresh token used to get a new token. If provided, returned refresh token will be this value. Defaults to None.

    Returns:
        (tuple[str, str, int): Access token, refresh token, expires in (in seconds).
    """
    if code:
        if not redirect_uri:
            raise Exception("Missing redirect_uri when using getting token using code")
        body = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }
    elif refresh_token:
        body = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    else:
        raise Exception("Missing code or refresh_token")
    auth_str = f"{client_id}:{client_secret}"
    encoded_auth = base64.b64encode(auth_str.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = requests.post(
        "https://accounts.spotify.com/api/token", data=body, headers=headers, timeout=10
    )

    response.raise_for_status()

    data = response.json()

    return (
        data["access_token"],
        data.get("refresh_token", refresh_token),
        data["expires_in"],
    )


def get_token():
    configs = get_configs()

    token, refresh_token, experies_in = get_spotify_tokens()
    if experies_in <= datetime.now():
        token, refresh_token, expires_in_seconds = _get_token(
            configs["client_id"],
            configs["client_secret"],
            refresh_token=refresh_token,
        )
        expires_in = datetime.now() + timedelta(seconds=expires_in_seconds - 5)
        save_spotify_tokens(token, refresh_token, expires_in)

    return token


def save_spotify_tokens(token: str, refresh_token: str, expires_in: datetime):
    create_db()

    conn = get_db_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO spotify_tokens (id, token, refresh_token, expires_in)
        VALUES (?, ?, ?, ?)
        """,
        (
            1,  # always using the same ID to update the same row
            encrypt_str(token),
            encrypt_str(refresh_token),
            expires_in,
        ),
    )

    conn.commit()
    conn.close()


def get_spotify_tokens():
    create_db()
    conn = get_db_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT token, refresh_token, expires_in
        FROM spotify_tokens
        """
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise Exception("No tokens found in DB")

    return (
        decrypt_str(row["token"]),
        decrypt_str(row["refresh_token"]),
        datetime.fromisoformat(row["expires_in"]),
    )


@check_for_rate_limit
def get_user_followed_artists(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    url = "https://api.spotify.com/v1/me/following?type=artist&limit=50"
    artists = []
    while True:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        artists.extend(data["artists"]["items"])
        if not data["artists"]["next"]:
            break
        url = data["artists"]["next"]

    return artists


@check_for_rate_limit
def get_artist_albums(access_token, id, include_groups: str | None = None):
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    url = f"https://api.spotify.com/v1/artists/{id}/albums?limit=50"
    if include_groups:
        url += f"&include_groups={include_groups}"
    albums = []
    while True:
        response = requests.get(url, headers=headers, timeout=10)

        response.raise_for_status()
        response.headers.get("retry-after")

        data = response.json()
        albums.extend(data["items"])
        if not data["next"]:
            break
        url = data["next"]

    return albums
