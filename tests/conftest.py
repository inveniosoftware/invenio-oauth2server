# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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


"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os

import pytest
from flask import Flask, url_for
from flask.views import MethodView
from flask_babelex import Babel
from flask_breadcrumbs import Breadcrumbs
from flask_cli import FlaskCLI
from flask_mail import Mail
from flask_menu import Menu
from helpers import create_oauth_client, patch_request
from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint as accounts_blueprint
from invenio_db import InvenioDB, db
from mock import MagicMock

from invenio_oauth2server import InvenioOAuth2Server
from invenio_oauth2server.decorators import require_api_auth, \
    require_oauth_scopes
from invenio_oauth2server.models import Client, Scope, Token
from invenio_oauth2server.views import server_blueprint, settings_blueprint


@pytest.fixture()
def app(request):
    """Flask application fixture."""
    app = Flask('testapp')
    app.config.update(
        TESTING=True,
        LOGIN_DISABLED=False,
        SECRET_KEY='test_key',
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                          'sqlite:///test.db'),
        WTF_CSRF_ENABLED=False,
        OAUTHLIB_INSECURE_TRANSPORT=True,
        OAUTH2_CACHE_TYPE='simple',
        SECURITY_PASSWORD_HASH='plaintext',
        SECURITY_PASSWORD_SCHEMES=['plaintext'],
    )
    FlaskCLI(app)
    Babel(app)
    Mail(app)
    Menu(app)
    Breadcrumbs(app)
    InvenioDB(app)
    InvenioAccounts(app)
    app.register_blueprint(accounts_blueprint)
    InvenioOAuth2Server(app)
    app.register_blueprint(server_blueprint)
    app.register_blueprint(settings_blueprint)

    with app.app_context():
        db.create_all()

    def teardown():
        with app.app_context():
            db.drop_all()

    request.addfinalizer(teardown)
    return app


@pytest.fixture
def models_fixture(app):
    """Fixture that contains the test data for models tests."""
    from invenio_oauth2server.proxies import current_oauth2server
    with app.app_context():
        # Register a test scope
        current_oauth2server.register_scope(Scope('test:scope1'))
        current_oauth2server.register_scope(Scope('test:scope2',
                                                  internal=True))
        datastore = app.extensions['security'].datastore
        with db.session.begin_nested():
            app.test_user = datastore.create_user(
                email='info@invenio-software.org', password='tester',
            )
            app.resource_owner = datastore.create_user(
                email='resource_owner@invenio-software.org', password='test'
            )
            app.consumer = datastore.create_user(
                email='consumer@invenio-software.org', password='test'
            )

            # create resource_owner -> client_1
            app.u1c1 = Client(client_id='client_test_u1c1',
                              client_secret='client_test_u1c1',
                              name='client_test_u1c1',
                              description='',
                              is_confidential=False,
                              user=app.resource_owner,
                              _redirect_uris='',
                              _default_scopes=""
                              )
            # create resource_owner -> client_1 / resource_owner -> token_1
            app.u1c1u1t1 = Token(client=app.u1c1,
                                 user=app.resource_owner,
                                 token_type='u',
                                 access_token='dev_access_1',
                                 refresh_token='dev_refresh_1',
                                 expires=None,
                                 is_personal=False,
                                 is_internal=False,
                                 _scopes='',
                                 )
            # create consumer -> client_1 / resource_owner -> token_2
            app.u1c1u2t2 = Token(client=app.u1c1,
                                 user=app.consumer,
                                 token_type='u',
                                 access_token='dev_access_2',
                                 refresh_token='dev_refresh_2',
                                 expires=None,
                                 is_personal=False,
                                 is_internal=False,
                                 _scopes='',
                                 )
            db.session.add(app.u1c1)
            db.session.add(app.u1c1u1t1)
            db.session.add(app.u1c1u2t2)
    return app


