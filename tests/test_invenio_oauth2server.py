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


"""Module tests."""

from __future__ import absolute_import, print_function

import pytest
from flask import Flask
from invenio_db import db

from invenio_oauth2server import InvenioOAuth2Server, InvenioOAuth2ServerREST
from invenio_oauth2server.ext import verify_oauth_token_and_set_current_user


def test_version():
    """Test version import."""
    from invenio_oauth2server import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = InvenioOAuth2Server(app)
    assert 'invenio-oauth2server' in app.extensions
    assert ext.app is app

    app = Flask('testapp')
    ext = InvenioOAuth2Server()
    assert 'invenio-oauth2server' not in app.extensions
    state = ext.init_app(app)
    assert 'invenio-oauth2server' in app.extensions
    assert state.app is app


def test_init_rest():
    """Test REST extension initialization."""
    app = Flask('testapp')
    ext = InvenioOAuth2ServerREST(app)
    assert verify_oauth_token_and_set_current_user in \
        app.before_request_funcs[None]

    app = Flask('testapp')
    ext = InvenioOAuth2ServerREST()
    assert verify_oauth_token_and_set_current_user not in \
        app.before_request_funcs.get(None, [])
    ext.init_app(app)
    assert verify_oauth_token_and_set_current_user in \
        app.before_request_funcs[None]


def test_init_rest_with_oauthlib_monkeypatch():
    """Test REST OAuthlib monkeypatching."""
    app = Flask('testapp')

    from oauthlib.common import urlencoded
    assert '^' not in urlencoded
    old_urlencoded = set(urlencoded)

    app.config['OAUTH2SERVER_ALLOWED_URLENCODE_CHARACTERS'] = '^'

    with pytest.warns(RuntimeWarning):
        InvenioOAuth2ServerREST(app)
    assert verify_oauth_token_and_set_current_user in \
        app.before_request_funcs[None]

    from oauthlib.common import urlencoded
    assert old_urlencoded != urlencoded
    assert '^' in urlencoded


def test_alembic(app):
    """Test alembic recipes."""
    ext = app.extensions['invenio-db']

    with app.app_context():
        if db.engine.name == 'sqlite':
            raise pytest.skip('Upgrades are not supported on SQLite.')

        assert not ext.alembic.compare_metadata()
        db.drop_all()
        ext.alembic.upgrade()

        assert not ext.alembic.compare_metadata()
        ext.alembic.downgrade(target='96e796392533')
        ext.alembic.upgrade()

        assert not ext.alembic.compare_metadata()
        ext.alembic.downgrade(target='96e796392533')


def test_jwt_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = InvenioOAuth2Server(app)
    assert 'invenio-oauth2server' in app.extensions
    assert ext.app.config.get('OAUTH2SERVER_JWT_SECRET_KEY') == \
        ext.app.config.get('SECRET_KEY')
