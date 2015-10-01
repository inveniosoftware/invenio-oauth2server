=============================
 Invenio-OAuth2Server v0.2.0
=============================

Invenio-OAuth2Server v0.2.0 was released on October 6, 2015.

About
-----

Invenio module that implements OAuth 2 server.

*This is an experimental development preview release.*

Incompatible changes
--------------------

- Removes legacy upgrade recipes. You **MUST** upgrade to the latest
  Invenio 2.1 before upgrading Invenio-Upgrader.

Bug fixes
---------

- Removes calls to PluginManager consider_setuptools_entrypoints()
  removed in PyTest 2.8.0.
- Adds missing `invenio_base` dependency.

Notes
-----

- Disables test_settings_index test case.

Installation
------------

   $ pip install invenio-oauth2server==0.2.0

Documentation
-------------

   http://invenio-oauth2server.readthedocs.org/en/v0.2.0

Happy hacking and thanks for flying Invenio-OAuth2Server.

| Invenio Development Team
|   Email: info@invenio-software.org
|   IRC: #invenio on irc.freenode.net
|   Twitter: http://twitter.com/inveniosoftware
|   GitHub: https://github.com/inveniosoftware/invenio-oauth2server
|   URL: http://invenio-software.org
