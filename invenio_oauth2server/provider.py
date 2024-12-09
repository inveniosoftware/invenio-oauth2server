# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2024 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Configuration of Flask-OAuthlib provider."""

from datetime import datetime, timedelta

from authlib.integrations.flask_oauth2 import ResourceProtector
from authlib.oauth2.rfc6749 import grants
from authlib.oauth2.rfc6749.errors import (
    MissingAuthorizationError,
    UnsupportedTokenTypeError,
)
from authlib.oauth2.rfc6750 import BearerTokenValidator
from flask import current_app, g
from flask_login import current_user

# from flask_oauthlib.provider import OAuth2Provider
from flask_principal import Identity, identity_changed
from flask_security.utils import verify_password

# from importlib_metadata import version
from invenio_db import db
from werkzeug.local import LocalProxy

from .models import Client, Token
from .scopes import email_scope

# oauth2 = OAuth2Provider()
# oauth2 = AuthorizationServer
datastore = LocalProxy(lambda: current_app.extensions["security"].datastore)


class InvenioTokenValidator(BearerTokenValidator):
    def authenticate_token(self, access_token):
        """Logic to fetch the token from your database."""

        print(f"InvenioTokenValidator.authenticate_token access_token: {access_token}")
        if access_token:
            t = Token.query.filter_by(access_token=access_token).first()
        # elif refresh_token:
        #     t = (
        #         Token.query.join(Token.client)
        #         .filter(
        #             Token.refresh_token == refresh_token,
        #             Token.is_personal == False,  # noqa
        #             Client.is_confidential == True,
        #         )
        #         .first()
        #     )
        else:
            return None
        return t if t and t.user.active else None

    # def validate_token(self, token, scopes, request):
    #     # Logic to validate token and scope
    #     print(f"InvenioTokenValidator.validate_token")
    #     # if token.is_expired():
    #     #     return False
    #     return token.scope in scopes


class InvenioPasswordGrant(grants.ResourceOwnerPasswordCredentialsGrant):
    def authenticate_user(self, username, password):
        """Get user for grant type password.

        Needed for grant type 'password'. Note, grant type password is by default
        disabled.

        :param email: User email.
        :param password: Password.
        :returns: The user instance or ``None``.
        """
        user = datastore.find_user(email=username)
        if user and user.active and verify_password(password, user.password):
            return user


class InvenioResourceProtector(ResourceProtector):
    # def parse_request_authorization(self, request):
    #     """Parse the token and token validator from request Authorization header.
    #     Here is an example of Authorization header::

    #         Authorization: Bearer a-token-string

    #     This method will parse this header, if it can find the validator for
    #     ``Bearer``, it will return the validator and ``a-token-string``.

    #     :return: validator, token_string
    #     :raise: MissingAuthorizationError
    #     :raise: UnsupportedTokenTypeError
    #     """

    #     auth = request.headers.get("Authorization")
    #     print(
    #         f"InvenioResourceProtector.parse_request_authorization request: {request.data()}, auth: {auth}"
    #     )
    #     if not auth:
    #         print("raise")
    #         raise MissingAuthorizationError(
    #             self._default_auth_type, self._default_realm
    #         )

    #     # https://tools.ietf.org/html/rfc6749#section-7.1
    #     token_parts = auth.split(None, 1)
    #     print(
    #         f"InvenioResourceProtector.parse_request_authorization request: {request}, auth: {auth}, token_parts: {token_parts}"
    #     )
    #     if len(token_parts) != 2:
    #         raise UnsupportedTokenTypeError(
    #             self._default_auth_type, self._default_realm
    #         )

    #     token_type, token_string = token_parts
    #     validator = self.get_token_validator(token_type)
    #     return validator, token_string

    def parse_request_authorization(self, request):
        print("InvenioResourceProtector.parse_request_authorization")
        try:
            # print(
            #     f"InvenioResourceProtector.parse_request_authorization request: {request}, request.data: {request.data()}"
            # )

            return super().parse_request_authorization(request)
        except MissingAuthorizationError:
            print(
                f"InvenioResourceProtector.parse_request_authorization MissingAuthorizationError request: {request._request.data()}"
            )
            # token_type, token_string = token_parts
            # validator = self.get_token_validator(token_type)
            # return validator, token_string
        except UnsupportedTokenTypeError:
            print(
                f"InvenioResourceProtector.parse_request_authorization request: {request}, request.data: {request.data}"
            )

            # token_parts = auth.split(None, 1)
            # token_type, token_string = token_parts
            # validator = self.get_token_validator(token_type)
            # return validator, token_string
        except Exception:
            print("InvenioResourceProtector.parse_request_authorization exception")


# Register the validator
require_oauth = InvenioResourceProtector()
require_oauth.register_token_validator(InvenioTokenValidator())


# @oauth2.usergetter
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


# moved to InvenioTokenValidator
# @oauth2.tokengetter
# def get_token(access_token=None, refresh_token=None):
#     """Load an access token.

#     Add support for personal access tokens compared to flask-oauthlib.
#     If the access token is ``None``, it looks for the refresh token.

#     :param access_token: The access token. (Default: ``None``)
#     :param refresh_token: The refresh token. (Default: ``None``)
#     :returns: The token instance or ``None``.
#     """
#     if access_token:
#         t = Token.query.filter_by(access_token=access_token).first()
#     elif refresh_token:
#         t = (
#             Token.query.join(Token.client)
#             .filter(
#                 Token.refresh_token == refresh_token,
#                 Token.is_personal == False,  # noqa
#                 Client.is_confidential == True,
#             )
#             .first()
#         )
#     else:
#         return None
#     return t if t and t.user.active else None


# @oauth2.clientgetter
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


# @oauth2.tokensetter
def save_token(token, request, *args, **kwargs):
    """Token persistence.

    :param token: A dictionary with the token data.
    :param request: The request instance.
    :returns: A :class:`invenio_oauth2server.models.Token` instance.
    """
    # Exclude the personal access tokens which doesn't expire.
    user = request.user if request.user else current_user

    # Add user information in token endpoint response.
    # Currently, this is the only way to have the access to the user of the
    # token as well as the token response.
    token.update(user={"id": user.get_id()})

    # Add email if scope granted.
    if email_scope.id in token.scopes:
        token["user"].update(
            email=user.email,
            email_verified=user.confirmed_at is not None,
        )

    tokens = Token.query.filter_by(
        client_id=request.client.client_id,
        user_id=user.id,
        is_personal=False,
    )

    # make sure that every client has only one token connected to a user
    if tokens:
        for tk in tokens:
            db.session.delete(tk)
        db.session.commit()

    expires_in = token.get("expires_in")
    expires = datetime.utcnow() + timedelta(seconds=int(expires_in))

    tok = Token(
        access_token=token["access_token"],
        refresh_token=token.get("refresh_token"),
        token_type=token["token_type"],
        _scopes=token["scope"],
        expires=expires,
        client_id=request.client.client_id,
        user_id=user.id,
        is_personal=False,
    )
    db.session.add(tok)
    db.session.commit()
    return tok


# @oauth2.after_request
def login_oauth2_user(valid, oauth=None):
    """Log in a user after having been verified."""
    if oauth is None:
        print(f"login_oauth2_user oauth: {oauth}")
        return valid
    if valid:
        oauth.user.login_via_oauth2 = True
        g._login_user = oauth.user
        identity_changed.send(
            current_app._get_current_object(), identity=Identity(oauth.user.id)
        )
    return valid, oauth
