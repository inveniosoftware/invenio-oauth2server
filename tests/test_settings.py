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

"""Test settings views."""

from __future__ import absolute_import, print_function

from flask import url_for
from flask_babelex import gettext as _
from helpers import login

from invenio_oauth2server.models import Client, Token


def test_personal_token_management(settings_fixture):
    """Test managing personal tokens through the views."""
    app = settings_fixture
    with app.test_request_context():
        with app.test_client() as client:
            login(client)

            # Non-existing token should return 404
            resp = client.get(
                url_for('invenio_oauth2server_settings.token_view',
                        token_id=1000)
            )
            resp.status_code == 404

            # Get the new token form
            resp = client.get(
                url_for('invenio_oauth2server_settings.token_new')
            )
            resp.status_code == 200
            assert _('New personal access token') in str(resp.get_data())

            # Create a new token
            resp = client.post(
                url_for('invenio_oauth2server_settings.token_new'),
                data={
                    'name': 'Test_Token',
                },
                follow_redirects=True
            )
            assert resp.status_code == 200
            assert 'Personal access token / Test_Token' in str(resp.get_data())
            assert 'test:scope' in str(resp.get_data())
            assert 'test:scope2' in str(resp.get_data())

            token = Token.query.first()

            # Rename the token
            resp = client.post(
               url_for('invenio_oauth2server_settings.token_view',
                       token_id=token.id),
               data=dict(name='Test_Token_Renamed')
            )
            assert resp.status_code == 200
            assert 'Test_Token_Renamed' in str(resp.get_data())

            # Token should be visible on index
            resp = client.get(url_for('invenio_oauth2server_settings.index'))
            assert resp.status_code == 200
            assert 'Test_Token_Renamed' in str(resp.get_data())

            # Delete the token
            resp = client.post(
                url_for('invenio_oauth2server_settings.token_view',
                        token_id=1),
                data=dict(delete=True),
                follow_redirects=True)
            assert resp.status_code == 200
            # Token should no longer exist on index
            assert 'Test_Token_Renamed' not in str(resp.get_data())


def test_client_management(settings_fixture):
    """Test managing clients through the views."""
    app = settings_fixture
    with app.test_request_context():
        with app.test_client() as client:
            login(client)

            # Non-existing client should return 404
            resp = client.get(
                url_for('invenio_oauth2server_settings.client_view',
                        client_id=1000)
            )
            assert resp.status_code == 404

            # Create a new client
            resp = client.post(
                url_for('invenio_oauth2server_settings.client_new'),
                data=dict(
                    name='Test_Client',
                    description='Test description for Test_Client.',
                    website='http://invenio-software.org/',
                    redirect_uris=url_for(
                        'invenio_oauth2server_settings.index', _external=True),
                    is_confditential=1
                ),
                follow_redirects=True)
            assert resp.status_code == 200
            assert 'Application / Test_Client' in str(resp.get_data())
            test_client = Client.query.first()
            assert test_client.client_id in str(resp.get_data())

            # Client should be visible on index
            resp = client.get(url_for('invenio_oauth2server_settings.index'))
            assert resp.status_code == 200
            assert 'Test_Client' in str(resp.get_data())

            # Reset client secret
            original_client_secret = test_client.client_secret
            resp = client.post(
                url_for('invenio_oauth2server_settings.client_reset',
                        client_id=test_client.client_id),
                data=dict(reset='yes'),
                follow_redirects=True
            )
            assert resp.status_code == 200
            assert test_client.client_secret in str(resp.get_data())
            assert original_client_secret not in str(resp.get_data())

            # Invalid redirect uri should error
            original_redirect_uris = test_client.redirect_uris
            resp = client.post(
                url_for('invenio_oauth2server_settings.client_view',
                        client_id=test_client.client_id),
                data=dict(
                    name='Test_Client',
                    description='Test description for Test_Client',
                    website='http://invenio-software.org/',
                    redirect_uris='https:/invalid',
                )
            )
            assert resp.status_code == 200
            assert test_client.redirect_uris == original_redirect_uris

            # Modify the client
            resp = client.post(
                url_for('invenio_oauth2server_settings.client_view',
                        client_id=test_client.client_id),
                data=dict(
                    name='Modified_Name',
                    description='Modified Description',
                    website='http://modified-url.org',
                    redirect_uris='https://example.org',
                )
            )
            assert resp.status_code == 200
            assert 'Modified_Name' in str(resp.get_data())
            assert 'Modified Description' in str(resp.get_data())
            assert 'http://modified-url.org' in str(resp.get_data())

            # Delete the client
            resp = client.post(
                url_for('invenio_oauth2server_settings.client_view',
                        client_id=test_client.client_id),
                follow_redirects=True,
                data=dict(delete=True)
            )
            assert resp.status_code == 200
            assert test_client.name not in str(resp.get_data())
