"""ADD WALLET AND NEWS

Revision ID: 68f9dc87a768
Revises: a445a410f486
Create Date: 2024-10-07 20:20:18.160945

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68f9dc87a768'
down_revision: Union[str, None] = 'a445a410f486'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('news',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('creator_name', sa.String(length=255), nullable=False),
    sa.Column('image_url', sa.Text(), nullable=True),
    sa.Column('link', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('solana_wallets',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('wallet', sa.BigInteger(), nullable=False),
    sa.Column('public_key', sa.String(length=255), nullable=False),
    sa.Column('encrypted_private_key', sa.LargeBinary(), nullable=False),
    sa.Column('sol_balance', sa.Integer(), nullable=False),
    sa.Column('number_of_trades', sa.Integer(), nullable=False),
    sa.Column('number_od_snipes', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['wallet'], ['wallets.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('wallet')
    )
    op.create_index(op.f('ix_solana_wallets_encrypted_private_key'), 'solana_wallets', ['encrypted_private_key'], unique=False)
    op.create_index(op.f('ix_solana_wallets_public_key'), 'solana_wallets', ['public_key'], unique=False)
    op.create_index(op.f('ix_solana_wallets_wallet'), 'solana_wallets', ['wallet'], unique=False)
    op.create_table('token_balances',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('solana_wallet', sa.BigInteger(), nullable=False),
    sa.Column('token_address', sa.String(length=255), nullable=False),
    sa.Column('token_symbol', sa.String(length=255), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['solana_wallet'], ['solana_wallets.wallet'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('solana_wallet')
    )
    op.create_index(op.f('ix_token_balances_solana_wallet'), 'token_balances', ['solana_wallet'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_token_balances_solana_wallet'), table_name='token_balances')
    op.drop_table('token_balances')
    op.drop_index(op.f('ix_solana_wallets_wallet'), table_name='solana_wallets')
    op.drop_index(op.f('ix_solana_wallets_public_key'), table_name='solana_wallets')
    op.drop_index(op.f('ix_solana_wallets_encrypted_private_key'), table_name='solana_wallets')
    op.drop_table('solana_wallets')
    op.drop_table('news')
    # ### end Alembic commands ###
