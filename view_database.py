"""
Database Viewer - Simple script to explore the SQLite database
"""

import sqlite3

def view_database():
    conn = sqlite3.connect('budget_planner.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("BUDGET PLANNER DATABASE VIEWER")
    print("="*60)

    # User Settings
    print("\n1. USER SETTINGS:")
    print("-" * 60)
    cursor.execute('SELECT * FROM user_settings')
    user = cursor.fetchone()
    if user:
        print(f"Name: {user['name']}")
        print(f"Monthly Budget: ${user['monthly_budget']:.2f}")
        print(f"Savings Goal: ${user['savings_goal']:.2f}")
        print(f"Savings Purpose: {user['savings_purpose']}")
    else:
        print("No user data")

    # Fixed Expenses
    print("\n2. FIXED EXPENSES:")
    print("-" * 60)
    cursor.execute('SELECT * FROM fixed_expenses')
    expenses = cursor.fetchall()
    total_fixed = 0
    for exp in expenses:
        amount = exp['amount'] if exp['frequency'] == 'monthly' else exp['amount'] * 4.33
        total_fixed += amount
        print(f"  {exp['name']}: ${exp['amount']:.2f}/{exp['frequency']}")
    print(f"\nTotal Fixed Expenses: ${total_fixed:.2f}/month")

    # Transaction Statistics
    print("\n3. TRANSACTION STATISTICS:")
    print("-" * 60)
    cursor.execute('SELECT COUNT(*) as count FROM transactions')
    total = cursor.fetchone()['count']
    print(f"Total Transactions: {total}")

    cursor.execute('SELECT category, COUNT(*) as count, SUM(amount) as total FROM transactions GROUP BY category')
    categories = cursor.fetchall()
    print("\nBy Category:")
    for cat in categories:
        print(f"  {cat['category']}: {cat['count']} transactions, ${cat['total']:.2f} total")

    # Anomalies
    print("\n4. ANOMALIES:")
    print("-" * 60)
    cursor.execute('SELECT COUNT(*) as count FROM transactions WHERE is_anomaly = 1')
    anomaly_count = cursor.fetchone()['count']
    print(f"Total Anomalies Detected: {anomaly_count}")

    if anomaly_count > 0:
        cursor.execute('SELECT date, category, amount, description, z_score FROM transactions WHERE is_anomaly = 1 ORDER BY z_score DESC LIMIT 5')
        anomalies = cursor.fetchall()
        print("\nTop 5 Anomalies (by z-score):")
        for a in anomalies:
            print(f"  ${a['amount']:.2f} on {a['category']} (z-score: {a['z_score']:.2f})")
            if a['description']:
                print(f"    Description: {a['description']}")

    # Recent Transactions
    print("\n5. RECENT TRANSACTIONS (Last 10):")
    print("-" * 60)
    cursor.execute('SELECT * FROM transactions ORDER BY date DESC LIMIT 10')
    recent = cursor.fetchall()
    for t in recent:
        anomaly = " [ANOMALY]" if t['is_anomaly'] else ""
        print(f"  {str(t['date'])[:10]} | {t['category']:20} | ${t['amount']:8.2f}{anomaly}")

    print("\n" + "="*60)
    print("End of Database View")
    print("="*60 + "\n")

    conn.close()

if __name__ == '__main__':
    view_database()
