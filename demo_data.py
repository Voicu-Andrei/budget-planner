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
    """Generate 6 months of demo transaction data and all related data"""
    db = get_db()

    if user_id is None:
        # Get from session or default to 1
        from flask import session
        user_id = session.get('user_id', 1)

    # Clear existing demo data for this user (if any)
    db.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM income WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM assets WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM recurring_transactions WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM tags WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM exchange_rates WHERE user_id = ?', (user_id,))
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

    # Generate income data
    generate_income_data(db, user_id, start_date)

    # Generate assets
    generate_assets_data(db, user_id)

    # Generate tags and assign to transactions
    generate_tags_data(db, user_id)

    # Generate recurring transactions
    generate_recurring_data(db, user_id)

    # Generate exchange rates
    generate_exchange_rates(db, user_id)

    db.commit()

    transaction_count = db.execute('SELECT COUNT(*) as count FROM transactions WHERE user_id = ?', (user_id,)).fetchone()['count']
    income_count = db.execute('SELECT COUNT(*) as count FROM income WHERE user_id = ?', (user_id,)).fetchone()['count']
    asset_count = db.execute('SELECT COUNT(*) as count FROM assets WHERE user_id = ?', (user_id,)).fetchone()['count']
    tag_count = db.execute('SELECT COUNT(*) as count FROM tags WHERE user_id = ?', (user_id,)).fetchone()['count']

    print(f"Generated demo data: {transaction_count} transactions, {income_count} income records, {asset_count} assets, {tag_count} tags")


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


def generate_income_data(db, user_id, start_date):
    """Generate 6 months of realistic income data"""
    income_sources = [
        ('Salary', 3500, 'monthly', True, 'Monthly salary'),
        ('Freelance', 800, 'monthly', True, 'Freelance work'),
    ]

    # Generate regular monthly income
    for month_offset in range(6):
        month_start = start_date + timedelta(days=30 * month_offset)

        for source, base_amount, frequency, recurring, description in income_sources:
            # Add some variation to income
            amount = base_amount + np.random.uniform(-50, 150)

            # Random day in month
            day = np.random.randint(1, 28)
            income_date = month_start + timedelta(days=day)

            db.execute('''
                INSERT INTO income (user_id, date, amount, source, description, recurring, frequency, currency, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, income_date, round(amount, 2), source, description, recurring, frequency, 'USD', datetime.now()))

    # Add some one-time income events
    bonus_date = start_date + timedelta(days=120)
    db.execute('''
        INSERT INTO income (user_id, date, amount, source, description, recurring, frequency, currency, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, bonus_date, 1500, 'Bonus', 'Performance bonus', False, 'one-time', 'USD', datetime.now()))

    gift_date = start_date + timedelta(days=60)
    db.execute('''
        INSERT INTO income (user_id, date, amount, source, description, recurring, frequency, currency, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, gift_date, 200, 'Gift', 'Birthday gift', False, 'one-time', 'USD', datetime.now()))


def generate_assets_data(db, user_id):
    """Generate realistic asset portfolio"""
    assets = [
        # (type, name, quantity, current_value, purchase_value, currency, description)
        ('stock', 'AAPL Stock', 10, 1850.00, 1500.00, 'USD', '10 shares of Apple Inc.'),
        ('stock', 'MSFT Stock', 5, 1925.00, 1750.00, 'USD', '5 shares of Microsoft'),
        ('savings', 'High-Yield Savings', 1, 5000.00, 5000.00, 'USD', 'Emergency fund savings account'),
        ('crypto', 'Bitcoin', 0.05, 2200.00, 1800.00, 'USD', '0.05 BTC'),
        ('crypto', 'Ethereum', 1, 2400.00, 2000.00, 'USD', '1 ETH'),
        ('property', 'Real Estate Investment', 1, 50000.00, 45000.00, 'USD', 'REIT investment'),
        ('bond', 'US Treasury Bonds', 10, 10200.00, 10000.00, 'USD', '10-year treasury bonds'),
        ('other', 'Gold', 2, 4000.00, 3800.00, 'USD', '2 oz of gold')
    ]

    # Purchase dates spread over last 2 years
    base_date = datetime.now() - timedelta(days=730)

    for i, (asset_type, name, quantity, current_value, purchase_value, currency, description) in enumerate(assets):
        purchase_date = base_date + timedelta(days=i * 90)

        db.execute('''
            INSERT INTO assets (user_id, asset_type, name, quantity, current_value, purchase_value, purchase_date, currency, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, asset_type, name, quantity, current_value, purchase_value, purchase_date, currency, description, datetime.now()))


