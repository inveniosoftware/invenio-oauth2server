..
    This file is part of Invenio.
    Copyright (C) 2015-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version 1.3.0a4 (released 2020-12-07)

- Sets `cancel` button's color to Semantic-UI default.
- Integrates Semantic-UI templates.

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
