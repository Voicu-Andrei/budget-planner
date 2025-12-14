"""
Demo Data Generator - Creates realistic fake data for testing

Generates 6 months of transaction data with:
- Realistic spending patterns per category
- Different distributions (normal, with variance)
- Some intentional anomalies
- Fixed expenses
"""

import numpy as np
from datetime import datetime, timedelta
from database import get_db


def generate_demo_data(user_id=None):
    """Generate 6 months of demo transaction data"""
    db = get_db()

    if user_id is None:
        # Get from session or default to 1
        from flask import session
        user_id = session.get('user_id', 1)

    # Clear existing demo data for this user (if any)
    db.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
    db.commit()

    # Categories with their monthly spending parameters (mean, std_dev)
    category_params = {
        'Food & Groceries': {
            'monthly_mean': 200,
            'monthly_std': 40,
            'transactions_per_month': 8,  # Weekly shopping + extras
            'amount_range': (15, 85)
        },
        'Dining Out': {
            'monthly_mean': 150,
            'monthly_std': 70,
            'transactions_per_month': 12,
            'amount_range': (8, 50)
        },
        'Entertainment': {
            'monthly_mean': 80,
            'monthly_std': 50,
            'transactions_per_month': 4,
            'amount_range': (10, 100)
        },
        'Transportation': {
            'monthly_mean': 120,
            'monthly_std': 30,
            'transactions_per_month': 15,  # Daily commute
            'amount_range': (5, 25)
        },
        'Shopping': {
            'monthly_mean': 100,
            'monthly_std': 80,
            'transactions_per_month': 3,
            'amount_range': (15, 200)
        },
        'Other': {
            'monthly_mean': 50,
            'monthly_std': 40,
            'transactions_per_month': 2,
            'amount_range': (10, 100)
        }
    }

    # Anomalies to inject (month_index, category, amount, description)
    anomalies = [
        (2, 'Transportation', 300, 'Car repair'),
        (4, 'Shopping', 250, 'New shoes'),
        (5, 'Dining Out', 180, 'Birthday dinner')
    ]

    # Generate 6 months of data
    start_date = datetime.now() - timedelta(days=180)

    for month_offset in range(6):
        month_start = start_date + timedelta(days=30 * month_offset)

        for category, params in category_params.items():
            # Determine monthly total (sample from normal distribution)
            monthly_total = np.random.normal(params['monthly_mean'], params['monthly_std'])
            monthly_total = max(0, monthly_total)  # Ensure positive

            # Distribute across individual transactions
            num_transactions = params['transactions_per_month']

            # Generate individual transaction amounts that sum to approximately monthly_total
            transaction_amounts = generate_transaction_amounts(
                monthly_total,
                num_transactions,
                params['amount_range']
            )

            # Create transactions spread throughout the month
            for i, amount in enumerate(transaction_amounts):
                # Spread transactions throughout the month
                day_offset = (30 / num_transactions) * i + np.random.uniform(-2, 2)
                day_offset = max(0, min(29, day_offset))

                transaction_date = month_start + timedelta(days=int(day_offset))

                # Generate description
                description = generate_description(category, amount)

                # Insert transaction
                db.execute('''
                    INSERT INTO transactions (user_id, date, amount, category, description, is_anomaly, z_score, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, transaction_date, round(amount, 2), category, description, False, 0.0, datetime.now()))

        # Add anomalies for specific months
        for anomaly_month, anomaly_category, anomaly_amount, anomaly_desc in anomalies:
            if anomaly_month == month_offset:
                anomaly_date = month_start + timedelta(days=np.random.randint(5, 25))
                db.execute('''
                    INSERT INTO transactions (user_id, date, amount, category, description, is_anomaly, z_score, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, anomaly_date, anomaly_amount, anomaly_category, anomaly_desc, True, 3.5, datetime.now()))

    db.commit()
    print(f"Generated demo data: {db.execute('SELECT COUNT(*) as count FROM transactions').fetchone()['count']} transactions")


def generate_transaction_amounts(total, count, amount_range):
    """
    Generate individual transaction amounts that sum to approximately total

    Uses Dirichlet distribution to create realistic proportions
    """
    min_amount, max_amount = amount_range

    # Generate proportions using Dirichlet distribution
    # This creates realistic variation while summing to 1
    alpha = np.ones(count)
    proportions = np.random.dirichlet(alpha)

    # Scale to total and constrain to range
    amounts = proportions * total

    # Adjust to fit within min/max constraints
    amounts = np.clip(amounts, min_amount, max_amount)

    # Rescale to match total (approximately)
    amounts = amounts * (total / np.sum(amounts))

    return amounts


def generate_description(category, amount):
    """Generate realistic transaction descriptions"""
    descriptions = {
        'Food & Groceries': [
            'Grocery shopping',
            'Supermarket',
            'Weekly groceries',
            'Fresh produce',
            'Farmers market',
            'Corner store'
        ],
        'Dining Out': [
            'Restaurant',
            'Lunch',
            'Coffee shop',
            'Fast food',
            'Dinner out',
            'Cafe',
            'Takeout'
        ],
        'Entertainment': [
            'Movie tickets',
            'Concert',
            'Streaming service',
            'Game purchase',
            'Books',
            'Museum entry',
            'Sports event'
        ],
        'Transportation': [
            'Gas',
            'Uber',
            'Taxi',
            'Bus fare',
            'Parking',
            'Train ticket',
            'Lyft'
        ],
        'Shopping': [
            'Clothing',
            'Electronics',
            'Home goods',
            'Online shopping',
            'Department store',
            'Shoes',
            'Accessories'
        ],
        'Other': [
            'Miscellaneous',
            'Gift',
            'Donation',
            'Personal care',
            'Pharmacy',
            'Pet supplies'
        ]
    }

    options = descriptions.get(category, ['Purchase'])
    return np.random.choice(options)


def initialize_demo_user():
    """Initialize demo user settings and fixed expenses"""
    db = get_db()

    # Check if user already exists
    existing = db.execute('SELECT * FROM user_settings WHERE id = 1').fetchone()
    if existing:
        return

    # Create demo user
    db.execute('''
        INSERT INTO user_settings (name, monthly_budget, savings_goal, savings_purpose, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', ('Demo User', 2000, 300, 'Emergency fund', datetime.now()))

    # Add fixed expenses
    fixed_expenses = [
        ('Rent', 800, 'monthly'),
        ('Netflix', 15, 'monthly'),
        ('Spotify', 10, 'monthly'),
        ('Gym Membership', 30, 'monthly')
    ]

    for name, amount, frequency in fixed_expenses:
        db.execute('''
            INSERT INTO fixed_expenses (name, amount, frequency, created_at)
            VALUES (?, ?, ?, ?)
        ''', (name, amount, frequency, datetime.now()))

    db.commit()
