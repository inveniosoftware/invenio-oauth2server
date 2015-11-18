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
from invenio_oauth2server.models import Client, Scope
from invenio_oauth2server.registry import scopes


def test_empty_redirect_uri_and_scope(app):
    with app.app_context():
        # Register a test scope
        scopes.register(Scope('test:scope1'))
        scopes.register(Scope('test:scope2', internal=True))

        test_user = User()

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
