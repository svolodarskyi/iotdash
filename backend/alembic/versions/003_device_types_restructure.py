"""Device types restructure: add device_types, device_type_metrics tables,
rename devices -> devices_provisioned, device_metrics -> device_provisioned_metrics.

Revision ID: 003
Revises: 002
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create device_types table
    op.create_table(
        "device_types",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # 2. Populate device_types from existing distinct device_type strings
    op.execute("""
        INSERT INTO device_types (id, name, description)
        SELECT gen_random_uuid(), device_type, NULL
        FROM (SELECT DISTINCT device_type FROM devices) AS dt
    """)

    # 3. Create device_type_metrics table
    op.create_table(
        "device_type_metrics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("device_type_id", sa.Uuid(), nullable=False),
        sa.Column("metric_id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["device_type_id"], ["device_types.id"]),
        sa.ForeignKeyConstraint(["metric_id"], ["metrics.id"]),
        sa.UniqueConstraint("device_type_id", "metric_id", name="uq_device_type_metric"),
    )

    # 4. Populate device_type_metrics from existing device_metrics joins
    op.execute("""
        INSERT INTO device_type_metrics (id, device_type_id, metric_id)
        SELECT gen_random_uuid(), dt.id, sub.metric_id
        FROM (
            SELECT DISTINCT d.device_type, dm.metric_id
            FROM devices d
            JOIN device_metrics dm ON dm.device_id = d.id
        ) sub
        JOIN device_types dt ON dt.name = sub.device_type
    """)

    # 5. Add device_type_id column to devices (nullable initially)
    op.add_column("devices", sa.Column("device_type_id", sa.Uuid(), nullable=True))

    # 6. Backfill device_type_id from the name mapping
    op.execute("""
        UPDATE devices
        SET device_type_id = dt.id
        FROM device_types dt
        WHERE devices.device_type = dt.name
    """)

    # 7. Make device_type_id NOT NULL, add FK constraint
    op.alter_column("devices", "device_type_id", nullable=False)
    op.create_foreign_key(
        "fk_devices_device_type_id",
        "devices",
        "device_types",
        ["device_type_id"],
        ["id"],
    )

    # 8. Drop old device_type VARCHAR column
    op.drop_column("devices", "device_type")

    # 9. Rename tables
    op.rename_table("devices", "devices_provisioned")
    op.rename_table("device_metrics", "device_provisioned_metrics")

    # 10. Update FK references in alerts table
    op.drop_constraint("alerts_device_id_fkey", "alerts", type_="foreignkey")
    op.create_foreign_key(
        "alerts_device_id_fkey",
        "alerts",
        "devices_provisioned",
        ["device_id"],
        ["id"],
    )

    # 11. Update FK references in device_provisioned_metrics
    op.drop_constraint("device_metrics_device_id_fkey", "device_provisioned_metrics", type_="foreignkey")
    op.create_foreign_key(
        "device_provisioned_metrics_device_id_fkey",
        "device_provisioned_metrics",
        "devices_provisioned",
        ["device_id"],
        ["id"],
    )

    # 12. Rename unique constraint on device_provisioned_metrics
    op.drop_constraint("uq_device_metric", "device_provisioned_metrics", type_="unique")
    op.create_unique_constraint(
        "uq_device_provisioned_metric",
        "device_provisioned_metrics",
        ["device_id", "metric_id"],
    )


def downgrade() -> None:
    # Reverse rename
    op.rename_table("device_provisioned_metrics", "device_metrics")
    op.rename_table("devices_provisioned", "devices")

    # Restore unique constraint name
    op.drop_constraint("uq_device_provisioned_metric", "device_metrics", type_="unique")
    op.create_unique_constraint("uq_device_metric", "device_metrics", ["device_id", "metric_id"])

    # Restore FK references
    op.drop_constraint("device_provisioned_metrics_device_id_fkey", "device_metrics", type_="foreignkey")
    op.create_foreign_key("device_metrics_device_id_fkey", "device_metrics", "devices", ["device_id"], ["id"])

    op.drop_constraint("alerts_device_id_fkey", "alerts", type_="foreignkey")
    op.create_foreign_key("alerts_device_id_fkey", "alerts", "devices", ["device_id"], ["id"])

    # Re-add device_type string column
    op.add_column("devices", sa.Column("device_type", sa.String(100), nullable=True))
    op.execute("""
        UPDATE devices
        SET device_type = dt.name
        FROM device_types dt
        WHERE devices.device_type_id = dt.id
    """)
    op.alter_column("devices", "device_type", nullable=False, server_default="sensor")

    # Drop device_type_id FK and column
    op.drop_constraint("fk_devices_device_type_id", "devices", type_="foreignkey")
    op.drop_column("devices", "device_type_id")

    # Drop new tables
    op.drop_table("device_type_metrics")
    op.drop_table("device_types")
