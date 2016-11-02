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

"""Test helper functions."""

from __future__ import absolute_import, print_function

from flask import Blueprint, abort, jsonify, request, session, url_for
from flask_oauthlib.client import OAuth, prepare_request
from mock import MagicMock
from six.moves.urllib.parse import urlparse
from werkzeug.urls import url_decode, url_parse, url_unparse


def patch_request(app):
    test_client = app.test_client()

    def make_request(uri, headers=None, data=None, method=None):
        uri, headers, data, method = prepare_request(
            uri, headers, data, method
        )
        if not headers and data is not None:
            headers = {
                'Content-Type': ' application/x-www-form-urlencoded'
            }

        # test client is a `werkzeug.test.Client`
        parsed = urlparse(uri)
        uri = '%s?%s' % (parsed.path, parsed.query)
        resp = test_client.open(
            uri, headers=headers, data=data, method=method,
        )
        # for compatible
        resp.code = resp.status_code
        return resp, resp.data
    return make_request


def parse_redirect(location, parse_fragment=False):
    scheme, netloc, script_root, qs, anchor = url_parse(location)
    return (
        url_unparse((scheme, netloc, script_root, '', '')),
        url_decode(anchor if parse_fragment else qs)
    )


def login(test_client, email='info@inveniosoftware.org', password='tester'):
    return test_client.post(
        url_for('security.login'),
        data={
            'email': email,
            'password': password,
        })


def create_oauth_client(app, name, **kwargs):
    """Helper function to create a OAuth2 client to test an OAuth2 provider."""
    blueprint = Blueprint('oauth2test', __name__, template_folder='templates')

    default = dict(
        consumer_key='confidential',
        consumer_secret='confidential',
        request_token_params={'scope': 'test:scope'},
        request_token_url=None,
        access_token_method='POST',
        access_token_url='/oauth/token',
        authorize_url='/oauth/authorize',
        content_type='application/json',
    )
    default.update(kwargs)

    oauth = OAuth(app)
    remote = oauth.remote_app(name, **default)

    @blueprint.route('/oauth2test/login')
    def login():
        return remote.authorize(callback=url_for('oauth2test.authorized',
                                                 _external=True))

    @blueprint.route('/oauth2test/logout')
    def logout():
        session.pop('confidential_token', None)
        return "logout"

    @blueprint.route('/oauth2test/authorized')
    @remote.authorized_handler
    def authorized(resp):
        if resp is None:
            return 'Access denied: error=%s' % (
                request.args.get('error', "unknown")
            )
        if isinstance(resp, dict) and 'access_token' in resp:
            session['confidential_token'] = (resp['access_token'], '')
            return jsonify(resp)
        return str(resp)

    def get_test(test_url):
        if 'confidential_token' not in session:
            abort(403)
        else:
            ret = remote.get(test_url)
            if ret.status != 200:
                return abort(ret.status)
            return ret.raw_data

    @blueprint.route('/oauth2test/test-ping')
    def test_ping():
        return get_test(url_for("invenio_oauth2server.ping"))

    @blueprint.route('/oauth2test/test-info')
    def test_info():
        return get_test(url_for('invenio_oauth2server.info'))

    @blueprint.route('/oauth2test/test-invalid')
    def test_invalid():
        return get_test(url_for('invenio_oauth2server.invalid'))

    @remote.tokengetter
    def get_oauth_token():
        return session.get('confidential_token')

    app.register_blueprint(blueprint)

    return remote
