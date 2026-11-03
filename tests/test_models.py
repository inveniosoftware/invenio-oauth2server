# SPDX-FileCopyrightText: 2015-2018 CERN.
# SPDX-FileCopyrightText: 2023-2024 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""OAuth2Server models test cases."""

from datetime import datetime, timedelta, timezone

import pytest
from invenio_accounts.models import User
from invenio_db import db

from invenio_oauth2server.errors import ScopeDoesNotExists
from invenio_oauth2server.models import Client, Token
from invenio_oauth2server.proxies import current_oauth2server


def test_empty_redirect_uri_and_scope(models_fixture):
    app = models_fixture
    with app.app_context():
        client = Client(
            client_id="dev2",
            client_secret="dev2",
            name="dev2",
            description="",
            is_confidential=False,
            user=app.test_user(),
            _redirect_uris="",
            _default_scopes="",
        )
        with db.session.begin_nested():
            db.session.add(client)

        assert client.default_redirect_uri is None
        assert client.redirect_uris == []
        assert client.default_scopes == []

        client.default_scopes = [
            "test:scope1",
            "test:scope2",
            "test:scope2",
        ]

        assert set(client.default_scopes) == set(["test:scope1", "test:scope2"])
        with pytest.raises(ScopeDoesNotExists):
            client.default_scopes = ["invalid"]

        with db.session.begin_nested():
            db.session.delete(client)


def test_token_scopes(models_fixture):
    app = models_fixture
    with app.app_context():
        client = Client(
            client_id="dev2",
            client_secret="dev2",
            name="dev2",
            description="",
            is_confidential=False,
            user=app.test_user(),
            _redirect_uris="",
            _default_scopes="",
        )
        token = Token(
            client=client,
            user=app.test_user(),
            token_type="bearer",
            access_token="dev_access",
            refresh_token="dev_refresh",
            expires=None,
            is_personal=False,
            is_internal=False,
            _scopes="",
        )
        token.scopes = ["test:scope1", "test:scope2", "test:scope2"]
        with db.session.begin_nested():
            db.session.add(client)
            db.session.add(token)

        assert set(token.scopes) == set(["test:scope1", "test:scope2"])
        with pytest.raises(ScopeDoesNotExists):
            token.scopes = ["invalid"]
        assert token.get_visible_scopes() == ["test:scope1"]

        with db.session.begin_nested():
            db.session.delete(client)


def test_registering_invalid_scope(models_fixture):
    app = models_fixture
    with app.app_context():
        with pytest.raises(TypeError):
            current_oauth2server.register_scope("test:scope")


def test_existing_client_and_token_rows_support_authlib_adapters(models_fixture):
    """Existing OAuth2 rows remain usable by Authlib adapters."""
    app = models_fixture
    with app.app_context():
        expires = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
        client = Client(
            client_id="legacy-client",
            client_secret="legacy-secret",
            name="legacy-client",
            description="Existing OAuth2 client",
            is_confidential=True,
            user=app.test_user(),
            _redirect_uris="http://localhost/authorized",
            _default_scopes="test:scope1 test:scope2",
        )
        token = Token(
            client=client,
            user=app.test_user(),
            token_type="bearer",
            access_token="legacy-access",
            refresh_token="legacy-refresh",
            expires=expires,
            is_personal=False,
            is_internal=False,
            _scopes="test:scope1 test:scope2",
        )
        with db.session.begin_nested():
            db.session.add(client)
            db.session.add(token)

        stored_client = db.session.get(Client, "legacy-client")
        stored_token = Token.query.filter_by(access_token="legacy-access").one()

        assert stored_client.get_client_id() == "legacy-client"
        assert stored_client.check_client_secret("legacy-secret")
        assert stored_client.check_redirect_uri("http://localhost/authorized")
        assert stored_client.check_grant_type("authorization_code")
        assert stored_client.check_response_type("code")
        assert stored_client.get_allowed_scope("test:scope1") == "test:scope1"

        assert stored_token.check_client(stored_client)
        assert stored_token.get_client() == stored_client
        assert stored_token.get_user() == app.test_user()
        assert stored_token.get_scope() == "test:scope1 test:scope2"
        assert stored_token.get_expires_in() > 0
        assert not stored_token.is_expired()
        assert not stored_token.is_revoked()

        with db.session.begin_nested():
            db.session.delete(client)


