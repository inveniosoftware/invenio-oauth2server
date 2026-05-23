# SPDX-FileCopyrightText: 2015-2018 CERN.
# SPDX-License-Identifier: MIT

"""Helper proxy to the state object."""

from flask import current_app
from werkzeug.local import LocalProxy

current_oauth2server = LocalProxy(
    lambda: current_app.extensions["invenio-oauth2server"]
)
"""Return current state of the OAuth2 server extension."""
