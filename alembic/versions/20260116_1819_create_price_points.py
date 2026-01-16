from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260116_1819"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "price_points",
        sa.Column(
            "id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False
        ),
        sa.Column("ticker", sa.Text(), nullable=False),
        sa.Column("ts_unix", sa.BigInteger(), nullable=False),
        sa.Column("price", sa.Numeric(20, 10), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("ticker", "ts_unix", name="uq_price_points_ticker_ts_unix"),
    )

    op.create_index(
        "ix_price_points_ticker_ts_unix",
        "price_points",
        ["ticker", "ts_unix"],
        unique=False,
    )
    op.create_index(
        "ix_price_points_ts_unix",
        "price_points",
        ["ts_unix"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_price_points_ts_unix", table_name="price_points")
    op.drop_index("ix_price_points_ticker_ts_unix", table_name="price_points")
    op.drop_table("price_points")
