"""
Database migration script to add new IP intelligence fields.
Run: python migrate_ip_fields.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.database import db

def migrate():
    app = create_app()
    with app.app_context():
        # Add new columns to ip_intelligence table
        new_columns = [
            ('latitude', 'FLOAT'),
            ('longitude', 'FLOAT'),
            ('asn', 'VARCHAR(30)'),
            ('timezone', 'VARCHAR(50)'),
            ('event_count', 'INTEGER DEFAULT 0'),
            ('alert_count', 'INTEGER DEFAULT 0'),
            ('first_seen', 'TIMESTAMP'),
            ('last_seen', 'TIMESTAMP'),
        ]

        for col_name, col_type in new_columns:
            try:
                db.session.execute(db.text(f'ALTER TABLE ip_intelligence ADD COLUMN {col_name} {col_type}'))
                print(f'[Migration] Added column: {col_name}')
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate column' in str(e).lower():
                    print(f'[Migration] Column {col_name} already exists, skipping.')
                else:
                    print(f'[Migration] Error adding {col_name}: {e}')

        db.session.commit()
        print('[Migration] IP intelligence migration complete.')

if __name__ == '__main__':
    migrate()
