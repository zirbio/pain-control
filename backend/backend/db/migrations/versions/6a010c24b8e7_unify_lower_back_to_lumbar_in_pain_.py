"""unify lower_back to lumbar in pain_records

Revision ID: 6a010c24b8e7
Revises: 913af3612ea7
Create Date: 2026-04-05 17:49:52.502673

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6a010c24b8e7"
down_revision: str | Sequence[str] | None = "913af3612ea7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Unify 'lower_back' → 'lumbar' in pain_records."""
    op.execute(sa.text("UPDATE pain_records SET location = 'lumbar' WHERE location = 'lower_back'"))


def downgrade() -> None:
    """Lossy revert: converts ALL 'lumbar' to 'lower_back', including pre-existing ones."""
    op.execute(sa.text("UPDATE pain_records SET location = 'lower_back' WHERE location = 'lumbar'"))
