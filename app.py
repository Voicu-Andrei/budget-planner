"""
Budget Planner - Main Flask Application
A personal budget tracking app using discrete mathematics and probability
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
from datetime import datetime, timedelta
import secrets

# Import our custom modules
from database import init_db, get_db
from math_engine import (
    calculate_category_stats,
    detect_anomaly,
    run_monte_carlo_simulation,
    calculate_health_score,
    get_spending_trends
)
from demo_data import generate_demo_data

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Initialize database on first run
init_db()


@app.route('/')
def index():
    """Home page - redirects to setup or dashboard"""
    db = get_db()
    user = db.execute('SELECT * FROM user_settings WHERE id = 1').fetchone()

    if user is None:
        return redirect(url_for('setup'))

    return redirect(url_for('dashboard'))


@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Initial setup wizard for new users"""
    if request.method == 'POST':
        data = request.json
        db = get_db()

        # Check if this is the name step or full setup
        if 'name' in data and len(data) == 1:
            # Just saving the name, continue to next step
            session['user_name'] = data['name']
            return jsonify({'success': True})

        # Full setup
        name = session.get('user_name', data.get('name', 'User'))
        monthly_budget = float(data.get('monthly_budget', 0))
        savings_goal = float(data.get('savings_goal', 0))
        savings_purpose = data.get('savings_purpose', '')

        # Insert user settings
        db.execute('''
            INSERT INTO user_settings (name, monthly_budget, savings_goal, savings_purpose, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, monthly_budget, savings_goal, savings_purpose, datetime.now()))

        # Insert fixed expenses
        fixed_expenses = data.get('fixed_expenses', [])
        for expense in fixed_expenses:
            db.execute('''
                INSERT INTO fixed_expenses (name, amount, frequency, created_at)
                VALUES (?, ?, ?, ?)
            ''', (expense['name'], float(expense['amount']), expense['frequency'], datetime.now()))

        db.commit()

        # Generate demo data if requested
        if data.get('load_demo', False):
            generate_demo_data()

        return jsonify({'success': True})

    return render_template('setup.html')


@app.route('/dashboard')
def dashboard():
    """Main dashboard page"""
    db = get_db()
    user = db.execute('SELECT * FROM user_settings WHERE id = 1').fetchone()

    if user is None:
        return redirect(url_for('setup'))

    # Get current month's data
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Get transactions for current month
    transactions = db.execute('''
        SELECT * FROM transactions
        WHERE date >= ?
        ORDER BY date DESC
    ''', (month_start,)).fetchall()

    # Calculate total spent this month
    total_spent = sum(t['amount'] for t in transactions)

    # Get fixed expenses total
    fixed_expenses = db.execute('SELECT * FROM fixed_expenses').fetchall()
    fixed_total = sum(
        e['amount'] if e['frequency'] == 'monthly' else e['amount'] * 4.33
        for e in fixed_expenses
    )

    # Calculate remaining budget
    remaining = user['monthly_budget'] - total_spent - fixed_total

    # Days left in month
    next_month = (month_start + timedelta(days=32)).replace(day=1)
    days_left = (next_month - now).days

    # Get anomalies
    anomalies = [t for t in transactions if t['is_anomaly']]

    # Calculate health score
    health_score = calculate_health_score(
        total_spent,
        user['monthly_budget'],
        fixed_total,
        user['savings_goal'],
        len(anomalies)
    )

    # Get insights
    insights = generate_insights(transactions, user, fixed_total)

    return render_template('dashboard.html',
                         user=user,
                         total_spent=total_spent,
                         remaining=remaining,
                         days_left=days_left,
                         health_score=health_score,
                         anomalies=anomalies,
                         insights=insights)


@app.route('/api/transactions', methods=['GET', 'POST'])
def transactions_api():
    """API endpoint for transaction management"""
    db = get_db()

    if request.method == 'POST':
        data = request.json

        # Parse transaction data
        date = datetime.strptime(data['date'], '%Y-%m-%d')
        amount = float(data['amount'])
        category = data['category']
        description = data.get('description', '')

        # Check for anomaly
        is_anomaly, z_score = detect_anomaly(category, amount)

        # Insert transaction
        db.execute('''
            INSERT INTO transactions (date, amount, category, description, is_anomaly, z_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (date, amount, category, description, is_anomaly, z_score, datetime.now()))
        db.commit()

        return jsonify({
            'success': True,
            'is_anomaly': is_anomaly,
            'z_score': z_score
        })

    # GET - return transactions
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 20, type=int)
    category = request.args.get('category', None)

    query = 'SELECT * FROM transactions'
    params = []

    if category and category != 'all':
        query += ' WHERE category = ?'
        params.append(category)

    query += ' ORDER BY date DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])

    transactions = db.execute(query, params).fetchall()

    # Get total count
    count_query = 'SELECT COUNT(*) as count FROM transactions'
    if category and category != 'all':
        count_query += ' WHERE category = ?'
        total = db.execute(count_query, [category] if category and category != 'all' else []).fetchone()['count']
    else:
        total = db.execute(count_query).fetchone()['count']

    return jsonify({
        'transactions': [dict(t) for t in transactions],
        'total': total,
        'has_more': offset + limit < total
    })


