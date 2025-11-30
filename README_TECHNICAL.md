# Budget Planner - Technical Documentation

## Overview
Budget Planner is a personal budget tracking web application that uses discrete mathematics, probability theory, and statistical analysis to help users manage their finances, predict future spending, and detect unusual transactions.

## Technology Stack

### Backend
- **Python 3.8+**
- **Flask 3.0.0** - Web framework
- **SQLite** - Database
- **NumPy 1.24.3** - Numerical computations
- **SciPy 1.11.4** - Statistical functions

### Frontend
- **HTML5** - Structure
- **CSS3** - Styling
- **JavaScript** - Interactivity
- **Chart.js 4.4.0** - Data visualization

## Project Structure

```
budget-planner/
├── app.py                  # Main Flask application
├── database.py             # Database management
├── math_engine.py          # All mathematical calculations
├── demo_data.py            # Demo data generator
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
├── templates/             # HTML templates
│   ├── base.html          # Base template with nav
│   ├── setup.html         # Initial setup wizard
│   ├── dashboard.html     # Main dashboard
│   ├── transactions.html  # Transaction management
│   ├── analysis.html      # Spending analysis
│   ├── prediction.html    # Monte Carlo predictions
│   └── settings.html      # Settings page
├── static/
│   ├── css/
│   │   └── style.css      # Main stylesheet
│   └── js/
│       └── main.js        # Main JavaScript file
└── budget_planner.db      # SQLite database (created on first run)
```

## Database Schema

### Table: user_settings
Stores user profile information.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | User's name |
| monthly_budget | REAL | Total monthly income/budget |
| savings_goal | REAL | Monthly savings target |
| savings_purpose | TEXT | What they're saving for (optional) |
| created_at | TIMESTAMP | When account was created |

### Table: fixed_expenses
Stores recurring fixed expenses.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | Expense name (e.g., "Rent") |
| amount | REAL | Expense amount |
| frequency | TEXT | "weekly" or "monthly" |
| created_at | TIMESTAMP | When added |

### Table: transactions
Stores all spending transactions.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| date | DATE | Transaction date |
| amount | REAL | Transaction amount |
| category | TEXT | Category name |
| description | TEXT | Optional description |
| is_anomaly | BOOLEAN | Whether flagged as anomaly |
| z_score | REAL | Calculated z-score |
| created_at | TIMESTAMP | When added |

### Table: monthly_stats
Cached monthly statistics (currently unused, reserved for optimization).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| month | TEXT | Month in format "YYYY-MM" |
| category | TEXT | Category name |
| total_spent | REAL | Total spent in category this month |
| mean | REAL | Average spending |
| std_dev | REAL | Standard deviation |
| transaction_count | INTEGER | Number of transactions |

## API Endpoints

### GET /
- **Description**: Home page, redirects to setup or dashboard
- **Returns**: Redirect to `/setup` or `/dashboard`

### GET/POST /setup
- **Description**: Initial setup wizard
- **GET**: Returns setup page
- **POST**: Creates user account and settings
- **Request Body** (POST):
  ```json
  {
    "name": "string",
    "monthly_budget": float,
    "savings_goal": float,
    "savings_purpose": "string",
    "fixed_expenses": [
      {"name": "string", "amount": float, "frequency": "monthly|weekly"}
    ],
    "load_demo": boolean
  }
  ```

### GET /dashboard
- **Description**: Main dashboard with health score and insights
- **Returns**: Rendered dashboard template

### GET /transactions
- **Description**: View all transactions page
- **Returns**: Rendered transactions template

### GET/POST /api/transactions
- **Description**: Transaction management API
- **GET Parameters**:
  - `offset`: int (pagination)
  - `limit`: int (results per page)
  - `category`: string (filter by category)
- **GET Returns**:
  ```json
  {
    "transactions": [...],
    "total": int,
    "has_more": boolean
  }
  ```
- **POST Request**:
  ```json
  {
    "date": "YYYY-MM-DD",
    "amount": float,
    "category": "string",
    "description": "string"
  }
  ```
- **POST Returns**:
  ```json
  {
    "success": boolean,
    "is_anomaly": boolean,
    "z_score": float
  }
  ```

### DELETE /api/delete-transaction/<id>
- **Description**: Delete a transaction
- **Returns**: `{"success": true}`

### GET /analysis
- **Description**: Spending analysis with charts and statistics
- **Returns**: Rendered analysis template with category stats

### GET /prediction
- **Description**: Monte Carlo prediction page
- **Returns**: Rendered prediction template

### POST /api/run-simulation
- **Description**: Run Monte Carlo simulation
- **Request Body**:
  ```json
  {
    "adjustments": {
      "Category Name": float  // adjustment amount
    }
  }
  ```
- **Returns**:
  ```json
  {
    "balances": [float],
    "mean": float,
    "std_dev": float,
    "probabilities": {
      "positive_balance": float,
      "meet_savings_goal": float,
      "over_budget": float
    },
    "percentiles": {
      "p10": float,
      "p25": float,
      "p50": float,
      "p75": float,
      "p90": float
    },
    "histogram": {
      "counts": [int],
      "bins": [float]
    }
  }
  ```

