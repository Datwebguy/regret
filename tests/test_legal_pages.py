def test_terms_of_use_is_public_html(client):
    response = client.get("/terms")
    assert response.status_code == 200
    text = response.text
    assert "Terms of Use" in text
    assert "not a broker-dealer" in text
    assert "data" in text and "trading" in text
    assert "account:write" in text


def test_privacy_policy_is_public_html(client):
    response = client.get("/privacy")
    assert response.status_code == 200
    text = response.text
    assert "Privacy Policy" in text
    assert "regret_session" in text
    assert "localStorage" in text
    assert "Fly.io" in text
    assert "Alpaca" in text


def test_legal_pages_do_not_require_a_session(client):
    assert client.get("/terms").status_code == 200
    assert client.get("/privacy").status_code == 200
    assert "text/html" in client.get("/terms").headers.get("content-type", "")
    css = client.get("/legal.css")
    assert css.status_code == 200
    assert "text/css" in css.headers.get("content-type", "")
    logo = client.get("/mark.png")
    assert logo.status_code == 200
    assert "image/png" in logo.headers.get("content-type", "")
    assert client.get("/favicon.ico").status_code == 200
