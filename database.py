"""
Database module - SQLite database setup and management
"""

import sqlite3
from flask import g
import os
from werkzeug.security import generate_password_hash

DATABASE = 'budget_planner.db'


def get_db():
    """Get database connection"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def init_db():
    """Initialize the database with tables"""
    if os.path.exists(DATABASE):
        return  # Database already exists

    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()

    # Create user_settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            monthly_budget REAL NOT NULL,
            savings_goal REAL NOT NULL,
            savings_purpose TEXT,
            created_at TIMESTAMP NOT NULL
        )
    ''')

    # Create fixed_expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fixed_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            frequency TEXT NOT NULL CHECK(frequency IN ('weekly', 'monthly')),
            created_at TIMESTAMP NOT NULL
        )
    ''')

    # Create transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            is_anomaly BOOLEAN DEFAULT 0,
            z_score REAL,
            created_at TIMESTAMP NOT NULL
        )
    ''')

    # Create monthly_stats table (for caching calculations)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL,
            category TEXT NOT NULL,
            total_spent REAL NOT NULL,
            mean REAL NOT NULL,
            std_dev REAL NOT NULL,
            transaction_count INTEGER NOT NULL,
            UNIQUE(month, category)
        )
    ''')

    db.commit()
    db.close()


def close_db(e=None):
    """Close database connection"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def migrate_to_multiuser():
    """Migrate existing database to support multi-user"""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()

    try:
        # Create income table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                amount REAL NOT NULL,
                source TEXT NOT NULL,
                description TEXT,
                recurring BOOLEAN DEFAULT 0,
                frequency TEXT CHECK(frequency IN ('weekly', 'bi-weekly', 'monthly', 'annually', 'one-time')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone() is None:
            # Create users table
            cursor.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    name TEXT NOT NULL,
                    email_verified BOOLEAN DEFAULT 0,
                    verification_token TEXT,
                    token_expiry TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')

            # Check if user_settings has user_id column
            cursor.execute("PRAGMA table_info(user_settings)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'user_id' not in columns:
                # Add user_id columns to existing tables
                cursor.execute('ALTER TABLE user_settings ADD COLUMN user_id INTEGER')
                cursor.execute('ALTER TABLE fixed_expenses ADD COLUMN user_id INTEGER')
                cursor.execute('ALTER TABLE transactions ADD COLUMN user_id INTEGER')
                cursor.execute('ALTER TABLE monthly_stats ADD COLUMN user_id INTEGER')

                # Check if there's existing data (old single-user mode)
                cursor.execute('SELECT COUNT(*) FROM user_settings')
                has_data = cursor.fetchone()[0] > 0

                if has_data:
                    # Get the name from user_settings
                    cursor.execute('SELECT name FROM user_settings LIMIT 1')
                    user_name = cursor.fetchone()[0]

                    # Create a default user from existing data
                    default_password = generate_password_hash('password123')
                    cursor.execute('''
                        INSERT INTO users (email, password_hash, name)
                        VALUES (?, ?, ?)
                    ''', ('user@budgetplanner.local', default_password, user_name))

                    default_user_id = cursor.lastrowid

                    # Update all existing records to belong to this user
                    cursor.execute('UPDATE user_settings SET user_id = ?', (default_user_id,))
                    cursor.execute('UPDATE fixed_expenses SET user_id = ?', (default_user_id,))
                    cursor.execute('UPDATE transactions SET user_id = ?', (default_user_id,))
                    cursor.execute('UPDATE monthly_stats SET user_id = ?', (default_user_id,))

                    print(f"Migration complete! Default user created:")
                    print(f"  Email: user@budgetplanner.local")
                    print(f"  Password: password123")
                    print(f"  Please change this password after logging in!")

            db.commit()

        # Add email verification columns to existing users table if they don't exist
        try:
            cursor.execute("PRAGMA table_info(users)")
            user_columns = [col[1] for col in cursor.fetchall()]

            if 'email_verified' not in user_columns:
                cursor.execute('ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0')
                print("Added email_verified column to users table")

            if 'verification_token' not in user_columns:
                cursor.execute('ALTER TABLE users ADD COLUMN verification_token TEXT')
                print("Added verification_token column to users table")

            if 'token_expiry' not in user_columns:
                cursor.execute('ALTER TABLE users ADD COLUMN token_expiry TIMESTAMP')
                print("Added token_expiry column to users table")

            db.commit()
        except Exception as e:
            print(f"Error adding verification columns: {e}")

        return True
    except Exception as e:
        db.rollback()
        print(f"Migration error: {e}")
        return False
    finally:
        db.close()
