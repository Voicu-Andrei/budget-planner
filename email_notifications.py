"""
Email Notifications Module
Handles sending email alerts for budget anomalies and weekly summaries
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from database import get_db
import os


class EmailConfig:
    """Email configuration settings"""
    # SMTP Settings - Update these with your email provider details
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')  # Your email address
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')  # Your email password or app password
    FROM_EMAIL = os.getenv('FROM_EMAIL', SMTP_USERNAME)
    FROM_NAME = 'Budget Planner'

    # Notification settings
    SEND_ANOMALY_ALERTS = os.getenv('SEND_ANOMALY_ALERTS', 'true').lower() == 'true'
    SEND_WEEKLY_SUMMARY = os.getenv('SEND_WEEKLY_SUMMARY', 'true').lower() == 'true'
    SEND_BUDGET_WARNINGS = os.getenv('SEND_BUDGET_WARNINGS', 'true').lower() == 'true'


def send_email(to_email, subject, html_content):
    """
    Send an email using SMTP

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML content of the email

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not EmailConfig.SMTP_USERNAME or not EmailConfig.SMTP_PASSWORD:
        print("Email not configured. Set SMTP_USERNAME and SMTP_PASSWORD environment variables.")
        return False

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{EmailConfig.FROM_NAME} <{EmailConfig.FROM_EMAIL}>"
        msg['To'] = to_email

        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        # Send email
        with smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT) as server:
            server.starttls()
            server.login(EmailConfig.SMTP_USERNAME, EmailConfig.SMTP_PASSWORD)
            server.send_message(msg)

        print(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def send_anomaly_alert(user_id, transaction):
    """
    Send email alert for anomalous transaction

    Args:
        user_id: User ID
        transaction: Transaction record with anomaly
    """
    if not EmailConfig.SEND_ANOMALY_ALERTS:
        return

    from app import app
    with app.app_context():
        db = get_db()
        user = db.execute('SELECT email, name FROM users WHERE id = ?', (user_id,)).fetchone()

        if not user:
            return

        subject = f"Unusual Transaction Detected - ${transaction['amount']:.2f}"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
                <h2 style="color: #ef4444;">⚠️ Unusual Transaction Detected</h2>

                <div style="background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p>Hi {user['name']},</p>

                    <p>We detected an unusual transaction on your account:</p>

                    <div style="background-color: #fef2f2; padding: 15px; border-left: 4px solid #ef4444; margin: 15px 0;">
                        <p style="margin: 5px 0;"><strong>Amount:</strong> ${transaction['amount']:.2f}</p>
                        <p style="margin: 5px 0;"><strong>Category:</strong> {transaction['category']}</p>
                        <p style="margin: 5px 0;"><strong>Date:</strong> {transaction['date']}</p>
                        <p style="margin: 5px 0;"><strong>Description:</strong> {transaction.get('description', 'N/A')}</p>
                        <p style="margin: 5px 0;"><strong>Z-Score:</strong> {transaction['z_score']:.2f} standard deviations from average</p>
                    </div>

                    <p>This transaction is significantly different from your typical spending in this category.</p>

                    <p style="margin-top: 20px;">
                        <a href="#" style="background-color: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            View Dashboard
                        </a>
                    </p>
                </div>

                <p style="color: #666; font-size: 12px; text-align: center;">
                    This is an automated notification from Budget Planner
                </p>
            </div>
        </body>
        </html>
        """

        send_email(user['email'], subject, html_content)


def send_weekly_summary(user_id):
    """
    Send weekly spending summary email

    Args:
        user_id: User ID
    """
    if not EmailConfig.SEND_WEEKLY_SUMMARY:
        return

    from app import app
    with app.app_context():
        db = get_db()
        user = db.execute('SELECT email, name FROM users WHERE id = ?', (user_id,)).fetchone()

        if not user:
            return

        # Get week data
        week_ago = datetime.now() - timedelta(days=7)
        transactions = db.execute('''
            SELECT SUM(amount) as total, category, COUNT(*) as count
            FROM transactions
            WHERE user_id = ? AND date >= ?
            GROUP BY category
        ''', (user_id, week_ago)).fetchall()

        total_spent = sum(t['total'] for t in transactions)

        # Get user settings
        settings = db.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,)).fetchone()

        subject = f"Your Weekly Budget Summary - ${total_spent:.2f} Spent"

        # Build category breakdown HTML
        category_rows = ""
        for t in transactions:
            category_rows += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{t['category']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: right;">${t['total']:.2f}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: right;">{t['count']}</td>
            </tr>
            """

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
                <h2 style="color: #2563eb;">📊 Your Weekly Budget Summary</h2>

                <div style="background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p>Hi {user['name']},</p>

                    <p>Here's your spending summary for the past week:</p>

                    <div style="background-color: #dbeafe; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                        <h3 style="margin: 0; color: #2563eb;">Total Spent This Week</h3>
                        <p style="font-size: 2em; font-weight: bold; margin: 10px 0;">${total_spent:.2f}</p>
                    </div>

                    <h3>Breakdown by Category:</h3>
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <thead>
                            <tr style="background-color: #f3f4f6;">
                                <th style="padding: 10px; text-align: left;">Category</th>
                                <th style="padding: 10px; text-align: right;">Amount</th>
                                <th style="padding: 10px; text-align: right;">Transactions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {category_rows}
                        </tbody>
                    </table>

                    <p style="margin-top: 20px;">
                        <a href="#" style="background-color: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            View Full Dashboard
                        </a>
                    </p>
                </div>

                <p style="color: #666; font-size: 12px; text-align: center;">
                    This is an automated weekly summary from Budget Planner
                </p>
            </div>
        </body>
        </html>
        """

        send_email(user['email'], subject, html_content)


def send_budget_warning(user_id, percentage_used):
    """
    Send budget warning when spending exceeds threshold

    Args:
        user_id: User ID
        percentage_used: Percentage of monthly budget used
    """
    if not EmailConfig.SEND_BUDGET_WARNINGS:
        return

    from app import app
    with app.app_context():
        db = get_db()
        user = db.execute('SELECT email, name FROM users WHERE id = ?', (user_id,)).fetchone()

        if not user:
            return

        subject = f"Budget Alert - {percentage_used:.0f}% of Monthly Budget Used"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
                <h2 style="color: #f59e0b;">⚠️ Budget Warning</h2>

                <div style="background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p>Hi {user['name']},</p>

                    <p>You've used <strong>{percentage_used:.0f}%</strong> of your monthly budget.</p>

                    <div style="background-color: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <div style="background-color: #e5e7eb; height: 20px; border-radius: 10px; overflow: hidden;">
                            <div style="background-color: #f59e0b; height: 100%; width: {min(percentage_used, 100):.0f}%;"></div>
                        </div>
                        <p style="text-align: center; margin-top: 10px; font-weight: bold;">{percentage_used:.0f}% Used</p>
                    </div>

                    <p>Consider reviewing your spending to stay within budget this month.</p>

                    <p style="margin-top: 20px;">
                        <a href="#" style="background-color: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display-inline-block;">
                            Review Budget
                        </a>
                    </p>
                </div>

                <p style="color: #666; font-size: 12px; text-align: center;">
                    This is an automated notification from Budget Planner
                </p>
            </div>
        </body>
        </html>
        """

        send_email(user['email'], subject, html_content)
