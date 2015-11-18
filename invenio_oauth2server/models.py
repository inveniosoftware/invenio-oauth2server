# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""OAuth2Server models."""

from __future__ import absolute_import, print_function

import six

from flask import current_app
from flask_babelex import gettext as _

from invenio_accounts.models import User
from invenio_db import db

from sqlalchemy_utils.types import URLType

from werkzeug.security import gen_salt

from wtforms import validators

from .errors import ScopeDoesNotExists
from .validators import validate_redirect_uri, validate_scopes


class Scope(object):
    """OAuth scope definition."""
    def __init__(self, id_, help_text='', group='', internal=False):
        """Initialize scope values."""
        self.id = id_
        self.group = group
        self.help_text = help_text
        self.is_internal = internal


class Client(db.Model):
    """A client is the app which want to use the resource of a user.

    It is suggested that the client is registered by a user on your site, but
    it is not required.

    The client should contain at least these information:

        client_id: A random string
        client_secret: A random string
        client_type: A string represents if it is confidential
        redirect_uris: A list of redirect uris
        default_redirect_uri: One of the redirect uris
        default_scopes: Default scopes of the client

    But it could be better, if you implemented:

        allowed_grant_types: A list of grant types
        allowed_response_types: A list of response types
        validate_scopes: A function to validate scopes
    """

    __tablename__ = 'oauth2CLIENT'

    name = db.Column(
        db.String(40),
        info=dict(
            label=_('Name'),
            description=_('Name of application (displayed to users).'),
            validators=[validators.DataRequired()]
        )
    )
    """Human readable name of the application."""

    description = db.Column(
        db.Text(),
        default=u'',
        info=dict(
            label=_('Description'),
            description=_('Optional. Description of the application'
                          ' (displayed to users).'),
        )
    )
    """Human readable description."""

    website = db.Column(
        URLType(),
        info=dict(
            label=_('Website URL'),
            description=_('URL of your application (displayed to users).'),
        ),
        default=u'',
    )

    user_id = db.Column(db.ForeignKey(User.id), nullable=True)
    """Creator of the client application."""

    client_id = db.Column(db.String(255), primary_key=True)
    """Client application ID."""

    client_secret = db.Column(
        db.String(255), unique=True, index=True, nullable=False
    )
    """Client application secret."""

    is_confidential = db.Column(db.Boolean, default=True)
    """Determine if client application is public or not."""

    is_internal = db.Column(db.Boolean, default=False)
    """Determins if client application is an internal application."""

    _redirect_uris = db.Column(db.Text)
    """A newline-separated list of redirect URIs. First is the default URI."""

    _default_scopes = db.Column(db.Text)
    """A space-separated list of default scopes of the client.

    The value of the scope parameter is expressed as a list of space-delimited,
    case-sensitive strings.
    """

    user = db.relationship(
        User,
        backref=db.backref(
            "oauth2clients",
            cascade="all, delete-orphan",
        )
    )
    """Relationship to user."""

    @property
    def allowed_grant_types(self):
        """Return allowed grant types."""
        return current_app.config['OAUTH2_ALLOWED_GRANT_TYPES']

    @property
    def allowed_response_types(self):
        """Return allowed response types."""
        return current_app.config['OAUTH2_ALLOWED_RESPONSE_TYPES']

    # def validate_scopes(self, scopes):
    #     return self._validate_scopes

    @property
    def client_type(self):
        """Return client type."""
        if self.is_confidential:
            return 'confidential'
        return 'public'

    @property
    def redirect_uris(self):
        """Return redirect uris."""
        if self._redirect_uris:
            return self._redirect_uris.splitlines()
        return []

    @redirect_uris.setter
    def redirect_uris(self, value):
        """Validate and store redirect URIs for client."""
        if isinstance(value, six.text_type):
            value = value.split("\n")

        value = [v.strip() for v in value]

        for v in value:
            validate_redirect_uri(v)

        self._redirect_uris = "\n".join(value) or ""

    @property
    def default_redirect_uri(self):
        """Return default redirect uri."""
        try:
            return self.redirect_uris[0]
        except IndexError:
            pass

    @property
    def default_scopes(self):
        """List of default scopes for client."""
        if self._default_scopes:
            return self._default_scopes.split(" ")
        return []

    @default_scopes.setter
    def default_scopes(self, scopes):
        """Set default scopes for client."""
        validate_scopes(scopes)
        self._default_scopes = " ".join(set(scopes)) if scopes else ""

    def validate_scopes(self, scopes):
        """Validate if client is allowed to access scopes."""
        try:
            validate_scopes(scopes)
            return True
        except ScopeDoesNotExists:
            return False

    def gen_salt(self):
        """Generate salt."""
        self.reset_client_id()
        self.reset_client_secret()

    def reset_client_id(self):
        """Reset client id."""
        self.client_id = gen_salt(
            current_app.config.get('OAUTH2_CLIENT_ID_SALT_LEN')
        )

    def reset_client_secret(self):
        """Reset client secret."""
        self.client_secret = gen_salt(
            current_app.config.get('OAUTH2_CLIENT_SECRET_SALT_LEN')
        )
