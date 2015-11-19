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

from flask import url_for

from invenio_db import db
from invenio_oauth2server.models import Client

from helpers import login, parse_redirect, sign_up


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


def invalid_authorize_requests(app):
    # First login on provider site
    with app.app_context():
        with app.test_client() as client:
            sign_up(client)
            login(client)

            for client_id in ['dev', 'confidential']:
                redirect_uri = '{0}/oauth2test/authorized'.format(
                    app.config['SERVER_NAME'])
                scope = 'test:scope'
                response_type = 'code'

                error_url = url_for('oauth2server.errors')

                # Valid request authorize request
                client.get(url_for('login'))
                r = client.get(
                    url_for('authorized'),
                    data={
                        'redirect_uri': redirect_uri,
                        'scope': scope,
                        'response_type': response_type,
                        'client_id': client_id,
                    })
                assert r.status_code == 200

                # Invalid scope
                r = client.get(url_for(
                    'authorized',
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
