# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
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

"""Utility function for handling SECRET_KEY changes."""
from flask import current_app
from invenio_db.utils import rebuild_encrypted_properties

from invenio_oauth2server.models import Token


def rebuild_access_tokens(old_key):
    """Rebuild the access_token field when the SECRET_KEY is changed.

    Needed to fix the access tokens used in the REST API calls.

    :param old_key: the old SECRET_KEY.
    """
    current_app.logger.info('rebuilding Token.access_token...')
    rebuild_encrypted_properties(old_key, Token,
                                 ['access_token', 'refresh_token'])
