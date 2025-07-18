..
    This file is part of Invenio.
    Copyright (C) 2015-2024 CERN.
    Copyright (C) 2024-2025 Graz University of Technology.
    Copyright (C) 2025 KTH Royal Institute of Technology.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version v3.3.0 (released 2025-07-17)

- i18n: pulled translations

Version v3.2.0 (released 2025-07-14)

- chores: replaced importlib_xyz with importlib
- i18n:push translations

Version v3.1.0 (released 2025-07-03)

- provided translated field labels
- fix: setuptools require underscores instead of dashes
- i18n: removed deprecated messages
- i18n: unified gettext formatting

Version v3.0.2 (released 2025-02-06)

- fix: avoid reading body of request when verifying token
    * This is to fix a bug that affects large file uploads,
      where we need to tell Flask that we expect a large body
      before actually starting to read/access it.

Version 3.0.1 (released 2025-01-28)

- fix: update iter_choices for WTForms 3.0.0 compatibility

Version 3.0.0 (released 2024-12-12)

- setup: move to flask-oauthlib-invenio
- global: replace werkzeug.url with urllib.parse
- tests: changed status_code
- fix: LegacyAPIWarning
- fix: DeprecationWarning:
- tests: apply changes for sqlalchemy>=2.0
- setup: bump major dependencies

Version 2.4.1 (release 2024-11-30)

- setup: change to reusable workflows
- setup: pin dependencies

Version 2.4.0 (released 2024-11-07)

- global: remove six usage
- compatibility: to werkzeug >= 2.3.0
- setup: unpin wtforms dependency
- fix: DeprecationWarning HTMLString
- settings: update page to reflect additional required parameter
- i18n: push translations

Version 2.3.1 (released 2024-05-17)

- settings-ui: fix token scopes list

Version 2.3.0 (released 2024-03-22)

- fix: before_first_request deprecation
  (add finalise app entrypoint)


Version 2.2.1 (released 2023-10-31)

- settings: simplify token query

Version 2.2.0 (released 2023-09-12)

- new-buttons: remove secondary class from buttons

Version 2.1.0 (released 2023-07-31)

- applications: Improve templates for UI and accessibility
- pulled translations

Version 2.0.0 (released 2023-03-02)

- drop python2.7 support
- remove deprecated flask-babelex dependency and imports
- upgrade invenio-i18n
- upgrade invenio-admin

Version 1.3.8 (released 2022-11-18)

- add translations

Version 1.3.7 (released 2022-08-04)

- save user in the flask global

Version 1.3.6 (released 2022-06-27)

- extract translation messages
- add German translations

Version 1.3.5 (released 2022-02-28)

- Replaces pkg_resources with importlib.
- Fix translation issue with fuzzy translations.
- Fix Flask 2 compatibility issue.

Version 1.3.4 (released 2021-07-15)

- Adds german translations

Version 1.3.3 (released 2021-06-01)

- Maximum version of WTForms set to <3.0.0 due to incompatibility issues.

Version 1.3.2 (released 2020-12-17)

- Adds theme dependent icons.
- Fixes layout and styling issues.
- Fixes UX issues related to button ordering.

Version 1.3.1 (released 2020-12-11)

- Fixes issue with form for application creation.
- Fixes problem with rendering errors in the form.

Version 1.3.0 (released 2020-12-09)

- Integrates Semantic-UI templates.
- Sets `cancel` button's color to Semantic-UI default.

Version 1.2.0 (released 2020-05-14)

- Allow bypassing CSRF checks when using bearer tokens.

Version 1.1.1 (released 2020-05-11)

- Deprecated Python versions lower than 3.6.0. Now supporting 3.6.0 and 3.7.0.
- Minimum version of Invenio-Accounts bumped to v1.2.1 due WTForms moving the
  email validation to an optional dependency.
- Maximum version of Sphinx set to 3 (lower than) due to an error with
  working outside the application context.
- Maximum version of SQLAlchemy-Utils set to 0.36 due to breaking changes
  with MySQL (VARCHAR length).

Version 1.1.0 (released 2020-03-10)

- Provides compatibility with werkzeug 1.0.0 for flask_oauthlib

Version 1.0.5 (released 2020-05-11)

- Deprecated Python versions lower than 3.6.0. Now supporting 3.6.0 and 3.7.0.
- Minimum version of Invenio-Accounts set to v1.1.4 due WTForms moving the
  email validation to an optional dependency.
- Minimum version of Flask-BableEx set to v0.9.4 due Werkzeug breaking imports.
- Minimum version of oauthlib set to v2.1.0.
- Maximum version of Sphinx set to 3 (lower than) due to an error with
  working outside the application context.
- Maximum version of SQLAlchemy-Utils set to 0.36 due to breaking changes
  with MySQL (VARCHAR length).

Version 1.0.4 (released 2019-12-05)

- Removes updating the ``expires`` for personal tokens.
- Removes ``OAUTH2_PROVIDER_TOKEN_EXPIRES_IN`` from configuration.

Version 1.0.3 (released 2019-01-15)

- Restrict oauthlib to latest v2.
- Restrict requests-oauthlib lower than 1.2.0 because of oauthlib 3.

Version 1.0.2 (released 2018-11-02)

- Fix incosistent OAuth2 state initialization between UI and REST applications.
- Basic token management CLI commands for creating/deleting personal access
  tokens.
- Better token creation warning messages.

Version 1.0.1 (released 2018-05-25)

- Flask v1.0 support.

Version 1.0.0 (released 2018-03-23)

- Initial public release.
