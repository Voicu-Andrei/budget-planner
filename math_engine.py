"""
Mathematical Engine - All discrete math and probability calculations

This module contains all the core mathematical functions:
- Statistical analysis (mean, standard deviation, variance)
- Probability distributions
- Anomaly detection using z-scores
- Monte Carlo simulations
- Health score calculations
"""

import numpy as np
from scipy import stats
from datetime import datetime, timedelta
from database import get_db


def calculate_category_stats(category, months=6, user_id=None):
    """
    Calculate statistical metrics for a category

    Returns: {
        'mean': average spending,
        'std_dev': standard deviation,
        'variance': variance,
        'min': minimum,
        'max': maximum,
        'count': number of transactions,
        'monthly_data': list of monthly totals
    }
    """
    db = get_db()

    # Get user_id from session if not provided
    if user_id is None:
        from flask import session
        user_id = session.get('user_id', 1)

    # Get data for last N months
    cutoff_date = datetime.now() - timedelta(days=30 * months)

    transactions = db.execute('''
        SELECT amount, date FROM transactions
        WHERE category = ? AND date >= ? AND user_id = ?
        ORDER BY date
    ''', (category, cutoff_date, user_id)).fetchall()

    if not transactions:
        return None

    amounts = [t['amount'] for t in transactions]

    # Group by month
    monthly_totals = {}
    for t in transactions:
        # Handle datetime with or without microseconds
        date_str = t['date']
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        month_key = date.strftime('%Y-%m')
        monthly_totals[month_key] = monthly_totals.get(month_key, 0) + t['amount']

    monthly_values = list(monthly_totals.values())

    # Calculate statistics
    mean = np.mean(monthly_values) if monthly_values else 0
    std_dev = np.std(monthly_values, ddof=1) if len(monthly_values) > 1 else 0
    variance = np.var(monthly_values, ddof=1) if len(monthly_values) > 1 else 0

    return {
        'mean': float(mean),
        'std_dev': float(std_dev),
        'variance': float(variance),
        'min': float(min(monthly_values)) if monthly_values else 0,
        'max': float(max(monthly_values)) if monthly_values else 0,
        'count': len(transactions),
        'monthly_data': monthly_totals,
        'transaction_mean': float(np.mean(amounts)) if amounts else 0,
        'transaction_std': float(np.std(amounts, ddof=1)) if len(amounts) > 1 else 0
    }


def detect_anomaly(category, amount, threshold=2.0, user_id=None):
    """
    Detect if a transaction is an anomaly using z-score

    Z-score formula: z = (x - μ) / σ
    where:
        x = transaction amount
        μ = mean of category
        σ = standard deviation of category

    Returns: (is_anomaly, z_score)
    """
    stats = calculate_category_stats(category, user_id=user_id)

    if not stats or stats['transaction_std'] == 0:
        return False, 0.0

    # Calculate z-score
    z_score = (amount - stats['transaction_mean']) / stats['transaction_std']

    # If |z_score| > threshold, it's an anomaly
    is_anomaly = abs(z_score) > threshold

    return is_anomaly, float(z_score)


