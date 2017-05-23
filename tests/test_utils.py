# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Test case for rebuilding access tokens."""

import sys
from datetime import datetime

import pytest
from flask import url_for
from invenio_db import db

from invenio_oauth2server.errors import JWTDecodeError, JWTExpiredToken, \
    JWTInvalidHeaderError, JWTInvalidIssuer
from invenio_oauth2server.models import Token
from invenio_oauth2server.utils import jwt_authorization_header, \
    jwt_create_token, jwt_decode_token, jwt_verify_token, \
    rebuild_access_tokens


def test_rebuilding_access_tokens(models_fixture):
    """Test rebuilding access tokens with random new SECRET_KEY."""
    app = models_fixture
    with app.app_context():
        old_secret_key = app.secret_key
        tokens_before = Token.query.order_by(Token.id).all()

        # Changing application SECRET_KEY
        app.secret_key = "NEW_SECRET_KEY"
        db.session.expunge_all()

        # Asserting the decoding error occurs with the stale SECRET_KEY
        if sys.version_info[0] < 3:  # python 2
            token = Token.query.filter(Token.id == tokens_before[0].id).one()
            assert token.access_token != tokens_before[0].access_token
        else:  # python 3
            with pytest.raises(UnicodeDecodeError):
                Token.query.filter(Token.id == tokens_before[0].id).one()

        db.session.expunge_all()
        rebuild_access_tokens(old_secret_key)
        tokens_after = Token.query.order_by(Token.id).all()

        for token_before, token_after in list(zip(tokens_before,
                                                  tokens_after)):
            assert token_before.access_token == token_after.access_token
            assert token_before.refresh_token == token_after.refresh_token


def test_jwt_token(app):
    """Test jwt creation."""
    with app.app_context():
        # Extra parameters
        extra = dict(
            defenders=['jessica', 'luke', 'danny', 'matt']
        )
        # Create token normally
        token = jwt_create_token(user_id=1, additional_data=extra)
        decode = jwt_decode_token(token)
        # Decode
        assert 'jessica' in decode.get('defenders')
        assert 1 == decode.get('sub')


def test_jwt_expired_token(app):
    """Test jwt creation."""
    with app.app_context():
        # Extra parameters
        extra = dict(
            exp=datetime(1970, 1, 1),
        )
        # Create token
        token = jwt_create_token(user_id=1, additional_data=extra)
        # Decode
        with pytest.raises(JWTExpiredToken):
            jwt_decode_token(token)
        # Random token
        with pytest.raises(JWTDecodeError):
            jwt_decode_token('Roadster SV')
