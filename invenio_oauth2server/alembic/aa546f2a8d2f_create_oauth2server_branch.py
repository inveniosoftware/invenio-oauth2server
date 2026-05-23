# SPDX-FileCopyrightText: 2016-2018 CERN.
# SPDX-FileCopyrightText: 2023 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Create oauth2server branch."""

# revision identifiers, used by Alembic.
revision = "aa546f2a8d2f"
down_revision = None
branch_labels = ("invenio_oauth2server",)
depends_on = "dbdbc1b19cf2"


def upgrade():
    """Upgrade database."""
    pass


def downgrade():
    """Downgrade database."""
    pass
