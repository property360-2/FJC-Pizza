"""
System Automation Engine for FCJ Pizza

Purpose:
- Automates background inventory & sales management workflows.
- Contains two primary background routines:
  1. Stale Order Auto-Cancellation: Automatically cancels PENDING orders older than 30 minutes.
  2. End-of-Day Sales Report: Compiles daily performance metrics and emails the management team.

Broader System Integration:
- Can be triggered manually from developer tools / admin views.
- Runs as an asynchronous background thread inside Django's main process, ensuring
  constant reliability without adding complex scheduler packages in local dev/demo environments.
"""

import os
import time
import logging
import threading
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.db.models import Sum, Count, Case, When, Value

from sales_inventory_system.orders.models import Order, Payment, OrderItem
from sales_inventory_system.system.models import AuditTrail

logger = logging.getLogger(__name__)

# Track thread state so we can stop it cleanly if Django reloads
_automation_thread_running = False

def cancel_stale_orders():
    """
    Scans the database for orders with 'PENDING' status that were created more than 30 minutes ago,
    marks them as 'EXPIRED', and logs each event in the Audit Trail.
    
    Returns:
        int: Number of cancelled stale orders.
    """
    logger.info("Automation: Starting stale orders cancellation check...")
    try:
        # Define the threshold (e.g., 30 minutes)
        stale_threshold = timezone.now() - timedelta(minutes=30)
        
        # Get pending orders created before the threshold
        stale_orders = Order.objects.filter(
            status='PENDING',
            created_at__lt=stale_threshold
        )
        
        count = 0
        for order in stale_orders:
            with transaction.atomic():
                order.status = 'EXPIRED'
                order.save()
                
                # Log to Audit Trail
                AuditTrail.objects.create(
                    user=None,  # System-generated action
                    action='UPDATE',
                    model_name='Order',
                    record_id=order.id,
                    description=f"🕒 AUTO-EXPIRE: Order '{order.order_number}' automatically expired after sitting in PENDING for >30 minutes."
                )
                count += 1
                
        if count > 0:
            logger.warning(f"Automation: Expired {count} stale pending orders.")
        else:
            logger.info("Automation: No stale pending orders found.")
            
        return count
    except Exception as e:
        logger.error(f"Automation error in cancel_stale_orders: {e}")
        return 0


