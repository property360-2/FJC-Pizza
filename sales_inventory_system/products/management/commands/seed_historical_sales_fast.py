from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
import uuid
from datetime import timedelta

from sales_inventory_system.accounts.models import User
from sales_inventory_system.products.models import Product
from sales_inventory_system.orders.models import Order, OrderItem, Payment


class Command(BaseCommand):
    help = 'Generate historical sales data FAST using bulk operations (90 days)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days of historical data to generate (default: 90)'
        )

    def handle(self, *args, **options):
        days = options['days']

        self.stdout.write(self.style.SUCCESS(f'Generating {days} days of historical sales data (FAST mode)...'))

        # Get users and products
        cashier_users = list(User.objects.filter(role='CASHIER'))
        if not cashier_users:
            self.stdout.write(self.style.ERROR('No cashier users found. Run seed_data first.'))
            return

        products = list(Product.objects.filter(is_archived=False))
        if not products:
            self.stdout.write(self.style.ERROR('No products found. Run seed_data first.'))
            return

        pizza_products = [p for p in products if 'pizza' in p.name.lower()]
        beverage_products = [p for p in products if p.category == 'Beverages']
        side_products = [p for p in products if p.category == 'Sides']

        # Prepare bulk data
        orders_to_create = []
        items_to_create = []
        payments_to_create = []

        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        self.stdout.write('Preparing data...')
        total_revenue = Decimal('0.00')

        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            day_of_week = current_date.weekday()

            # Weekend = more orders
            if day_of_week in [4, 5, 6]:
                base_orders = random.randint(25, 40)
            else:
                base_orders = random.randint(15, 25)

            # Trend
            trend_factor = 1 + (day_offset / days) * 0.3
            num_orders = int(base_orders * trend_factor)
            num_orders = max(10, num_orders + random.randint(-5, 5))

            for _ in range(num_orders):
                # Order time
                if random.random() < 0.4:
                    hour = random.randint(11, 14)
                else:
                    hour = random.randint(17, 21)

                minute = random.randint(0, 59)
                order_time = current_date.replace(hour=hour, minute=minute, second=random.randint(0, 59))

                # Create order (not saved yet)
                customer_name = f'{random.choice(["John", "Jane", "Maria", "Carlos", "Sarah"])} {random.choice(["Smith", "Garcia", "Johnson", "Lopez", "Brown"])}'
                order = Order(
                    order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",  # Generate order number
                    customer_name=customer_name,
                    table_number=str(random.randint(1, 25)),
                    status='FINISHED',
                    notes='Historical order',
                    processed_by=random.choice(cashier_users),
                    created_at=order_time,
                    total_amount=Decimal('0.00')  # Will update later
                )
                orders_to_create.append(order)

        # Bulk create orders
        self.stdout.write('Creating orders...')
        Order.objects.bulk_create(orders_to_create, batch_size=500)
        self.stdout.write(f'  Created {len(orders_to_create)} orders')

        # Get all created orders
        created_orders = list(Order.objects.filter(
            created_at__gte=start_date,
            notes='Historical order'
        ).order_by('created_at'))

        # Create items and payments
        self.stdout.write('Creating order items and payments...')
        order_totals = {}

        for order in created_orders:
            # Items for this order
            num_items = random.choices([1, 2, 3, 4], weights=[0.3, 0.4, 0.2, 0.1])[0]

            order_total = Decimal('0.00')

            # Pizza
            if pizza_products:
                pizza = random.choice(pizza_products)
                quantity = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
                subtotal = pizza.price * quantity
                order_total += subtotal

                items_to_create.append(OrderItem(
                    order=order,
                    product=pizza,
                    product_name=pizza.name,
                    product_price=pizza.price,
                    quantity=quantity,
                    subtotal=subtotal
                ))

            # Additional items
            for _ in range(num_items - 1):
                if random.random() < 0.6 and beverage_products:
                    product = random.choice(beverage_products)
                elif side_products:
                    product = random.choice(side_products)
                else:
                    product = random.choice(products)

                quantity = random.choices([1, 2], weights=[0.8, 0.2])[0]
                subtotal = product.price * quantity
                order_total += subtotal

                items_to_create.append(OrderItem(
                    order=order,
                    product=product,
                    product_name=product.name,
                    product_price=product.price,
                    quantity=quantity,
                    subtotal=subtotal
                ))

            order_totals[order.id] = order_total
            total_revenue += order_total

            # Payment
            payment_method = random.choices(['CASH', 'ONLINE', 'CARD'], weights=[0.5, 0.3, 0.2])[0]
            payments_to_create.append(Payment(
                order=order,
                method=payment_method,
                status='SUCCESS',
                amount=order_total,
                reference_number=f'HIST-{order.order_number}',
                processed_by=random.choice(cashier_users),
                created_at=order.created_at + timedelta(minutes=random.randint(1, 5))
            ))

        # Bulk create items and payments
        OrderItem.objects.bulk_create(items_to_create, batch_size=1000)
        self.stdout.write(f'  Created {len(items_to_create)} order items')

        Payment.objects.bulk_create(payments_to_create, batch_size=500)
        self.stdout.write(f'  Created {len(payments_to_create)} payments')

        # Update order totals
        self.stdout.write('Updating order totals...')
        for order in created_orders:
            order.total_amount = order_totals.get(order.id, Decimal('0.00'))
        Order.objects.bulk_update(created_orders, ['total_amount'], batch_size=500)

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('Historical Sales Data Generation Complete!'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(f'  Days of data: {days}')
        self.stdout.write(f'  Orders created: {len(created_orders):,}')
        self.stdout.write(f'  Total revenue: ₱{total_revenue:,.2f}')
        self.stdout.write(f'  Average daily revenue: ₱{(total_revenue / days):,.2f}')
        self.stdout.write(f'  Average order value: ₱{(total_revenue / len(created_orders)):,.2f}')
        self.stdout.write('')
        self.stdout.write('You can now test the forecasting at:')
        self.stdout.write('  http://127.0.0.1:8000/analytics/forecast/')
        self.stdout.write('')
