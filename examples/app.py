# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016, 2017 CERN.
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


r"""Minimal Flask application example for development.

Run example development server:

.. code-block:: console

   $ pip install -e .[all]
   $ cd examples
   $ export FLASK_APP=app.py
   $ flask db init
   $ flask db create
   $ flask fixtures users
   $ flask run

Open the admin page to generate a token:

.. code-block:: console

   $ open http://0.0.0.0:5000/account/settings/applications

Make a login with:

    username: admin@inveniosoftware.org
    password: 123456

Click on "New token" and compile the form:
insert the name "foobar", check scope "test:scope" and click "create".
The server will show you the generated Access Token.

Make a request to test the token:

.. code-block:: console

    export TOKEN=<generated Access Token>
    curl -i -X GET -H "Content-Type:application/json" http://0.0.0.0:5000/ \
        -H "Authorization:Bearer $TOKEN"

Or, if you are logged in through the browser, try to open the homepage with it:


.. code-block:: console

   $ open http://0.0.0.0:5000/

"""

from __future__ import absolute_import, print_function

import os

from flask import Flask, render_template
from flask_breadcrumbs import Breadcrumbs
from flask_oauthlib.provider import OAuth2Provider
from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint as accounts_blueprint
from invenio_admin import InvenioAdmin
from invenio_assets import InvenioAssets
from invenio_db import InvenioDB, db
from invenio_i18n import InvenioI18N
from invenio_theme import InvenioTheme

from invenio_oauth2server import InvenioOAuth2Server, \
    InvenioOAuth2ServerREST, current_oauth2server, require_api_auth, \
    require_oauth_scopes
from invenio_oauth2server.models import Scope
from invenio_oauth2server.views import server_blueprint, settings_blueprint

# Create Flask application
app = Flask(__name__)
app.config.update(
    CELERY_ALWAYS_EAGER=True,
    CELERY_CACHE_BACKEND='memory',
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    CELERY_RESULT_BACKEND='cache',
    OAUTH2SERVER_CACHE_TYPE='simple',
    OAUTHLIB_INSECURE_TRANSPORT=True,
    TESTING=True,
    SECRET_KEY='test_key',
    SECURITY_PASSWORD_HASH='plaintext',
    SECURITY_PASSWORD_SCHEMES=['plaintext'],
    SECURITY_DEPRECATED_PASSWORD_SCHEMES=[],
    LOGIN_DISABLED=False,
    TEMPLATE_AUTO_RELOAD=True,
    SQLALCHEMY_TRACK_MODIFICATIONS=True,
    SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                      'sqlite:///example.db'),
    I18N_LANGUAGES=[('fr', 'French'), ('de', 'German'), ('it', 'Italian'),
                    ('es', 'Spanish')],
)
InvenioAssets(app)
InvenioTheme(app)
InvenioI18N(app)
Breadcrumbs(app)
InvenioDB(app)
InvenioAdmin(app)
OAuth2Provider(app)
InvenioOAuth2ServerREST(app)

accounts = InvenioAccounts(app)
app.register_blueprint(accounts_blueprint)

InvenioOAuth2Server(app)

# register blueprints
app.register_blueprint(settings_blueprint)
app.register_blueprint(server_blueprint)

with app.app_context():
    # Register a test scope
    current_oauth2server.register_scope(Scope('test:scope'))


@app.route('/jwt', methods=['GET'])
def jwt():
    """JWT."""
    return render_template('jwt.html')


@app.route('/', methods=['GET', 'POST'])
@require_api_auth()
@require_oauth_scopes('test:scope')
def index():
    """Protected endpoint."""
    return 'hello world'


@app.cli.group()
def fixtures():
    """Command for working with test data."""


@fixtures.command()
def users():
    """Load user fixtures."""
    accounts.datastore.create_user(
        email='admin@inveniosoftware.org',
        password='123456',
        active=True,
    )
    accounts.datastore.create_user(
        email='reader@inveniosoftware.org',
        password='123456',
        active=True,
    )
    db.session.commit()