def test_deletion_of_consumer_resource_owner(models_fixture):
    """Test deleting of connected user."""
    app = models_fixture
    with app.app_context():
        # delete consumer
        with db.session.begin_nested():
            db.session.delete(db.session.get(User, app.consumer_id))

            # assert that t2 deleted
            assert (
                db.session.query(
                    Token.query.filter(Token.id == app.u1c1u2t2_id).exists()
                ).scalar()
                is False
            )
            # still exist resource_owner and client_1 and token_1
            assert (
                db.session.query(
                    User.query.filter(User.id == app.resource_owner_id).exists()
                ).scalar()
                is True
            )

            assert (
                db.session.query(
                    Client.query.filter(Client.client_id == app.u1c1_id).exists()
                ).scalar()
                is True
            )

            assert (
                db.session.query(
                    Token.query.filter(Token.id == app.u1c1u1t1_id).exists()
                ).scalar()
                is True
            )

            # delete resource_owner
            db.session.delete(db.session.get(User, app.resource_owner_id))

            # still resource_owner and client_1 and token_1 deleted
            assert (
                db.session.query(
                    Client.query.filter(Client.client_id == app.u1c1_id).exists()
                ).scalar()
                is False
            )

            assert (
                db.session.query(
                    Token.query.filter(Token.id == app.u1c1u1t1_id).exists()
                ).scalar()
                is False
            )


def test_deletion_of_resource_owner_consumer(models_fixture):
    """Test deleting of connected user."""
    app = models_fixture

    with app.app_context():
        with db.session.begin_nested():
            db.session.delete(db.session.get(User, app.resource_owner_id))

        # assert that c1, t1, t2 deleted
        assert (
            db.session.query(
                Client.query.filter(Client.client_id == app.u1c1_id).exists()
            ).scalar()
            is False
        )

        assert (
            db.session.query(
                Token.query.filter(Token.id == app.u1c1u1t1_id).exists()
            ).scalar()
            is False
        )

        assert (
            db.session.query(
                Token.query.filter(Token.id == app.u1c1u2t2_id).exists()
            ).scalar()
            is False
        )

        # still exist consumer
        assert (
            db.session.query(
                User.query.filter(User.id == app.consumer_id).exists()
            ).scalar()
            is True
        )

        # delete consumer
        db.session.delete(db.session.get(User, app.consumer_id))


def test_deletion_of_client1(models_fixture):
    """Test deleting of connected user."""
    app = models_fixture

    # delete client_1
    with app.app_context():
        with db.session.begin_nested():
            db.session.delete(db.session.get(Client, app.u1c1_id))

            # assert that token_1, token_2 deleted
            assert (
                db.session.query(
                    Token.query.filter(Token.id == app.u1c1u1t1_id).exists()
                ).scalar()
                is False
            )

            assert (
                db.session.query(
                    Token.query.filter(Token.id == app.u1c1u2t2_id).exists()
                ).scalar()
                is False
            )

            # still exist resource_owner, consumer
            assert (
                db.session.query(
                    User.query.filter(User.id == app.resource_owner_id).exists()
                ).scalar()
                is True
            )

            assert (
                db.session.query(
                    User.query.filter(User.id == app.consumer_id).exists()
                ).scalar()
                is True
            )

            # delete consumer
            db.session.delete(db.session.get(User, app.consumer_id))


def test_deletion_of_token1(models_fixture):
    """Test deleting of connected user."""
    app = models_fixture

    # delete token_1
    with app.app_context():
        with db.session.begin_nested():
            db.session.delete(db.session.get(Token, app.u1c1u1t1_id))

        # still exist resource_owner, consumer, client_1, token_2
        assert (
            db.session.query(
                User.query.filter(User.id == app.resource_owner_id).exists()
            ).scalar()
            is True
        )

        assert (
            db.session.query(
                User.query.filter(User.id == app.consumer_id).exists()
            ).scalar()
            is True
        )

        assert (
            db.session.query(
                Client.query.filter(Client.client_id == app.u1c1_id).exists()
            ).scalar()
            is True
        )

        assert (
            db.session.query(
                Token.query.filter(Token.id == app.u1c1u2t2_id).exists()
            ).scalar()
            is True
        )

        # delete consumer
        db.session.delete(db.session.get(User, app.consumer_id))


def test_deletion_of_token2(models_fixture):
    """Test deleting of connected user."""
    app = models_fixture

    # delete token_2
    with app.app_context():
        with db.session.begin_nested():
            db.session.delete(db.session.get(Token, app.u1c1u2t2_id))

        # still exist resource_owner, consumer, client_1, token_1
        assert (
            db.session.query(
                User.query.filter(User.id == app.resource_owner_id).exists()
            ).scalar()
            is True
        )

        assert (
            db.session.query(
                User.query.filter(User.id == app.consumer_id).exists()
            ).scalar()
            is True
        )

        assert (
            db.session.query(
                Client.query.filter(Client.client_id == app.u1c1_id).exists()
            ).scalar()
            is True
        )

        assert (
            db.session.query(
                Token.query.filter(Token.id == app.u1c1u1t1_id).exists()
            ).scalar()
            is True
        )

        # delete consumer
        db.session.delete(db.session.get(User, app.consumer_id))
