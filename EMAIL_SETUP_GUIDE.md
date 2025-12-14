# Email Verification Setup Guide - FREE with Gmail

## Quick Start (5 minutes)

Email verification is now enabled! Follow these steps to configure it with your FREE Gmail account.

### Step 1: Enable 2-Factor Authentication on Gmail

1. Go to https://myaccount.google.com/security
2. Click on "2-Step Verification"
3. Follow the steps to enable it (you'll need your phone)

### Step 2: Create App Password

1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" for the app
3. Select "Other (Custom name)" for device
4. Type "Budget Planner"
5. Click "Generate"
6. **Copy the 16-character password** (it will look like: `xxxx xxxx xxxx xxxx`)

### Step 3: Configure Budget Planner

1. Open the file: `C:\Projects\Claude\budget-planner\config.py`

2. Replace these lines:
   ```python
   SMTP_EMAIL = 'your-email@gmail.com'     # Your Gmail address
   SMTP_PASSWORD = 'your-app-password'      # The 16-char password from Step 2
   ```

3. Example:
   ```python
   SMTP_EMAIL = 'john.doe@gmail.com'
   SMTP_PASSWORD = 'abcd efgh ijkl mnop'
   ```

4. Save the file

### Step 4: Test It!

1. Run your application:
   ```bash
   python app.py
   ```

2. Sign up with a new account
3. Check your email for the verification link
4. Click the link to verify your email

**That's it! Completely FREE with no limits for personal use.**

---

## How Email Verification Works

### New User Flow:
1. User signs up → Account created (not verified)
2. Email sent with verification link
3. User clicks link → Email verified
4. User redirected to setup page
5. Welcome email sent

### Security Benefits:
- Ensures users own the email address
- Prevents fake accounts
- Enables password reset functionality
- Allows sending important notifications

---

## Troubleshooting

### "Authentication failed" error
- Make sure you're using an App Password, NOT your regular Gmail password
- Double-check 2-Factor Authentication is enabled
- Copy the App Password exactly (remove spaces when pasting)

### Email not arriving
- Check spam/junk folder
- Wait a few minutes (can take 1-5 minutes)
- Try the "Resend Verification Email" button
- Check that SMTP_ENABLED is set to `True` in config.py

### "SMTP disabled" in console
- This means emails are being printed to console instead of sent
- Set `SMTP_ENABLED = True` in config.py
- Make sure config.py has your Gmail credentials

---

## Advanced: Using SendGrid (Free 100 emails/day)

If you want more reliable delivery for production:

1. Sign up at https://sendgrid.com/free/
2. Create an API key
3. Update config.py:
   ```python
   # For SendGrid
   SMTP_SERVER = 'smtp.sendgrid.net'
   SMTP_PORT = 587
   SMTP_EMAIL = 'apikey'  # Literally type "apikey"
   SMTP_PASSWORD = 'YOUR_SENDGRID_API_KEY'
   ```

---

## Cost Summary

**Gmail SMTP:**
- Cost: FREE forever
- Limit: 500 emails/day
- Best for: Personal use, development

**SendGrid Free Tier:**
- Cost: FREE forever
- Limit: 100 emails/day
- Best for: Small production apps

**Brevo (Sendinblue):**
- Cost: FREE forever
- Limit: 300 emails/day
- Best for: Small apps needing more emails

**All options are completely FREE for your budget planner app!**

---

## Security Notes

1. **Never commit config.py to Git**
   - Add `config.py` to `.gitignore`
   - Keep your passwords secret

2. **Use environment variables for production**
   ```python
   import os
   SMTP_EMAIL = os.environ.get('SMTP_EMAIL', 'your-email@gmail.com')
   SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'your-password')
   ```

3. **Rotate App Passwords periodically**
   - Delete old App Passwords in your Google Account
   - Create new ones every few months

---

## Disabling Email Verification (for testing)

If you want to test without email setup:

1. Open `config.py`
2. Set: `SMTP_ENABLED = False`
3. Emails will print to console instead of sending
4. You can still test the full verification flow

---

## Need Help?

- Gmail App Passwords: https://support.google.com/accounts/answer/185833
- SendGrid Docs: https://docs.sendgrid.com/
- SMTP Settings: https://support.google.com/mail/answer/7126229

**Remember: This is all FREE! No credit card needed.**
