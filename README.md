# Budget Planner 💰

A personal budget tracking web application that uses **discrete mathematics**, **probability theory**, and **statistical analysis** to help you manage finances intelligently.

## Features

- 📊 **Smart Analytics**: Statistical analysis of your spending patterns
- 🔍 **Anomaly Detection**: Automatically flag unusual transactions using z-scores
- 🎲 **Monte Carlo Predictions**: Predict future outcomes with probability distributions
- 📈 **Visualizations**: Beautiful charts and graphs of your spending
- ⚡ **Real-time Insights**: Get alerts and recommendations as you spend
- 🎯 **Health Score**: Track your overall budget health (0-100)

## Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   cd budget-planner
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Open your browser** to:
   ```
   http://localhost:5000
   ```

5. **First time setup**:
   - Enter your name
   - Set your monthly budget and savings goal
   - Add fixed expenses (rent, subscriptions, etc.)
   - Choose "Load Demo Data" to see it in action, or "Start Fresh"

## Usage

### Dashboard
Your main hub showing:
- Budget health score
- Current month spending
- Alerts for unusual transactions
- Quick insights

### Transactions
- Add, view, and manage all your spending
- Automatic anomaly detection
- Filter by category
- Pagination for large datasets

### Analysis
- Statistical breakdown by category
- Mean, standard deviation, variance
- 6-month spending trends
- Visual charts

### Prediction
- Run Monte Carlo simulations (1,000 scenarios)
- See probability of meeting savings goals
- "What-if" analysis with adjustable spending
- Histogram of possible outcomes

### Settings
- Update your budget and goals
- Manage fixed expenses
- Load demo data or clear transactions

## Mathematical Concepts Used

This project demonstrates:

- **Arrays & Data Structures**: Store and manipulate transaction data
- **Mean & Standard Deviation**: Analyze spending patterns
- **Probability Distributions**: Model spending with normal distribution
- **Z-Scores**: Detect statistical outliers (anomalies)
- **Monte Carlo Simulation**: Predict future outcomes through random sampling
- **Percentiles**: Show best/worst/likely case scenarios
- **Expected Value**: Calculate probable future balances
- **Confidence Intervals**: Quantify uncertainty in estimates

## Project Structure

```
budget-planner/
├── app.py                    # Main Flask application
├── database.py               # Database management
├── math_engine.py            # All mathematical calculations
├── demo_data.py              # Demo data generator
├── templates/                # HTML templates
├── static/                   # CSS and JavaScript
├── README.md                 # This file
├── README_TECHNICAL.md       # Technical documentation
└── README_EDUCATIONAL.md     # Math concepts explained
```

## Documentation

- **[README_TECHNICAL.md](README_TECHNICAL.md)**: Complete technical documentation for developers
- **[README_EDUCATIONAL.md](README_EDUCATIONAL.md)**: Detailed explanation of all math concepts for educational purposes

## Technologies

- **Backend**: Python, Flask, SQLite
- **Math**: NumPy, SciPy
- **Frontend**: HTML5, CSS3, JavaScript
- **Visualization**: Chart.js

## Demo Data

The app includes a demo data generator that creates 6 months of realistic transaction data:
- Different spending patterns for each category
- Realistic variation using probability distributions
- Intentional anomalies for testing
- ~300 total transactions

Access via Settings → "Load Demo Data"

## Screenshots

### Dashboard
View your budget health, spending summary, and personalized insights.

### Analysis
Statistical breakdown of spending by category with visualizations.

### Prediction
Monte Carlo simulation showing probability distributions of future outcomes.

## Educational Purpose

This project was created for a Discrete Mathematics and Python course to demonstrate:
- Practical applications of probability and statistics
- Real-world problem-solving with mathematical concepts
- Clean code architecture and documentation
- Full-stack web development

## Future Enhancements

Potential additions:
- User authentication and multiple accounts
- Mobile app version
- Export to PDF reports
- CSV import from bank statements
- Category budget limits with tracking
- Email/SMS notifications
- Machine learning for automatic categorization

## Troubleshooting

**Database issues?**
- Delete `budget_planner.db` and restart the app

**Port already in use?**
- Change the port in `app.py`: `app.run(debug=True, port=5001)`

**Charts not showing?**
- Check your internet connection (Chart.js loads from CDN)
- Check browser console for errors

**Need more help?**
- See [README_TECHNICAL.md](README_TECHNICAL.md) for detailed troubleshooting

## License

Educational project - free to use and modify.

## Author

Created for Discrete Mathematics course project.

---

**Enjoy managing your budget with the power of mathematics!** 🎓💰