def generate_tags_data(db, user_id):
    """Generate tags and assign them to transactions"""
    tags = [
        ('Work Related', '#3b82f6'),
        ('Necessary', '#10b981'),
        ('Luxury', '#f59e0b'),
        ('Tax Deductible', '#8b5cf6'),
        ('Subscription', '#ef4444'),
        ('Health', '#ec4899')
    ]

    tag_ids = []
    for name, color in tags:
        cursor = db.execute('''
            INSERT INTO tags (user_id, name, color, created_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, name, color, datetime.now()))
        tag_ids.append(cursor.lastrowid)

    # Assign tags to random transactions
    transactions = db.execute('SELECT id FROM transactions WHERE user_id = ? LIMIT 100', (user_id,)).fetchall()

    for transaction in transactions:
        # Randomly assign 0-2 tags to each transaction
        num_tags = np.random.choice([0, 1, 1, 2], p=[0.3, 0.4, 0.2, 0.1])

        if num_tags > 0:
            selected_tags = np.random.choice(tag_ids, size=num_tags, replace=False)
            for tag_id in selected_tags:
                try:
                    db.execute('''
                        INSERT INTO transaction_tags (transaction_id, tag_id)
                        VALUES (?, ?)
                    ''', (transaction['id'], int(tag_id)))
                except:
                    pass  # Skip if duplicate


def generate_recurring_data(db, user_id):
    """Generate recurring transaction templates"""
    recurring = [
        # (amount, category, description, currency, frequency)
        (15.99, 'Entertainment', 'Netflix Subscription', 'USD', 'monthly'),
        (9.99, 'Entertainment', 'Spotify Premium', 'USD', 'monthly'),
        (50.00, 'Transportation', 'Monthly Transit Pass', 'USD', 'monthly'),
        (30.00, 'Other', 'Gym Membership', 'USD', 'monthly'),
        (12.00, 'Other', 'Cloud Storage', 'USD', 'monthly'),
        (100.00, 'Food & Groceries', 'Weekly Groceries', 'USD', 'weekly'),
        (25.00, 'Dining Out', 'Weekly Coffee', 'USD', 'weekly')
    ]

    start_date = datetime.now() - timedelta(days=90)
    now = datetime.now()

    for amount, category, description, currency, frequency in recurring:
        # Calculate next due date based on frequency
        if frequency == 'weekly':
            next_due = now + timedelta(days=7)
        elif frequency == 'bi-weekly':
            next_due = now + timedelta(days=14)
        elif frequency == 'monthly':
            next_due = now + timedelta(days=30)
        else:
            next_due = now

        db.execute('''
            INSERT INTO recurring_transactions (user_id, amount, category, description, currency, frequency, start_date, last_generated, next_due_date, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, amount, category, description, currency, frequency, start_date, start_date, next_due, True, datetime.now()))


def generate_exchange_rates(db, user_id):
    """Generate common exchange rates"""
    rates = [
        # (from_currency, to_currency, rate)
        ('USD', 'EUR', 0.92),
        ('USD', 'GBP', 0.79),
        ('USD', 'JPY', 149.50),
        ('USD', 'CAD', 1.36),
        ('USD', 'AUD', 1.53),
        ('EUR', 'USD', 1.09),
        ('GBP', 'USD', 1.27),
        ('JPY', 'USD', 0.0067),
        ('CAD', 'USD', 0.74),
        ('AUD', 'USD', 0.65)
    ]

    for from_curr, to_curr, rate in rates:
        db.execute('''
            INSERT INTO exchange_rates (user_id, from_currency, to_currency, rate, last_updated)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, from_curr, to_curr, rate, datetime.now()))


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