@pytest.fixture
def provider_fixture(app):
    """Fixture that contains test data for provider tests."""
    from invenio_oauth2server.proxies import current_oauth2server
    # Mock the oauth client calls to prevent them from going online.
    oauth_client = create_oauth_client(app, 'oauth2test')
    oauth_client.http_request = MagicMock(
        side_effect=patch_request(app)
    )
    datastore = app.extensions['security'].datastore
    with app.test_request_context():
        with db.session.begin_nested():
            current_oauth2server.register_scope(Scope('test:scope'))

            app.user1 = datastore.create_user(
                email='info@invenio-software.org', password='tester',
                active=True,
            )
            app.user2 = datastore.create_user(
                email='abuse@invenio-software.org', password='tester2',
                active=True
            )

            app.c1 = Client(client_id='dev',
                            client_secret='dev',
                            name='dev',
                            description='',
                            is_confidential=False,
                            user=app.user1,
                            _redirect_uris=url_for(
                                'oauth2test.authorized', _external=True
                            ),
                            _default_scopes='test:scope'
                            )

            app.c2 = Client(client_id='confidential',
                            client_secret='confidential',
                            name='confidential',
                            description='',
                            is_confidential=True,
                            user=app.user1,
                            _redirect_uris=url_for(
                                'oauth2test.authorized', _external=True
                            ),
                            _default_scopes='test:scope'
                            )
            db.session.add(app.c1)
            db.session.add(app.c2)
        app.personal_token = Token.create_personal('test-personal',
                                                   app.user1.id,
                                                   scopes=[],
                                                   is_internal=True)

    return app


@pytest.fixture
def resource_fixture(app):
    """Fixture that contains the test data for models tests."""
    from flask import request
    from invenio_oauth2server.proxies import current_oauth2server

    # Setup API resources
    class Test1Resource(MethodView):
        # NOTE: Method decorators are applied in reverse order
        decorators = [
            require_oauth_scopes('test:testscope'),
            require_api_auth(),
        ]

        def get(self):
            assert request.oauth.access_token
            return "success", 200

        def post(self):
            assert request.oauth.access_token
            return "success", 200

    class Test2Resource(MethodView):

        @require_api_auth()
        @require_oauth_scopes('test:testscope')
        def get(self):
            assert request.oauth.access_token
            return "success", 200

        @require_api_auth()
        @require_oauth_scopes('test:testscope')
        def post(self):
            assert request.oauth.access_token
            return "success", 200

    # Register API resources
    app.add_url_rule(
        '/api/test1/decoratorstestcase/',
        view_func=Test1Resource.as_view('test1resource'),
    )
    app.add_url_rule(
        '/api/test2/decoratorstestcase/',
        view_func=Test2Resource.as_view('test2resource'),
    )

    datastore = app.extensions['security'].datastore
    with app.app_context():
        # Register a test scope
        current_oauth2server.register_scope(Scope(
            'test:testscope',
            group='Test',
            help_text='Test scope'
        ))
        with db.session.begin_nested():
            app.user = datastore.create_user(
                email='info@invenio-software.org', password='tester',
                active=True,
            )

        # Create tokens
        app.token = Token.create_personal(
            'test-', app.user.id, scopes=['test:testscope'], is_internal=True)
        app.token_noscope = Token.create_personal(
            'test-', app.user.id, scopes=[], is_internal=True)

    with app.test_request_context():
        app.url_for_test1resource = url_for('test1resource')
        app.url_for_test2resource = url_for('test2resource')
        app.url_for_test1resource_token = url_for(
            'test1resource', access_token=app.token.access_token
        )
        app.url_for_test2resource_token = url_for(
            'test2resource', access_token=app.token.access_token
        )
        app.url_for_test1resource_token_noscope = url_for(
            'test1resource', access_token=app.token_noscope.access_token
        )
        app.url_for_test2resource_token_noscope = url_for(
            'test2resource', access_token=app.token_noscope.access_token
        )

    return app
