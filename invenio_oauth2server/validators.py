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

"""Validators for OAuth 2.0 redirect URIs and scopes."""

from __future__ import absolute_import, print_function

from oauthlib.oauth2.rfc6749.errors import InsecureTransportError, \
    InvalidRedirectURIError
from six.moves.urllib_parse import urlparse

from .errors import ScopeDoesNotExists
from .proxies import current_oauth2server


def validate_redirect_uri(value):
    """Validate a redirect URI.

    Redirect URIs must be a valid URL and use https unless the host is
    localhost for which http is accepted.

    :param value: The redirect URI.
    """
    sch, netloc, path, par, query, fra = urlparse(value)
    if not (sch and netloc):
        raise InvalidRedirectURIError()
    if sch != 'https':
        if ':' in netloc:
            netloc, port = netloc.split(':', 1)
        if not (netloc in ('localhost', '127.0.0.1') and sch == 'http'):
            raise InsecureTransportError()


def validate_scopes(value_list):
    """Validate if each element in a list is a registered scope.

    :param value_list: The list of scopes.
    :raises invenio_oauth2server.errors.ScopeDoesNotExists: The exception is
        raised if a scope is not registered.
    :returns: ``True`` if it's successfully validated.
    """
    for value in value_list:
        if value not in current_oauth2server.scopes:
            raise ScopeDoesNotExists(value)
    return True