@app.route('/transactions')
def transactions_page():
    """View all transactions page"""
    db = get_db()

    # Get current month total
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    transactions = db.execute('''
        SELECT SUM(amount) as total FROM transactions
        WHERE date >= ?
    ''', (month_start,)).fetchone()

    total_this_month = transactions['total'] if transactions['total'] else 0

    return render_template('transactions.html', total_this_month=total_this_month)


@app.route('/analysis')
def analysis():
    """Spending analysis page with charts and statistics"""
    db = get_db()

    categories = ['Food & Groceries', 'Dining Out', 'Entertainment', 'Transportation', 'Shopping', 'Other']
    category_stats = {}

    for category in categories:
        stats = calculate_category_stats(category)
        category_stats[category] = stats

    # Get current month breakdown for pie chart
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    current_month = db.execute('''
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE date >= ?
        GROUP BY category
    ''', (month_start,)).fetchall()

    current_month_data = {row['category']: row['total'] for row in current_month}

    # Get 6-month trend data
    trend_data = get_spending_trends(months=6)

    return render_template('analysis.html',
                         category_stats=category_stats,
                         current_month_data=current_month_data,
                         trend_data=trend_data,
                         categories=categories)


@app.route('/prediction')
def prediction():
    """Monte Carlo prediction page"""
    return render_template('prediction.html')


@app.route('/api/run-simulation', methods=['POST'])
def run_simulation():
    """Run Monte Carlo simulation"""
    data = request.json
    adjustments = data.get('adjustments', {})

    results = run_monte_carlo_simulation(simulations=1000, adjustments=adjustments)

    return jsonify(results)


@app.route('/settings', methods=['GET', 'POST'])
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
                WHERE id = 1
            ''', (data['name'], float(data['monthly_budget']), float(data['savings_goal'])))
            db.commit()
            return jsonify({'success': True})

        elif action == 'add_expense':
            db.execute('''
                INSERT INTO fixed_expenses (name, amount, frequency, created_at)
                VALUES (?, ?, ?, ?)
            ''', (data['name'], float(data['amount']), data['frequency'], datetime.now()))
            db.commit()
            return jsonify({'success': True})

        elif action == 'delete_expense':
            db.execute('DELETE FROM fixed_expenses WHERE id = ?', (data['id'],))
            db.commit()
            return jsonify({'success': True})

        elif action == 'load_demo':
            generate_demo_data()
            return jsonify({'success': True})

        elif action == 'clear_all':
            db.execute('DELETE FROM transactions')
            db.commit()
            return jsonify({'success': True})

    # GET request
    user = db.execute('SELECT * FROM user_settings WHERE id = 1').fetchone()
    fixed_expenses = db.execute('SELECT * FROM fixed_expenses ORDER BY amount DESC').fetchall()

    fixed_total = sum(
        e['amount'] if e['frequency'] == 'monthly' else e['amount'] * 4.33
        for e in fixed_expenses
    )

    return render_template('settings.html',
                         user=user,
                         fixed_expenses=fixed_expenses,
                         fixed_total=fixed_total)


@app.route('/api/delete-transaction/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """Delete a transaction"""
    db = get_db()
    db.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
    db.commit()
    return jsonify({'success': True})


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
