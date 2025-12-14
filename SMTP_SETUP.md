# SMTP Email Setup Guide

This guide will help you configure email notifications for your Budget Planner application.

## What is SMTP?

SMTP (Simple Mail Transfer Protocol) allows the application to send email notifications for:
- Anomaly alerts (unusual transactions)
- Budget warnings
- Monthly summaries
- Savings goal updates

## Quick Setup Options

### Option 1: Gmail (Recommended for Testing)

1. **Enable 2-Factor Authentication** on your Google account:
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Create an App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Name it "Budget Planner"
   - Copy the 16-character password

3. **Configure in your application**:
   ```python
   SMTP_SERVER = 'smtp.gmail.com'
   SMTP_PORT = 587
   SMTP_EMAIL = 'your-email@gmail.com'
   SMTP_PASSWORD = 'your-16-char-app-password'
   ```

### Option 2: Outlook/Hotmail

1. **Configuration settings**:
   ```python
   SMTP_SERVER = 'smtp-mail.outlook.com'
   SMTP_PORT = 587
   SMTP_EMAIL = 'your-email@outlook.com'
   SMTP_PASSWORD = 'your-password'
   ```

### Option 3: Other Email Providers

Common SMTP servers:
- **Yahoo**: `smtp.mail.yahoo.com`, Port 587
- **ProtonMail**: `smtp.protonmail.com`, Port 587
- **Zoho**: `smtp.zoho.com`, Port 587

## How to Add to Budget Planner

### Step 1: Create Configuration File

Create a file named `config.py` in your budget-planner folder:

```python
# config.py
SMTP_ENABLED = True
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_EMAIL = 'your-email@gmail.com'
SMTP_PASSWORD = 'your-app-password'
```

### Step 2: Add Email Module

Create a file named `email_notifications.py`:

```python
# email_notifications.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SMTP_SERVER, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD, SMTP_ENABLED

def send_email(to_email, subject, body):
    """Send an email notification"""
    if not SMTP_ENABLED:
        return False

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        # Connect to SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)

        # Send email
        text = msg.as_string()
        server.sendmail(SMTP_EMAIL, to_email, text)
        server.quit()

        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def send_anomaly_alert(user_email, transaction_amount, category, z_score):
    """Send alert for unusual transaction"""
    subject = "Budget Alert: Unusual Transaction Detected"
    body = f"""
    <html>
    <body>
        <h2>Unusual Transaction Detected</h2>
        <p>A transaction was flagged as unusual:</p>
        <ul>
            <li><strong>Amount:</strong> ${transaction_amount:.2f}</li>
            <li><strong>Category:</strong> {category}</li>
            <li><strong>Z-Score:</strong> {abs(z_score):.2f} standard deviations</li>
        </ul>
        <p>This transaction is significantly different from your typical spending in this category.</p>
    </body>
    </html>
    """
    return send_email(user_email, subject, body)

def send_budget_warning(user_email, remaining, budget):
    """Send warning when budget is low"""
    percentage = (remaining / budget * 100) if budget > 0 else 0

    subject = "Budget Alert: Low Budget Warning"
    body = f"""
    <html>
    <body>
        <h2>Budget Warning</h2>
        <p>Your budget is running low this month:</p>
        <ul>
            <li><strong>Remaining:</strong> ${remaining:.2f}</li>
            <li><strong>Budget:</strong> ${budget:.2f}</li>
            <li><strong>Percentage Left:</strong> {percentage:.1f}%</li>
        </ul>
        <p>Consider reviewing your spending for the rest of the month.</p>
    </body>
    </html>
    """
    return send_email(user_email, subject, body)
```

### Step 3: Integrate with app.py

Add to your `app.py`:

```python
from email_notifications import send_anomaly_alert, send_budget_warning

# In the transactions API, after detecting anomaly:
if is_anomaly:
    # Get user email from session or database
    user_email = session.get('user_email')
    if user_email:
        send_anomaly_alert(user_email, amount, category, z_score)

# In dashboard, check if budget is low:
if remaining < user['monthly_budget'] * 0.2:  # Less than 20% remaining
    send_budget_warning(session.get('user_email'), remaining, user['monthly_budget'])
```

## Testing Your Setup

1. **Send a test email**:
   ```python
   # test_email.py
   from email_notifications import send_email

   send_email(
       'your-email@example.com',
       'Test Email',
       '<h1>Test</h1><p>If you receive this, SMTP is working!</p>'
   )
   ```

2. **Run the test**:
   ```bash
   python test_email.py
   ```

## Security Best Practices

1. **Never commit credentials**: Add `config.py` to `.gitignore`
   ```
   # .gitignore
   config.py
   *.pyc
   __pycache__/
   ```

2. **Use environment variables** (Advanced):
   ```python
   import os
   SMTP_EMAIL = os.environ.get('SMTP_EMAIL')
   SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
   ```

3. **Use app-specific passwords**: Never use your main email password

## Troubleshooting

### Common Issues

**"Authentication failed"**
- Double-check your email and password
- For Gmail, make sure you're using an App Password, not your regular password
- Verify 2-Factor Authentication is enabled

**"Connection refused"**
- Check the SMTP server address and port
- Ensure your firewall allows SMTP connections
- Try port 465 (SSL) instead of 587 (TLS)

**"Timeout error"**
- Check your internet connection
- Some networks block SMTP ports
- Try a different email provider

### Enable Debug Mode

Add to your email function:
```python
server.set_debuglevel(1)  # Shows detailed SMTP communication
```

## Disabling Email Notifications

To turn off emails without removing the code:

```python
# config.py
SMTP_ENABLED = False  # Change to False
```

## Alternative: Development Mode

For development/testing without real emails, print to console:

```python
def send_email(to_email, subject, body):
    print(f"\n--- EMAIL ---")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    print(f"--- END EMAIL ---\n")
    return True
```

## Need Help?

If you encounter issues:
1. Check your email provider's SMTP documentation
2. Verify your firewall settings
3. Try a different email provider
4. Consider using a service like SendGrid or Mailgun for production

---

**Note**: Email notifications are optional. The application works perfectly without SMTP configured.
