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

"""OAuth2Server decorators test cases."""

from flask_security import url_for_security


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
    from invenio_oauth2server import InvenioOAuth2ServerREST
    app = resource_fixture
    InvenioOAuth2ServerREST(app)
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
        # try to access to login_required zone (and redirected to login)
        res = client.post(app.url_for_test3resource)
        assert 302 == res.status_code
        assert 'Set-Cookie' in res.headers
        assert res.headers[
            'Location'].startswith('http://localhost/login/?next=')
        # try to access a scope protected zone (and pass)
        res = client.post(app.url_for_test2resource_token)
        assert 200 == res.status_code
        # try to access to login_required zone (and redirected to login)
        res = client.post(app.url_for_test3resource)
        assert 302 == res.status_code
        assert 'Set-Cookie' in res.headers
        # try to access a scope protected zone (and fail)
        assert res.headers[
            'Location'].startswith('http://localhost/login/?next=')
        res = client.post(app.url_for_test2resource_token_noscope)
        assert 403 == res.status_code
        # try to access to login_required zone (and redirected to login)
        res = client.post(app.url_for_test3resource)
        assert 302 == res.status_code
        assert 'Set-Cookie' in res.headers
        # login
        res = client.post(url_for_security('login'), data=dict(
            email="info@invenio-software.org",
            password="tester"
        ))
        assert 'Set-Cookie' in res.headers
        # try to access to login_required zone (and pass)
        res = client.post(app.url_for_test3resource)
        assert 200 == res.status_code
        assert 'Set-Cookie' not in res.headers
