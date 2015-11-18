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

from flask import Flask
from flask_cli import FlaskCLI
from flask_registry import Registry

from invenio_accounts.models import User
from invenio_db import InvenioDB, db
from invenio_oauth2server.models import Client, Token


@pytest.fixture
def app():
    """Flask application fixture."""
    app = Flask('testapp')
    app.config.update(
        TESTING=True,
        SECRET_KEY='test_key',
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                          'sqlite://'),
    )
    FlaskCLI(app)
    Registry(app)
    InvenioDB(app)
    with app.app_context():
        db.create_all()

    def teardown():
        with app.app_context():
            db.drop_all()

    # Initiate test data
    with app.app_context():
        with db.session.begin_nested():
            app.resource_owner =\
                User(email='resource_owner@invenio-software.org',
                     password='test')
            app.consumer = User(email='consumer@invenio-software.org',
                                password='test')
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
            db.session.add(app.resource_owner)
            db.session.add(app.consumer)
            db.session.add(app.u1c1)
            db.session.add(app.u1c1u1t1)
            db.session.add(app.u1c1u2t2)

    return app