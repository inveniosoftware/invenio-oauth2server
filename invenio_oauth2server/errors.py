# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2017 CERN.
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

"""Errors raised by Invenio-OAuth2Server."""

from invenio_rest.errors import RESTException


class OAuth2ServerError(Exception):
    """Base class for errors in oauth2server module."""


class ScopeDoesNotExists(OAuth2ServerError):
    """Scope is not registered it scopes registry."""

    def __init__(self, scope, *args, **kwargs):
        """Initialize exception by storing invalid scope."""
        super(ScopeDoesNotExists, self).__init__(*args, **kwargs)
        self.scope = scope


class JWTExtendedException(RESTException):
    """Base exception for all JWT errors."""

    code = 500


class JWTDecodeError(JWTExtendedException):
    """Exception raised when decoding is failed."""

    code = 400
    description = 'The JWT token has invalid format.'


class JWTInvalidIssuer(JWTExtendedException):
    """Exception raised when the user is not valid."""

    code = 403
    description = 'The JWT token is not valid.'


class JWTExpiredToken(JWTExtendedException):
    """Exception raised when JWT is expired."""

    code = 403
    description = 'The JWT token is expired.'


class JWTInvalidHeaderError(JWTExtendedException):
    """Exception raised when header argument is missing."""

    code = 400
    description = 'Missing required header argument.'


class JWTNoAuthorizationError(JWTExtendedException):
    """Exception raised when permission denied."""

    code = 400
    description = "The JWT token is not valid."
