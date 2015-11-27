# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (c) 2015 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""OAuth2Server models test cases."""

import pytest
from invenio_accounts.models import User
from invenio_db import db

from invenio_oauth2server.errors import ScopeDoesNotExists
from invenio_oauth2server.models import Client, Scope, Token
from invenio_oauth2server.proxies import current_oauth2server


def test_empty_redirect_uri_and_scope(models_fixture):
    app = models_fixture
    with app.app_context():

        client = Client(
            client_id='dev2',
            client_secret='dev2',
            name='dev2',
            description='',
            is_confidential=False,
            user=app.test_user,
            _redirect_uris='',
            _default_scopes=""
        )
        with db.session.begin_nested():
            db.session.add(client)

        assert client.default_redirect_uri is None
        assert client.redirect_uris == []
        assert client.default_scopes == []

        client.default_scopes = ['test:scope1', 'test:scope2', 'test:scope2', ]

        assert set(client.default_scopes) == set(
            ['test:scope1', 'test:scope2'])
        with pytest.raises(ScopeDoesNotExists):
            client.default_scopes = ['invalid']

        with db.session.begin_nested():
            db.session.delete(client)


def test_token_scopes(models_fixture):
    app = models_fixture
    with app.app_context():
        client = Client(
            client_id='dev2',
            client_secret='dev2',
            name='dev2',
            description='',
            is_confidential=False,
            user=app.test_user,
            _redirect_uris='',
            _default_scopes=""
        )
        token = Token(
            client=client,
            user=app.test_user,
            token_type='bearer',
            access_token='dev_access',
            refresh_token='dev_refresh',
            expires=None,
            is_personal=False,
            is_internal=False,
            _scopes='',
        )
        token.scopes = ['test:scope1', 'test:scope2', 'test:scope2']
        with db.session.begin_nested():
            db.session.add(client)
            db.session.add(token)

        assert set(token.scopes) == set(
            ['test:scope1', 'test:scope2'])
        with pytest.raises(ScopeDoesNotExists):
            token.scopes = ['invalid']
        assert token.get_visible_scopes() == ['test:scope1']

        with db.session.begin_nested():
            db.session.delete(client)


def test_registering_invalid_scope(models_fixture):
    app = models_fixture
    with app.app_context():
        with pytest.raises(TypeError):
            current_oauth2server.register_scope('test:scope')


def test_deletion_of_consumer_resource_owner(models_fixture):
    """Test deleting of connected user."""
    app = models_fixture
    with app.app_context():
        uid_1 = app.resource_owner.id
        cid_1 = app.u1c1.client_id
        tid_1 = app.u1c1u1t1.id
        tid_2 = app.u1c1u2t2.id

        # start testing

        # delete consumer
        with db.session.begin_nested():
            db.session.delete(app.consumer)

        # assert that t2 deleted
            assert db.session.query(
                Token.query.filter(
                    Token.id == tid_2).exists()).scalar() is False
        # still exist resource_owner and client_1 and token_1
            assert db.session.query(
                User.query.filter(User.id == uid_1).exists()).scalar() is True

            assert db.session.query(
                Client.query.filter(
                    Client.client_id == cid_1).exists()).scalar() is True

            assert db.session.query(
                Token.query.filter(Token.id == tid_1).exists()).scalar() is \
                True

        # delete resource_owner
            db.session.delete(app.resource_owner)

        # still resource_owner and client_1 and token_1 deleted
            assert db.session.query(
                Client.query.filter(
                    Client.client_id == cid_1).exists()).scalar() is False

            assert db.session.query(
                Token.query.filter(Token.id == tid_1).exists()).scalar() is \
                False


def test_deletion_of_resource_owner_consumer(models_fixture):
    """Test deleting of connected user."""
    app = models_fixture

    uid_consumer = app.consumer.id
    cid_1 = app.u1c1.client_id
    tid_1 = app.u1c1u1t1.id
    tid_2 = app.u1c1u2t2.id

    # start testing

    # delete consumer
    with app.app_context():
        with db.session.begin_nested():
            db.session.delete(app.resource_owner)

        # assert that c1, t1, t2 deleted
        assert db.session.query(
            Client.query.filter(
                Client.client_id == cid_1).exists()).scalar() is False

        assert db.session.query(
            Token.query.filter(
                Token.id == tid_1).exists()).scalar() is False

        assert db.session.query(
            Token.query.filter(
                Token.id == tid_2).exists()).scalar() is False

        # still exist consumer
        assert db.session.query(
            User.query.filter(
                User.id == uid_consumer).exists()).scalar() is True

        # delete consumer
        db.session.delete(app.consumer)


def test_deletion_of_client1(models_fixture):
    """Test deleting of connected user."""
    app = models_fixture

    uid_resource_manager = app.resource_owner.id
    uid_consumer = app.consumer.id
    tid_1 = app.u1c1u1t1.id
    tid_2 = app.u1c1u2t2.id

    # start testing

    # delete client_1
    with app.app_context():
        with db.session.begin_nested():
            db.session.delete(app.u1c1)

            # assert that token_1, token_2 deleted
            assert db.session.query(
                Token.query.filter(
                    Token.id == tid_1).exists()).scalar() is False

            assert db.session.query(
                Token.query.filter(
                    Token.id == tid_2).exists()).scalar() is False

            # still exist resource_owner, consumer
            assert db.session.query(
                User.query.filter(
                    User.id == uid_resource_manager).exists()
                ).scalar() is True

            assert db.session.query(
                User.query.filter(
                    User.id == uid_consumer).exists()).scalar() is True

            # delete consumer
            db.session.delete(app.consumer)


def test_deletion_of_token1(models_fixture):
    """Test deleting of connected user."""
    app = models_fixture

    uid_resource_manager = app.resource_owner.id
    uid_consumer = app.consumer.id
    cid_1 = app.u1c1.client_id
    tid_2 = app.u1c1u2t2.id

    # start testing

    # delete token_1
    with app.app_context():
        with db.session.begin_nested():
            db.session.delete(app.u1c1u1t1)

        # still exist resource_owner, consumer, client_1, token_2
        assert db.session.query(
            User.query.filter(
                User.id == uid_resource_manager).exists()).scalar() is True

        assert db.session.query(
            User.query.filter(
                User.id == uid_consumer).exists()).scalar() is True

        assert db.session.query(
            Client.query.filter(
                Client.client_id == cid_1).exists()).scalar() is True

        assert db.session.query(
            Token.query.filter(
                Token.id == tid_2).exists()).scalar() is True

        # delete consumer
        db.session.delete(app.consumer)


def test_deletion_of_token2(models_fixture):
    """Test deleting of connected user."""
    app = models_fixture
    uid_resource_manager = app.resource_owner.id
    uid_consumer = app.consumer.id
    cid_1 = app.u1c1.client_id
    tid_1 = app.u1c1u1t1.id

    # start testing

    # delete token_2
    with app.app_context():
        with db.session.begin_nested():
            db.session.delete(app.u1c1u2t2)

        # still exist resource_owner, consumer, client_1, token_1
        assert db.session.query(
            User.query.filter(
                User.id == uid_resource_manager).exists()).scalar() is True

        assert db.session.query(
            User.query.filter(
                User.id == uid_consumer).exists()).scalar() is True

        assert db.session.query(
            Client.query.filter(
                Client.client_id == cid_1).exists()).scalar() is True

        assert db.session.query(
            Token.query.filter(
                Token.id == tid_1).exists()).scalar() is True

        # delete consumer
        db.session.delete(app.consumer)
