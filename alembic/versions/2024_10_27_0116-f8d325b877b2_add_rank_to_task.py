"""add rank to task

Revision ID: f8d325b877b2
Revises: 4f1679d6d883
Create Date: 2024-10-27 01:16:48.087521

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8d325b877b2'
down_revision: Union[str, None] = '5d83a413b5a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tasks', sa.Column('rank', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tasks', 'rank')
    # ### end Alembic commands ###
