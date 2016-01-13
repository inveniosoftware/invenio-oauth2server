# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
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

"""Test OAuth2Server providers."""

from __future__ import absolute_import, print_function

from datetime import datetime, timedelta

from flask import json, url_for
from helpers import login, parse_redirect
from invenio_db import db

from invenio_oauth2server.models import Client, Token


def test_client_salt(provider_fixture):
    app = provider_fixture
    with app.app_context():
        with db.session.begin_nested():
            client = Client(
                name='Test something',
                is_confidential=True,
                user_id=1,
            )

            client.gen_salt()
            assert len(client.client_id) == \
                app.config['OAUTH2SERVER_CLIENT_ID_SALT_LEN']
            assert len(client.client_secret) == \
                app.config['OAUTH2SERVER_CLIENT_SECRET_SALT_LEN']

            db.session.add(client)

        with db.session.begin_nested():
            db.session.delete(client)


def test_invalid_authorize_requests(provider_fixture):
    app = provider_fixture
    # First login on provider site
    with app.test_request_context():
        redirect_uri = url_for('oauth2test.authorized', _external=True)

        with app.test_client() as client:
            login(client)

            for client_id in ['dev', 'confidential']:
                scope = 'test:scope'
                response_type = 'code'

                error_url = url_for('invenio_oauth2server.errors',
                                    _external=True)

                # Valid request authorize request
                r = client.get(
                    url_for('invenio_oauth2server.authorize'),
                    data={
                        'redirect_uri': redirect_uri,
                        'scope': scope,
                        'response_type': response_type,
                        'client_id': client_id,
                    })
                assert r.status_code == 200

                # Invalid scope
                r = client.get(url_for(
                    'invenio_oauth2server.authorize',
                    redirect_uri=redirect_uri,
                    scope='INVALID',
                    response_type=response_type,
                    client_id=client_id,
                ))
                assert r.status_code == 302
                next_url, data = parse_redirect(r.location)
                assert data['error'] == 'invalid_scope'
                assert next_url == redirect_uri

                # Invalid response type
                r = client.get(url_for(
                    'invenio_oauth2server.authorize',
                    redirect_uri=redirect_uri,
                    scope=scope,
                    response_type='invalid',
                    client_id=client_id,
                ))
                assert r.status_code == 302
                next_url, data = parse_redirect(r.location)
                assert data['error'] == 'unauthorized_client'
                assert next_url == redirect_uri

                # Missing response_type
                r = client.get(url_for(
                    'invenio_oauth2server.authorize',
                    redirect_uri=redirect_uri,
                    scope=scope,
                    client_id=client_id,
                ))
                assert r.status_code == 302
                next_url, data = parse_redirect(r.location)
                assert data['error'] == 'invalid_request'
                assert next_url == redirect_uri

                # Duplicate parameter
                r = client.get(url_for(
                    'invenio_oauth2server.authorize',
                    redirect_uri=redirect_uri,
                    scope=scope,
                    response_type='invalid',
                    client_id=client_id,
                ) + "&client_id={0}".format(client_id))
                assert r.status_code == 302
                next_url, data = parse_redirect(r.location)
                assert data['error'] == 'invalid_request'
                assert next_url == redirect_uri

                # Invalid client_id
                r = client.get(url_for(
                    'invenio_oauth2server.authorize',
                    redirect_uri=redirect_uri,
                    scope=scope,
                    response_type=response_type,
                    client_id='invalid',
                ))
                assert r.status_code == 302
                next_url, data = parse_redirect(r.location)
                assert data['error'] == 'invalid_client_id'
                assert error_url in next_url

                r = client.get(next_url, query_string=data)
                assert 'invalid_client_id' in str(r.data)

                # Invalid redirect uri
                r = client.get(url_for(
                    'invenio_oauth2server.authorize',
                    redirect_uri='http://localhost/',
                    scope=scope,
                    response_type=response_type,
                    client_id=client_id,
                ))
                assert r.status_code == 302
                next_url, data = parse_redirect(r.location)
                assert data['error'] == 'mismatching_redirect_uri'
                assert error_url in next_url


