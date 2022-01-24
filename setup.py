# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2022 RERO.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module that implements OAuth 2 server."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'pytest-invenio>=1.4.0',
]

extras_require = {
    'admin': [
        'invenio-admin>=1.2.1'
    ],
    'docs': [
        'Sphinx>=4.2.0',
    ],
    'redis': [
        'redis>=2.10.5',
    ],
    'mysql': [
        'invenio-db[mysql,versioning]>=1.0.9,<2.0.0',
    ],
    'postgresql': [
        'invenio-db[postgresql,versioning]>=1.0.9,<2.0.0',
    ],
    'sqlite': [
        'invenio-db[versioning]>=1.0.9,<2.0.0',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for name, reqs in extras_require.items():
    if name in {'mysql', 'postgresql', 'sqlite'}:
        continue
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=2.8',
]

install_requires = [
    # package needed to patch flask-oauthlib
    'cachelib>=0.1',
    'Flask-Breadcrumbs>=0.4.0',
    'Flask-OAuthlib>=0.9.5',
    'Flask-WTF>=0.14.3',
    'future>=0.16.0',
    'invenio-accounts>=1.3.1',
    'invenio-base>=1.2.4',
    'invenio-i18n>=1.2.0',
    'invenio-theme>=1.3.4',
    'pyjwt>=1.5.0',
    'requests-oauthlib>=1.1.0,<1.2.0',
    'WTForms-Alchemy>=0.15.0',
    'WTForms>=2.3.3,<3.0.0',
    'importlib_metadata>=4.4'
]

packages = find_packages()

# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_oauth2server', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-oauth2server',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio OAuth2 server',
    license='MIT',
    author='CERN',
    author_email='info@inveniosoftware.org',
    url='https://github.com/inveniosoftware/invenio-oauth2server',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'flask.commands': [
            'tokens = invenio_oauth2server.cli:tokens',
        ],
        'invenio_admin.views': [
            'invenio_oauth2server_clients_adminview = '
            'invenio_oauth2server.admin:oauth2server_clients_adminview',
            'invenio_oauth2server_tokens_adminview = '
            'invenio_oauth2server.admin:oauth2server_tokens_adminview',
        ],
        'invenio_base.apps': [
            'invenio_oauth2server = invenio_oauth2server:InvenioOAuth2Server',
        ],
        'invenio_base.api_apps': [
            'invenio_oauth2server = invenio_oauth2server:InvenioOAuth2Server',
            'invenio_oauth2server_rest ='
            ' invenio_oauth2server:InvenioOAuth2ServerREST',
        ],
        'invenio_base.blueprints': [
            'invenio_oauth2server ='
            ' invenio_oauth2server.views.server:blueprint',
            'invenio_oauth2server_settings ='
            ' invenio_oauth2server.views.settings:blueprint',
        ],
        'invenio_db.alembic': [
            'invenio_oauth2server = invenio_oauth2server:alembic',
        ],
        'invenio_db.models': [
            'invenio_oauth2server = invenio_oauth2server.models',
        ],
        'invenio_oauth2server.scopes': [
            'oauth_email = invenio_oauth2server.scopes:email_scope',
        ],
        'invenio_i18n.translations': [
            'messages = invenio_oauth2server',
        ],
        'invenio_base.secret_key': [
            'invenio_oauth2server = '
            'invenio_oauth2server.utils:rebuild_access_tokens',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Development Status :: 5 - Production/Stable',
    ],
)
