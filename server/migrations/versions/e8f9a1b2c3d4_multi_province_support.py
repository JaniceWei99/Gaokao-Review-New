"""multi_province_support

Revision ID: e8f9a1b2c3d4
Revises: a1b2c3d4e5f6
Create Date: 2026-05-30

Add province-level support for multi-region expansion:
- students: add province column, rename district → region_code
- milestones: rename applicable_districts → applicable_regions, add applicable_provinces
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e8f9a1b2c3d4"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("students", "district", new_column_name="region_code",
                    existing_type=sa.String(20), existing_nullable=True)

    op.add_column("students", sa.Column(
        "province", sa.String(30), nullable=True,
        server_default="shanghai",
        comment="省份ID (e.g. shanghai, beijing)"
    ))

    op.alter_column("milestones", "applicable_districts",
                    new_column_name="applicable_regions",
                    existing_type=postgresql.JSONB, existing_nullable=True)

    op.add_column("milestones", sa.Column(
        "applicable_provinces", postgresql.JSONB, nullable=True,
        comment="适用的省份列表 e.g. ['shanghai']"
    ))


def downgrade() -> None:
    op.drop_column("milestones", "applicable_provinces")

    op.alter_column("milestones", "applicable_regions",
                    new_column_name="applicable_districts",
                    existing_type=postgresql.JSONB, existing_nullable=True)

    op.drop_column("students", "province")

    op.alter_column("students", "region_code", new_column_name="district",
                    existing_type=sa.String(20), existing_nullable=True)
