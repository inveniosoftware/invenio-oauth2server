# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""OAuth 2.0 Provider."""

from functools import wraps

from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
)
from flask_breadcrumbs import register_breadcrumb
from flask_login import login_required
from invenio_i18n import lazy_gettext as _
from oauthlib.oauth2.rfc6749.errors import InvalidClientError, OAuth2Error

from ..models import Client
from ..provider import oauth2
from ..proxies import current_oauth2server

blueprint = Blueprint(
    "invenio_oauth2server",
    __name__,
    url_prefix="/oauth",
    static_folder="../static",
    template_folder="../templates",
)


def error_handler(f):
    """Handle uncaught OAuth errors."""

    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except OAuth2Error as e:
            # Only FatalClientError are handled by Flask-OAuthlib (as these
            # errors should not be redirect back to the client - see
            # http://tools.ietf.org/html/rfc6749#section-4.2.2.1)
            if hasattr(e, "redirect_uri"):
                return redirect(e.in_uri(e.redirect_uri))
            else:
                return redirect(e.in_uri(oauth2.error_uri))

    return decorated


#
# Views
#
@blueprint.route("/authorize", methods=["GET", "POST"])
@register_breadcrumb(blueprint, ".", _("Authorize application"))
@login_required
@error_handler
@oauth2.authorize_handler
def authorize(*args, **kwargs):
    """View for rendering authorization request."""
    if request.method == "GET":
        client = Client.query.filter_by(client_id=kwargs.get("client_id")).first()

        if not client:
            abort(404)

        scopes = current_oauth2server.scopes
        ctx = dict(
            client=client,
            oauth_request=kwargs.get("request"),
            scopes=[scopes[x] for x in kwargs.get("scopes", [])],
        )
        return render_template("invenio_oauth2server/authorize.html", **ctx)

    confirm = request.form.get("confirm", "no")
    return confirm == "yes"


@blueprint.route(
    "/token",
    methods=[
        "POST",
    ],
)
@oauth2.token_handler
def access_token():
    """Token view handles exchange/refresh access tokens."""
    client = Client.query.filter_by(client_id=request.form.get("client_id")).first()

    if not client:
        abort(404)

    if not client.is_confidential and "client_credentials" == request.form.get(
        "grant_type"
    ):
        error = InvalidClientError()
        response = jsonify(dict(error.twotuples))
        response.status_code = error.status_code
        abort(response)

    # Return None or a dictionary. Dictionary will be merged with token
    # returned to the client requesting the access token.
    # Response is in application/json
    return None


@blueprint.route("/errors")
def errors():
    """Error view in case of invalid oauth requests."""
    from oauthlib.oauth2.rfc6749.errors import raise_from_error

    try:
        error = None
        raise_from_error(request.values.get("error"), params=dict())
    except OAuth2Error as raised:
        error = raised
    return render_template("invenio_oauth2server/errors.html", error=error)


@blueprint.route("/ping", methods=["GET", "POST"])
@oauth2.require_oauth()
def ping():
    """Test to verify that you have been authenticated."""
    return jsonify(dict(ping="pong"))


@blueprint.route("/info")
@oauth2.require_oauth("test:scope")
def info():
    """Test to verify that you have been authenticated."""
    if current_app.testing or current_app.debug:
        return jsonify(
            dict(
                user=request.oauth.user.id,
                client=request.oauth.client.client_id,
                scopes=list(request.oauth.scopes),
            )
        )
    else:
        abort(404)


@blueprint.route("/invalid")
@oauth2.require_oauth("invalid_scope")
def invalid():
    """Test to verify that you have been authenticated."""
    if current_app.testing or current_app.debug:
        # Not reachable
        return jsonify(dict(ding="dong"))
    else:
        abort(404)
