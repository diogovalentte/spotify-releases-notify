import base64
from datetime import datetime, timedelta
from time import sleep

import requests

from src.db import get_db_conn
from src.utils import decrypt_str, encrypt_str, get_configs, get_logger


class SpotifyClient:
    def __init__(self):
        self.token = None
        self.refresh_token = None
        self.expires_in = None
        self.client_id = None
        self.client_secret = None
        self.redirect_uri = None

    def _request(self, method: str, url: str, headers: dict | None = None, **kwargs):
        logger = get_logger()
        default_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._get_token()}",
        }
        if headers:
            default_headers.update(headers)
        headers = default_headers
        try:
            res = requests.request(method, url, headers=headers, **kwargs)
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            response = e.response
            if not response:
                raise e
            if response.status_code == 429:
                retry_after_str = response.headers.get("retry-after")
                if retry_after_str:
                    retry_after = 0
                    try:
                        retry_after = int(retry_after_str)
                    except ValueError as e:
                        err = f"Error converting retry-after header '{retry_after_str}' to int: {response}"
                        logger.error(err)
                        raise Exception(err)
                    if retry_after >= 86400:
                        err = f"Rate limit exceeded. Retry-after header found ({retry_after_str}) but it's greater or equal than 86400 (24 hours). Will not wait and retry"
                        logger.error(err)
                        raise Exception(err)
                    logger.warning(
                        f"Rate limit exceeded. Retry-after header found ({retry_after_str}), waiting for {retry_after} + 10 seconds"
                    )
                    sleep(retry_after + 10)
                    res = requests.request(method, url, headers=headers, **kwargs)
                    res.raise_for_status()
                else:
                    err = (
                        f"Rate limit exceeded. Not retry-after header found: {response}"
                    )
                    logger.error(err)
                    raise Exception(err)
            elif response.status_code == 401:
                try:
                    json = response.json()
                except ValueError:
                    error = f"Could not parse response JSON: {response}"
                    logger.error(error)
                    raise Exception(error)
                if json.get("message") == "The access token expired":
                    headers["Authorization"] = f"Bearer {self._get_token()}"
                    res = requests.request(method, url, headers=headers, **kwargs)
                    res.raise_for_status()
                error = f"Error: {response.status_code} - {json}"
                logger.error(error)
                raise Exception(error)
            else:
                raise e
        except Exception as e:
            raise e

        return res

    def _get_token_from_API(
        self,
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
            (tuple[str, str, int]): Access token, refresh token, expires in (in seconds).
        """
        if code:
            if not redirect_uri:
                raise Exception(
                    "Missing redirect_uri when using getting token using code"
                )
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
            "https://accounts.spotify.com/api/token",
            data=body,
            headers=headers,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        return (
            data["access_token"],
            data.get("refresh_token", refresh_token),
            data["expires_in"],
        )

    def _get_token(self):
        if self.expires_in:
            if self.expires_in <= datetime.now() - timedelta(seconds=5):
                self.token, self.refresh_token, expires_in_seconds = (
                    self._get_token_from_API(
                        self.client_id,
                        self.client_secret,
                        refresh_token=self.refresh_token,
                    )
                )
                self.expires_in = datetime.now() + timedelta(
                    seconds=expires_in_seconds - 5
                )
                self.save_spotify_tokens(
                    self.token, self.refresh_token, self.expires_in
                )
        else:
            configs = get_configs()
            self.token, self.refresh_token, self.experies_in = (
                self._get_tokens_from_db()
            )
            if self.experies_in <= datetime.now() - timedelta(seconds=5):
                self.token, self.refresh_token, expires_in_seconds = (
                    self._get_token_from_API(
                        configs["client_id"],
                        configs["client_secret"],
                        refresh_token=self.refresh_token,
                    )
                )
                self.expires_in = datetime.now() + timedelta(
                    seconds=expires_in_seconds - 5
                )
                self.save_spotify_tokens(
                    self.token, self.refresh_token, self.expires_in
                )

        return self.token

    def save_spotify_tokens(self, token: str, refresh_token: str, expires_in: datetime):
        """Saves Spotify tokens in the DB.

        Args:
            token (str): Spotify API token.
            refresh_token (str): Spotify API refresh token.
            expires_in (datetime): Spotify API token expires in.
        """
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

    def _get_tokens_from_db(self):
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

    def get_user_followed_artists(self):
        url = "https://api.spotify.com/v1/me/following?type=artist&limit=50"
        artists = []
        while True:
            response = self._request("GET", url, timeout=10)
            response.raise_for_status()
            data = response.json()
            artists.extend(data["artists"]["items"])
            if not data["artists"]["next"]:
                break
            url = data["artists"]["next"]

        return artists

    def get_artist_albums(self, id, include_groups: str | None = None):
        """Get an artist's albums.

        Args:
            id: Artist ID.
            include_groups (str | None, optional): can be a combination of "album", "single", "appears_on", like "album,single,apeears_on". Defaults to all.

        Returns:
            (list[dic[str, Any]]): Artist albums.

        Raises:
            requests.exceptions.HTTPError: If the API request fails/status code is not 2xx.
        """
        url = f"https://api.spotify.com/v1/artists/{id}/albums?limit=50"
        if include_groups:
            url += f"&include_groups={include_groups}"
        else:
            url += "&include_groups=album,single,appears_on"
        albums = []
        while True:
            response = self._request("GET", url, timeout=10)

            response.raise_for_status()
            response.headers.get("retry-after")

            data = response.json()
            albums.extend(data["items"])
            if not data["next"]:
                break
            url = data["next"]

        return albums