def run_monte_carlo_simulation(simulations=1000, adjustments=None, user_id=None):
    """
    Run Monte Carlo simulation to predict next month's spending

    Process:
    1. For each simulation:
        - For each category, sample spending from normal distribution
        - Add fixed expenses
        - Calculate ending balance
    2. Analyze distribution of outcomes
    3. Calculate probabilities

    Returns: {
        'balances': list of ending balances,
        'probabilities': dict of various probabilities,
        'percentiles': dict of percentile values
    }
    """
    db = get_db()

    # Get user_id from session if not provided
    if user_id is None:
        from flask import session
        user_id = session.get('user_id', 1)

    # Get user settings
    user = db.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,)).fetchone()
    if not user:
        return {'error': 'User not set up'}

    monthly_budget = user['monthly_budget']
    savings_goal = user['savings_goal']

    # Get fixed expenses
    fixed_expenses = db.execute('SELECT * FROM fixed_expenses WHERE user_id = ?', (user_id,)).fetchall()
    fixed_total = sum(
        e['amount'] if e['frequency'] == 'monthly' else e['amount'] * 4.33
        for e in fixed_expenses
    )

    # Get statistics for each category
    categories = ['Food & Groceries', 'Dining Out', 'Entertainment', 'Transportation', 'Shopping', 'Other']
    category_distributions = {}

    for category in categories:
        stats = calculate_category_stats(category, user_id=user_id)
        if stats and stats['mean'] > 0:
            # Apply adjustments if provided
            mean = stats['mean']
            if adjustments and category in adjustments:
                mean += adjustments[category]

            category_distributions[category] = {
                'mean': mean,
                'std_dev': stats['std_dev']
            }

    # Run simulations
    ending_balances = []

    for _ in range(simulations):
        total_spending = 0

        # Sample from each category's distribution
        for category, dist in category_distributions.items():
            # Sample from normal distribution: N(μ, σ²)
            sampled_amount = np.random.normal(dist['mean'], dist['std_dev'])
            # Ensure non-negative
            sampled_amount = max(0, sampled_amount)
            total_spending += sampled_amount

        # Calculate ending balance
        ending_balance = monthly_budget - fixed_total - total_spending
        ending_balances.append(ending_balance)

    # Convert to numpy array for analysis
    balances = np.array(ending_balances)

    # Calculate probabilities and statistics
    prob_positive = np.mean(balances > 0) * 100
    prob_meet_savings = np.mean(balances >= savings_goal) * 100
    prob_over_budget = np.mean(balances < 0) * 100

    # Calculate percentiles
    percentiles = {
        'p10': float(np.percentile(balances, 10)),
        'p25': float(np.percentile(balances, 25)),
        'p50': float(np.percentile(balances, 50)),  # median
        'p75': float(np.percentile(balances, 75)),
        'p90': float(np.percentile(balances, 90))
    }

    # Create histogram data
    hist, bin_edges = np.histogram(balances, bins=30)
    histogram = {
        'counts': hist.tolist(),
        'bins': bin_edges.tolist()
    }

    return {
        'balances': balances.tolist(),
        'mean': float(np.mean(balances)),
        'std_dev': float(np.std(balances)),
        'probabilities': {
            'positive_balance': float(prob_positive),
            'meet_savings_goal': float(prob_meet_savings),
            'over_budget': float(prob_over_budget)
        },
        'percentiles': percentiles,
        'histogram': histogram,
        'savings_goal': savings_goal,
        'fixed_expenses': fixed_total
    }


def calculate_health_score(total_spent, monthly_budget, fixed_total, savings_goal, anomaly_count):
    """
    Calculate budget health score (0-100)

    Components:
    - 40 points: Staying under budget
    - 30 points: Meeting savings goal
    - 20 points: Low variance (consistent spending)
    - 10 points: No anomalies
    """
    score = 0

    total_expenses = total_spent + fixed_total

    # 40 points for staying under budget
    if total_expenses <= monthly_budget:
        ratio = total_expenses / monthly_budget if monthly_budget > 0 else 1
        score += 40 * (1 - ratio * 0.5)  # Better score for spending less

    # 30 points for meeting savings goal
    remaining = monthly_budget - total_expenses
    if remaining >= savings_goal:
        score += 30
    elif remaining > 0:
        score += 30 * (remaining / savings_goal)

    # 20 points for consistency (awarded by default, deducted for high variance)
    # This would need historical data to calculate properly
    score += 15  # Simplified version

    # 10 points for no anomalies
    if anomaly_count == 0:
        score += 10
    elif anomaly_count <= 2:
        score += 5

    return min(100, max(0, int(score)))


def get_spending_trends(months=6, user_id=None):
    """
    Get spending trends over last N months

    Returns data formatted for Chart.js
    """
    db = get_db()

    # Get user_id from session if not provided
    if user_id is None:
        from flask import session
        user_id = session.get('user_id', 1)

    cutoff_date = datetime.now() - timedelta(days=30 * months)

    transactions = db.execute('''
        SELECT date, category, amount FROM transactions
        WHERE date >= ? AND user_id = ?
        ORDER BY date
    ''', (cutoff_date, user_id)).fetchall()

    # Group by month and category
    monthly_data = {}

    for t in transactions:
        # Handle datetime with or without microseconds
        date_str = t['date']
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        month_key = date.strftime('%Y-%m')

        if month_key not in monthly_data:
            monthly_data[month_key] = {}

        category = t['category']
        monthly_data[month_key][category] = monthly_data[month_key].get(category, 0) + t['amount']

    # Sort months
    sorted_months = sorted(monthly_data.keys())

    # Get all categories
    categories = ['Food & Groceries', 'Dining Out', 'Entertainment', 'Transportation', 'Shopping', 'Other']

    # Format for Chart.js
    datasets = {}
    for category in categories:
        datasets[category] = [monthly_data.get(month, {}).get(category, 0) for month in sorted_months]

    return {
        'labels': sorted_months,
        'datasets': datasets
    }


def calculate_confidence_interval(data, confidence=0.90):
    """
    Calculate confidence interval for a dataset

    Returns: (lower_bound, upper_bound)
    """
    if len(data) < 2:
        return (0, 0)

    mean = np.mean(data)
    std_err = stats.sem(data)
    interval = std_err * stats.t.ppf((1 + confidence) / 2, len(data) - 1)

    return (mean - interval, mean + interval)
