# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module that implements OAuth 2 server."""

from __future__ import absolute_import, print_function

from .ext import InvenioOAuth2Server, InvenioOAuth2ServerREST
from .proxies import current_oauth2server
from .version import __version__
from .decorators import require_api_auth, require_oauth_scopes

__all__ = (
    '__version__',
    'InvenioOAuth2Server',
    'InvenioOAuth2ServerREST',
    'require_api_auth',
    'require_oauth_scopes',
    'current_oauth2server',
)