def test_refresh_flow(provider_fixture):
    app = provider_fixture
    with app.test_request_context():
        base_url = 'https://{0}'.format(app.config['SERVER_NAME'])
        redirect_uri = url_for('oauth2test.authorized', _external=True)

        with app.test_client() as client:
            # First login on provider site
            login(client)

            data = dict(
                redirect_uri=redirect_uri,
                scope='test:scope',
                response_type='code',
                client_id='confidential',
                state='mystate'
            )

            r = client.get(url_for('invenio_oauth2server.authorize', **data))
            assert r.status_code == 200

            data['confirm'] = 'yes'
            data['scope'] = 'test:scope'
            data['state'] = 'mystate'

            # Obtain one time code
            r = client.post(
                url_for('invenio_oauth2server.authorize'), data=data
            )
            r.status_code == 302
            next_url, res_data = parse_redirect(r.location)
            assert res_data['code']
            assert res_data['state'] == 'mystate'

            # Exchange one time code for access token
            r = client.post(
                url_for('invenio_oauth2server.access_token'), data=dict(
                    client_id='confidential',
                    client_secret='confidential',
                    grant_type='authorization_code',
                    code=res_data['code'],
                )
            )
            assert r.status_code == 200
            json_resp = json.loads(r.get_data())
            assert json_resp['access_token']
            assert json_resp['refresh_token']
            assert json_resp['scope'] == 'test:scope'
            assert json_resp['token_type'] == 'Bearer'
            refresh_token = json_resp['refresh_token']
            old_access_token = json_resp['access_token']

            # Access token valid
            r = client.get(url_for('invenio_oauth2server.info',
                           access_token=old_access_token))
            assert r.status_code == 200

            # Obtain new access token with refresh token
            r = client.post(
                url_for('invenio_oauth2server.access_token'), data=dict(
                    client_id='confidential',
                    client_secret='confidential',
                    grant_type='refresh_token',
                    refresh_token=refresh_token,
                )
            )
            r.status_code == 200
            json_resp = json.loads(r.get_data())
            assert json_resp['access_token']
            assert json_resp['refresh_token']
            assert json_resp['access_token'] != old_access_token
            assert json_resp['refresh_token'] != refresh_token
            assert json_resp['scope'] == 'test:scope'
            assert json_resp['token_type'] == 'Bearer'

            # New access token valid
            r = client.get(url_for('invenio_oauth2server.info',
                                   access_token=json_resp['access_token']))
            assert r.status_code == 200

            # Old access token no longer valid
            r = client.get(url_for('invenio_oauth2server.info',
                                   access_token=old_access_token,),
                           base_url=base_url)
            assert r.status_code == 401


def web_auth_flow(provider_fixture):
        app = provider_fixture
        # Go to login - should redirect to oauth2 server for login an
        # authorization
        with app.app_context():
            with app.test_client() as client:
                r = client.get('/oauth2test/test-ping')

                # First login on provider site
                login(client)

                r = client.get('/oauth2test/login')
                assert r.status_code == 302
                next_url, data = parse_redirect(r.location)

                # Authorize page
                r = client.get(next_url, query_string=data)
                assert r.status_code == 200

                # User confirms request
                data['confirm'] = 'yes'
                data['scope'] = 'test:scope'
                data['state'] = ''

                r = client.post(next_url, data=data)
                assert r.status_code == 302
                next_url, data = parse_redirect(r.location)
                assert next_url == 'http://{0}/oauth2test/authorized'.format(
                    app.config['SERVER_NAME'])
                assert 'code' in data

                # User is redirected back to client site.
                # - The client view /oauth2test/authorized will in the
                #   background fetch the access token.
                r = client.get(next_url, query_string=data)
                assert r.status_code == 200

                # Authentication flow has now been completed, and the access
                # token can be used to access protected resources.
                r = client.get('/oauth2test/test-ping')
                assert r.status_code == 200
                assert json.loads(r.get_data()) == dict(ping='pong')

                # Authentication flow has now been completed, and the access
                # token can be used to access protected resources.
                r = client.get('/oauth2test/test-ping')
                assert r.status_code == 200
                assert json.loads(r.get_data()) == dict(ping='pong')

                r = client.get('/oauth2test/test-info')
                assert r.status_code == 200
                json_resp = json.loads(r.get_data())
                assert json_resp['client'] == 'confidential'
                assert json_resp['user'] == app.user1_id
                assert json_resp['scopes'] == [u'test:scope']

                # Access token doesn't provide access to this URL.
                r = client.get(
                    '/oauth2test/test-invalid',
                    base_url='http://{0}'.format(app.config['SERVER_NAME'])
                )
                assert r.status_code == 401

                # # Now logout
                r = client.get('/oauth2test/logout')
                assert r.status_code == 200
                assert r.data == "logout"

                # And try to access the information again
                r = client.get('/oauth2test/test-ping')
                assert r.status_code == 403


