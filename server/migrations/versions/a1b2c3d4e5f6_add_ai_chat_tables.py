"""add ai_chat tables and subscription payment fields

Revision ID: a1b2c3d4e5f6
Revises: cf3d8aef1f11
Create Date: 2026-05-28

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'cf3d8aef1f11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_chat_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('student_id', sa.Uuid(), nullable=False),
        sa.Column('created_date', sa.Date(), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['student_id'], ['students.id']),
    )
    op.create_index(
        'ix_ai_chat_sessions_user_date',
        'ai_chat_sessions',
        ['user_id', 'created_date'],
    )

    op.create_table(
        'ai_chat_messages',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('session_id', sa.Uuid(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['ai_chat_sessions.id']),
    )

    op.add_column('user_subscriptions', sa.Column('out_trade_no', sa.String(length=64), nullable=True, comment='WeChat Pay out_trade_no'))
    op.add_column('user_subscriptions', sa.Column('payment_status', sa.String(length=20), nullable=True, comment='pending | paid | failed | refunded'))
    op.add_column('user_subscriptions', sa.Column('transaction_id', sa.String(length=64), nullable=True, comment='WeChat Pay transaction_id'))


def downgrade() -> None:
    op.drop_column('user_subscriptions', 'transaction_id')
    op.drop_column('user_subscriptions', 'payment_status')
    op.drop_column('user_subscriptions', 'out_trade_no')
    op.drop_table('ai_chat_messages')
    op.drop_index('ix_ai_chat_sessions_user_date', table_name='ai_chat_sessions')
    op.drop_table('ai_chat_sessions')
