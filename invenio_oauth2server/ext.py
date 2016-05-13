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

"""Invenio module that implements OAuth 2 server."""

from __future__ import absolute_import, print_function

import os
from warnings import warn

import pkg_resources
from flask import request
from flask_oauthlib.contrib.oauth2 import bind_cache_grant, bind_sqlalchemy
from flask_security import current_user
from invenio_db import db

from . import config
from .models import Client, OAuthUserProxy, Scope
from .provider import oauth2


class _OAuth2ServerState(object):
    """OAuth2 server state storing registered scopes."""

    def __init__(self, app, entry_point_group=None):
        """Initialize state."""
        self.app = app
        self.scopes = {}

        # Initialize OAuth2 provider
        oauth2.init_app(app)

        # Configures the OAuth2 provider to use the SQLALchemy models for
        # getters and setters for user, client and tokens.
        bind_sqlalchemy(oauth2, db.session, client=Client)

        # Flask-OAuthlib does not support CACHE_REDIS_URL
        if app.config['OAUTH2_CACHE_TYPE'] == 'redis' and app.config.get(
                'CACHE_REDIS_URL'):
            from redis import from_url as redis_from_url
            app.config.setdefault(
                'OAUTH2_CACHE_REDIS_HOST',
                redis_from_url(app.config['CACHE_REDIS_URL'])
            )

        # Configures an OAuth2Provider instance to use configured caching
        # system to get and set the grant token.
        bind_cache_grant(app, oauth2, lambda: OAuthUserProxy(current_user))

        # Disables oauthlib's secure transport detection in in debug mode.
        if app.debug or app.testing:
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

        if entry_point_group:
            self.load_entry_point_group(entry_point_group)

    def scope_choices(self, exclude_internal=True):
        """Return list of scope choices."""
        return [
            (k, scope) for k, scope in sorted(self.scopes.items())
            if not exclude_internal or not scope.is_internal
        ]

    def register_scope(self, scope):
        """Register a scope."""
        if not isinstance(scope, Scope):
            raise TypeError("Invalid scope type.")
        assert scope.id not in self.scopes
        self.scopes[scope.id] = scope

    def load_entry_point_group(self, entry_point_group):
        """Load actions from an entry point group."""
        for ep in pkg_resources.iter_entry_points(group=entry_point_group):
            self.register_scope(ep.load())


class InvenioOAuth2Server(object):
    """Invenio-OAuth2Server extension."""

    def __init__(self, app=None, **kwargs):
        """Extension initialization."""
        if app:
            self.init_app(app, **kwargs)

    def init_app(self, app, entry_point_group='invenio_oauth2server.scopes',
                 **kwargs):
        """Flask application initialization."""
        self.init_config(app)
        state = _OAuth2ServerState(app, entry_point_group=entry_point_group)
        app.extensions['invenio-oauth2server'] = state

    def init_config(self, app):
        """Initialize configuration."""
        app.config.setdefault(
            'OAUTH2SERVER_BASE_TEMPLATE',
            app.config.get('BASE_TEMPLATE',
                           'invenio_oauth2server/base.html'))
        app.config.setdefault(
            'OAUTH2SERVER_SETTINGS_TEMPLATE',
            app.config.get('SETTINGS_TEMPLATE',
                           'invenio_oauth2server/settings/base.html'))

        for k in dir(config):
            if k.startswith('OAUTH2SERVER_') or k.startswith('OAUTH2_'):
                app.config.setdefault(k, getattr(config, k))


def verify_oauth_token_and_set_current_user():
    """Verify OAuth token and set current user on request stack.

    This function should be used **only** on REST application.

    .. code-block:: python

        app.before_request(verify_oauth_token_and_set_current_user)
    """
    from flask_oauthlib.utils import extract_params
    from .views.server import login_oauth2_user

    if not hasattr(request, 'oauth') or not request.oauth:
        scopes = []
        # FIXME Replace by oauth2.verify_request() when using
        #       Flask-OAuthlib>=0.8.0
        # valid, req = oauth2.verify_request(scopes)
        uri, http_method, body, headers = extract_params()
        valid, req = oauth2.server.verify_request(
            uri, http_method, body, headers, scopes
        )
        login_oauth2_user(valid, req)


class InvenioOAuth2ServerREST(object):
    """Invenio-OAuth2Server REST extension."""

    def __init__(self, app=None, **kwargs):
        """Extension initialization."""
        if app:
            self.init_app(app, **kwargs)

    def init_app(self, app, **kwargs):
        """Flask application initialization."""
        app.before_request(verify_oauth_token_and_set_current_user)
