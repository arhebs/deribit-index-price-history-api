from __future__ import annotations

from collections.abc import Sequence

from alembic import op


revision: str = "20260116_1932"
down_revision: str | None = "20260116_1819"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_price_points_ticker_ts_unix", table_name="price_points")


def downgrade() -> None:
    op.create_index(
        "ix_price_points_ticker_ts_unix",
        "price_points",
        ["ticker", "ts_unix"],
        unique=False,
    )
