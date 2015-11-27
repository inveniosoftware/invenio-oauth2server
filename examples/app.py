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


"""Minimal Flask application example for development.

Run example development server:

.. code-block:: console

   $ cd examples
   $ python app.py
"""

from __future__ import absolute_import, print_function

import os

from flask import Flask
from flask_babelex import Babel
from flask_cli import FlaskCLI
from flask_mail import Mail
from flask_menu import Menu
from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint as accounts_blueprint
from invenio_db import InvenioDB, db

from invenio_oauth2server import InvenioOAuth2Server
from invenio_oauth2server.views import server_blueprint, settings_blueprint

# Create Flask application
app = Flask(__name__)
app.config.update(
    CELERY_ALWAYS_EAGER=True,
    CELERY_CACHE_BACKEND="memory",
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    CELERY_RESULT_BACKEND="cache",
    OAUTH2_CACHE_TYPE='simple',
    OAUTHLIB_INSECURE_TRANSPORT=True,
    SECRET_KEY='test_key',
    SECURITY_PASSWORD_HASH='plaintext',
    SECURITY_PASSWORD_SCHEMES=['plaintext'],
    SQLALCHEMY_TRACK_MODIFICATIONS=True,
    SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                      'sqlite:///example.db'),
)
FlaskCLI(app)
Babel(app)
Mail(app)
Menu(app)
InvenioDB(app)

accounts = InvenioAccounts(app)
app.register_blueprint(accounts_blueprint)

InvenioOAuth2Server(app)
app.register_blueprint(settings_blueprint)
app.register_blueprint(server_blueprint)


@app.cli.group()
def fixtures():
    """Command for working with test data."""


@fixtures.command()
def users():
    """Load user fixtures."""
    accounts.datastore.create_user(
        email='admin@invenio-software.org',
        password='123456',
        active=True,
    )
    accounts.datastore.create_user(
        email='reader@invenio-software.org',
        password='123456',
        active=True,
    )
    db.session.commit()
