"""normalize order status enum to lowercase

Revision ID: 2e3a5e335c88
Revises: badc59c5f1fe
Create Date: 2026-05-19 19:04:45.150119

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2e3a5e335c88"
down_revision: Union[str, Sequence[str], None] = "badc59c5f1fe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ADD VALUE must be committed before the new value can be used in an UPDATE.
    with op.get_context().autocommit_block():
        op.execute(sa.text("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'pending'"))
        op.execute(sa.text("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'shipped'"))
        op.execute(
            sa.text("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'cancelled'")
        )
    op.execute(sa.text("UPDATE orders SET status = 'pending' WHERE status = 'PENDING'"))
    op.execute(sa.text("UPDATE orders SET status = 'shipped' WHERE status = 'SHIPPED'"))
    op.execute(
        sa.text("UPDATE orders SET status = 'cancelled' WHERE status = 'CANCELLED'")
    )


def downgrade() -> None:
    pass  # Postgres does not support dropping enum values