def test_implicit_flow(provider_fixture):
    app = provider_fixture
    with app.test_request_context():
        redirect_uri = url_for('oauth2test.authorized', _external=True)

        with app.test_client() as client:
            # First login on provider site
            login(client)

            for client_id in ['dev', 'confidential']:
                data = dict(
                    redirect_uri=redirect_uri,
                    response_type='token',  # For implicit grant type
                    client_id=client_id,
                    scope='test:scope',
                    state='teststate'
                )

                # Authorize page
                r = client.get(url_for(
                    'invenio_oauth2server.authorize',
                    **data
                ), follow_redirects=True)
                assert r.status_code == 200

                # User confirms request
                data['confirm'] = 'yes'
                data['scope'] = 'test:scope'
                data['state'] = 'teststate'

                r = client.post(url_for('invenio_oauth2server.authorize'),
                                data=data)
                assert r.status_code == 302
                # Important - access token exists in URI fragment and must not
                # be sent to the client.
                next_url, data = parse_redirect(r.location,
                                                parse_fragment=True)

                assert data['access_token']
                assert data['token_type'] == 'Bearer'
                assert data['state'] == 'teststate'
                assert data['scope'] == 'test:scope'
                assert data.get('refresh_token') is None
                assert next_url == redirect_uri

                # Authentication flow has now been completed, and the client
                # can use the access token to make request to the provider.
                r = client.get(url_for('invenio_oauth2server.info',
                                       access_token=data['access_token']))
                assert r.status_code == 200
                assert json.loads(r.get_data()).get('client') == client_id
                assert json.loads(r.get_data()).get('user') == app.user1_id
                assert json.loads(r.get_data()).get('scopes') \
                    == [u'test:scope']


def test_client_flow(provider_fixture):
    app = provider_fixture
    with app.test_request_context():
        with app.test_client() as client:
            data = dict(
                client_id='dev',
                client_secret='dev',  # A public client should NOT do this!
                grant_type='client_credentials',
                scope='test:scope',
            )

            # Public clients are not allowed to use
            # grant_type=client_credentials
            r = client.post(url_for(
                'invenio_oauth2server.access_token'
            ), data=data)
            assert r.status_code == 401
            assert json.loads(r.get_data()).get('error') == 'invalid_client'

            data = dict(
                client_id='confidential',
                client_secret='confidential',
                grant_type='client_credentials',
                scope='test:scope',
            )

            # Retrieve access token using client_credentials
            r = client.post(url_for(
                'invenio_oauth2server.access_token'
            ), data=data)
            assert r.status_code == 200

            data = json.loads(r.get_data())
            assert data['access_token']
            assert data['token_type'] == 'Bearer'
            assert data['scope'] == 'test:scope'
            assert data.get('refresh_token') is None

            # Authentication flow has now been completed, and the client can
            # use the access token to make request to the provider.
            r = client.get(url_for('invenio_oauth2server.info',
                                   access_token=data['access_token']))
            assert r.status_code == 200
            assert json.loads(r.get_data()).get('client') == 'confidential'
            assert json.loads(r.get_data()).get('user') == app.user1_id
            assert json.loads(r.get_data()).get('scopes') == [u'test:scope']


def test_auth_flow_denied(provider_fixture):
    app = provider_fixture
    with app.test_request_context():
        redirect_uri = url_for('oauth2test.authorized', _external=True)
        with app.test_client() as client:
            # First login on provider site
            login(client)

            r = client.get(url_for('oauth2test.login'))
            assert r.status_code == 302
            next_url, data = parse_redirect(r.location)

            # Authorize page
            r = client.get(next_url, query_string=data)
            assert r.status_code == 200

            # User rejects request
            data['confirm'] = 'no'
            data['scope'] = 'test:scope'
            data['state'] = ''

            r = client.post(next_url, data=data)
            assert r.status_code == 302
            next_url, data = parse_redirect(r.location)
            assert next_url == redirect_uri
            assert data.get('error') == 'access_denied'

        # Returned
        r = client.get(next_url, query_string=data)
        assert r.status_code == 200
        assert r.data == b'Access denied: error=access_denied'


def test_personal_access_token(provider_fixture):
    app = provider_fixture
    with app.test_request_context():
        with app.test_client() as client:
            r = client.get(
                url_for('invenio_oauth2server.ping'),
                query_string="access_token={0}".format(
                    app.personal_token)
            )
            assert r.status_code == 200
            assert json.loads(r.get_data()) == dict(ping='pong')

            # Access token is not valid for this scope
            r = client.get(
                url_for('invenio_oauth2server.info'),
                query_string="access_token={0}".format(
                    app.personal_token),
            )
            assert r.status_code == 401


