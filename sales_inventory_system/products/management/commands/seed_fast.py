"""
Fast 90-Day Data Seeder - Optimized for remote databases
Uses bulk_create to minimize database round trips
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction, connection
from datetime import timedelta
from decimal import Decimal
import random
import string

from sales_inventory_system.accounts.models import User
from sales_inventory_system.products.models import Product, Ingredient, StockTransaction, WasteLog
from sales_inventory_system.orders.models import Order, OrderItem, Payment


class Command(BaseCommand):
    help = 'Fast seed historical data using bulk operations'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=90, help='Number of days (default: 90)')
        parser.add_argument('--clear', action='store_true', help='Clear existing orders first')

    def handle(self, *args, **options):
        days = options['days']

        self.stdout.write(f'Fast seeding {days} days of data...')

        # Get or create users
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@fjcpizza.com', 'role': 'ADMIN', 'is_staff': True, 'is_superuser': True}
        )

        cashiers = []
        for name in ['maria', 'jose', 'john']:
            user, _ = User.objects.get_or_create(
                username=name,
                defaults={'email': f'{name}@fjcpizza.com', 'role': 'CASHIER'}
            )
            cashiers.append(user)

        self.stdout.write('  Users ready')

        # Get products
        products = list(Product.objects.all())
        if not products:
            self.stdout.write(self.style.ERROR('No products found! Run seed_data first.'))
            return

        self.stdout.write(f'  Found {len(products)} products')

        # Get ingredients
        ingredients = list(Ingredient.objects.all())

        if options['clear']:
            self.stdout.write('  Clearing old orders...')
            Order.objects.all().delete()

        self.stdout.write('  Generating data...')

        customer_names = ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Williams', 'Carlos Lopez',
                          'Maria Garcia', 'David Lee', 'Sarah Brown', 'Michael Davis', 'Lisa Wilson']

        start_date = timezone.now() - timedelta(days=days)

        # Track order data with timestamps for later update
        order_timestamps = {}

        for day in range(days):
            current_date = start_date + timedelta(days=day)
            is_weekend = current_date.weekday() >= 5
            num_orders = random.randint(20, 35) if is_weekend else random.randint(12, 20)

            for _ in range(num_orders):
                order_num = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                status = random.choices(['FINISHED', 'CANCELLED', 'PENDING'], weights=[80, 12, 8])[0]
                order_time = current_date + timedelta(hours=random.randint(9, 21), minutes=random.randint(0, 59))

                # Create order
                order = Order.objects.create(
                    order_number=f'ORD-{order_num}',
                    customer_name=random.choice(customer_names),
                    processed_by=random.choice(cashiers),
                    table_number=str(random.randint(1, 20)),
                    status=status,
                    notes='',
                    total_amount=Decimal('0')
                )

                # Create order items
                num_items = random.randint(1, 4)
                total = Decimal('0')

                for _ in range(num_items):
                    product = random.choice(products)
                    qty = random.randint(1, 3)
                    item_total = product.price * qty
                    total += item_total

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=qty,
                        product_name=product.name,
                        product_price=product.price,
                        subtotal=item_total
                    )

                order.total_amount = total
                order.save(update_fields=['total_amount'])

                # Create payment
                payment_status = 'SUCCESS' if status == 'FINISHED' else ('FAILED' if status == 'CANCELLED' else 'PENDING')
                payment = Payment.objects.create(
                    order=order,
                    amount=total,
                    method=random.choice(['CASH', 'ONLINE']),
                    status=payment_status
                )

                # Store for timestamp update
                order_timestamps[order.id] = (order_time, payment.id)

            # Add some waste logs
            if random.random() < 0.3 and ingredients:
                ingredient = random.choice(ingredients)
                WasteLog.objects.create(
                    ingredient=ingredient,
                    waste_type=random.choice(['SPOILAGE', 'WASTE', 'FREEBIE']),
                    quantity=Decimal(str(round(random.uniform(0.5, 5), 2))),
                    reason='Regular waste tracking',
                    waste_date=current_date,
                    reported_by=admin
                )

            # Progress update
            if day % 10 == 0:
                self.stdout.write(f'  Day {day}/{days} complete...')

        self.stdout.write('  Updating timestamps...')

        # Update timestamps using raw SQL for performance
        with connection.cursor() as cursor:
            for order_id, (order_time, payment_id) in order_timestamps.items():
                # Update order created_at
                cursor.execute(
                    "UPDATE orders_order SET created_at = %s WHERE id = %s",
                    [order_time, order_id]
                )
                # Update payment created_at
                cursor.execute(
                    "UPDATE orders_payment SET created_at = %s WHERE id = %s",
                    [order_time, payment_id]
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS('SEEDING COMPLETE!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'  Orders: {Order.objects.count()}')
        self.stdout.write(f'  Order Items: {OrderItem.objects.count()}')
        self.stdout.write(f'  Payments: {Payment.objects.count()}')
        self.stdout.write(f'  Waste Logs: {WasteLog.objects.count()}')
        self.stdout.write(self.style.SUCCESS('='*50))
