# Budget Planner - New Features Guide

This document explains all the new features added to your Budget Planner application.

## What's New

### 1. Dark Mode
Toggle between light and dark themes with a single click!

**How to use:**
- Click the moon/sun icon in the navigation bar
- Your preference is saved automatically in browser storage
- Works across all pages

### 2. Advanced Transaction Filtering
Filter transactions with multiple criteria simultaneously.

**Features:**
- **Date Range**: Filter by start and end date
- **Search**: Search transaction descriptions
- **Amount Range**: Set minimum and maximum amounts
- **Category**: Filter by spending category
- **Clear Filters**: Reset all filters with one click

**How to use:**
1. Go to Transactions page
2. Use the filter panel above the transaction table
3. Filters apply in real-time

### 3. Comparison Views
New page showing month-over-month and year-over-year spending comparisons.

**Features:**
- **Month-over-Month**: Last 7 months of spending with bar chart
- **Category Comparison**: Last 3 months breakdown by category
- **Year-over-Year**: Compare current year vs last year
- **Automatic Insights**: Smart insights generated from your patterns

**How to access:**
- Click "Comparisons" in the navigation menu

### 4. Advanced Visualizations

#### Heatmap Calendar
Visual calendar showing spending intensity over the last 90 days.

**Features:**
- Color-coded by spending amount
- Hover to see exact amounts
- Identify high-spending days at a glance

#### Spending Velocity Chart
Track how fast you're spending throughout the month.

**Features:**
- Shows cumulative spending progression
- Helps predict if you'll exceed budget
- Day-by-day breakdown

**How to access:**
- Both charts are on the Analysis page

### 5. Multi-User Authentication
Multiple users can now have separate accounts and data.

**Features:**
- Secure login/signup system
- Password hashing for security
- User isolation (each user sees only their data)
- Session management

**How to use:**

#### First Time Setup (Existing Users):
If you already have data:
1. Run the app - migration happens automatically
2. A default user is created:
   - **Email**: `user@budgetplanner.local`
   - **Password**: `password123`
3. **IMPORTANT**: Change this password after logging in!

#### New Users:
1. Visit `/signup` to create an account
2. Enter your name, email, and password
3. You'll be redirected to set up your budget

#### Logging In:
1. Visit `/login`
2. Enter your email and password
3. Access your personal budget dashboard

### 6. Email Notifications
Receive automated email alerts for important budget events.

**Notification Types:**
1. **Anomaly Alerts**: When unusual transactions are detected
2. **Weekly Summary**: Weekly spending breakdown
3. **Budget Warnings**: When you exceed spending thresholds

**How to configure:**

#### Option 1: Environment Variables (Recommended)
Create a `.env` file in the project root:

```env
# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com

# Notification Settings (true/false)
SEND_ANOMALY_ALERTS=true
SEND_WEEKLY_SUMMARY=true
SEND_BUDGET_WARNINGS=true
```

#### Option 2: System Environment Variables
Set these in your system:
- `SMTP_SERVER`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`

#### Gmail Setup Example:
1. Enable 2-factor authentication on your Google account
2. Generate an App Password:
   - Go to Google Account → Security → App Passwords
   - Create a new app password for "Mail"
3. Use the 16-character app password in `SMTP_PASSWORD`

#### Testing Email Notifications:
```python
from email_notifications import send_weekly_summary, send_budget_warning

# Send test weekly summary
send_weekly_summary(user_id=1)

# Send test budget warning (85% of budget used)
send_budget_warning(user_id=1, percentage_used=85)
```

## Completing Multi-User Migration

The database migration adds multi-user support automatically. However, you need to update routes to fully isolate user data:

### Routes That Need Protection:
Add `@login_required` decorator to these routes in `app.py`:
- `dashboard()`
- `transactions_api()`
- `transactions_page()`
- `analysis()`
- `comparisons()`
- `prediction()`
- `run_simulation()`
- `settings()`
- `delete_transaction()`

### Example:
```python
@app.route('/dashboard')
@login_required  # Add this decorator
def dashboard():
    # existing code...
```

### Database Queries to Update:
Replace queries like:
```python
db.execute('SELECT * FROM transactions WHERE id = ?', (id,))
```

With:
```python
db.execute('SELECT * FROM transactions WHERE id = ? AND user_id = ?',
           (id, session['user_id']))
```

Apply to:
- All queries in `dashboard()`
- All queries in `transactions_api()`
- All queries in `analysis()`
- All queries in `comparisons()`
- All queries in `settings()`
- `demo_data.py` - add `user_id` when generating demo data

## Security Best Practices

1. **Change Default Password**: If migrating from single-user mode
2. **Use Strong Passwords**: Minimum 6 characters (enforced)
3. **Environment Variables**: Never commit `.env` files to version control
4. **HTTPS**: Use HTTPS in production
5. **Session Secret**: Change `app.secret_key` to a secure random value

## Troubleshooting

### Email Not Sending:
- Check SMTP credentials in environment variables
- For Gmail, ensure 2FA is enabled and using App Password
- Check firewall/antivirus isn't blocking SMTP
- Look for error messages in console

### Dark Mode Not Working:
- Clear browser cache
- Check if JavaScript is enabled
- Try different browser

### Login Issues:
- Verify email and password are correct
- Check database migration completed successfully
- Look for error messages on login page

### Database Migration Failed:
1. Backup your `budget_planner.db` file
2. Check console for migration errors
3. Manually run migration:
   ```python
   from database import migrate_to_multiuser
   migrate_to_multiuser()
   ```

## Running the App

```bash
# Install new dependencies (if needed)
pip install -r requirements.txt

# Run the app
python app.py
```

Visit `http://localhost:5000`

## Feature Checklist

- [x] Dark mode with theme toggle
- [x] Advanced transaction filtering (date, search, amount range)
- [x] Comparison views (month-over-month, year-over-year)
- [x] Heatmap calendar visualization
- [x] Spending velocity chart
- [x] Multi-user authentication (login/signup/logout)
- [x] Email notifications (anomalies, summaries, warnings)
- [ ] Route protection (needs manual completion)
- [ ] User data isolation (needs manual completion)

## Next Steps

1. **Test all features** with the app running
2. **Configure email** if you want notifications
3. **Complete user isolation** by updating remaining routes
4. **Add additional users** via signup page
5. **Customize email templates** in `email_notifications.py`

## Support

For issues or questions:
- Check the console output for errors
- Review this guide
- Check the main README files

Enjoy your enhanced Budget Planner! 🎉
