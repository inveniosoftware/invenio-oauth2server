# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015, 2016, 2017 CERN.
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

"""OAuth2Server configuration variables."""

from datetime import timedelta

OAUTH2_CACHE_TYPE = 'redis'
"""Type of cache to use for storing the temporary grant token."""

OAUTH2_PROVIDER_ERROR_ENDPOINT = 'invenio_oauth2server.errors'
"""Error view endpoint."""

OAUTH2_PROVIDER_TOKEN_EXPIRES_IN = 3600
"""Life time of an access token."""

OAUTH2SERVER_CLIENT_ID_SALT_LEN = 40
"""Length of client id."""

OAUTH2SERVER_CLIENT_SECRET_SALT_LEN = 60
"""Length of the client secret."""

OAUTH2SERVER_TOKEN_PERSONAL_SALT_LEN = 60
"""Length of the personal access token."""

OAUTH2SERVER_ALLOWED_GRANT_TYPES = {
    'authorization_code', 'client_credentials', 'refresh_token',
}
"""A set of allowed grant types.

The allowed values are ``authorization_code``, ``password``,
``client_credentials``, ``refresh_token``). By default password is disabled,
as it requires the client application to gain access to the username and
password of the resource owner.
"""

OAUTH2SERVER_ALLOWED_RESPONSE_TYPES = {
    'code', 'token',
}
"""A set of allowed response types.

The allowed values are ``code`` and ``token``.

- ``code`` is used for authorization_code grant types
- ``token`` is used for implicit grant types
"""

OAUTH2SERVER_ALLOWED_URLENCODE_CHARACTERS = '=&;:%+~,*@!()/?'
"""A string of special characters that should be valid inside a query string.

.. seealso::

    See :py:func:`monkeypatch_oauthlib_urlencode_chars
    <invenio_oauth2server.ext.InvenioOAuth2ServerREST.monkeypatch_oauthlib_urlencode_chars>`
    for a full explanation.
"""

OAUTH2SERVER_JWT_AUTH_HEADER = 'Authorization'
"""Header for the JWT.

.. note::

    Authorization: Bearer xxx
"""

OAUTH2SERVER_JWT_AUTH_HEADER_TYPE = 'Bearer'
"""Header Authorization type.

.. note::

    By default the authorization type is ``Bearer`` as recommented by
    `JWT  <https://jwt.io>`_
"""

OAUTH2SERVER_JWT_VERYFICATION_FACTORY = 'invenio_oauth2server.utils:' \
    'jwt_verify_token'
"""Import path of factory used to verify JWT.

The ``request.headers`` should be passed as parameter.
"""
