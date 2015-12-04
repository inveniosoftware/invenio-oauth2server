# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (c) 2015 CERN.
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

"""OAuth2Server decorators test cases."""


def test_require_api_auth_test1(resource_fixture):
    app = resource_fixture
    with app.test_client() as client:
        res = client.get(app.url_for_test1resource)
        assert 401 == res.status_code
        res = client.get(app.url_for_test1resource_token)
        assert 200 == res.status_code


def test_require_api_auth_test2(resource_fixture):
    app = resource_fixture
    with app.test_client() as client:
        res = client.get(app.url_for_test2resource)
        assert 401 == res.status_code
        res = client.get(app.url_for_test2resource_token)
        assert 200 == res.status_code


def test_require_oauth_scopes_test1(resource_fixture):
    app = resource_fixture
    with app.test_client() as client:
        res = client.post(app.url_for_test1resource_token)
        assert 200 == res.status_code
        res = client.post(app.url_for_test1resource_token_noscope)
        assert 403 == res.status_code


def test_require_oauth_scopes_test2(resource_fixture):
    app = resource_fixture
    with app.test_client() as client:
        res = client.post(app.url_for_test2resource_token)
        assert 200 == res.status_code
        res = client.post(app.url_for_test2resource_token_noscope)
        assert 403 == res.status_code
