# Installation Guide - Budget Planner

## Step-by-Step Setup Instructions

### Step 1: Verify Python Installation

1. Open Command Prompt (Windows) or Terminal (Mac/Linux)
2. Type:
   ```bash
   python --version
   ```
3. You should see something like `Python 3.8.x` or higher
4. If not installed, download from: https://www.python.org/downloads/
   - **IMPORTANT**: During installation, check "Add Python to PATH"

### Step 2: Install Required Packages

1. Open Command Prompt
2. Navigate to the project folder:
   ```bash
   cd C:\Projects\Claude\discrete-math-project
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Wait for installation to complete (may take 1-2 minutes)

### Step 3: Run the Application

1. From the project folder, run:
   ```bash
   python app.py
   ```
2. You should see:
   ```
   * Running on http://127.0.0.1:5000
   * Debug mode: on
   ```
3. **DO NOT CLOSE THIS WINDOW** - keep it running

### Step 4: Open in Browser

1. Open your web browser (Chrome, Firefox, Edge, Safari)
2. Go to:
   ```
   http://localhost:5000
   ```
   or
   ```
   http://127.0.0.1:5000
   ```

### Step 5: First Time Setup

1. You'll see a welcome screen
2. Enter your name
3. Click "Get Started"
4. Fill in:
   - Monthly budget (e.g., 2000)
   - Add fixed expenses (e.g., Rent: $800/month)
   - Savings goal (e.g., 300)
5. Choose:
   - **"Load Demo Data"** - for testing (generates 6 months of fake data)
   - **"Start Fresh"** - to use it for real

### Step 6: Explore!

- Dashboard: See your budget health
- Transactions: Add and view spending
- Analysis: See charts and statistics
- Prediction: Run Monte Carlo simulation
- Settings: Modify your budget

## Common Issues

### Issue: "python is not recognized"
**Solution**: Python not in PATH. Reinstall Python and check "Add to PATH"

### Issue: "pip is not recognized"
**Solution**: Use `python -m pip install -r requirements.txt` instead

### Issue: "ModuleNotFoundError: No module named 'flask'"
**Solution**: Run `pip install -r requirements.txt` again

### Issue: "Address already in use"
**Solution**:
1. Close other programs using port 5000
2. Or change port in app.py:
   ```python
   app.run(debug=True, port=5001)
   ```

### Issue: Database errors
**Solution**: Delete `budget_planner.db` file and restart

## VS Code Setup (Optional but Recommended)

1. Install VS Code from: https://code.visualstudio.com/
2. Install Python extension in VS Code
3. Open project folder in VS Code
4. Install recommended extension: SQLite Viewer (to view database)
5. Use integrated terminal to run `python app.py`

## For Development

### Recommended VS Code Extensions:
- Python (Microsoft)
- SQLite Viewer (alexcvzz)
- HTML CSS Support
- JavaScript (ES6) code snippets

### To Reset Database:
```bash
# Delete the database file
del budget_planner.db  # Windows
rm budget_planner.db   # Mac/Linux

# Run app again - it will create fresh database
python app.py
```

### To View Database:
1. Install SQLite Viewer extension in VS Code
2. Right-click `budget_planner.db`
3. Select "Open Database"

## Testing the Application

### Test Checklist:

✅ **Setup**
- [ ] Can enter name and settings
- [ ] Can add fixed expenses
- [ ] Demo data loads successfully

✅ **Dashboard**
- [ ] Shows health score
- [ ] Displays correct statistics
- [ ] Insights appear

✅ **Transactions**
- [ ] Can add transaction
- [ ] Anomaly detection works (try adding $500 to a low-spending category)
- [ ] Can filter by category
- [ ] Load more button works
- [ ] Can delete transactions

✅ **Analysis**
- [ ] Pie chart displays
- [ ] Line chart shows trends
- [ ] Category statistics show correctly
- [ ] Bar charts appear for each category

✅ **Prediction**
- [ ] Simulation runs
- [ ] Histogram displays
- [ ] Probabilities calculate correctly
- [ ] What-if sliders work

✅ **Settings**
- [ ] Can update name/budget
- [ ] Can add/delete fixed expenses
- [ ] Load demo works
- [ ] Clear all works

## Next Steps

1. **Read the documentation**:
   - `README_TECHNICAL.md` - How everything works
   - `README_EDUCATIONAL.md` - Math concepts explained

2. **Customize for yourself**:
   - Add your real budget and expenses
   - Start tracking actual spending

3. **For presentation**:
   - Use demo data for clean demonstration
   - Practice explaining the math concepts
   - Prepare to show code in VS Code

## Getting Help

If you encounter issues:
1. Check this guide first
2. Read error messages carefully
3. Check `README_TECHNICAL.md` troubleshooting section
4. Google the specific error message

## Success!

If you see the dashboard with the welcome message, you're all set! 🎉

The app is running locally on your computer. No internet connection needed after initial setup.
