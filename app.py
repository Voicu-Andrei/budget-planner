"""
Budget Planner - Main Flask Application
A personal budget tracking app using discrete mathematics and probability
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file, make_response
import os
from datetime import datetime, timedelta
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import csv
import io

# Import our custom modules
from database import init_db, get_db, migrate_to_multiuser
from math_engine import (
    calculate_category_stats,
    detect_anomaly,
    run_monte_carlo_simulation,
    calculate_health_score,
    get_spending_trends
)
from demo_data import generate_demo_data
from email_utils import send_verification_email, send_welcome_email, generate_verification_token


def convert_currency(amount, from_currency, to_currency, user_id):
    """Convert amount from one currency to another using user's exchange rates"""
    if from_currency == to_currency:
        return amount

    db = get_db()

    # Try to find direct conversion rate
    rate = db.execute('''
        SELECT rate FROM exchange_rates
        WHERE user_id = ? AND from_currency = ? AND to_currency = ?
    ''', (user_id, from_currency, to_currency)).fetchone()

    if rate:
        return amount * rate['rate']

    # Try reverse conversion (1/rate)
    reverse_rate = db.execute('''
        SELECT rate FROM exchange_rates
        WHERE user_id = ? AND from_currency = ? AND to_currency = ?
    ''', (user_id, to_currency, from_currency)).fetchone()

    if reverse_rate:
        return amount / reverse_rate['rate']

    # Default to 1:1 if no rate found
    return amount

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Initialize database on first run
init_db()
migrate_to_multiuser()


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        data = request.json if request.is_json else request.form
        email = data.get('email')
        password = data.get('password')

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']

            if request.is_json:
                return jsonify({'success': True})
            return redirect(url_for('dashboard'))
        else:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
            return render_template('login.html', error='Invalid email or password')

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User signup with email verification"""
    if request.method == 'POST':
        data = request.json if request.is_json else request.form
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')

        db = get_db()

        # Check if user already exists
        existing_user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if existing_user:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Email already registered'}), 400
            return render_template('signup.html', error='Email already registered')

        # Generate verification token
        verification_token = generate_verification_token()
        token_expiry = datetime.now() + timedelta(hours=24)

        # Create new user (not verified yet)
        password_hash = generate_password_hash(password)
        db.execute('''
            INSERT INTO users (email, password_hash, name, email_verified, verification_token, token_expiry)
            VALUES (?, ?, ?, 0, ?, ?)
        ''', (email, password_hash, name, verification_token, token_expiry))
        db.commit()

        # Send verification email
        send_verification_email(email, name, verification_token)

        # Return success message
        if request.is_json:
            return jsonify({'success': True, 'message': 'Verification email sent!'})

        return render_template('verification_sent.html', email=email)

    return render_template('signup.html')


@app.route('/verify-email')
def verify_email():
    """Verify user email address"""
    token = request.args.get('token')

    if not token:
        return render_template('verification_error.html', error='Invalid verification link')

    db = get_db()

    # Find user with this token
    user = db.execute('''
        SELECT * FROM users
        WHERE verification_token = ? AND token_expiry > ?
    ''', (token, datetime.now())).fetchone()

    if not user:
        return render_template('verification_error.html', error='Invalid or expired verification link')

    # Mark email as verified
    db.execute('''
        UPDATE users
        SET email_verified = 1, verification_token = NULL, token_expiry = NULL
        WHERE id = ?
    ''', (user['id'],))
    db.commit()

    # Log the user in
    session['user_id'] = user['id']
    session['user_name'] = user['name']
    session['user_email'] = user['email']

    # Send welcome email
    send_welcome_email(user['email'], user['name'])

    # Redirect to setup
    return redirect(url_for('setup'))


@app.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend verification email"""
    data = request.json
    email = data.get('email')

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ? AND email_verified = 0', (email,)).fetchone()

    if not user:
        return jsonify({'success': False, 'error': 'User not found or already verified'}), 404

    # Generate new token
    verification_token = generate_verification_token()
    token_expiry = datetime.now() + timedelta(hours=24)

    db.execute('''
        UPDATE users
        SET verification_token = ?, token_expiry = ?
        WHERE id = ?
    ''', (verification_token, token_expiry, user['id']))
    db.commit()

    # Send email
    send_verification_email(user['email'], user['name'], verification_token)

    return jsonify({'success': True, 'message': 'Verification email sent!'})


