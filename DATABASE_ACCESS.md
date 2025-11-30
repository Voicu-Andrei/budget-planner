# How to Access the SQLite Database

You have **3 ways** to view and explore the database:

---

## Method 1: Python Script (Easiest)

I created a simple viewer script for you!

### Run:
```bash
cd C:\Projects\Claude\discrete-math-project
python view_database.py
```

### This shows:
- User settings (name, budget, savings goal)
- Fixed expenses
- Transaction statistics by category
- Anomalies detected
- Recent transactions

---

## Method 2: VS Code SQLite Extension (Visual, Best for Exploring)

### Step 1: Install Extension
1. Open VS Code
2. Click Extensions icon (or press `Ctrl+Shift+X`)
3. Search for: **SQLite Viewer** (by alexcvzz)
4. Click Install

### Step 2: View Database
1. Open your project folder in VS Code
2. Find `budget_planner.db` in the file explorer
3. **Right-click** → **Open Database**
4. You'll see all tables on the left
5. Click any table to view its data in a nice table format

### What you can do:
- Browse all tables visually
- Run custom SQL queries
- Export data
- See relationships

---

## Method 3: Command Line SQL (Advanced)

### Open SQLite directly:
```bash
cd C:\Projects\Claude\discrete-math-project
sqlite3 budget_planner.db
```

### Useful commands:
```sql
-- List all tables
.tables

-- View user settings
SELECT * FROM user_settings;

-- View all transactions
SELECT * FROM transactions ORDER BY date DESC LIMIT 10;

-- Count transactions by category
SELECT category, COUNT(*) as count
FROM transactions
GROUP BY category;

-- View anomalies
SELECT date, category, amount, z_score
FROM transactions
WHERE is_anomaly = 1
ORDER BY z_score DESC;

-- View total spending by category
SELECT category, SUM(amount) as total
FROM transactions
GROUP BY category
ORDER BY total DESC;

-- Exit
.quit
```

---

## Database Schema

### Table: **user_settings**
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | User's name |
| monthly_budget | REAL | Total budget |
| savings_goal | REAL | Monthly savings target |
| savings_purpose | TEXT | What saving for |
| created_at | TIMESTAMP | When created |

### Table: **fixed_expenses**
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | Expense name |
| amount | REAL | Amount |
| frequency | TEXT | "weekly" or "monthly" |
| created_at | TIMESTAMP | When added |

### Table: **transactions**
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| date | DATE | Transaction date |
| amount | REAL | Amount spent |
| category | TEXT | Category name |
| description | TEXT | Optional description |
| is_anomaly | BOOLEAN | Flagged as unusual? |
| z_score | REAL | Statistical z-score |
| created_at | TIMESTAMP | When added |

### Table: **monthly_stats**
(Currently unused - reserved for future caching)

---

## Quick Database Queries

### Your current data:

**User:**
- Name: Andrei Voicu
- Budget: $2,000/month
- Savings Goal: $400/month

**Fixed Expenses:**
- Rent: $600/month
- Netflix: $14/month
- **Total Fixed: $614/month**

**Transactions:**
- Total: 270 transactions
- Food & Groceries: 48 transactions ($1,233.55)
- Dining Out: 74 transactions ($851.03)
- Transportation: 91 transactions ($962.65)
- Shopping: 21 transactions ($1,466.93)
- Entertainment: 24 transactions ($537.73)
- Other: 12 transactions ($264.87)

**Anomalies Detected:**
- 4 unusual transactions flagged
- Highest z-score: 6.87 ($500 on Shopping)

---

## Recommended: Use Method 1 or 2

- **Method 1** (Python script): Quick overview, perfect for checking data
- **Method 2** (VS Code): Best for exploring, visual, easy to use
- **Method 3** (Command line): Advanced users, custom queries

---

## Backup Your Database

To backup your data:
```bash
# Copy the database file
copy budget_planner.db budget_planner_backup.db
```

Or just copy `budget_planner.db` to another location.

---

## Reset Database

To start fresh:
```bash
# Delete database
del budget_planner.db

# Run app again - it will create a new one
python app.py
```

Then go through setup again.
