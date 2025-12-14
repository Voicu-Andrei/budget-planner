"""
Reports Module - PDF generation and advanced reporting
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from datetime import datetime, timedelta
import io
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from database import get_db


def generate_monthly_report(user_id, year, month):
    """Generate a comprehensive monthly financial report as PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=12,
        spaceBefore=12
    )

    # Get database connection
    db = get_db()

    # Get user info
    user = db.execute('SELECT name FROM users WHERE id = ?', (user_id,)).fetchone()
    user_name = user['name'] if user else 'User'

    # Report title
    month_name = datetime(year, month, 1).strftime('%B %Y')
    story.append(Paragraph(f"Monthly Financial Report", title_style))
    story.append(Paragraph(f"{month_name}", styles['Heading2']))
    story.append(Paragraph(f"Prepared for: {user_name}", styles['Normal']))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    # Date range for the month
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"

    # --- INCOME SECTION ---
    story.append(Paragraph("Income Summary", heading_style))

    income_data = db.execute('''
        SELECT
            source,
            SUM(amount) as total,
            COUNT(*) as count
        FROM income
        WHERE user_id = ? AND date >= ? AND date < ?
        GROUP BY source
    ''', (user_id, start_date, end_date)).fetchall()

    if income_data:
        income_table_data = [['Source', 'Count', 'Amount']]
        total_income = 0
        for row in income_data:
            income_table_data.append([
                row['source'],
                str(row['count']),
                f"${row['total']:,.2f}"
            ])
            total_income += row['total']

        income_table_data.append(['TOTAL INCOME', '', f"${total_income:,.2f}"])

        income_table = Table(income_table_data, colWidths=[3*inch, 1.5*inch, 2*inch])
        income_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e0e7ff')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(income_table)
    else:
        story.append(Paragraph("No income recorded this month.", styles['Normal']))
        total_income = 0

    story.append(Spacer(1, 0.3*inch))

    # --- EXPENSES SECTION ---
    story.append(Paragraph("Expense Summary", heading_style))

    expense_data = db.execute('''
        SELECT
            category,
            SUM(amount) as total,
            COUNT(*) as count
        FROM transactions
        WHERE user_id = ? AND date >= ? AND date < ?
        GROUP BY category
        ORDER BY total DESC
    ''', (user_id, start_date, end_date)).fetchall()

    if expense_data:
        expense_table_data = [['Category', 'Transactions', 'Amount', '% of Total']]
        total_expenses = sum(row['total'] for row in expense_data)

        for row in expense_data:
            percentage = (row['total'] / total_expenses * 100) if total_expenses > 0 else 0
            expense_table_data.append([
                row['category'],
                str(row['count']),
                f"${row['total']:,.2f}",
                f"{percentage:.1f}%"
            ])

        expense_table_data.append(['TOTAL EXPENSES', '', f"${total_expenses:,.2f}", '100%'])

        expense_table = Table(expense_table_data, colWidths=[2.5*inch, 1.2*inch, 1.8*inch, 1*inch])
        expense_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e0e7ff')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(expense_table)
    else:
        story.append(Paragraph("No expenses recorded this month.", styles['Normal']))
        total_expenses = 0

    story.append(Spacer(1, 0.3*inch))

    # --- FINANCIAL SUMMARY ---
    story.append(Paragraph("Financial Summary", heading_style))

    net_income = total_income - total_expenses
    savings_rate = (net_income / total_income * 100) if total_income > 0 else 0

    summary_data = [
        ['Metric', 'Amount'],
        ['Total Income', f"${total_income:,.2f}"],
        ['Total Expenses', f"${total_expenses:,.2f}"],
        ['Net Income (Savings)', f"${net_income:,.2f}"],
        ['Savings Rate', f"{savings_rate:.1f}%"]
    ]

    summary_table = Table(summary_data, colWidths=[3.5*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -2), (-1, -1), 12),
        ('BACKGROUND', (0, -2), (-1, -1), colors.HexColor('#f0fdf4') if net_income >= 0 else colors.HexColor('#fef2f2')),
        ('TEXTCOLOR', (0, -2), (-1, -1), colors.HexColor('#166534') if net_income >= 0 else colors.HexColor('#991b1b')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    story.append(summary_table)

    story.append(Spacer(1, 0.3*inch))

    # --- ASSETS SECTION ---
    story.append(Paragraph("Asset Portfolio", heading_style))

    assets_data = db.execute('''
        SELECT
            asset_type,
            SUM(current_value) as total_value,
            SUM(purchase_value) as total_purchase,
            COUNT(*) as count
        FROM assets
        WHERE user_id = ?
        GROUP BY asset_type
    ''', (user_id,)).fetchall()

    if assets_data:
        assets_table_data = [['Asset Type', 'Count', 'Current Value', 'Purchase Value', 'Gain/Loss']]
        total_current = 0
        total_purchase = 0

        for row in assets_data:
            current = row['total_value'] or 0
            purchase = row['total_purchase'] or 0
            gain_loss = current - purchase
            total_current += current
            total_purchase += purchase

            assets_table_data.append([
                row['asset_type'].title(),
                str(row['count']),
                f"${current:,.2f}",
                f"${purchase:,.2f}",
                f"${gain_loss:,.2f}"
            ])

        total_gain_loss = total_current - total_purchase
        assets_table_data.append([
            'TOTAL',
            '',
            f"${total_current:,.2f}",
            f"${total_purchase:,.2f}",
            f"${total_gain_loss:,.2f}"
        ])

        assets_table = Table(assets_table_data, colWidths=[1.8*inch, 0.8*inch, 1.5*inch, 1.5*inch, 1.4*inch])
        assets_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e0e7ff')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(assets_table)
    else:
        story.append(Paragraph("No assets recorded.", styles['Normal']))

    # Footer
    story.append(Spacer(1, 0.5*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Budget Planner - Personal Finance Management", footer_style))
    story.append(Paragraph(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_annual_report(user_id, year):
    """Generate a comprehensive annual financial report as PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=12,
        spaceBefore=12
    )

    # Get database connection
    db = get_db()

    # Get user info
    user = db.execute('SELECT name FROM users WHERE id = ?', (user_id,)).fetchone()
    user_name = user['name'] if user else 'User'

    # Report title
    story.append(Paragraph(f"Annual Financial Report", title_style))
    story.append(Paragraph(f"Year {year}", styles['Heading2']))
    story.append(Paragraph(f"Prepared for: {user_name}", styles['Normal']))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    # Date range for the year
    start_date = f"{year}-01-01"
    end_date = f"{year + 1}-01-01"

    # --- YEARLY SUMMARY ---
    story.append(Paragraph("Yearly Summary", heading_style))

    # Get yearly income
    yearly_income = db.execute('''
        SELECT SUM(amount) as total FROM income
        WHERE user_id = ? AND date >= ? AND date < ?
    ''', (user_id, start_date, end_date)).fetchone()
    total_income = yearly_income['total'] if yearly_income and yearly_income['total'] else 0

    # Get yearly expenses
    yearly_expenses = db.execute('''
        SELECT SUM(amount) as total FROM transactions
        WHERE user_id = ? AND date >= ? AND date < ?
    ''', (user_id, start_date, end_date)).fetchone()
    total_expenses = yearly_expenses['total'] if yearly_expenses and yearly_expenses['total'] else 0

    net_income = total_income - total_expenses
    savings_rate = (net_income / total_income * 100) if total_income > 0 else 0

    summary_data = [
        ['Metric', 'Amount'],
        ['Total Annual Income', f"${total_income:,.2f}"],
        ['Total Annual Expenses', f"${total_expenses:,.2f}"],
        ['Net Annual Savings', f"${net_income:,.2f}"],
        ['Annual Savings Rate', f"{savings_rate:.1f}%"],
        ['Average Monthly Income', f"${total_income/12:,.2f}"],
        ['Average Monthly Expenses', f"${total_expenses/12:,.2f}"]
    ]

    summary_table = Table(summary_data, colWidths=[3.5*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))

    # --- MONTHLY BREAKDOWN ---
    story.append(Paragraph("Monthly Breakdown", heading_style))

    monthly_data = [['Month', 'Income', 'Expenses', 'Net', 'Savings Rate']]

    for month in range(1, 13):
        month_start = f"{year}-{month:02d}-01"
        if month == 12:
            month_end = f"{year + 1}-01-01"
        else:
            month_end = f"{year}-{month + 1:02d}-01"

        month_income = db.execute('''
            SELECT SUM(amount) as total FROM income
            WHERE user_id = ? AND date >= ? AND date < ?
        ''', (user_id, month_start, month_end)).fetchone()

        month_expenses = db.execute('''
            SELECT SUM(amount) as total FROM transactions
            WHERE user_id = ? AND date >= ? AND date < ?
        ''', (user_id, month_start, month_end)).fetchone()

        income_val = month_income['total'] if month_income and month_income['total'] else 0
        expense_val = month_expenses['total'] if month_expenses and month_expenses['total'] else 0
        net_val = income_val - expense_val
        rate = (net_val / income_val * 100) if income_val > 0 else 0

        monthly_data.append([
            datetime(year, month, 1).strftime('%B'),
            f"${income_val:,.2f}",
            f"${expense_val:,.2f}",
            f"${net_val:,.2f}",
            f"{rate:.1f}%"
        ])

    monthly_table = Table(monthly_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch, 1*inch])
    monthly_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    story.append(monthly_table)
    story.append(PageBreak())

    # --- CATEGORY ANALYSIS ---
    story.append(Paragraph("Expense Category Analysis", heading_style))

    category_data = db.execute('''
        SELECT
            category,
            SUM(amount) as total,
            COUNT(*) as count,
            AVG(amount) as avg_amount
        FROM transactions
        WHERE user_id = ? AND date >= ? AND date < ?
        GROUP BY category
        ORDER BY total DESC
    ''', (user_id, start_date, end_date)).fetchall()

    if category_data:
        category_table_data = [['Category', 'Total Spent', '# Transactions', 'Avg/Transaction', '% of Total']]

        for row in category_data:
            percentage = (row['total'] / total_expenses * 100) if total_expenses > 0 else 0
            category_table_data.append([
                row['category'],
                f"${row['total']:,.2f}",
                str(row['count']),
                f"${row['avg_amount']:,.2f}",
                f"{percentage:.1f}%"
            ])

        category_table = Table(category_table_data, colWidths=[1.8*inch, 1.3*inch, 1.2*inch, 1.3*inch, 0.9*inch])
        category_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(category_table)

    # Footer
    story.append(Spacer(1, 0.5*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Budget Planner - Personal Finance Management", footer_style))
    story.append(Paragraph(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_category_report(user_id, category, start_date, end_date):
    """Generate a detailed category analysis report"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=12,
        spaceBefore=12
    )

    # Get database connection
    db = get_db()

    # Get user info
    user = db.execute('SELECT name FROM users WHERE id = ?', (user_id,)).fetchone()
    user_name = user['name'] if user else 'User'

    # Report title
    story.append(Paragraph(f"Category Analysis Report", title_style))
    story.append(Paragraph(f"Category: {category}", styles['Heading2']))
    story.append(Paragraph(f"Period: {start_date} to {end_date}", styles['Normal']))
    story.append(Paragraph(f"Prepared for: {user_name}", styles['Normal']))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    # Get all transactions for this category
    transactions = db.execute('''
        SELECT date, amount, description
        FROM transactions
        WHERE user_id = ? AND category = ? AND date >= ? AND date <= ?
        ORDER BY date DESC
    ''', (user_id, category, start_date, end_date)).fetchall()

    if transactions:
        # Summary statistics
        story.append(Paragraph("Summary Statistics", heading_style))

        total = sum(t['amount'] for t in transactions)
        count = len(transactions)
        avg = total / count if count > 0 else 0

        stats_data = [
            ['Metric', 'Value'],
            ['Total Transactions', str(count)],
            ['Total Spent', f"${total:,.2f}"],
            ['Average Transaction', f"${avg:,.2f}"],
            ['Largest Transaction', f"${max(t['amount'] for t in transactions):,.2f}"],
            ['Smallest Transaction', f"${min(t['amount'] for t in transactions):,.2f}"]
        ]

        stats_table = Table(stats_data, colWidths=[3*inch, 3.5*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 0.3*inch))

        # Transaction details
        story.append(Paragraph("Transaction Details", heading_style))

        # Limit to recent 50 transactions to avoid overly long reports
        display_transactions = transactions[:50]
        trans_data = [['Date', 'Description', 'Amount']]

        for t in display_transactions:
            trans_data.append([
                t['date'],
                t['description'][:40] if t['description'] else 'N/A',
                f"${t['amount']:,.2f}"
            ])

        if len(transactions) > 50:
            trans_data.append(['...', f'({len(transactions) - 50} more transactions)', '...'])

        trans_table = Table(trans_data, colWidths=[1.5*inch, 3.5*inch, 1.5*inch])
        trans_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(trans_table)
    else:
        story.append(Paragraph("No transactions found for this category in the selected period.", styles['Normal']))

    # Footer
    story.append(Spacer(1, 0.5*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Budget Planner - Personal Finance Management", footer_style))
    story.append(Paragraph(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
