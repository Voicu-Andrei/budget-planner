# Budget Planner

A professional personal budget tracking web application that uses discrete mathematics, probability theory, and statistical analysis to help you manage your finances intelligently.

## Features

### Core Functionality
- **Multi-User Support**: Secure authentication system with individual user accounts
- **Smart Dashboard**: Visual overview of your financial health at a glance
- **Transaction Management**: Track all your expenses with detailed categorization
- **Statistical Analysis**: View spending trends and patterns over time
- **Budget Tracking**: Set monthly budgets and savings goals
- **Fixed Expenses**: Manage recurring expenses separately
- **Dark Mode**: Professional light and dark themes

### Advanced Analytics
- **Anomaly Detection**: Automatically flag unusual transactions using z-scores
- **Monte Carlo Predictions**: Predict future budget outcomes using probability distributions
- **Spending Comparisons**: Month-over-month and category-based analysis
- **Health Metrics**: Simplified budget health tracking based on percentage remaining

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone or download this repository

2. Install dependencies:
   ```bash
   cd budget-planner
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open your browser to:
   ```
   http://localhost:5000
   ```

5. Create an account and complete the initial setup wizard

## Usage

### Getting Started

1. **Sign Up**: Create your account with email and password
2. **Initial Setup**: Configure your monthly budget, savings goal, and fixed expenses
3. **Add Transactions**: Start tracking your daily expenses
4. **Monitor Progress**: View your dashboard for real-time insights

### Dashboard

Your main hub displaying:
- Budget health percentage (how much budget remains)
- Total spent vs. budget this month
- Savings progress toward your goal
- Spending breakdown by category
- Daily spending trends

### Transactions Page

- View all transactions with advanced filtering
- Filter by date range, amount range, category, or search
- Add, edit, or delete transactions
- Transactions are automatically checked for anomalies

### Analysis Page

Four-tab interface for deep insights:
1. **Current Month**: Overview of this month's spending patterns
2. **6-Month Trends**: Historical spending analysis
3. **Comparisons**: Month-over-month and year-over-year comparisons
4. **Predictions**: Monte Carlo simulations for future outcomes

### Settings

Manage your account:
- Update name, email, and password
- Switch between light and dark themes
- Adjust monthly budget and savings goals
- Manage fixed expenses
- Load demo data or clear all transactions

## Technical Details

### Built With
- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Charts**: Chart.js
- **Math Libraries**: NumPy, SciPy

### Key Mathematical Concepts
- Z-score anomaly detection for outlier transactions
- Monte Carlo simulation for probabilistic forecasting
- Statistical analysis (mean, standard deviation, percentiles)
- Time-series analysis for spending trends

### Security
- Password hashing using Werkzeug security
- Session-based authentication
- User data isolation in multi-user environment

## Project Structure

```
budget-planner/
├── app.py                  # Main Flask application
├── database.py             # Database initialization and management
├── math_engine.py          # Statistical calculations and algorithms
├── demo_data.py            # Demo data generation
├── requirements.txt        # Python dependencies
├── templates/              # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── signup.html
│   ├── setup.html
│   ├── dashboard.html
│   ├── transactions.html
│   ├── analysis.html
│   └── settings.html
└── static/
    ├── css/
    │   └── style.css      # Application styles
    └── js/
        └── main.js        # JavaScript utilities

```

## License

This project is provided as-is for educational and personal use.

## Support

For issues or questions, please open an issue in the project repository.