### GET/POST /settings
- **Description**: Settings page
- **GET**: Returns settings page
- **POST Actions**:
  - `update_user`: Update user information
  - `add_expense`: Add fixed expense
  - `delete_expense`: Delete fixed expense
  - `load_demo`: Generate demo data
  - `clear_all`: Clear all transactions

## Core Mathematical Functions

All mathematical functions are in `math_engine.py`.

### calculate_category_stats(category, months=6)
Calculates statistical metrics for a spending category over the last N months.

**Returns**:
- `mean`: Average monthly spending
- `std_dev`: Standard deviation
- `variance`: Variance
- `min`, `max`: Range
- `count`: Number of transactions
- `monthly_data`: Dictionary of monthly totals

### detect_anomaly(category, amount, threshold=2.0)
Detects if a transaction is statistically unusual using z-score.

**Formula**: `z = (x - μ) / σ`

**Returns**: `(is_anomaly, z_score)`

### run_monte_carlo_simulation(simulations=1000, adjustments=None)
Runs Monte Carlo simulation to predict next month's outcomes.

**Process**:
1. Get category statistics (mean, std_dev) from historical data
2. For each simulation:
   - Sample spending from normal distribution for each category
   - Add fixed expenses
   - Calculate ending balance
3. Analyze distribution of results

**Returns**: Probabilities, percentiles, histogram data

### calculate_health_score(...)
Calculates budget health score (0-100).

**Components**:
- 40 points: Staying under budget
- 30 points: Meeting savings goal
- 20 points: Consistency
- 10 points: No anomalies

### get_spending_trends(months=6)
Gets spending trends formatted for Chart.js line graphs.

## Demo Data Generator

The `demo_data.py` module generates 6 months of realistic fake data:

- **Categories**: Food, Dining, Entertainment, Transportation, Shopping, Other
- **Distribution**: Each category uses different mean and standard deviation
- **Transactions**: Realistic number per category (e.g., 15 transportation transactions/month for daily commute)
- **Anomalies**: Intentionally injected unusual transactions

## Running the Application

### Installation

1. **Install Python 3.8+** from https://python.org

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Open browser** to `http://localhost:5000`

### First Time Setup

1. The app will redirect to `/setup`
2. Enter your name
3. Set monthly budget, savings goal, and fixed expenses
4. Choose "Load Demo Data" to populate with 6 months of fake data, or "Start Fresh" to begin clean

### Using Demo Data

- From Settings page, click "Load Demo Data"
- Generates 6 months of transactions across all categories
- Includes intentional anomalies for testing
- Creates realistic spending patterns

## Modifying the Application

### Adding New Categories

1. Update the `categories` list in relevant routes (dashboard, analysis, prediction)
2. Add the category to dropdown menus in HTML templates
3. Optionally add to `demo_data.py` for demo data generation

### Changing Anomaly Detection Threshold

In `math_engine.py`, modify the `threshold` parameter in `detect_anomaly()`:
- Current: `threshold=2.0` (2 standard deviations)
- More sensitive: `threshold=1.5`
- Less sensitive: `threshold=2.5`

### Adjusting Health Score Weights

In `calculate_health_score()` function, modify the point allocations:
```python
# Budget adherence: currently 40 points
score += 40 * (calculation)

# Savings goal: currently 30 points
score += 30 * (calculation)
```

### Customizing Monte Carlo Simulations

In `run_monte_carlo_simulation()`:
- Change `simulations=1000` to run more/fewer simulations
- Modify distribution sampling (currently uses `np.random.normal`)
- Add different probability distributions for different categories

## Future Development Ideas

### Potential Enhancements

1. **Export Reports**: PDF monthly summaries
2. **Multiple Users**: Login system with user authentication
3. **Budget Limits per Category**: Set and track category budgets
4. **Recurring Transaction Templates**: Quick-add for common purchases
5. **Mobile App**: React Native or Flutter version
6. **CSV Import**: Import transactions from bank exports
7. **Goal Tracking**: Track progress toward specific savings goals
8. **Notifications**: Email/SMS alerts for anomalies or budget warnings
9. **Advanced Visualizations**: More chart types, interactive dashboards
10. **Machine Learning**: Predict categories automatically from descriptions

### Performance Optimization

- Implement `monthly_stats` table caching
- Add database indexing on frequently queried columns
- Lazy load transactions (already implemented with pagination)
- Cache Monte Carlo results for common scenarios

## Troubleshooting

### Database Issues
- Delete `budget_planner.db` to reset database
- Run `python -c "from database import init_db; init_db()"` to reinitialize

### Port Already in Use
- Change port in `app.py`: `app.run(debug=True, port=5001)`

### Charts Not Displaying
- Check browser console for JavaScript errors
- Ensure Chart.js CDN is accessible
- Verify data is being passed correctly to templates

### Calculations Seem Wrong
- Check you have enough historical data (at least 2 months recommended)
- Verify transactions are in correct categories
- Check for data entry errors in amounts

## License

This project is created for educational purposes.

## Author

Created for Discrete Mathematics and Python course project.
