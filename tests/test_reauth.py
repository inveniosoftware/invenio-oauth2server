# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-License-Identifier: MIT

"""Test re-authentication before creating API credentials."""

import re

from flask import url_for
from helpers import login, parse_redirect

from invenio_oauth2server.models import Client, Token


def _reauth(app, client):
    """Re-authenticate with the code sent by email."""
    reauth_url = url_for("invenio_accounts.reauth")
    with app.extensions["mail"].record_messages() as outbox:
        client.post(reauth_url, data={"action": "send"})
    assert len(outbox) == 1
    code = re.search(r"\b(\d{6})\b", outbox[0].body).group(1)
    res = client.post(reauth_url, data={"action": "verify", "verify-code": code})
    assert res.status_code == 302


def _is_reauth_redirect(res):
    return res.status_code == 302 and "/account/settings/reauth" in res.location


def test_token_new_requires_reauth(reauth_enabled, settings_fixture):
    app = settings_fixture
    with app.test_request_context():
        with app.test_client() as client:
            login(client)
            token_new_url = url_for("invenio_oauth2server_settings.token_new")

            assert _is_reauth_redirect(client.get(token_new_url))
            res = client.post(token_new_url, data={"name": "Test_Token"})
            assert _is_reauth_redirect(res)
            assert Token.query.count() == 0

            _reauth(app, client)
            assert client.get(token_new_url).status_code == 200
            res = client.post(
                token_new_url, data={"name": "Test_Token"}, follow_redirects=True
            )
            assert res.status_code == 200
            assert Token.query.count() == 1


def test_token_edit_requires_reauth_but_delete_does_not(
    reauth_enabled, settings_fixture
):
    app = settings_fixture
    with app.test_request_context():
        with app.test_client() as client:
            login(client)
            _reauth(app, client)
            client.post(
                url_for("invenio_oauth2server_settings.token_new"),
                data={"name": "Test_Token"},
            )
            token = Token.query.one()
            token_url = url_for(
                "invenio_oauth2server_settings.token_view", token_id=token.id
            )

    with app.test_request_context():
        with app.test_client() as client:
            login(client)
            assert client.get(token_url).status_code == 200

            res = client.post(token_url, data={"name": "Renamed"})
            assert _is_reauth_redirect(res)
            assert Token.query.one().client.name == "Test_Token"

            res = client.post(token_url, data={"delete": True})
            assert res.status_code == 302
            assert Token.query.count() == 0


def test_client_management_requires_reauth(reauth_enabled, settings_fixture):
    app = settings_fixture
    with app.test_request_context():
        with app.test_client() as client:
            login(client)
            client_new_url = url_for("invenio_oauth2server_settings.client_new")
            data = dict(
                name="Test",
                description="desc",
                website="http://inveniosoftware.org",
                redirect_uris="http://localhost/oauth/authorized/",
                is_confidential=True,
            )

            assert _is_reauth_redirect(client.get(client_new_url))
            assert _is_reauth_redirect(client.post(client_new_url, data=data))
            assert Client.query.count() == 0

            _reauth(app, client)
            res = client.post(client_new_url, data=data)
            assert res.status_code == 302
            c = Client.query.one()
            secret = c.client_secret

    with app.test_request_context():
        with app.test_client() as client:
            login(client)
            view_url = url_for(
                "invenio_oauth2server_settings.client_view", client_id=c.client_id
            )
            reset_url = url_for(
                "invenio_oauth2server_settings.client_reset", client_id=c.client_id
            )

            assert client.get(view_url).status_code == 200
            data["redirect_uris"] = "https://evil.org/"
            assert _is_reauth_redirect(client.post(view_url, data=data))
            assert _is_reauth_redirect(client.post(reset_url, data={"reset": "yes"}))
            c = Client.query.one()
            assert c.client_secret == secret
            assert "evil.org" not in c._redirect_uris

            res = client.post(view_url, data={"delete": True})
            assert res.status_code == 302
            assert Client.query.count() == 0


def test_authorize_consent_requires_reauth(reauth_enabled, provider_fixture):
    app = provider_fixture
    with app.test_request_context():
        redirect_uri = url_for("oauth2test.authorized", _external=True)
        with app.test_client() as client:
            login(client)
            data = dict(
                redirect_uri=redirect_uri,
                scope="test:scope",
                response_type="code",
                client_id="confidential",
                state="mystate",
            )
            authorize_url = url_for("invenio_oauth2server.authorize")

            # The consent page itself is shown without re-authentication
            r = client.get(url_for("invenio_oauth2server.authorize", **data))
            assert r.status_code == 200

            # Approving is not
            r = client.post(authorize_url, data=dict(data, confirm="yes"))
            assert _is_reauth_redirect(r)
            _, params = parse_redirect(r.location)
            next_url, next_data = parse_redirect(params["next"][0])
            assert next_url == authorize_url
            assert next_data["client_id"] == ["confidential"]
            assert next_data["state"] == ["mystate"]

            # Rejecting still works without re-authentication
            r = client.post(authorize_url, data=dict(data, confirm="no"))
            next_url, res_data = parse_redirect(r.location)
            assert next_url == redirect_uri
            assert res_data["error"] == ["access_denied"]

            _reauth(app, client)
            r = client.post(authorize_url, data=dict(data, confirm="yes"))
            assert r.status_code == 302
            next_url, res_data = parse_redirect(r.location)
            assert next_url == redirect_uri
            assert res_data["code"]


def test_disabled_by_default(settings_fixture):
    app = settings_fixture
    with app.test_request_context():
        with app.test_client() as client:
            login(client)
            res = client.get(url_for("invenio_oauth2server_settings.token_new"))
            assert res.status_code == 200
