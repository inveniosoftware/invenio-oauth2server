# SPDX-FileCopyrightText: 2017-2018 CERN.
# SPDX-FileCopyrightText: 2023 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""OAuth2 scopes."""

from invenio_i18n import lazy_gettext as _

from invenio_oauth2server.models import Scope

email_scope = Scope(
    id_="user:email",
    group="user",
    help_text=_("Allow access to email address (read-only)."),
)
"""Scope to protect the user's email address."""
