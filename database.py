"""
Database module - SQLite database setup and management
"""

import sqlite3
from flask import g
import os

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
