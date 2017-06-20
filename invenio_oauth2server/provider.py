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

"""Configuration of Flask-OAuthlib provider."""

from datetime import datetime, timedelta

from flask import current_app
from flask_login import current_user
from flask_oauthlib.provider import OAuth2Provider
from flask_security.utils import verify_password
from invenio_accounts.models import User
from invenio_db import db
from werkzeug.local import LocalProxy

from .models import Client, Token

oauth2 = OAuth2Provider()
datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


@oauth2.usergetter
def get_user(email, password, *args, **kwargs):
    """Get user for grant type password.

    Needed for grant type 'password'. Note, grant type password is by default
    disabled.

    :param email: User email.
    :param password: Password.
    :returns: The user instance or ``None``.
    """
    user = datastore.find_user(email=email)
    if user and user.active and verify_password(password, user.password):
        return user


@oauth2.tokengetter
def get_token(access_token=None, refresh_token=None):
    """Load an access token.

    Add support for personal access tokens compared to flask-oauthlib.
    If the access token is ``None``, it looks for the refresh token.

    :param access_token: The access token. (Default: ``None``)
    :param refresh_token: The refresh token. (Default: ``None``)
    :returns: The token instance or ``None``.
    """
    if access_token:
        t = Token.query.filter_by(access_token=access_token).first()
        if t and t.is_personal and t.user.active:
            t.expires = datetime.utcnow() + timedelta(
                seconds=int(current_app.config.get(
                    'OAUTH2_PROVIDER_TOKEN_EXPIRES_IN'
                ))
            )
    elif refresh_token:
        t = Token.query.join(Token.client).filter(
            Token.refresh_token == refresh_token,
            Token.is_personal == False,  # noqa
            Client.is_confidential == True,
        ).first()
    else:
        return None
    return t if t and t.user.active else None


@oauth2.clientgetter
def get_client(client_id):
    """Load the client.

    Needed for grant_type client_credentials.

    Add support for OAuth client_credentials access type, with user
    inactivation support.

    :param client_id: The client ID.
    :returns: The client instance or ``None``.
    """
    client = Client.query.get(client_id)
    if client and client.user.active:
        return client


@oauth2.tokensetter
def save_token(token, request, *args, **kwargs):
    """Token persistence.

    :param token: A dictionary with the token data.
    :param request: The request instance.
    :returns: A :class:`invenio_oauth2server.models.Token` instance.
    """
    # Exclude the personal access tokens which doesn't expire.
    uid = request.user.id if request.user else current_user.get_id()

    tokens = Token.query.filter_by(
        client_id=request.client.client_id,
        user_id=uid,
        is_personal=False,
    )

    # make sure that every client has only one token connected to a user
    if tokens:
        for tk in tokens:
            db.session.delete(tk)
        db.session.commit()

    expires_in = token.get('expires_in')
    expires = datetime.utcnow() + timedelta(seconds=int(expires_in))

    tok = Token(
        access_token=token['access_token'],
        refresh_token=token.get('refresh_token'),
        token_type=token['token_type'],
        _scopes=token['scope'],
        expires=expires,
        client_id=request.client.client_id,
        user_id=uid,
        is_personal=False,
    )
    db.session.add(tok)
    db.session.commit()
    return tok
