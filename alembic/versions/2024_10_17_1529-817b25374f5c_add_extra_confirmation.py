"""Add extra confirmation

Revision ID: 817b25374f5c
Revises: 0c6a58e58e2f
Create Date: 2024-10-17 15:29:58.809825

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '817b25374f5c'
down_revision: Union[str, None] = '0c6a58e58e2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('extra_confirmation', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'extra_confirmation')
    # ### end Alembic commands ###