def test_resource_auth_methods(provider_fixture):
    app = provider_fixture
    with app.test_request_context():
        with app.test_client() as client:
            # Query string
            r = client.get(
                url_for('invenio_oauth2server.ping'),
                query_string="access_token={0}".format(
                    app.personal_token)
            )
            r.status_code == 200
            assert json.loads(r.get_data()) == dict(ping='pong')

            # POST request body
            r = client.post(
                url_for('invenio_oauth2server.ping'),
                data=dict(access_token=app.personal_token),
            )
            assert r.status_code == 200
            assert json.loads(r.get_data()) == dict(ping='pong')

            # Authorization Header
            r = client.get(
                url_for('invenio_oauth2server.ping'),
                headers=[
                    ("Authorization",
                     "Bearer {0}".format(app.personal_token))]
                )
            assert r.status_code == 200
            assert json.loads(r.get_data()) == dict(ping='pong')


def test_settings_index(provider_fixture):
    app = provider_fixture
    with app.test_request_context():
        with app.test_client() as client:
            # Create a remote account (linked account)
            r = client.get(
                url_for('invenio_oauth2server_settings.index'),
                follow_redirects=True,
            )
            # assert 401 == r.status_code
            login(client)

            res = client.get(
                url_for('invenio_oauth2server_settings.index'),
            )
            assert 200 == res.status_code

            res = client.get(
                url_for('invenio_oauth2server_settings.client_new'),
            )
            assert 200 == res.status_code

            # Valid POST
            res = client.post(
                url_for('invenio_oauth2server_settings.client_new'),
                data=dict(
                    name='Test',
                    description='Test description',
                    website='http://invenio-software.org',
                    is_confidential=True,
                    redirect_uris="http://localhost/oauth/authorized/"
                )
            )
            assert 302 == res.status_code

            # Invalid redirect_uri (must be https)
            res = client.post(
                url_for('invenio_oauth2server_settings.client_new'),
                data=dict(
                    name='Test',
                    description='Test description',
                    website='http://invenio-software.org',
                    is_confidential=True,
                    redirect_uris="http://example.org/oauth/authorized/"
                )
            )
            assert 200 == res.status_code

            # Valid
            res = client.post(
                url_for('invenio_oauth2server_settings.client_new'),
                data=dict(
                    name='Test',
                    description='Test description',
                    website='http://invenio-software.org',
                    is_confidential=True,
                    redirect_uris="https://example.org/oauth/authorized/\n"
                                  "http://localhost:4000/oauth/authorized/"
                )
            )
            assert 302 == res.status_code


def test_info_not_accessible_in_production(provider_fixture):
    """Info route should not be available in production mode."""
    app = provider_fixture
    with app.test_request_context():
        with app.test_client() as client:
            app.config.update(
                DEBUG=False,
                TESTING=False,
            )
            data = dict(
                client_id='dev',
                client_secret='dev',  # A public client should NOT do this!
                grant_type='client_credentials',
                scope='test:scope',
            )

            # Public clients are not allowed to use
            # grant_type=client_credentials
            r = client.post(url_for(
                'invenio_oauth2server.access_token'
            ), data=data)
            assert r.status_code == 401
            assert json.loads(r.get_data()).get('error') == 'invalid_client'

            data = dict(
                client_id='confidential',
                client_secret='confidential',
                grant_type='client_credentials',
                scope='test:scope',
            )

            # Retrieve access token using client_credentials
            r = client.post(url_for(
                'invenio_oauth2server.access_token'
            ), data=data)
            assert r.status_code == 200

            data = json.loads(r.get_data())
            assert data['access_token']
            assert data['token_type'] == 'Bearer'
            assert data['scope'] == 'test:scope'
            assert data.get('refresh_token') is None

            # Authentication flow has now been completed, and the client can
            # use the access token to make request to the provider.
            r = client.get(url_for('invenio_oauth2server.info',
                                   access_token=data['access_token']))
            assert r.status_code == 404


