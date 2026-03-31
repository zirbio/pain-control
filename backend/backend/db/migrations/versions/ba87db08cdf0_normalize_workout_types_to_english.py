"""normalize workout types to english

Revision ID: ba87db08cdf0
Revises: 6247613924fc
Create Date: 2026-03-31 11:53:27.945950

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ba87db08cdf0"
down_revision: str | Sequence[str] | None = "6247613924fc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Same mapping used in backend/importers/apple_health.py
_TYPE_MAP = {
    "Entrenamiento de Fuerza Funcional": "Rehabilitation",
    "Interior Ciclismo": "Indoor Cycling",
    "Caminata": "Walking",
    "Natación": "Swimming",
    "Ciclismo": "Cycling",
    "Elíptica": "Elliptical",
    "Estiramientos": "Stretching",
    "Golf": "Golf",
    # "Pilates" → "Pilates" and "Yoga" → "Yoga" are no-ops, skip them
}

_REVERSE_MAP = {v: k for k, v in _TYPE_MAP.items()}


def upgrade() -> None:
    conn = op.get_bind()
    for spanish, english in _TYPE_MAP.items():
        conn.execute(
            sa.text("UPDATE workout_records SET workout_type = :new WHERE workout_type = :old"),
            {"new": english, "old": spanish},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for english, spanish in _REVERSE_MAP.items():
        conn.execute(
            sa.text("UPDATE workout_records SET workout_type = :new WHERE workout_type = :old"),
            {"new": spanish, "old": english},
        )
