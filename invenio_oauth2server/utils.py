# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
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

"""Utility functions."""

import uuid
from datetime import datetime

from flask import abort, current_app
from flask_login import current_user
from invenio_db.utils import rebuild_encrypted_properties
from jwt import DecodeError, ExpiredSignatureError, decode, encode

from .errors import JWTDecodeError, JWTExpiredToken, JWTInvalidHeaderError, \
    JWTInvalidIssuer
from .models import Token


def rebuild_access_tokens(old_key):
    """Rebuild the access_token field when the SECRET_KEY is changed.

    Needed to fix the access tokens used in the REST API calls.

    :param old_key: the old SECRET_KEY.
    """
    current_app.logger.info('rebuilding Token.access_token...')
    rebuild_encrypted_properties(old_key, Token,
                                 ['access_token', 'refresh_token'])


def jwt_authorization_header(headers):
    """Read the authorization token from the headers.

    :param dict headers: The request headers.
    :returns: The token.
    :rtype: str
    """
    code = headers.get(
        current_app.config['OAUTH2SERVER_JWT_AUTH_HEADER']
    )
    if code is None:
        raise JWTInvalidHeaderError
    return code


def jwt_verify_token(headers):
    """Verify the JWT token.

    :param dict headers: The request headers.
    :returns: The token data.
    :rtype: dict
    """
    # Get the token from headers
    token = jwt_authorization_header(headers)
    # Get the prefix and the token
    prefix, code = token.split()
    # Check if the type matches
    if prefix != current_app.config['OAUTH2SERVER_JWT_AUTH_HEADER_TYPE']:
        raise JWTInvalidHeaderError
    # Get the token data
    decode = jwt_decode_token(code)
    # Check the integrity of the user
    if current_user.get_id() != decode.get('sub'):
        raise JWTInvalidIssuer
    return decode


def jwt_create_token(user_id=None, additional_data=None):
    """Encode the JWT token.

    :param int user_id: Addition of user_id.
    :param dict additional_data: Additional information for the token.
    :returns: The encoded token.
    :rtype: str

    .. note::
        Definition of the JWT claims:

        * exp: ((Expiration Time) expiration time of the JWT.
        * sub: (subject) the principal that is the subject of the JWT.
        * jti: (JWT ID) UID for the JWT.
    """
    # Create an ID
    uid = str(uuid.uuid4())
    # The time in UTC now
    now = datetime.utcnow()
    # Build the token data
    token_data = {
        'exp': now + current_app.config['OAUTH2SERVER_JWT_EXPIRATION_DELTA'],
        'sub': user_id or current_user.get_id(),
        'jti': uid,
    }
    # Add any additional data to the token
    if additional_data is not None:
        token_data.update(additional_data)

    # Encode the token and send it back
    encoded_token = encode(
        token_data,
        current_app.config['OAUTH2SERVER_JWT_SECRET_KEY'],
        current_app.config['OAUTH2SERVER_JWT_ALOGORITHM']
    ).decode('utf-8')
    return encoded_token


def jwt_decode_token(token):
    """Decode the JWT token.

    :param str token: Additional information for the token.
    :returns: The token data.
    :rtype: dict
    """
    try:
        return decode(
            token,
            current_app.config['OAUTH2SERVER_JWT_SECRET_KEY'],
            algorithms=[
                current_app.config['OAUTH2SERVER_JWT_ALOGORITHM']
            ]
        )
    except DecodeError:
        raise JWTDecodeError
    except ExpiredSignatureError:
        raise JWTExpiredToken
