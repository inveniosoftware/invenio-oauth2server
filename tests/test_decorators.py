# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (c) 2015, 2016, 2017 CERN.
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

"""OAuth2Server decorators test cases."""

from datetime import datetime

from flask import url_for
from invenio_accounts.proxies import current_accounts

from invenio_oauth2server.utils import rebuild_access_tokens


def test_require_api_auth_oauthlib_urldecode_issue(resource_fixture):
    app = resource_fixture
    with app.test_client() as client:
        res = client.get(app.url_for_test1resource, query_string='q=k:v')
        assert 401 == res.status_code


def test_require_api_auth_test1(resource_fixture):
    app = resource_fixture
    with app.test_client() as client:
        res = client.get(app.url_for_test1resource)
        assert 401 == res.status_code
        assert 'Set-Cookie' not in res.headers
        res = client.get(app.url_for_test1resource_token)
        assert 200 == res.status_code
        assert 'Set-Cookie' not in res.headers


def test_require_api_auth_test2(resource_fixture):
    app = resource_fixture
    with app.test_client() as client:
        res = client.get(app.url_for_test2resource)
        assert 401 == res.status_code
        assert 'Set-Cookie' not in res.headers
        res = client.get(app.url_for_test2resource_token)
        assert 200 == res.status_code
        assert 'Set-Cookie' not in res.headers


def test_require_oauth_scopes_test1(resource_fixture):
    app = resource_fixture
    with app.test_client() as client:
        res = client.post(app.url_for_test1resource_token)
        assert 200 == res.status_code
        assert 'Set-Cookie' not in res.headers
        res = client.post(app.url_for_test1resource_token_noscope)
        assert 403 == res.status_code
        assert 'Set-Cookie' not in res.headers


def test_require_oauth_scopes_test2(resource_fixture):
    app = resource_fixture
    with app.test_client() as client:
        res = client.post(app.url_for_test2resource_token)
        assert 200 == res.status_code
        assert 'Set-Cookie' not in res.headers
        res = client.post(app.url_for_test2resource_token_noscope)
        assert 403 == res.status_code
        assert 'Set-Cookie' not in res.headers


def test_require_oauth_scopes_allow_anonymous(resource_fixture):
    app = resource_fixture
    with app.test_client() as client:
        res = client.get(app.url_for_test4resource)
        assert 200 == res.status_code
        assert b'None' == res.data
        assert 'Set-Cookie' not in res.headers

        res = client.get(app.url_for_test4resource_token)
        assert 200 == res.status_code
        assert u'{0}'.format(app.user_id).encode('utf-8') == res.data
        assert 'Set-Cookie' not in res.headers


def test_rest_extension(resource_fixture):
    app = resource_fixture
    with app.test_client() as client:
        res = client.post(app.url_for_test4resource)
        assert 200 == res.status_code
        assert b'None' == res.data
        assert 'Set-Cookie' not in res.headers

        res = client.post(app.url_for_test4resource_token)
        assert 200 == res.status_code
        assert u'{0}'.format(app.user_id).encode('utf-8') == res.data
        assert 'Set-Cookie' not in res.headers


def test_access_login_required(resource_fixture):
    app = resource_fixture
    with app.test_client() as client:
        # try to access to authentication required zone
        res = client.post(app.url_for_test3resource)
        assert 401 == res.status_code
        assert 'Set-Cookie' not in res.headers
        # try to access a scope protected zone (and pass)
        res = client.post(app.url_for_test2resource_token)
        assert 200 == res.status_code
        # try to access to authentication required zone
        res = client.post(app.url_for_test3resource)
        assert 401 == res.status_code
        assert 'Set-Cookie' not in res.headers
        # try to access a scope protected zone (and fail)
        res = client.post(app.url_for_test2resource_token_noscope)
        assert 403 == res.status_code
        # try to access to login_required zone (and redirected to login)
        res = client.post(app.url_for_test3resource)
        assert 401 == res.status_code
        assert 'Set-Cookie' not in res.headers
        # login
        res = client.post(url_for('security.login'), data=dict(
            email='info@inveniosoftware.org',
            password='tester'
        ))
        assert 'Set-Cookie' in res.headers
        # try to access to login_required zone (and pass)
        res = client.post(app.url_for_test3resource)
        assert 200 == res.status_code
        assert 'Set-Cookie' not in res.headers
        # logout
        res = client.get(url_for('security.logout'))
        assert 302 == res.status_code
        # try to access to login_required zone (and pass)
        res = client.post(app.url_for_test3resource)
        assert 401 == res.status_code
        assert 'Set-Cookie' not in res.headers


def test_jwt_client(resource_fixture):
    """Test client."""
    app = resource_fixture
    # Enable JWT
    app.config['ACCOUNTS_JWT_ENABLE'] = True
    with app.test_client() as client:

        # Try to access to authentication required zone
        res = client.post(app.url_for_test3resource)
        assert 401 == res.status_code

        # Login
        res = client.post(url_for('security.login'), data=dict(
            email='info@inveniosoftware.org',
            password='tester'
        ))
        assert 'Set-Cookie' in res.headers
        # Try to access to without a JWT
        res = client.post(app.url_for_test3resource)
        assert 400 == res.status_code

        # Generate a token
        token = current_accounts.jwt_creation_factory()
        # Make the request
        res = client.post(
            app.url_for_test3resource,
            headers=[
                ('Authorization', 'Bearer {}'.format(token))
            ]
        )
        assert 200 == res.status_code

        # Try with invalid user
        token = current_accounts.jwt_creation_factory(user_id=-20)
        # Make the request
        res = client.post(
            app.url_for_test3resource,
            headers=[
                ('Authorization', 'Bearer {}'.format(token))
            ]
        )
        assert 403 == res.status_code
        assert 'The JWT token is not valid.' in res.get_data(as_text=True)

        # Try to access with expired token
        extra = dict(
            exp=datetime(1970, 1, 1),
        )
        # Create token
        token = current_accounts.jwt_creation_factory(additional_data=extra)
        # Make the request
        res = client.post(
            app.url_for_test3resource,
            headers=[
                ('Authorization', 'Bearer {0}'.format(token))
            ]
        )
        assert 'The JWT token is expired.' in res.get_data(as_text=True)

        # Not correct Schema
        # Generate a token
        token = current_accounts.jwt_creation_factory()
        # Make the request
        res = client.post(
            app.url_for_test3resource,
            headers=[
                ('Authorization', 'Avengers {}'.format(token))
            ]
        )
        assert 400 == res.status_code
        assert 'Missing required header argument.' in res.get_data(
            as_text=True)

        # Check different header type
        app.config['OAUTH2SERVER_JWT_AUTH_HEADER'] = 'X-Travis-Mark-XLII'
        app.config['OAUTH2SERVER_JWT_AUTH_HEADER_TYPE'] = None
        # Create token
        token = current_accounts.jwt_creation_factory()
        # Make the request
        res = client.post(
            app.url_for_test3resource,
            headers=[
                ('X-Travis-Mark-XLII', '{0}'.format(token))
            ]
        )
        assert 200 == res.status_code