@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
def index():
    """Home page - redirects to setup or dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    user = db.execute('SELECT * FROM user_settings WHERE user_id = ?', (session['user_id'],)).fetchone()

    if user is None:
        return redirect(url_for('setup'))

    return redirect(url_for('dashboard'))


@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Initial setup wizard for new users"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.json
        db = get_db()

        # Full setup
        name = session.get('user_name', 'User')
        monthly_budget = float(data.get('monthly_budget', 0))
        savings_goal = float(data.get('savings_goal', 0))
        user_id = session['user_id']

        # Insert user settings
        db.execute('''
            INSERT INTO user_settings (user_id, name, monthly_budget, savings_goal, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, name, monthly_budget, savings_goal, datetime.now()))

        # Insert fixed expenses
        fixed_expenses = data.get('fixed_expenses', [])
        for expense in fixed_expenses:
            db.execute('''
                INSERT INTO fixed_expenses (user_id, name, amount, frequency, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, expense['name'], float(expense['amount']), expense['frequency'], datetime.now()))

        db.commit()

        # Generate demo data if requested
        if data.get('load_demo', False):
            generate_demo_data(user_id)

        return jsonify({'success': True})

    return render_template('setup.html', user_name=session.get('user_name', 'User'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page"""
    db = get_db()
    user_id = session['user_id']
    user = db.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,)).fetchone()

    if user is None:
        return redirect(url_for('setup'))

    # Get current month's data
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Get transactions for current month
    transactions = db.execute('''
        SELECT * FROM transactions
        WHERE date >= ? AND user_id = ?
        ORDER BY date DESC
    ''', (month_start, user_id)).fetchall()

    # Calculate total spent this month
    total_spent = sum(t['amount'] for t in transactions)

    # Get income for current month
    income_records = db.execute('''
        SELECT * FROM income
        WHERE date >= ? AND user_id = ?
        ORDER BY date DESC
    ''', (month_start, user_id)).fetchall()

    total_income = sum(i['amount'] for i in income_records)

    # Get fixed expenses total
    fixed_expenses = db.execute('SELECT * FROM fixed_expenses WHERE user_id = ?', (user_id,)).fetchall()
    fixed_total = sum(
        e['amount'] if e['frequency'] == 'monthly' else e['amount'] * 4.33
        for e in fixed_expenses
    )

    # Calculate remaining budget
    remaining = user['monthly_budget'] - total_spent - fixed_total

    # Calculate net income (income - all expenses)
    net_income = total_income - total_spent - fixed_total

    # Calculate budget percentage (simplified health score)
    budget_percentage = int((remaining / user['monthly_budget'] * 100) if user['monthly_budget'] > 0 else 0)
    budget_percentage = max(0, budget_percentage)  # Don't show negative

    # Calculate projected savings
    projected_savings = max(0, remaining)

    # Calculate savings percentage for progress bar
    savings_percentage = min(100, int((projected_savings / user['savings_goal'] * 100) if user['savings_goal'] > 0 else 0))

    # Days left in month
    next_month = (month_start + timedelta(days=32)).replace(day=1)
    days_left = (next_month - now).days

    # Generate category data for chart
    category_totals = {}
    for t in transactions:
        category_totals[t['category']] = category_totals.get(t['category'], 0) + t['amount']

    category_data = {
        'labels': list(category_totals.keys()),
        'values': list(category_totals.values())
    }

    # Generate daily trend data
    daily_totals = {}
    for t in transactions:
        try:
            date = datetime.strptime(t['date'], '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            date = datetime.strptime(t['date'], '%Y-%m-%d %H:%M:%S')
        date_key = date.strftime('%m/%d')
        daily_totals[date_key] = daily_totals.get(date_key, 0) + t['amount']

    # Sort by date
    sorted_dates = sorted(daily_totals.keys(), key=lambda x: datetime.strptime(x, '%m/%d').replace(year=now.year))
    trend_data = {
        'labels': sorted_dates,
        'values': [daily_totals[d] for d in sorted_dates]
    }

    return render_template('dashboard.html',
                         user=user,
                         total_spent=total_spent,
                         total_income=total_income,
                         net_income=net_income,
                         remaining=remaining,
                         days_left=days_left,
                         budget_percentage=budget_percentage,
                         projected_savings=projected_savings,
                         savings_percentage=savings_percentage,
                         category_data=category_data,
                         trend_data=trend_data)


@app.route('/api/transactions', methods=['GET', 'POST'])
@login_required
def transactions_api():
    """API endpoint for transaction management"""
    db = get_db()
    user_id = session['user_id']

    if request.method == 'POST':
        data = request.json

        # Parse transaction data
        date = datetime.strptime(data['date'], '%Y-%m-%d')
        amount = float(data['amount'])
        category = data['category']
        description = data.get('description', '')
        currency = data.get('currency', 'USD')

        # Check for anomaly
        is_anomaly, z_score = detect_anomaly(category, amount)

        # Insert transaction with user_id and currency
        db.execute('''
            INSERT INTO transactions (user_id, date, amount, category, description, currency, is_anomaly, z_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, date, amount, category, description, currency, is_anomaly, z_score, datetime.now()))
        db.commit()

        return jsonify({
            'success': True,
            'is_anomaly': is_anomaly,
            'z_score': z_score
        })

    # GET - return transactions for current user
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 20, type=int)
    category = request.args.get('category', None)
    search = request.args.get('search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    amount_min = request.args.get('amount_min', '')
    amount_max = request.args.get('amount_max', '')

    query = 'SELECT * FROM transactions'
    params = []
    conditions = ['user_id = ?']
    params.append(user_id)

    if category and category != 'all':
        conditions.append('category = ?')
        params.append(category)

    if search:
        conditions.append('description LIKE ?')
        params.append(f'%{search}%')

    if date_from:
        conditions.append('date >= ?')
        params.append(date_from)

    if date_to:
        conditions.append('date <= ?')
        params.append(date_to)

    if amount_min:
        conditions.append('amount >= ?')
        params.append(float(amount_min))

    if amount_max:
        conditions.append('amount <= ?')
        params.append(float(amount_max))

    query += ' WHERE ' + ' AND '.join(conditions)
    query += ' ORDER BY date DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])

    transactions = db.execute(query, params).fetchall()

    # Get total count for current user
    count_query = 'SELECT COUNT(*) as count FROM transactions WHERE ' + ' AND '.join(conditions)
    # Use the same params but without limit and offset
    total = db.execute(count_query, params[:-2]).fetchone()['count']

    return jsonify({
        'transactions': [dict(t) for t in transactions],
        'total': total,
        'has_more': offset + limit < total
    })


@app.route('/transactions')
@login_required
def transactions_page():
    """View all transactions page"""
    db = get_db()
    user_id = session['user_id']

    # Get current month total for this user
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    transactions = db.execute('''
        SELECT SUM(amount) as total FROM transactions
        WHERE date >= ? AND user_id = ?
    ''', (month_start, user_id)).fetchone()

    total_this_month = transactions['total'] if transactions['total'] else 0

    return render_template('transactions.html', total_this_month=total_this_month)


@app.route('/analysis')
@login_required
def analysis():
    """Spending analysis page with charts and statistics"""
    db = get_db()
    user_id = session['user_id']

    categories = ['Food & Groceries', 'Dining Out', 'Entertainment', 'Transportation', 'Shopping', 'Other']
    category_stats = {}

    for category in categories:
        stats = calculate_category_stats(category, user_id=user_id)
        category_stats[category] = stats

    # Get current month breakdown for pie chart
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    current_month = db.execute('''
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE date >= ? AND user_id = ?
        GROUP BY category
    ''', (month_start, user_id)).fetchall()

    current_month_data = {row['category']: row['total'] for row in current_month}

    # Get 6-month trend data
    trend_data = get_spending_trends(months=6, user_id=user_id)

    # Get heatmap data (last 90 days)
    ninety_days_ago = now - timedelta(days=90)
    daily_spending = db.execute('''
        SELECT date, SUM(amount) as total
        FROM transactions
        WHERE date >= ? AND user_id = ?
        GROUP BY date
        ORDER BY date
    ''', (ninety_days_ago, user_id)).fetchall()

    heatmap_data = [{'date': row['date'], 'amount': row['total']} for row in daily_spending]

    # Get velocity data (current month daily cumulative)
    velocity_data = db.execute('''
        SELECT date, amount
        FROM transactions
        WHERE date >= ? AND user_id = ?
        ORDER BY date
    ''', (month_start, user_id)).fetchall()

    cumulative_spending = []
    total = 0
    for row in velocity_data:
        total += row['amount']
        cumulative_spending.append({
            'date': row['date'],
            'cumulative': total
        })

    return render_template('analysis.html',
                         category_stats=category_stats,
                         current_month_data=current_month_data,
                         trend_data=trend_data,
                         categories=categories,
                         heatmap_data=heatmap_data,
                         velocity_data=cumulative_spending)


@app.route('/prediction')
def prediction():
    """Monte Carlo prediction page"""
    return render_template('prediction.html')


@app.route('/comparisons')
def comparisons():
    """Comparison views page - month-over-month and year-over-year"""
    db = get_db()

    # Get month-over-month data (last 6 months)
    month_over_month = []
    for i in range(6, 0, -1):
        month_date = datetime.now() - timedelta(days=i*30)
        month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = (month_start + timedelta(days=32)).replace(day=1)

        total = db.execute('''
            SELECT SUM(amount) as total FROM transactions
            WHERE date >= ? AND date < ?
        ''', (month_start, next_month)).fetchone()['total'] or 0

        month_over_month.append({
            'month': month_start.strftime('%B %Y'),
            'total': total
        })

    # Get current month
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = (month_start + timedelta(days=32)).replace(day=1)
    current_month_total = db.execute('''
        SELECT SUM(amount) as total FROM transactions
        WHERE date >= ? AND date < ?
    ''', (month_start, next_month)).fetchone()['total'] or 0

    month_over_month.append({
        'month': month_start.strftime('%B %Y'),
        'total': current_month_total
    })

    # Get category breakdown for last 3 months
    category_comparison = []
    categories = ['Food & Groceries', 'Dining Out', 'Entertainment', 'Transportation', 'Shopping', 'Other']

    for i in range(2, -1, -1):
        month_date = datetime.now() - timedelta(days=i*30)
        month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = (month_start + timedelta(days=32)).replace(day=1)

        category_data = {
            'month': month_start.strftime('%B %Y'),
            'categories': {}
        }

        for category in categories:
            total = db.execute('''
                SELECT SUM(amount) as total FROM transactions
                WHERE date >= ? AND date < ? AND category = ?
            ''', (month_start, next_month, category)).fetchone()['total'] or 0
            category_data['categories'][category] = total

        category_comparison.append(category_data)

    # Year-over-year comparison (same month last year vs this year)
    year_over_year = []
    current_year = now.year

    for month_num in range(1, 13):
        # This year
        this_year_start = datetime(current_year, month_num, 1)
        this_year_end = (this_year_start + timedelta(days=32)).replace(day=1)
        this_year_total = db.execute('''
            SELECT SUM(amount) as total FROM transactions
            WHERE date >= ? AND date < ?
        ''', (this_year_start, this_year_end)).fetchone()['total'] or 0

        # Last year
        last_year_start = datetime(current_year - 1, month_num, 1)
        last_year_end = (last_year_start + timedelta(days=32)).replace(day=1)
        last_year_total = db.execute('''
            SELECT SUM(amount) as total FROM transactions
            WHERE date >= ? AND date < ?
        ''', (last_year_start, last_year_end)).fetchone()['total'] or 0

        year_over_year.append({
            'month': this_year_start.strftime('%B'),
            'this_year': this_year_total,
            'last_year': last_year_total
        })

    return render_template('comparisons.html',
                         month_over_month=month_over_month,
                         category_comparison=category_comparison,
                         year_over_year=year_over_year,
                         current_year=current_year)


@app.route('/api/comparison-data')
@login_required
def comparison_data():
    """Get month-over-month comparison data"""
    db = get_db()
    user_id = session['user_id']
    month_over_month = []

    for i in range(6, -1, -1):
        month_date = datetime.now() - timedelta(days=i*30)
        month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = (month_start + timedelta(days=32)).replace(day=1)

        total = db.execute('''
            SELECT SUM(amount) as total FROM transactions
            WHERE date >= ? AND date < ? AND user_id = ?
        ''', (month_start, next_month, user_id)).fetchone()['total'] or 0

        month_over_month.append({
            'month': month_start.strftime('%b %Y'),
            'total': total
        })

    return jsonify(month_over_month)


@app.route('/api/update-account', methods=['POST'])
def update_account():
    """Update user account information"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    data = request.json
    name = data.get('name')
    email = data.get('email')

    db = get_db()

    # Check if email is already taken by another user
    existing = db.execute('SELECT * FROM users WHERE email = ? AND id != ?',
                         (email, session['user_id'])).fetchone()
    if existing:
        return jsonify({'success': False, 'error': 'Email already in use'})

    # Update user
    db.execute('UPDATE users SET name = ?, email = ? WHERE id = ?',
              (name, email, session['user_id']))
    db.commit()

    # Update session
    session['user_name'] = name
    session['user_email'] = email

    return jsonify({'success': True})


@app.route('/api/change-password', methods=['POST'])
def change_password():
    """Change user password"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    # Verify current password
    if not check_password_hash(user['password_hash'], current_password):
        return jsonify({'success': False, 'error': 'Current password is incorrect'})

    # Update password
    new_hash = generate_password_hash(new_password)
    db.execute('UPDATE users SET password_hash = ? WHERE id = ?',
              (new_hash, session['user_id']))
    db.commit()

    return jsonify({'success': True})


@app.route('/api/run-simulation', methods=['POST'])
def run_simulation():
    """Run Monte Carlo simulation"""
    data = request.json
    adjustments = data.get('adjustments', {})

    results = run_monte_carlo_simulation(simulations=1000, adjustments=adjustments)

    return jsonify(results)


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Settings page"""
    db = get_db()

    if request.method == 'POST':
        data = request.json
        action = data.get('action')

        if action == 'update_user':
            db.execute('''
                UPDATE user_settings
                SET name = ?, monthly_budget = ?, savings_goal = ?
                WHERE user_id = ?
            ''', (data['name'], float(data['monthly_budget']), float(data['savings_goal']), session['user_id']))
            db.commit()
            return jsonify({'success': True})

        elif action == 'add_expense':
            db.execute('''
                INSERT INTO fixed_expenses (user_id, name, amount, frequency, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (session['user_id'], data['name'], float(data['amount']), data['frequency'], datetime.now()))
            db.commit()
            return jsonify({'success': True})

        elif action == 'delete_expense':
            db.execute('DELETE FROM fixed_expenses WHERE id = ?', (data['id'],))
            db.commit()
            return jsonify({'success': True})

        elif action == 'load_demo':
            generate_demo_data(session['user_id'])
            return jsonify({'success': True})

        elif action == 'clear_all':
            db.execute('DELETE FROM transactions WHERE user_id = ?', (session['user_id'],))
            db.commit()
            return jsonify({'success': True})

    # GET request
    user_id = session['user_id']
    user = db.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,)).fetchone()
    fixed_expenses = db.execute('SELECT * FROM fixed_expenses WHERE user_id = ? ORDER BY amount DESC', (user_id,)).fetchall()

    fixed_total = sum(
        e['amount'] if e['frequency'] == 'monthly' else e['amount'] * 4.33
        for e in fixed_expenses
    )

    return render_template('settings.html',
                         user=user,
                         fixed_expenses=fixed_expenses,
                         fixed_total=fixed_total)


