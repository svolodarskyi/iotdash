"""Initial schema — organisations, users, devices, grafana_dashboards, alerts

Revision ID: 001
Revises:
Create Date: 2025-04-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_uuid = UUID(as_uuid=True)
_uuid_default = sa.text("gen_random_uuid()")


def upgrade() -> None:
    op.create_table(
        "organisations",
        sa.Column("id", _uuid, primary_key=True, server_default=_uuid_default),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("grafana_org_id", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "users",
        sa.Column("id", _uuid, primary_key=True, server_default=_uuid_default),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column(
            "organisation_id",
            _uuid,
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column("role", sa.String(50), nullable=False, server_default="viewer"),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "devices",
        sa.Column("id", _uuid, primary_key=True, server_default=_uuid_default),
        sa.Column("device_code", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "organisation_id",
            _uuid,
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column(
            "device_type",
            sa.String(100),
            nullable=False,
            server_default="sensor",
        ),
        sa.Column("metadata", JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "grafana_dashboards",
        sa.Column("id", _uuid, primary_key=True, server_default=_uuid_default),
        sa.Column(
            "organisation_id",
            _uuid,
            sa.ForeignKey("organisations.id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("grafana_uid", sa.String(255), nullable=False),
        sa.Column("grafana_org_id", sa.Integer, nullable=True),
        sa.Column("panel_ids", JSONB, nullable=True),
        sa.Column("embed_base_url", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "alerts",
        sa.Column("id", _uuid, primary_key=True, server_default=_uuid_default),
        sa.Column(
            "device_id",
            _uuid,
            sa.ForeignKey("devices.id"),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            _uuid,
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("metric", sa.String(100), nullable=False),
        sa.Column("condition", sa.String(20), nullable=False),
        sa.Column("threshold", sa.Float, nullable=False),
        sa.Column(
            "duration_seconds",
            sa.Integer,
            nullable=False,
            server_default=sa.text("60"),
        ),
        sa.Column("notification_email", sa.String(255), nullable=True),
        sa.Column("is_enabled", sa.Boolean, server_default=sa.text("true")),
        sa.Column("grafana_rule_uid", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("grafana_dashboards")
    op.drop_table("devices")
    op.drop_table("users")
    op.drop_table("organisations")
