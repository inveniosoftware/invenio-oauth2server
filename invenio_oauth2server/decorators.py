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

"""Useful decorators for checking authentication and scopes."""

import sys
from functools import wraps

from flask import abort, request
from flask_security import current_user
from six import reraise
from werkzeug.exceptions import Unauthorized

from .provider import oauth2


#
# Decorators
#
def require_api_auth(allow_anonymous=False):
    """Decorator to require API authentication using OAuth token.

    :param allow_anonymous: Allow access without OAuth token
        (default: ``False``).
    """
    def wrapper(f):
        """Wrap function with oauth require decorator."""
        f_oauth_required = oauth2.require_oauth()(f)

        @wraps(f)
        def decorated(*args, **kwargs):
            """Require OAuth 2.0 Authentication."""
            if current_user.is_authenticated:
                # fully logged in with normal session
                return f(*args, **kwargs)
            else:
                # otherwise, try oauth2
                try:
                    return f_oauth_required(*args, **kwargs)
                except Unauthorized:
                    if allow_anonymous:
                        return f(*args, **kwargs)
                    reraise(*sys.exc_info())
        return decorated
    return wrapper


def require_oauth_scopes(*scopes):
    """Decorator to require a list of OAuth scopes.

    Decorator must be preceded by a ``require_api_auth()`` decorator.
    Note, API key authentication is bypassing this check.
    """
    required_scopes = set(scopes)

    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Variable requests.oauth is only defined for oauth requests (see
            # require_api_auth() above).
            if hasattr(request, 'oauth') and request.oauth is not None:
                token_scopes = set(request.oauth.access_token.scopes)
                if not required_scopes.issubset(token_scopes):
                    abort(403)
            return f(*args, **kwargs)
        return decorated
    return wrapper
