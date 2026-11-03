# SPDX-FileCopyrightText: 2015-2018 CERN.
# SPDX-FileCopyrightText: 2022 RERO.
# SPDX-FileCopyrightText: 2023-2025 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Invenio module that implements OAuth 2 server."""

import six
from flask import abort, request
from flask_login import current_user
from flask_menu import current_menu
from flask_oauthlib.contrib.oauth2 import bind_cache_grant
from invenio_base.utils import entry_points
from invenio_i18n import LazyString
from invenio_i18n import lazy_gettext as _
from invenio_rest.csrf import csrf
from werkzeug.utils import cached_property, import_string

from . import config
from .models import OAuthUserProxy, Scope
from .provider import oauth2


class _OAuth2ServerState(object):
    """OAuth2 server state storing registered scopes."""

    def __init__(self, app, entry_point_group=None):
        """Initialize state."""
        self.app = app
        self.scopes = {}

        # Initialize OAuth2 provider
        oauth2.init_app(app)

        # Configures an OAuth2Provider instance to use the application-level
        # Invenio-Cache backend to get and set authorization-code grants.
        bind_cache_grant(app, oauth2, lambda: OAuthUserProxy(current_user))

        if entry_point_group:
            self.load_entry_point_group(entry_point_group)

    def scope_choices(self, exclude_internal=True):
        """Return list of scope choices.

        :param exclude_internal: Exclude internal scopes or not.
            (Default: ``True``)
        :returns: A list of tuples (id, scope).
        """
        return [
            (k, scope)
            for k, scope in sorted(self.scopes.items())
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
        for ep in entry_points(group=entry_point_group):
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
    def jwt_verification_factory(self):
        """Load default JWT verification factory."""
        return self.load_obj_or_import_string("OAUTH2SERVER_JWT_VERIFICATION_FACTORY")


class InvenioOAuth2Server(object):
    """Invenio-OAuth2Server extension."""

    def __init__(self, app=None, **kwargs):
        """Extension initialization.

        :param app: An instance of :class:`flask.Flask`.
        """
        if app:
            self._state = self.init_app(app, **kwargs)

    def init_app(self, app, entry_point_group="invenio_oauth2server.scopes", **kwargs):
        """Flask application initialization.

        :param app: An instance of :class:`flask.Flask`.
        :param entry_point_group: The entrypoint group name to load plugins.
            (Default: ``'invenio_oauth2server.scopes'``)
        """
        self.init_config(app)
        state = _OAuth2ServerState(app, entry_point_group=entry_point_group)

        app.extensions["invenio-oauth2server"] = state
        return state

    def init_config(self, app):
        """Initialize configuration.

        :param app: An instance of :class:`flask.Flask`.
        """
        app.config.setdefault(
            "OAUTH2SERVER_BASE_TEMPLATE",
            app.config.get("BASE_TEMPLATE", "invenio_oauth2server/base.html"),
        )
        app.config.setdefault(
            "OAUTH2SERVER_COVER_TEMPLATE",
            app.config.get("COVER_TEMPLATE", "invenio_oauth2server/base.html"),
        )
        app.config.setdefault(
            "OAUTH2SERVER_SETTINGS_TEMPLATE",
            app.config.get(
                "SETTINGS_TEMPLATE", "invenio_oauth2server/settings/base.html"
            ),
        )

        for k in dir(config):
            if k.startswith("OAUTH2SERVER_") or k.startswith("OAUTH2_"):
                app.config.setdefault(k, getattr(config, k))

    def __getattr__(self, name):
        """Proxy to state object."""
        return getattr(self._state, name, None)


def _get_uri_from_request(request):
    """Get uri from request.

    The uri returned from request.uri is not properly urlencoded
    (sometimes it's partially urldecoded) This is a weird hack to get
    werkzeug to return the proper urlencoded string uri

    copy pasted code from flask-oauthlib-invenio
    """
    uri = request.base_url
    if request.query_string:
        uri += "?" + request.query_string.decode("utf-8")
    return uri


def extract_params():
    """Extract request params.

    copy pasted code from flask-oauthlib-invenio
    """
    uri = _get_uri_from_request(request)
    http_method = request.method
    headers = dict(request.headers)
    if "wsgi.input" in headers:
        del headers["wsgi.input"]
    if "wsgi.errors" in headers:
        del headers["wsgi.errors"]
    # Werkzeug, and subsequently Flask provide a safe Authorization header
    # parsing, so we just replace the Authorization header with the extraced
    # info if it was successfully parsed.
    if request.authorization:
        headers["Authorization"] = str(request.authorization)

    # request.form could create problems on file upload
    body = {}  # request.form.to_dict()
    return uri, http_method, body, headers


def verify_request(scopes):
    """Verify request."""
    return oauth2.verify_request(scopes)


def verify_oauth_token_and_set_current_user():
    """Verify OAuth token and set current user on request stack.

    This function should be used **only** on REST application.

    .. code-block:: python

        app.before_request(verify_oauth_token_and_set_current_user)
    """
    # Since this function can be evoked multiple times
    # we add a check to not run it if it has already run.
    if hasattr(request, "oauth_verify_has_run"):
        return

    for func in oauth2._before_request_funcs:
        func()

    if not hasattr(request, "oauth") or not request.oauth:
        scopes = []
        try:
            valid, req = verify_request(scopes)
        except ValueError:
            abort(400, "Error trying to decode a non urlencoded string.")

        for func in oauth2._after_request_funcs:
            valid, req = func(valid, req)

        if valid:
            request.oauth = req

    if hasattr(request, "oauth"):
        request.skip_csrf_check = True

    request.oauth_verify_has_run = True


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
        # Add check to skip CSRF validation for valid OAuth bearer requests.
        csrf.before_csrf_protect(verify_oauth_token_and_set_current_user)
        app.before_request(verify_oauth_token_and_set_current_user)


def finalize_app(app):
    """Finalize app."""
    icons = app.extensions["invenio-theme"].icons

    current_menu.submenu("settings.applications").register(
        endpoint="invenio_oauth2server_settings.index",
        text=_(
            "%(icon)s Applications",
            icon=LazyString(lambda: f'<i class="{icons.codepen}"></i>'),
        ),
        order=21,
        active_when=lambda: request.endpoint.startswith(
            "invenio_oauth2server_settings."
        ),
    )
