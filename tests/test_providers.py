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

from invenio_db import db
from invenio_oauth2server.models import Client


def test_client_salt(app):
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
