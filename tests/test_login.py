def test_login(client):
    actual = client.get("/spotify/login")
    expected = 302

    assert actual.status_code == expected