def send_online_receipt(order):
    """
    Sends a beautiful HTML and plain text online receipt to the customer's email
    if the customer provided an email address during checkout.
    
    Accepts:
        order: An Order model instance.
    """
    if not order.customer_email:
        logger.debug(f"No customer email specified for order {order.order_number}. Skipping receipt.")
        return False
        
    logger.info(f"Automation: Dispatching online receipt for order {order.order_number} to {order.customer_email}...")
    
    try:
        # Build items table
        items_html = ""
        items_text = ""
        
        for item in order.items.all():
            items_text += f"• {item.quantity}x {item.product_name} - ₱{item.subtotal:.2f}\n"
            items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{item.quantity}x {item.product_name}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">₱{item.subtotal:.2f}</td>
            </tr>
            """
            
        subject = f"🍕 [FCJ Pizza] Online Receipt - Order {order.order_number}"
        
        text_message = (
            f"Thank you for dining with FCJ Pizza!\n\n"
            f"Here is the online receipt for your order.\n\n"
            f"Order Details:\n"
            f"--------------\n"
            f"Order Number: {order.order_number}\n"
            f"Customer: {order.customer_name or 'Valued Customer'}\n"
            f"Table Number: {order.table_number or 'Takeout / No Table'}\n"
            f"Date/Time: {order.created_at.strftime('%B %d, %Y %I:%M %p')}\n\n"
            f"Items:\n"
            f"------\n"
            f"{items_text}\n"
            f"--------------------------------------------------\n"
            f"Total Amount: ₱{order.total_amount:.2f}\n\n"
            f"We hope you enjoy your meal! See you again soon.\n"
        )
        
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; background-color: #fafafa; padding: 20px;">
            <div style="max-width: 500px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 12px; border: 1px solid #eef0f2; box-shadow: 0 8px 24px rgba(0,0,0,0.04);">
                <!-- Header -->
                <div style="text-align: center; border-bottom: 2px dashed #eef0f2; padding-bottom: 20px; margin-bottom: 20px;">
                    <span style="font-size: 40px; display: block; margin-bottom: 10px;">🍕</span>
                    <h2 style="color: #d32f2f; margin: 0; font-weight: 700; font-family: 'Outfit', sans-serif;">FCJ Pizza Online Receipt</h2>
                    <p style="color: #777; margin: 5px 0 0 0; font-size: 13px;">Thank you for your purchase!</p>
                </div>
                
                <!-- Order Summary -->
                <table style="width: 100%; font-size: 14px; margin-bottom: 20px;">
                    <tr>
                        <td style="color: #888; padding: 3px 0;">Order Number:</td>
                        <td style="font-weight: bold; text-align: right; padding: 3px 0;">{order.order_number}</td>
                    </tr>
                    <tr>
                        <td style="color: #888; padding: 3px 0;">Customer Name:</td>
                        <td style="font-weight: bold; text-align: right; padding: 3px 0;">{order.customer_name or 'Valued Customer'}</td>
                    </tr>
                    <tr>
                        <td style="color: #888; padding: 3px 0;">Table Number:</td>
                        <td style="font-weight: bold; text-align: right; padding: 3px 0;">{order.table_number or 'Takeout / No Table'}</td>
                    </tr>
                    <tr>
                        <td style="color: #888; padding: 3px 0;">Date:</td>
                        <td style="font-weight: bold; text-align: right; padding: 3px 0;">{order.created_at.strftime('%B %d, %Y %I:%M %p')}</td>
                    </tr>
                </table>
                
                <!-- Items Table -->
                <h4 style="color: #1976d2; border-bottom: 1px solid #eee; padding-bottom: 5px; margin-top: 25px; margin-bottom: 10px;">Order Items</h4>
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                    {items_html}
                    <tr style="font-weight: bold; font-size: 16px;">
                        <td style="padding: 15px 10px 10px 10px; color: #d32f2f;">Total Amount</td>
                        <td style="padding: 15px 10px 10px 10px; text-align: right; color: #d32f2f;">₱{order.total_amount:.2f}</td>
                    </tr>
                </table>
                
                <!-- Footer Info -->
                <div style="margin-top: 30px; padding-top: 20px; border-top: 2px dashed #eef0f2; text-align: center; font-size: 12px; color: #888;">
                    <p style="margin: 0;">If you have any questions about this receipt, please contact support@fcjpizza.com.</p>
                    <p style="margin: 5px 0 0 0; font-weight: bold;">FCJ Pizza - Deliciousness in Every Slice!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        send_mail(
            subject,
            text_message,
            None,
            [order.customer_email],
            html_message=html_message,
            fail_silently=False
        )
        
        # Log to Audit Trail
        AuditTrail.objects.create(
            user=None,
            action='UPDATE',
            model_name='Order',
            record_id=order.id,
            description=f"📧 RECEIPT SENT: Automated online receipt emailed for order {order.order_number} to {order.customer_email}."
        )
        
        logger.warning(f"Automation: Sent online receipt for order {order.order_number} to {order.customer_email}")
        return True
    except Exception as err:
        logger.error(f"Error sending receipt email: {err}")
        return False



def generate_daily_sales_report(date_to_report=None):
    """
    Compiles daily sales and inventory figures, drafts an elegant HTML/text report,
    simulates an email dispatch, and creates a system audit record.
    
    Accepts:
        date_to_report: A datetime.date object. Defaults to today's date.
        
    Returns:
        dict: Compiled sales metrics.
    """
    if date_to_report is None:
        date_to_report = timezone.now().date()
        
    logger.info(f"Automation: Compiling daily sales report for {date_to_report}...")
    
    try:
        # Define start and end of the targeted day
        day_start = timezone.make_aware(datetime.combine(date_to_report, datetime.min.time()))
        day_end = timezone.make_aware(datetime.combine(date_to_report, datetime.max.time()))
        
        # Aggregate revenue
        revenue_data = Payment.objects.filter(
            status='SUCCESS',
            created_at__range=(day_start, day_end)
        ).aggregate(
            total_revenue=Sum('amount'),
            payment_count=Count('id')
        )
        
        total_revenue = revenue_data['total_revenue'] or Decimal('0.00')
        payment_count = revenue_data['payment_count'] or 0
        
        # Aggregate order stats
        order_stats = Order.objects.filter(
            created_at__range=(day_start, day_end)
        ).aggregate(
            total_orders=Count('id'),
            completed_orders=Count(Case(When(status='FINISHED', then=1))),
            expired_orders=Count(Case(When(status='EXPIRED', then=1))),
            cancelled_orders=Count(Case(When(status='CANCELLED', then=1))),
        )
        
        total_orders = order_stats['total_orders'] or 0
        completed_orders = order_stats['completed_orders'] or 0
        expired_orders = order_stats['expired_orders'] or 0
        cancelled_orders = order_stats['cancelled_orders'] or 0
        
        # Top-selling items for today
        top_items_qs = OrderItem.objects.filter(
            order__payment__status='SUCCESS',
            created_at__range=(day_start, day_end)
        ).values('product_name').annotate(
            qty=Sum('quantity'),
            rev=Sum('subtotal')
        ).order_by('-qty')[:5]
        
        top_items_html = ""
        top_items_text = ""
        for i, item in enumerate(top_items_qs, 1):
            top_items_text += f"{i}. {item['product_name']}: {item['qty']} sold (₱{item['rev']:.2f})\n"
            top_items_html += f"<tr><td style='padding: 8px; border-bottom: 1px solid #eee;'>{i}</td><td style='padding: 8px; border-bottom: 1px solid #eee;'>{item['product_name']}</td><td style='padding: 8px; border-bottom: 1px solid #eee;'>{item['qty']}</td><td style='padding: 8px; border-bottom: 1px solid #eee; text-align: right;'>₱{item['rev']:.2f}</td></tr>"
            
        if not top_items_html:
            top_items_text = "No sales recorded today."
            top_items_html = "<tr><td colspan='4' style='text-align: center; padding: 12px; color: #777;'>No sales recorded today.</td></tr>"

        # Log daily report in AuditTrail
        AuditTrail.objects.create(
            user=None,
            action='CREATE',
            model_name='Report',
            record_id=int(date_to_report.strftime('%Y%m%d')),
            description=f"📊 DAILY REPORT: Automated daily summary compiled. Revenue: ₱{total_revenue:.2f} | Completed: {completed_orders} / {total_orders} orders."
        )
        
        # Send Daily Report Email (simulated via console printer in dev)
        subject = f"📊 [FCJ Pizza] Daily Sales Summary - {date_to_report.strftime('%B %d, %Y')}"
        
        text_message = (
            f"FCJ Pizza End-of-Day Daily Sales Summary\n"
            f"Date: {date_to_report.strftime('%A, %B %d, %Y')}\n"
            f"==================================================\n\n"
            f"Financial Highlights:\n"
            f"---------------------\n"
            f"• Total Revenue: ₱{total_revenue:.2f}\n"
            f"• Confirmed Paid Transactions: {payment_count}\n\n"
            f"Order Breakdown:\n"
            f"----------------\n"
            f"• Total Placed Orders: {total_orders}\n"
            f"• Completed/Fulfilled: {completed_orders}\n"
            f"• Expired (Stale): {expired_orders}\n"
            f"• Cancelled: {cancelled_orders}\n\n"
            f"Top Selling Items Today:\n"
            f"-----------------------\n"
            f"{top_items_text}\n"
            f"This is an automated system-generated report. No action required.\n"
        )
        
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.5; padding: 10px; background-color: #f9f9f9;">
            <div style="max-width: 600px; margin: 0 auto; padding: 25px; border: 1px solid #e0e0e0; border-radius: 12px; background-color: #ffffff; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                <div style="text-align: center; border-bottom: 2px solid #d32f2f; padding-bottom: 15px; margin-bottom: 20px;">
                    <span style="font-size: 28px;">🍕</span>
                    <h2 style="color: #d32f2f; margin: 5px 0 0 0; font-weight: 700; font-family: 'Outfit', sans-serif;">FCJ Pizza Daily Performance</h2>
                    <p style="color: #666; margin: 5px 0 0 0;">Automated System-Generated Insights</p>
                </div>
                <p><strong>Reporting Date:</strong> {date_to_report.strftime('%A, %B %d, %Y')}</p>
                
                <h3 style="color: #1976d2; border-left: 4px solid #1976d2; padding-left: 8px; margin-top: 25px;">💰 Financial Performance</h3>
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <tr style="background-color: #f7f7f7;">
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #eee; font-weight: 600;">Metric</th>
                        <th style="padding: 10px; text-align: right; border-bottom: 2px solid #eee; font-weight: 600;">Value</th>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">Total Daily Revenue</td>
                        <td style="padding: 10px; text-align: right; border-bottom: 1px solid #eee; font-weight: bold; color: #2e7d32; font-size: 18px;">₱{total_revenue:.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">Paid Transactions</td>
                        <td style="padding: 10px; text-align: right; border-bottom: 1px solid #eee;">{payment_count}</td>
                    </tr>
                </table>

                <h3 style="color: #1976d2; border-left: 4px solid #1976d2; padding-left: 8px; margin-top: 25px;">📦 Order Volumes</h3>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-top: 10px; background-color: #fcfcfc; padding: 15px; border-radius: 8px; border: 1px solid #f0f0f0;">
                    <div><strong>Total Placed:</strong> {total_orders}</div>
                    <div><strong>Completed/Fulfilled:</strong> <span style="color: #2e7d32; font-weight: bold;">{completed_orders}</span></div>
                    <div><strong>Auto-Expired (Stale):</strong> {expired_orders}</div>
                    <div><strong>Cancelled:</strong> {cancelled_orders}</div>
                </div>

                <h3 style="color: #1976d2; border-left: 4px solid #1976d2; padding-left: 8px; margin-top: 25px;">🍕 Top Sellers</h3>
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <tr style="background-color: #f7f7f7;">
                        <th style="padding: 8px; text-align: left; border-bottom: 2px solid #eee;">Rank</th>
                        <th style="padding: 8px; text-align: left; border-bottom: 2px solid #eee;">Item Name</th>
                        <th style="padding: 8px; text-align: left; border-bottom: 2px solid #eee;">Qty</th>
                        <th style="padding: 8px; text-align: right; border-bottom: 2px solid #eee;">Total Revenue</th>
                    </tr>
                    {top_items_html}
                </table>
                
                <hr style="margin-top: 35px; border: 0; border-top: 1px solid #eee;">
                <p style="font-size: 11px; color: #888; text-align: center; margin: 15px 0 0 0;">
                    FCJ Pizza Automation Engine • All systems nominal.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Get active admin email addresses dynamically instead of hardcoding
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin_emails = list(User.objects.filter(
            role='ADMIN', 
            is_active=True, 
            is_archived=False
        ).exclude(email='').values_list('email', flat=True))
        
        # Fallback to default email if no active admins with emails exist in system
        if not admin_emails:
            admin_emails = ['junalvior21@gmail.com']

        send_mail(
            subject,
            text_message,
            None,
            admin_emails,
            html_message=html_message,
            fail_silently=True
        )
        logger.warning(f"Automation: Sent end-of-day sales report for {date_to_report} to {admin_emails}.")
        
        return {
            'date': date_to_report,
            'revenue': total_revenue,
            'orders': total_orders,
            'completed': completed_orders
        }
    except Exception as e:
        logger.error(f"Automation error in generate_daily_sales_report: {e}")
        return {}


def _run_background_loop():
    """
    Main loop executed in a background daemon thread.
    Periodically triggers stale order cancellations and checks if it's the end of the day to send reports.
    """
    global _automation_thread_running
    logger.info("Automation background daemon thread successfully started.")
    
    # Track the last day a daily report was generated to prevent multiple runs per day
    last_report_date = None
    
    while _automation_thread_running:
        try:
            # 1. Run stale orders cancellation
            cancel_stale_orders()
            
            # 2. Check for daily sales report at 11:50 PM (23:50)
            now = timezone.now()
            today_date = now.date()
            
            if now.hour == 23 and now.minute >= 50 and last_report_date != today_date:
                # Compile and send daily report
                generate_daily_sales_report(today_date)
                last_report_date = today_date
                
        except Exception as err:
            logger.error(f"Error in automation background loop: {err}")
            
        # Sleep for 5 minutes (300 seconds)
        time.sleep(300)

    logger.info("Automation background daemon thread stopped.")


def start_automation_engine():
    """
    Spawns and starts the automation loop thread if it is not already running.
    """
    global _automation_thread_running
    if _automation_thread_running:
        return
        
    # Prevent running in the auto-reloader sub-process to avoid dual execution
    if os.environ.get('RUN_MAIN') != 'true':
        logger.debug("Automation: Reloader process ignored.")
        return
        
    _automation_thread_running = True
    thread = threading.Thread(target=_run_background_loop, name="FCJPizzaAutomationEngine")
    thread.daemon = True
    thread.start()
