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

        # Create assets table for investment & assets tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                asset_type TEXT NOT NULL CHECK(asset_type IN ('stock', 'savings', 'property', 'crypto', 'bond', 'other')),
                name TEXT NOT NULL,
                current_value REAL NOT NULL,
                purchase_value REAL,
                purchase_date DATE,
                quantity REAL DEFAULT 1,
                currency TEXT DEFAULT 'USD',
                description TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Create asset_history table for tracking value changes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL,
                value REAL NOT NULL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
            )
        ''')

        # Create recurring_transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recurring_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                currency TEXT DEFAULT 'USD',
                frequency TEXT NOT NULL CHECK(frequency IN ('daily', 'weekly', 'bi-weekly', 'monthly', 'quarterly', 'annually')),
                start_date DATE NOT NULL,
                end_date DATE,
                last_generated DATE,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Create exchange_rates table for currency conversion
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchange_rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                from_currency TEXT NOT NULL,
                to_currency TEXT NOT NULL,
                rate REAL NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, from_currency, to_currency),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Add currency column to transactions if it doesn't exist
        cursor.execute("PRAGMA table_info(transactions)")
        transaction_columns = [col[1] for col in cursor.fetchall()]
        if 'currency' not in transaction_columns:
            cursor.execute('ALTER TABLE transactions ADD COLUMN currency TEXT DEFAULT "USD"')

        # Add currency column to income if it doesn't exist (already added currency to assets earlier)
        cursor.execute("PRAGMA table_info(income)")
        income_columns = [col[1] for col in cursor.fetchall()]
        if 'currency' not in income_columns:
            cursor.execute('ALTER TABLE income ADD COLUMN currency TEXT DEFAULT "USD"')

        # Add base_currency to user_settings if it doesn't exist
        cursor.execute("PRAGMA table_info(user_settings)")
        settings_columns = [col[1] for col in cursor.fetchall()]
        if 'base_currency' not in settings_columns:
            cursor.execute('ALTER TABLE user_settings ADD COLUMN base_currency TEXT DEFAULT "USD"')

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

        # Add email verification and password reset columns to existing users table if they don't exist
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

            if 'reset_token' not in user_columns:
                cursor.execute('ALTER TABLE users ADD COLUMN reset_token TEXT')
                print("Added reset_token column to users table")

            if 'reset_token_expiry' not in user_columns:
                cursor.execute('ALTER TABLE users ADD COLUMN reset_token_expiry TIMESTAMP')
                print("Added reset_token_expiry column to users table")

            db.commit()
        except Exception as e:
            print(f"Error adding verification/reset columns: {e}")

        # Create indexes for better performance
        try:
            # Index on transactions table
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)')

            # Index on income table
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_income_user_date ON income(user_id, date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_income_user_id ON income(user_id)')

            # Index on assets table
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_assets_user_id ON assets(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(asset_type)')

            # Index on users table
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_reset_token ON users(reset_token)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_verification_token ON users(verification_token)')

            # Index on exchange_rates table
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_exchange_rates_user ON exchange_rates(user_id, from_currency, to_currency)')

            # Index on asset_history table
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_asset_history_asset ON asset_history(asset_id, recorded_at)')

            db.commit()
            print("Database indexes created successfully")
        except Exception as e:
            print(f"Error creating indexes: {e}")

        return True
    except Exception as e:
        db.rollback()
        print(f"Migration error: {e}")
        return False
    finally:
        db.close()
