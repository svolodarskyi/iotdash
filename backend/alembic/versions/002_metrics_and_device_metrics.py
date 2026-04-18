"""Metrics catalog and device-metric assignments

Revision ID: 002
Revises: 001
Create Date: 2025-05-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_uuid = UUID(as_uuid=True)
_uuid_default = sa.text("gen_random_uuid()")


def upgrade() -> None:
    op.create_table(
        "metrics",
        sa.Column("id", _uuid, primary_key=True, server_default=_uuid_default),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("data_type", sa.String(50), nullable=False, server_default="float"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "device_metrics",
        sa.Column("id", _uuid, primary_key=True, server_default=_uuid_default),
        sa.Column(
            "device_id",
            _uuid,
            sa.ForeignKey("devices.id"),
            nullable=False,
        ),
        sa.Column(
            "metric_id",
            _uuid,
            sa.ForeignKey("metrics.id"),
            nullable=False,
        ),
        sa.Column("is_enabled", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column(
            "enabled_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("device_id", "metric_id", name="uq_device_metric"),
    )


def downgrade() -> None:
    op.drop_table("device_metrics")
    op.drop_table("metrics")
