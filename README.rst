======================
 Invenio-OAuth2Server
======================

.. image:: https://img.shields.io/travis/inveniosoftware/invenio-oauth2server.svg
        :target: https://travis-ci.org/inveniosoftware/invenio-oauth2server

.. image:: https://img.shields.io/coveralls/inveniosoftware/invenio-oauth2server.svg
        :target: https://coveralls.io/r/inveniosoftware/invenio-oauth2server

.. image:: https://img.shields.io/github/tag/inveniosoftware/invenio-oauth2server.svg
        :target: https://github.com/inveniosoftware/invenio-oauth2server/releases

.. image:: https://img.shields.io/pypi/dm/invenio-oauth2server.svg
        :target: https://pypi.python.org/pypi/invenio-oauth2server

.. image:: https://img.shields.io/github/license/inveniosoftware/invenio-oauth2server.svg
        :target: https://github.com/inveniosoftware/invenio-oauth2server/blob/master/LICENSE


Invenio module that implements OAuth 2 server.

* Free software: MIT license
* Documentation: https://invenio-oauth2server.readthedocs.io/

Features
========
* Implements the OAuth 2.0 authentication protocol.
    - Provides REST API to provide access tokens.
    - Provides decorators that can be used to restrict access to resources.
* Handles authentication using JSON Web Tokens.
* Adds support for CSRF protection in REST API.