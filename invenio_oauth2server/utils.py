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

"""OAuth 2.0 Provider."""

from __future__ import absolute_import, print_function

from functools import wraps

from flask import request
from werkzeug.urls import url_encode


def request_urlreencode():
    """Re-encode request URL."""
    if request.args:
        request.url = request.base_url + "?" + url_encode(request.args)


def urlreencode(f):
    """Re-encode query string.

    OAuthLib's URL decoding is very strict and very often chokes on
    common user mistakes like not encoding colons, hence let Flask decode the
    request args and reencode them.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        request_urlreencode()
        return f(*args, **kwargs)
    return decorated
