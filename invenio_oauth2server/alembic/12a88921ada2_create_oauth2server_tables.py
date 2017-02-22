#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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

"""Create oauth2server tables."""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = '12a88921ada2'
down_revision = 'aa546f2a8d2f'
branch_labels = ()
depends_on = '9848d0149abd'


def upgrade():
    """Upgrade database."""
    op.create_table(
        'oauth2server_client',
        sa.Column('name', sa.String(length=40), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'website',
            sqlalchemy_utils.types.url.URLType(),
            nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('client_id', sa.String(length=255), nullable=False),
        sa.Column('client_secret', sa.String(length=255), nullable=False),
        sa.Column(
            'is_confidential',
            sa.Boolean(name='is_confidential'),
            nullable=True),
        sa.Column(
            'is_internal',
            sa.Boolean(name='is_internal'),
            nullable=True),
        sa.Column('_redirect_uris', sa.Text(), nullable=True),
        sa.Column('_default_scopes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], [u'accounts_user.id'], ),
        sa.PrimaryKeyConstraint('client_id')
    )
    op.create_index(
        op.f('ix_oauth2server_client_client_secret'),
        'oauth2server_client',
        ['client_secret'],
        unique=True
    )
    op.create_table(
        'oauth2server_token',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('token_type', sa.String(length=255), nullable=True),
        sa.Column(
            'access_token',
            sqlalchemy_utils.types.encrypted.EncryptedType(),
            nullable=True),
        sa.Column(
            'refresh_token',
            sqlalchemy_utils.types.encrypted.EncryptedType(),
            nullable=True),
        sa.Column('expires', sa.DateTime(), nullable=True),
        sa.Column('_scopes', sa.Text(), nullable=True),
        sa.Column(
            'is_personal',
            sa.Boolean(name='is_personal'),
            nullable=True),
        sa.Column(
            'is_internal',
            sa.Boolean(name='is_internal'),
            nullable=True),
        sa.ForeignKeyConstraint(
            ['client_id'], [u'oauth2server_client.client_id'], ),
        sa.ForeignKeyConstraint(
            ['user_id'], [u'accounts_user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        'ix_oauth2server_token_access_token',
        'oauth2server_token',
        ['access_token'],
        unique=True,
        mysql_length=255)
    op.create_index(
        'ix_oauth2server_token_refresh_token',
        'oauth2server_token',
        ['refresh_token'],
        unique=True,
        mysql_length=255)


def downgrade():
    """Downgrade database."""
    op.drop_index(
        'ix_oauth2server_token_refresh_token',
        table_name='oauth2server_token')
    op.drop_index(
        'ix_oauth2server_token_access_token',
        table_name='oauth2server_token')
    op.drop_table('oauth2server_token')
    op.drop_index(
        op.f('ix_oauth2server_client_client_secret'),
        table_name='oauth2server_client')
    op.drop_table('oauth2server_client')
