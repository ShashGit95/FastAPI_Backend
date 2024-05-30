"""Add columns to UserToken model

Revision ID: 38f08ef79606
Revises: b70f352532d7
Create Date: 2024-02-22 22:49:44.356138

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38f08ef79606'
down_revision: Union[str, None] = 'b70f352532d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_tokens', sa.Column('access_key', sa.String(length=250), nullable=True))
    op.add_column('user_tokens', sa.Column('refresh_key', sa.String(length=250), nullable=True))
    op.add_column('user_tokens', sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
    op.add_column('user_tokens', sa.Column('expires_at', sa.DateTime(), nullable=False))
    op.create_index(op.f('ix_user_tokens_access_key'), 'user_tokens', ['access_key'], unique=False)
    op.create_index(op.f('ix_user_tokens_refresh_key'), 'user_tokens', ['refresh_key'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_tokens_refresh_key'), table_name='user_tokens')
    op.drop_index(op.f('ix_user_tokens_access_key'), table_name='user_tokens')
    op.drop_column('user_tokens', 'expires_at')
    op.drop_column('user_tokens', 'created_at')
    op.drop_column('user_tokens', 'refresh_key')
    op.drop_column('user_tokens', 'access_key')
    # ### end Alembic commands ###
