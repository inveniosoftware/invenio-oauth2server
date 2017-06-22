# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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

"""Admin views for managing access to actions."""

from flask_admin.contrib.sqla import ModelView
from invenio_db import db

from .models import Client, Token


def _(x):
    """Identity."""
    return x


class ClientView(ModelView):
    """View for managing access to actions by users."""

    can_delete = True
    can_create = False
    can_view_details = True
    column_display_all_relations = True

    list_all = ('name', 'description', 'website', 'user_id', 'client_id', )

    column_list = \
        column_searchable_list = \
        column_sortable_list = \
        column_details_list = \
        list_all

    column_list = list_all
    column_default_sort = ('client_id', True)


class TokenView(ModelView):
    """View for managing access to actions by users with given role."""

    can_delete = True
    can_create = False
    can_view_details = True
    list_all = ('id', 'client_id', 'user_id', 'token_type', 'expires', )
    column_list = \
        column_searchable_list = \
        column_sortable_list = \
        column_details_list = \
        list_all


oauth2server_clients_adminview = {
    'view_class': ClientView,
    'args': [Client, db.session],
    'kwargs': {
        'name': _('OAuth Applications'),
        'category': _('User Management'),
    }
}

oauth2server_tokens_adminview = {
    'view_class': TokenView,
    'args': [Token, db.session],
    'kwargs': {
        'name': _('OAuth Application Tokens'),
        'category': _('User Management'),
    }
}

__all__ = (
    'oauth2server_clients_adminview',
    'oauth2server_tokens_adminview',
)
