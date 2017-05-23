# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016, 2017 CERN.
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
import warnings

import oauthlib.common as oauthlib_commmon
import pkg_resources
import six
from flask import request
from flask_login import current_user
from flask_oauthlib.contrib.oauth2 import bind_cache_grant, bind_sqlalchemy
from invenio_db import db
from werkzeug.utils import cached_property, import_string

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
        """Return list of scope choices.

        :param exclude_internal: Exclude internal scopes or not.
            (Default: ``True``)
        :returns: A list of tuples (id, scope).
        """
        return [
            (k, scope) for k, scope in sorted(self.scopes.items())
            if not exclude_internal or not scope.is_internal
        ]

    def register_scope(self, scope):
        """Register a scope.

        :param scope: A :class:`invenio_oauth2server.models.Scope` instance.
        """
        if not isinstance(scope, Scope):
            raise TypeError("Invalid scope type.")
        assert scope.id not in self.scopes
        self.scopes[scope.id] = scope

    def load_entry_point_group(self, entry_point_group):
        """Load actions from an entry point group.

        :param entry_point_group: The entrypoint group name to load plugins.
        """
        for ep in pkg_resources.iter_entry_points(group=entry_point_group):
            self.register_scope(ep.load())

    def load_obj_or_import_string(self, value):
        """Import string or return object.

        :params value: Import path or class object to instantiate.
        :params default: Default object to return if the import fails.
        :returns: The imported object.
        """
        imp = self.app.config.get(value)
        if isinstance(imp, six.string_types):
            return import_string(imp)
        elif imp:
            return imp

    @cached_property
    def jwt_veryfication_factory(self):
        """Load default JWT veryfication factory."""
        return self.load_obj_or_import_string(
            'OAUTH2SERVER_JWT_VERYFICATION_FACTORY'
        )

    @cached_property
    def jwt_creation_factory(self):
        """Load default JWT creation factory."""
        return self.load_obj_or_import_string(
            'OAUTH2SERVER_JWT_CREATION_FACTORY'
        )


class InvenioOAuth2Server(object):
    """Invenio-OAuth2Server extension."""

    def __init__(self, app=None, **kwargs):
        """Extension initialization.

        :param app: An instance of :class:`flask.Flask`.
        """
        if app:
            self._state = self.init_app(app, **kwargs)

    def init_app(self, app, entry_point_group='invenio_oauth2server.scopes',
                 **kwargs):
        """Flask application initialization.

        :param app: An instance of :class:`flask.Flask`.
        :param entry_point_group: The entrypoint group name to load plugins.
            (Default: ``'invenio_oauth2server.scopes'``)
        """
        self.init_config(app)
        state = _OAuth2ServerState(app, entry_point_group=entry_point_group)

        if app.config['OAUTH2SERVER_JWT_DOM_TOKEN']:
            from invenio_oauth2server.context_processors.jwt import \
                jwt_proccessor
            app.context_processor(jwt_proccessor)

        app.extensions['invenio-oauth2server'] = state
        return state

    def init_config(self, app):
        """Initialize configuration.

        :param app: An instance of :class:`flask.Flask`.
        """
        app.config.setdefault(
            'OAUTH2SERVER_BASE_TEMPLATE',
            app.config.get('BASE_TEMPLATE',
                           'invenio_oauth2server/base.html'))
        app.config.setdefault(
            'OAUTH2SERVER_SETTINGS_TEMPLATE',
            app.config.get('SETTINGS_TEMPLATE',
                           'invenio_oauth2server/settings/base.html'))
        app.config.setdefault(
            'OAUTH2SERVER_JWT_SECRET_KEY',
            app.config.get('OAUTH2SERVER_JWT_SECRET_KEY',
                           app.config.get('SECRET_KEY')))

        for k in dir(config):
            if k.startswith('OAUTH2SERVER_') or k.startswith('OAUTH2_'):
                app.config.setdefault(k, getattr(config, k))

    def __getattr__(self, name):
        """Proxy to state object."""
        return getattr(self._state, name, None)