def test_expired_refresh_flow(expiration_fixture):
    """Test refresh flow with an expired token."""
    app = expiration_fixture
    # First login on provider site
    with app.test_request_context():
        with app.test_client() as client:
            login(client)

            data = dict(
                redirect_uri=url_for('oauth2test.authorized', _external=True),
                scope='test:scope',
                response_type='code',
                client_id='confidential',
                state='mystate'
            )

            r = client.get(url_for('invenio_oauth2server.authorize', **data))
            assert r.status_code == 200

            data['confirm'] = 'yes'
            data['scope'] = 'test:scope'
            data['state'] = 'mystate'

            # Obtain one time code
            r = client.post(
                url_for('invenio_oauth2server.authorize'), data=data
            )
            assert r.status_code == 302
            next_url, res_data = parse_redirect(r.location)
            assert res_data['code']
            assert res_data['state'] == 'mystate'

            # Exchange one time code for access token
            r = client.post(
                url_for('invenio_oauth2server.access_token'), data=dict(
                    client_id='confidential',
                    client_secret='confidential',
                    grant_type='authorization_code',
                    code=res_data['code'],
                )
            )
            assert r.status_code == 200
            assert json.loads(r.get_data())['access_token']
            assert json.loads(r.get_data())['refresh_token']
            assert json.loads(r.get_data())['expires_in'] > 0
            assert json.loads(r.get_data())['scope'] == 'test:scope'
            assert json.loads(r.get_data())['token_type'] == 'Bearer'
            refresh_token = json.loads(r.get_data())['refresh_token']
            old_access_token = json.loads(r.get_data())['access_token']

            # Access token valid
            r = client.get(url_for('invenio_oauth2server.info',
                                   access_token=old_access_token))
            assert r.status_code == 200

            Token.query.filter_by(access_token=old_access_token).update(
                dict(expires=datetime.utcnow() - timedelta(seconds=1))
            )
            db.session.commit()

            # Access token is expired
            r = client.get(url_for('invenio_oauth2server.info',
                                   access_token=old_access_token))
            assert r.status_code == 401

            # Obtain new access token with refresh token
            r = client.post(
                url_for('invenio_oauth2server.access_token'), data=dict(
                    client_id='confidential',
                    client_secret='confidential',
                    grant_type='refresh_token',
                    refresh_token=refresh_token,
                )
            )
            assert r.status_code == 200
            resp_json = json.loads(r.get_data())
            assert resp_json['access_token']
            assert resp_json['refresh_token']
            assert resp_json['expires_in'] > 0
            assert resp_json['access_token'] != old_access_token
            assert resp_json['refresh_token'] != refresh_token
            assert resp_json['scope'] == 'test:scope'
            assert resp_json['token_type'] == 'Bearer'

            # New access token valid
            r = client.get(url_for('invenio_oauth2server.info',
                                   access_token=resp_json['access_token']))
            assert r.status_code == 200

            # Old access token no longer valid
            r = client.get(url_for('invenio_oauth2server.info',
                                   access_token=old_access_token))
            assert r.status_code == 401


def test_not_allowed_public_refresh_flow(expiration_fixture):
    """Public token should not allow refreshing."""
    app = expiration_fixture
    # First login on provider site
    with app.test_request_context():
        with app.test_client() as client:
            login(client)

            data = dict(
                redirect_uri=url_for('oauth2test.authorized', _external=True),
                scope='test:scope',
                response_type='code',
                client_id='dev',
                state='mystate'
            )

            r = client.get(url_for('invenio_oauth2server.authorize', **data))
            assert r.status_code == 200

            data['confirm'] = 'yes'
            data['scope'] = 'test:scope'
            data['state'] = 'mystate'

            # Obtain one time code
            r = client.post(
                url_for('invenio_oauth2server.authorize'), data=data
            )
            assert r.status_code == 302
            next_url, res_data = parse_redirect(r.location)
            assert res_data['code']
            assert res_data['state'] == 'mystate'

            # Exchange one time code for access token
            r = client.post(
                url_for('invenio_oauth2server.access_token'), data=dict(
                    client_id='dev',
                    client_secret='dev',
                    grant_type='authorization_code',
                    code=res_data['code'],
                )
            )
            assert r.status_code == 200
            json_resp = json.loads(r.get_data())
            assert json_resp['access_token']
            assert json_resp['refresh_token']
            assert json_resp['expires_in'] > 0
            assert json_resp['scope'] == 'test:scope'
            assert json_resp['token_type'] == 'Bearer'
            refresh_token = json_resp['refresh_token']
            old_access_token = json_resp['access_token']

            # Access token valid
            r = client.get(url_for('invenio_oauth2server.info',
                                   access_token=old_access_token))
            assert r.status_code == 200

            Token.query.filter_by(access_token=old_access_token).update(
                dict(expires=datetime.utcnow() - timedelta(seconds=1))
            )
            db.session.commit()

            # Access token is expired
            r = client.get(url_for('invenio_oauth2server.info',
                           access_token=old_access_token),
                           follow_redirects=True)
            assert r.status_code == 401

            # Obtain new access token with refresh token
            r = client.post(
                url_for('invenio_oauth2server.access_token'), data=dict(
                    client_id='dev',
                    client_secret='dev',
                    grant_type='refresh_token',
                    refresh_token=refresh_token,
                ),
                follow_redirects=True
            )

            # Only confidential clients can refresh expired token.
            assert r.status_code == 401
