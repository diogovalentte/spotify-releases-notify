# Spotify Releases Notify

Project to notify you about new releases of your followed artists on Spotify.

It does it by running an API where you can login with your Spotify account and do requests to notify new releases. The API is projected to notify all releases from a specific day, so you should run it only once a day.

# How to install

## Docker

1. Create a [Spotify app](https://developer.spotify.com/dashboard). It'll be used to get your followed artists and releases.

- App name and description can be anything you want.
- Redirect URL should be an URL where you can access the container's API from your web-browser + `/spotify/callback`. Examples:
- `http://localhost:8000/spotify/callback`
- `https://yourdomain.com/spotify/callback`

2. Use the `docker-compose.yml` file in this repository to run the project. Use your Spotify's app client ID, secret, and redirect URL in the environment variables.

3. After the container is running, access the API route `/spotify/login` to authenticate with Spotify. Examples:

- `http://localhost:8000/spotify/login`
- `https://yourdomain.com/spotify/login`

4. You should be redirected to the API's callback route with the "OK" message after agreeing with the Spotify's permissions.
5. After this, the token used by the API is encrypted and saved in a database on `/config` inside the container.
6. Now that the API is authenticated, you can use the `/spotify/notify` route to get the new releases from your followed artists. It accepts query parameters:

- `include_groups`: A comma-separated list of keywords that will be used to filter the releases. The possible values are: `album`, `single`, `appears_on`, `compilation`. Default is `album,single,appears_on`.
- `notify_error`: If `true`, the API will send a notification to the user if an error occurs. Default is `true`.
- `date`: The date to get the releases from. It can be `today`, `yesterday`, or a specific date in the format `YYYY-MM-DD`. Default is today's date.

Examples:

- `http://localhost:8000/spotify/notify?date=1958-08-29&notify_error=false`
- `https://yourdomain.com/spotify/notify?date=yesterday&include_groups=album,single`

You can use a cron job to run the API once a day with the desired parameters:

```
0 0 * * * curl -X GET -H "accept: application/json" "http://localhost:8000/spotify/notify?date=yesterday&include_groups=album,single"
```

# Notes

## No API authentication system

This project doesn't have an authentication system to access the API. It's recommended to use it only in a private environment and exposing it only to login.

## Spotify's API rate limit

Spotify's API has a rate limit. If you follow many artists, the API will execute more call on the Spotify API.

If the API runs into the rate limit, the Spotify API's usually sends back how many seconds the API should wait before making another request. The API will wait and retry the request unless Spotify says it has to wait more than 24 hours. In this case, the API will return an error.
