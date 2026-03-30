"""One-time migration: copy data from child tables into DailyEntry columns.

Run from project root:
    python backend/scripts/migrate_child_to_entry.py

Or from backend/ directory:
    python scripts/migrate_child_to_entry.py

Idempotent — safe to re-run. Only updates NULL fields on DailyEntry.
"""

import sys
from pathlib import Path

# Project root is three levels up: scripts/ -> backend/ -> project root
DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "pain-control.db"


def migrate():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        sys.exit(1)

    from sqlalchemy import create_engine, text

    engine = create_engine(f"sqlite:///{DB_PATH}")
    with engine.begin() as conn:
        # Mood → mood_score, mood_emotions
        conn.execute(
            text("""
            UPDATE daily_entries SET
                mood_score = (
                    SELECT score FROM mood_records
                    WHERE mood_records.entry_id = daily_entries.id
                    LIMIT 1
                ),
                mood_emotions = (
                    SELECT emotions FROM mood_records
                    WHERE mood_records.entry_id = daily_entries.id
                    LIMIT 1
                )
            WHERE mood_score IS NULL
              AND EXISTS (SELECT 1 FROM mood_records WHERE mood_records.entry_id = daily_entries.id)
        """)
        )

        # Stress → stress_source
        conn.execute(
            text("""
            UPDATE daily_entries SET
                stress_source = (
                    SELECT source FROM stress_records
                    WHERE stress_records.entry_id = daily_entries.id
                    LIMIT 1
                )
            WHERE stress_source IS NULL
              AND EXISTS (
                    SELECT 1 FROM stress_records
                    WHERE stress_records.entry_id = daily_entries.id
                )
        """)
        )

        # Activity → activity_pain_effect
        conn.execute(
            text("""
            UPDATE daily_entries SET
                activity_pain_effect = (
                    SELECT pain_effect FROM activity_records
                    WHERE activity_records.entry_id = daily_entries.id
                      AND pain_effect IS NOT NULL
                    LIMIT 1
                )
            WHERE activity_pain_effect IS NULL
              AND EXISTS (
                  SELECT 1 FROM activity_records
                  WHERE activity_records.entry_id = daily_entries.id
                    AND pain_effect IS NOT NULL
              )
        """)
        )

        # Nutrition → alcohol
        conn.execute(
            text("""
            UPDATE daily_entries SET
                alcohol = (
                    SELECT alcohol FROM nutrition_records
                    WHERE nutrition_records.entry_id = daily_entries.id
                    LIMIT 1
                )
            WHERE alcohol IS NULL
              AND EXISTS (
                    SELECT 1 FROM nutrition_records
                    WHERE nutrition_records.entry_id = daily_entries.id
                )
        """)
        )

        # Set defaults for new boolean fields (historical entries)
        for field in ("heavy_dinner", "omega3", "vitamin_d", "magnesium", "turmeric"):
            conn.execute(text(f"UPDATE daily_entries SET {field} = 0 WHERE {field} IS NULL"))

        # Verify migration
        result = conn.execute(
            text("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN mood_score IS NOT NULL THEN 1 ELSE 0 END) as with_mood,
                SUM(CASE WHEN alcohol IS NOT NULL THEN 1 ELSE 0 END) as with_alcohol
            FROM daily_entries
        """)
        ).fetchone()

        mood_in_old = conn.execute(
            text("SELECT COUNT(DISTINCT entry_id) FROM mood_records")
        ).scalar()

        alcohol_in_old = conn.execute(
            text("SELECT COUNT(DISTINCT entry_id) FROM nutrition_records WHERE alcohol IS NOT NULL")
        ).scalar()

        print(f"Total entries: {result[0]}")
        print(f"Entries with mood_score: {result[1]} (source records: {mood_in_old})")
        print(f"Entries with alcohol: {result[2]} (source records: {alcohol_in_old})")
        print("Migration complete.")


if __name__ == "__main__":
    migrate()
