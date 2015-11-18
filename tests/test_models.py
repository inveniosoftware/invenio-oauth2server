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

from flask_registry import RegistryError

from invenio_accounts.models import User
from invenio_db import db
from invenio_oauth2server.errors import ScopeDoesNotExists
from invenio_oauth2server.models import Client, Scope, Token
from invenio_oauth2server.registry import scopes


def test_empty_redirect_uri_and_scope(app):
    with app.app_context():
        # Register a test scope
        scopes.register(Scope('test:scope1'))
        scopes.register(Scope('test:scope2', internal=True))

        test_user = User(email='info@invenio-software.org')

        client = Client(
            client_id='dev',
            client_secret='dev',
            name='dev',
            description='',
            is_confidential=False,
            user=test_user,
            _redirect_uris='',
            _default_scopes=""
        )
        with db.session.begin_nested():
            db.session.add(client)

        assert client.default_redirect_uri is None
        assert client.redirect_uris == []
        assert client.default_scopes == []

        client.default_scopes = ['test:scope1', 'test:scope2', 'test:scope2', ]

        assert client.default_scopes == ['test:scope1', 'test:scope2']
        with pytest.raises(ScopeDoesNotExists):
            client.default_scopes = ['invalid']

        with db.session.begin_nested():
            db.session.delete(client)


def test_token_scopes(app):
    with app.app_context():
        # Register a test scope
        scopes.register(Scope('test:scope1'))
        scopes.register(Scope('test:scope2', internal=True))

        test_user = User(email='info@invenio-software.org')

        client = Client(
            client_id='dev2',
            client_secret='dev2',
            name='dev2',
            description='',
            is_confidential=False,
            user=test_user,
            _redirect_uris='',
            _default_scopes=""
        )
        token = Token(
            client=client,
            user=test_user,
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

        assert token.scopes == ['test:scope1', 'test:scope2']
        with pytest.raises(ScopeDoesNotExists):
            token.scopes = ['invalid']
        assert token.get_visible_scopes() == ['test:scope1']

        with db.session.begin_nested():
            db.session.delete(client)


def test_registering_invalid_scope(app):
    with app.app_context():
        with pytest.raises(RegistryError):
            scopes.register('test:scope')


def test_deletion_of_consumer_resource_owner(app):
    """Test deleting of connected user."""
    with app.app_context():
        resource_owner = None
        consumer = None
        user1_client1 = None
        u1c1u1t1 = None
        u1c1u2t2 = None
        with db.session.begin_nested():
            resource_owner = User(email='resource_owner@invenio-software.org',
                                  password='test')
            consumer = User(email='consumer@invenio-software.org',
                            password='test')
            # create resource_owner -> client_1
            user1_client1 = Client(client_id='client_test_u1c1',
                                   client_secret='client_test_u1c1',
                                   name='client_test_u1c1',
                                   description='',
                                   is_confidential=False,
                                   user=resource_owner,
                                   _redirect_uris='',
                                   _default_scopes=""
                                   )
            # create resource_owner -> client_1 / resource_owner -> token_1
            u1c1u1t1 = Token(client=user1_client1,
                             user=resource_owner,
                             token_type='u',
                             access_token='dev_access_1',
                             refresh_token='dev_refresh_1',
                             expires=None,
                             is_personal=False,
                             is_internal=False,
                             _scopes='',
                             )
            # create consumer -> client_1 / resource_owner -> token_2
            u1c1u2t2 = Token(client=user1_client1,
                             user=consumer,
                             token_type='u',
                             access_token='dev_access_2',
                             refresh_token='dev_refresh_2',
                             expires=None,
                             is_personal=False,
                             is_internal=False,
                             _scopes='',
                             )
            db.session.add(resource_owner)
            db.session.add(consumer)
            db.session.add(user1_client1)
            db.session.add(u1c1u1t1)
            db.session.add(u1c1u2t2)
        uid_1 = resource_owner.id
        cid_1 = user1_client1.client_id
        tid_1 = u1c1u1t1.id
        tid_2 = u1c1u2t2.id

        # start testing

        # delete consumer
        with db.session.begin_nested():
            db.session.delete(consumer)

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
            db.session.delete(resource_owner)

        # still resource_owner and client_1 and token_1 deleted
            assert db.session.query(
                Client.query.filter(
                    Client.client_id == cid_1).exists()).scalar() is False

            assert db.session.query(
                Token.query.filter(Token.id == tid_1).exists()).scalar() is \
                False