@app.route('/api/delete-transaction/<int:transaction_id>', methods=['DELETE'])
@login_required
def delete_transaction(transaction_id):
    """Delete a transaction"""
    db = get_db()
    # Only allow deleting your own transactions
    db.execute('DELETE FROM transactions WHERE id = ? AND user_id = ?', (transaction_id, session['user_id']))
    db.commit()
    return jsonify({'success': True})


@app.route('/api/income', methods=['GET', 'POST'])
@login_required
def income_api():
    """API endpoint for income management"""
    db = get_db()
    user_id = session['user_id']

    if request.method == 'POST':
        data = request.json

        # Parse income data
        date = datetime.strptime(data['date'], '%Y-%m-%d')
        amount = float(data['amount'])
        source = data['source']
        description = data.get('description', '')
        recurring = data.get('recurring', False)
        frequency = data.get('frequency', 'one-time')

        # Insert income record
        db.execute('''
            INSERT INTO income (user_id, date, amount, source, description, recurring, frequency, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, date, amount, source, description, recurring, frequency, datetime.now()))
        db.commit()

        return jsonify({'success': True})

    # GET - return income records for current user
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 50, type=int)
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    query = 'SELECT * FROM income WHERE user_id = ?'
    params = [user_id]

    if date_from:
        query += ' AND date >= ?'
        params.append(date_from)

    if date_to:
        query += ' AND date <= ?'
        params.append(date_to)

    query += ' ORDER BY date DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])

    income_records = db.execute(query, params).fetchall()

    # Get total count
    count_query = 'SELECT COUNT(*) as count FROM income WHERE user_id = ?'
    count_params = [user_id]

    if date_from:
        count_query += ' AND date >= ?'
        count_params.append(date_from)

    if date_to:
        count_query += ' AND date <= ?'
        count_params.append(date_to)

    total = db.execute(count_query, count_params).fetchone()['count']

    return jsonify({
        'income': [dict(i) for i in income_records],
        'total': total,
        'has_more': offset + limit < total
    })


@app.route('/api/delete-income/<int:income_id>', methods=['DELETE'])
@login_required
def delete_income(income_id):
    """Delete an income record"""
    db = get_db()
    # Only allow deleting your own income records
    db.execute('DELETE FROM income WHERE id = ? AND user_id = ?', (income_id, session['user_id']))
    db.commit()
    return jsonify({'success': True})


@app.route('/income')
@login_required
def income_page():
    """Income tracking page"""
    db = get_db()
    user_id = session['user_id']

    # Get current month income total
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    income = db.execute('''
        SELECT SUM(amount) as total FROM income
        WHERE date >= ? AND user_id = ?
    ''', (month_start, user_id)).fetchone()

    total_this_month = income['total'] if income['total'] else 0

    return render_template('income.html', total_this_month=total_this_month)


@app.route('/api/assets', methods=['GET', 'POST'])
@login_required
def assets_api():
    """API endpoint for assets management"""
    db = get_db()
    user_id = session['user_id']

    if request.method == 'POST':
        data = request.json

        # Parse asset data
        asset_type = data['asset_type']
        name = data['name']
        current_value = float(data['current_value'])
        purchase_value = float(data.get('purchase_value', 0)) if data.get('purchase_value') else None
        purchase_date = data.get('purchase_date')
        quantity = float(data.get('quantity', 1))
        currency = data.get('currency', 'USD')
        description = data.get('description', '')

        # Insert asset
        cursor = db.execute('''
            INSERT INTO assets (user_id, asset_type, name, current_value, purchase_value, purchase_date, quantity, currency, description, last_updated, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, asset_type, name, current_value, purchase_value, purchase_date, quantity, currency, description, datetime.now(), datetime.now()))

        asset_id = cursor.lastrowid

        # Record initial value in history
        db.execute('''
            INSERT INTO asset_history (asset_id, value, recorded_at)
            VALUES (?, ?, ?)
        ''', (asset_id, current_value, datetime.now()))

        db.commit()

        return jsonify({'success': True})

    # GET - return all assets for current user
    assets = db.execute('''
        SELECT * FROM assets
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,)).fetchall()

    # Calculate total value and gains
    total_value = sum(a['current_value'] for a in assets)
    total_invested = sum(a['purchase_value'] or 0 for a in assets)
    total_gain = total_value - total_invested if total_invested > 0 else 0
    gain_percentage = (total_gain / total_invested * 100) if total_invested > 0 else 0

    return jsonify({
        'assets': [dict(a) for a in assets],
        'summary': {
            'total_value': total_value,
            'total_invested': total_invested,
            'total_gain': total_gain,
            'gain_percentage': gain_percentage
        }
    })


@app.route('/api/assets/<int:asset_id>', methods=['PUT', 'DELETE'])
@login_required
def asset_operations(asset_id):
    """Update or delete an asset"""
    db = get_db()
    user_id = session['user_id']

    if request.method == 'DELETE':
        # Only allow deleting your own assets
        db.execute('DELETE FROM assets WHERE id = ? AND user_id = ?', (asset_id, user_id))
        db.commit()
        return jsonify({'success': True})

    elif request.method == 'PUT':
        data = request.json
        new_value = float(data['current_value'])

        # Update asset value
        db.execute('''
            UPDATE assets
            SET current_value = ?, last_updated = ?
            WHERE id = ? AND user_id = ?
        ''', (new_value, datetime.now(), asset_id, user_id))

        # Record value change in history
        db.execute('''
            INSERT INTO asset_history (asset_id, value, recorded_at)
            VALUES (?, ?, ?)
        ''', (asset_id, new_value, datetime.now()))

        db.commit()

        return jsonify({'success': True})


@app.route('/assets')
@login_required
def assets_page():
    """Assets & investments tracking page"""
    return render_template('assets.html')


@app.route('/api/exchange-rates', methods=['GET', 'POST'])
@login_required
def exchange_rates_api():
    """API endpoint for exchange rates management"""
    db = get_db()
    user_id = session['user_id']

    if request.method == 'POST':
        data = request.json
        from_currency = data['from_currency']
        to_currency = data['to_currency']
        rate = float(data['rate'])

        # Insert or update exchange rate
        db.execute('''
            INSERT INTO exchange_rates (user_id, from_currency, to_currency, rate, last_updated)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, from_currency, to_currency)
            DO UPDATE SET rate = ?, last_updated = ?
        ''', (user_id, from_currency, to_currency, rate, datetime.now(), rate, datetime.now()))
        db.commit()

        return jsonify({'success': True})

    # GET - return all exchange rates for current user
    rates = db.execute('''
        SELECT * FROM exchange_rates
        WHERE user_id = ?
        ORDER BY from_currency, to_currency
    ''', (user_id,)).fetchall()

    return jsonify({
        'rates': [dict(r) for r in rates]
    })


@app.route('/api/exchange-rates/<int:rate_id>', methods=['DELETE'])
@login_required
def delete_exchange_rate(rate_id):
    """Delete an exchange rate"""
    db = get_db()
    user_id = session['user_id']

    db.execute('DELETE FROM exchange_rates WHERE id = ? AND user_id = ?', (rate_id, user_id))
    db.commit()

    return jsonify({'success': True})


@app.route('/currency-settings')
@login_required
def currency_settings_page():
    """Currency settings page"""
    return render_template('currency_settings.html')


@app.route('/api/export/transactions')
@login_required
def export_transactions():
    """Export transactions to CSV"""
    db = get_db()
    user_id = session['user_id']

    # Get all transactions for this user
    transactions = db.execute('''
        SELECT date, amount, category, description, is_anomaly, z_score
        FROM transactions
        WHERE user_id = ?
        ORDER BY date DESC
    ''', (user_id,)).fetchall()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['Date', 'Amount', 'Category', 'Description', 'Is Anomaly', 'Z-Score'])

    # Write data
    for t in transactions:
        writer.writerow([
            t['date'],
            f"{t['amount']:.2f}",
            t['category'],
            t['description'] or '',
            'Yes' if t['is_anomaly'] else 'No',
            f"{t['z_score']:.2f}" if t['z_score'] else '0.00'
        ])

    # Prepare response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=transactions_{datetime.now().strftime("%Y%m%d")}.csv'
    response.headers['Content-Type'] = 'text/csv'

    return response


@app.route('/api/export/income')
@login_required
def export_income():
    """Export income to CSV"""
    db = get_db()
    user_id = session['user_id']

    # Get all income records for this user
    income_records = db.execute('''
        SELECT date, amount, source, description, recurring, frequency
        FROM income
        WHERE user_id = ?
        ORDER BY date DESC
    ''', (user_id,)).fetchall()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['Date', 'Amount', 'Source', 'Description', 'Recurring', 'Frequency'])

    # Write data
    for i in income_records:
        writer.writerow([
            i['date'],
            f"{i['amount']:.2f}",
            i['source'],
            i['description'] or '',
            'Yes' if i['recurring'] else 'No',
            i['frequency'] or 'one-time'
        ])

    # Prepare response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=income_{datetime.now().strftime("%Y%m%d")}.csv'
    response.headers['Content-Type'] = 'text/csv'

    return response


@app.route('/api/export/financial-summary')
@login_required
def export_financial_summary():
    """Export comprehensive financial summary to CSV"""
    db = get_db()
    user_id = session['user_id']

    # Get monthly summary data
    months = db.execute('''
        SELECT
            strftime('%Y-%m', date) as month,
            SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as expenses
        FROM transactions
        WHERE user_id = ?
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month DESC
    ''', (user_id,)).fetchall()

    income_months = db.execute('''
        SELECT
            strftime('%Y-%m', date) as month,
            SUM(amount) as income
        FROM income
        WHERE user_id = ?
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month DESC
    ''', (user_id,)).fetchall()

    # Combine income and expenses by month
    monthly_data = {}
    for m in months:
        monthly_data[m['month']] = {'expenses': m['expenses'], 'income': 0}

    for i in income_months:
        if i['month'] in monthly_data:
            monthly_data[i['month']]['income'] = i['income']
        else:
            monthly_data[i['month']] = {'expenses': 0, 'income': i['income']}

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['Month', 'Income', 'Expenses', 'Net Income', 'Savings Rate %'])

    # Write data
    for month in sorted(monthly_data.keys(), reverse=True):
        data = monthly_data[month]
        income = data['income']
        expenses = data['expenses']
        net = income - expenses
        savings_rate = (net / income * 100) if income > 0 else 0

        writer.writerow([
            month,
            f"{income:.2f}",
            f"{expenses:.2f}",
            f"{net:.2f}",
            f"{savings_rate:.1f}"
        ])

    # Prepare response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=financial_summary_{datetime.now().strftime("%Y%m%d")}.csv'
    response.headers['Content-Type'] = 'text/csv'

    return response


def generate_insights(transactions, user, fixed_total):
    """Generate insights for dashboard"""
    insights = []

    if not transactions:
        insights.append({
            'type': 'info',
            'icon': '📝',
            'message': 'No transactions yet. Start adding your expenses!'
        })
        return insights

    # Check if on track for savings
    total_spent = sum(t['amount'] for t in transactions)
    projected_total = total_spent + fixed_total
    will_save = user['monthly_budget'] - projected_total

    if will_save >= user['savings_goal']:
        insights.append({
            'type': 'success',
            'icon': '✅',
            'message': f'On track to save ${will_save:.2f} this month (goal: ${user["savings_goal"]:.2f})'
        })
    else:
        insights.append({
            'type': 'warning',
            'icon': '⚠️',
            'message': f'May fall short of savings goal. Projected savings: ${will_save:.2f} (goal: ${user["savings_goal"]:.2f})'
        })

    # Check for anomalies
    recent_anomalies = [t for t in transactions[:5] if t['is_anomaly']]
    if recent_anomalies:
        t = recent_anomalies[0]
        insights.append({
            'type': 'warning',
            'icon': '⚠️',
            'message': f'Unusual purchase detected: ${t["amount"]:.2f} on {t["category"]}'
        })

    # Category spending check
    db = get_db()
    now = datetime.now()
    month_start = now.replace(day=1)

    for category in ['Dining Out', 'Entertainment', 'Shopping']:
        current = db.execute('''
            SELECT SUM(amount) as total FROM transactions
            WHERE category = ? AND date >= ?
        ''', (category, month_start)).fetchone()['total'] or 0

        stats = calculate_category_stats(category)
        if stats and stats['mean'] > 0:
            if current > stats['mean'] * 1.3:
                insights.append({
                    'type': 'info',
                    'icon': '📊',
                    'message': f'{category} spending is {((current/stats["mean"] - 1) * 100):.0f}% above average'
                })

    return insights


if __name__ == '__main__':
    app.run(debug=True, port=5000)
