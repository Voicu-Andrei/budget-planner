"""
Email utilities for sending verification and notification emails
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets

try:
    from config import SMTP_SERVER, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD, SMTP_ENABLED, APP_URL
except ImportError:
    # Default values if config.py doesn't exist
    SMTP_ENABLED = False
    SMTP_SERVER = ''
    SMTP_PORT = 587
    SMTP_EMAIL = ''
    SMTP_PASSWORD = ''
    APP_URL = 'http://localhost:5000'


def send_email(to_email, subject, html_body):
    """Send an email"""
    if not SMTP_ENABLED:
        print(f"\n--- EMAIL (SMTP DISABLED) ---")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Body: {html_body}")
        print(f"--- END EMAIL ---\n")
        return True

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = SMTP_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject

        # Attach HTML body
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)

        # Connect to SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)

        # Send email
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        server.quit()

        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def generate_verification_token():
    """Generate a secure random token for email verification"""
    return secrets.token_urlsafe(32)


def send_verification_email(user_email, user_name, verification_token):
    """Send email verification link to new user"""
    verification_url = f"{APP_URL}/verify-email?token={verification_token}"

    subject = "Verify Your Email - Budget Planner"

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0;">Budget Planner</h1>
        </div>

        <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px;">
            <h2 style="color: #333;">Welcome, {user_name}!</h2>

            <p style="color: #666; font-size: 16px; line-height: 1.6;">
                Thank you for signing up for Budget Planner. To complete your registration and
                start managing your finances, please verify your email address.
            </p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_url}"
                   style="background: #667eea; color: white; padding: 15px 40px; text-decoration: none;
                          border-radius: 5px; font-weight: bold; display: inline-block;">
                    Verify Email Address
                </a>
            </div>

            <p style="color: #999; font-size: 14px;">
                If the button doesn't work, copy and paste this link into your browser:<br>
                <a href="{verification_url}" style="color: #667eea; word-break: break-all;">{verification_url}</a>
            </p>

            <p style="color: #999; font-size: 14px; margin-top: 30px;">
                This link will expire in 24 hours. If you didn't create an account,
                you can safely ignore this email.
            </p>
        </div>

        <div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
            Budget Planner - Your Personal Finance Manager
        </div>
    </body>
    </html>
    """

    return send_email(user_email, subject, html_body)


def send_password_reset_email(user_email, user_name, reset_token):
    """Send password reset link"""
    reset_url = f"{APP_URL}/reset-password?token={reset_token}"

    subject = "Reset Your Password - Budget Planner"

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0;">Budget Planner</h1>
        </div>

        <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px;">
            <h2 style="color: #333;">Password Reset Request</h2>

            <p style="color: #666; font-size: 16px; line-height: 1.6;">
                Hi {user_name},<br><br>
                We received a request to reset your password. Click the button below to create a new password:
            </p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}"
                   style="background: #667eea; color: white; padding: 15px 40px; text-decoration: none;
                          border-radius: 5px; font-weight: bold; display: inline-block;">
                    Reset Password
                </a>
            </div>

            <p style="color: #999; font-size: 14px;">
                If the button doesn't work, copy and paste this link into your browser:<br>
                <a href="{reset_url}" style="color: #667eea; word-break: break-all;">{reset_url}</a>
            </p>

            <p style="color: #999; font-size: 14px; margin-top: 30px;">
                This link will expire in 1 hour. If you didn't request a password reset,
                you can safely ignore this email.
            </p>
        </div>

        <div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
            Budget Planner - Your Personal Finance Manager
        </div>
    </body>
    </html>
    """

    return send_email(user_email, subject, html_body)


def send_welcome_email(user_email, user_name):
    """Send welcome email after verification"""
    subject = "Welcome to Budget Planner!"

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0;">Welcome to Budget Planner!</h1>
        </div>

        <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px;">
            <h2 style="color: #333;">You're all set, {user_name}!</h2>

            <p style="color: #666; font-size: 16px; line-height: 1.6;">
                Your email has been verified and your account is ready to use.
                Here's what you can do with Budget Planner:
            </p>

            <ul style="color: #666; font-size: 16px; line-height: 1.8;">
                <li>Track your daily expenses and income</li>
                <li>Set monthly budgets and savings goals</li>
                <li>View spending trends and analytics</li>
                <li>Get anomaly detection alerts for unusual spending</li>
                <li>Predict future spending with Monte Carlo simulations</li>
            </ul>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{APP_URL}/dashboard"
                   style="background: #667eea; color: white; padding: 15px 40px; text-decoration: none;
                          border-radius: 5px; font-weight: bold; display: inline-block;">
                    Go to Dashboard
                </a>
            </div>

            <p style="color: #666; font-size: 16px; line-height: 1.6;">
                Start by setting up your monthly budget and adding your first transactions!
            </p>
        </div>

        <div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
            Budget Planner - Your Personal Finance Manager
        </div>
    </body>
    </html>
    """

    return send_email(user_email, subject, html_body)
