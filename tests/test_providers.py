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

"""Test OAuth2Server providers."""

from __future__ import absolute_import, print_function

from flask import json, url_for

from invenio_db import db
from invenio_oauth2server.models import Client

from helpers import login, parse_redirect


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
                app.config['OAUTH2_CLIENT_ID_SALT_LEN']
            assert len(client.client_secret) == \
                app.config['OAUTH2_CLIENT_SECRET_SALT_LEN']

            db.session.add(client)

        with db.session.begin_nested():
            db.session.delete(client)


def test_invalid_authorize_requests(provider_fixture):
    app = provider_fixture
    # First login on provider site
    with app.app_context():
        with app.test_client() as client:
            login(client)

            for client_id in ['dev', 'confidential']:
                redirect_uri = 'http://{0}{1}'.format(
                    app.config['SERVER_NAME'],
                    url_for('oauth2test.authorized')
                )
                scope = 'test:scope'
                response_type = 'code'

                error_url = url_for('oauth2server.errors')

                # Valid request authorize request
                r = client.get(
                    url_for('oauth2server.authorize'),
                    data={
                        'redirect_uri': redirect_uri,
                        'scope': scope,
                        'response_type': response_type,
                        'client_id': client_id,
                    })
                assert r.status_code == 200

                # Invalid scope
                r = client.get(url_for(
                    'oauth2server.authorize',
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
                    'oauth2server.authorize',
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
                    'oauth2server.authorize',
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
                    'oauth2server.authorize',
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
                    'oauth2server.authorize',
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
                    'oauth2server.authorize',
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
    with app.app_context():
        with app.test_client() as client:
            # First login on provider site
            login(client)

            data = dict(
                redirect_uri='http://{0}{1}'.format(
                    app.config['SERVER_NAME'],
                    url_for('oauth2test.authorized')),
                scope='test:scope',
                response_type='code',
                client_id='confidential',
                state='mystate'
            )

            r = client.get(url_for('oauth2server.authorize', **data))
            assert r.status_code == 200

            data['confirm'] = 'yes'
            data['scope'] = 'test:scope'
            data['state'] = 'mystate'

            # Obtain one time code
            r = client.post(
                url_for('oauth2server.authorize'), data=data
            )
            r.status_code == 302
            next_url, res_data = parse_redirect(r.location)
            assert res_data['code']
            assert res_data['state'] == 'mystate'

            # Exchange one time code for access token
            r = client.post(
                url_for('oauth2server.access_token'), data=dict(
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
            r = client.get(url_for('oauth2server.info',
                           access_token=old_access_token))
            assert r.status_code == 200

            # Obtain new access token with refresh token
            r = client.post(
                url_for('oauth2server.access_token'), data=dict(
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
            r = client.get(url_for('oauth2server.info',
                                   access_token=json_resp['access_token']))
            assert r.status_code == 200

            # Old access token no longer valid
            r = client.get(url_for('oauth2server.info',
                                   access_token=old_access_token,),
                           base_url='http://' + app.config['SERVER_NAME'])
            assert r.status_code == 401
