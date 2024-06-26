"""Added user verification and timestamps

Revision ID: b70f352532d7
Revises: 9ebe805148a2
Create Date: 2024-02-20 22:05:36.617163

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b70f352532d7'
down_revision: Union[str, None] = '9ebe805148a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('verified_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'created_at')
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'verified_at')
    # ### end Alembic commands ###
