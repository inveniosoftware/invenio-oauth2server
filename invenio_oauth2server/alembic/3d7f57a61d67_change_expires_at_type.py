# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
# Copyright (C) 2026 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Change expires_at type to utc aware datetime."""

from alembic import op
from invenio_db import db

# revision identifiers, used by Alembic.
revision = "3d7f57a61d67"
down_revision = "4e57407b8e4a"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.alter_column(
        "oauth2server_token",
        "expires",
        type_=db.UTCDateTime(),
        existing_type=db.DateTime(),
        existing_nullable=True,
    )


def downgrade():
    """Downgrade database."""
    op.alter_column(
        "oauth2server_token",
        "expires",
        type_=db.DateTime(),
        existing_type=db.UTCDateTime(),
        existing_nullable=True,
    )