def verify_oauth_token_and_set_current_user():
    """Verify OAuth token and set current user on request stack.

    This function should be used **only** on REST application.

    .. code-block:: python

        app.before_request(verify_oauth_token_and_set_current_user)
    """
    for func in oauth2._before_request_funcs:
        func()

    if not hasattr(request, 'oauth') or not request.oauth:
        scopes = []
        valid, req = oauth2.verify_request(scopes)

        for func in oauth2._after_request_funcs:
            valid, req = func(valid, req)

        if valid:
            request.oauth = req


class InvenioOAuth2ServerREST(object):
    """Invenio-OAuth2Server REST extension."""

    def __init__(self, app=None, **kwargs):
        """Extension initialization.

        :param app: An instance of :class:`flask.Flask`.
        """
        if app:
            self.init_app(app, **kwargs)

    def init_app(self, app, **kwargs):
        """Flask application initialization.

        :param app: An instance of :class:`flask.Flask`.
        """
        self.init_config(app)

        allowed_urlencode_chars = app.config.get(
            'OAUTH2SERVER_ALLOWED_URLENCODE_CHARACTERS')
        if allowed_urlencode_chars:
            InvenioOAuth2ServerREST.monkeypatch_oauthlib_urlencode_chars(
                allowed_urlencode_chars)
        app.before_request(verify_oauth_token_and_set_current_user)

    def init_config(self, app):
        """Initialize configuration."""
        app.config.setdefault(
            'OAUTH2SERVER_ALLOWED_URLENCODE_CHARACTERS',
            getattr(config, 'OAUTH2SERVER_ALLOWED_URLENCODE_CHARACTERS'))

    @staticmethod
    def monkeypatch_oauthlib_urlencode_chars(chars):
        """Monkeypatch OAuthlib set of "URL encoded"-safe characters.

        .. note::

            OAuthlib keeps a set of characters that it considers as valid
            inside an URL-encoded query-string during parsing of requests. The
            issue is that this set of characters wasn't designed to be
            configurable since it should technically follow various RFC
            specifications about URIs, like for example `RFC3986
            <https://www.ietf.org/rfc/rfc3986.txt>`_. Many online services and
            frameworks though have designed their APIs in ways that aim at
            keeping things practical and readable to the API consumer, making
            use of special characters to mark or seperate query-string
            arguments. Such an example is the usage of embedded JSON strings
            inside query-string arguments, which of course have to contain the
            "colon" character (:) for key/value pair definitions.

            Users of the OAuthlib library, in order to integrate with these
            services and frameworks, end up either circumventing these "static"
            restrictions of OAuthlib by pre-processing query-strings, or -in
            search of a more permanent solution- directly make Pull Requests
            to OAuthlib to include additional characters in the set, and
            explain the logic behind their decision (one can witness these
            efforts inside the git history of the source file that includes
            this set of characters `here
            <https://github.com/idan/oauthlib/commits/master/oauthlib/common.py>`_).
            This kind of tactic leads easily to misconceptions about the
            ability one has over the usage of specific features of services and
            frameworks. In order to tackle this issue in Invenio-OAuth2Server,
            we are monkey-patching this set of characters using a configuration
            variable, so that usage of any special characters is a conscious
            decision of the package user.
        """
        modified_chars = set(chars)
        always_safe = set(oauthlib_commmon.always_safe)
        original_special_chars = oauthlib_commmon.urlencoded - always_safe
        if modified_chars != original_special_chars:
            warnings.warn(
                'You are overriding the default OAuthlib "URL encoded" set of '
                'valid characters. Make sure that the characters defined in '
                'oauthlib.common.urlencoded are indeed limitting your needs.',
                RuntimeWarning
            )
            oauthlib_commmon.urlencoded = always_safe | modified_chars
