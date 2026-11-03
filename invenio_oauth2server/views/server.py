# SPDX-FileCopyrightText: 2015-2018 CERN.
# SPDX-FileCopyrightText: 2023 Graz University of Technology.
# SPDX-FileCopyrightText: 2026 KTH Royal Institute of Technology.
# SPDX-License-Identifier: MIT

"""OAuth 2.0 Provider."""

from functools import wraps

from authlib.oauth2 import OAuth2Error
from authlib.oauth2.rfc6749.errors import InvalidClientError
from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
)
from flask_login import login_required

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
            status, body, headers = e(
                getattr(e, "redirect_uri", None) or oauth2.error_uri
            )
            location = dict(headers).get("Location")
            if location:
                return redirect(location)
            return redirect(oauth2.error_uri)

    return decorated


#
# Views
#
@blueprint.route("/authorize", methods=["GET", "POST"])
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
        return render_template(
            current_app.config["OAUTH2SERVER_AUTHORIZE_TEMPLATE"], **ctx
        )

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
        error = InvalidClientError(status_code=401)
        response = jsonify(dict(error.get_body()))
        response.status_code = error.status_code
        abort(response)

    # Return None or a dictionary. Dictionary will be merged with token
    # returned to the client requesting the access token.
    # Response is in application/json
    return None


@blueprint.route("/errors")
def errors():
    """Error view in case of invalid oauth requests."""
    error = None
    if request.values.get("error"):
        error = OAuth2Error(
            error=request.values.get("error"),
            description=request.values.get("error_description"),
        )
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
