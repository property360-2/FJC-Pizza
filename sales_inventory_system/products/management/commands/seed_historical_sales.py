from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta, datetime

from sales_inventory_system.accounts.models import User
from sales_inventory_system.products.models import Product
from sales_inventory_system.orders.models import Order, OrderItem, Payment


class Command(BaseCommand):
    help = 'Generate realistic historical sales data for forecasting (90 days)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days of historical data to generate (default: 90)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing orders before seeding'
        )

    def handle(self, *args, **options):
        days = options['days']
        clear_existing = options['clear']

        self.stdout.write(self.style.SUCCESS(f'Generating {days} days of historical sales data...'))

        # Clear existing data if requested
        if clear_existing:
            self.stdout.write('Clearing existing orders and payments...')
            Order.objects.all().delete()
            Payment.objects.all().delete()
            self.stdout.write(self.style.WARNING('  Cleared all existing orders and payments'))

        # Get or create users
        cashier_users = self.get_or_create_users()
        if not cashier_users:
            self.stdout.write(self.style.ERROR('No cashier users found. Run seed_data first.'))
            return

        # Get products
        products = list(Product.objects.filter(is_archived=False))
        if not products:
            self.stdout.write(self.style.ERROR('No products found. Run seed_data first.'))
            return

        pizza_products = [p for p in products if 'pizza' in p.name.lower()]
        beverage_products = [p for p in products if p.category == 'Beverages']
        side_products = [p for p in products if p.category == 'Sides']

        # Generate historical orders
        self.stdout.write('Generating historical sales...')
        orders_created = 0
        total_revenue = Decimal('0.00')

        # Calculate start date
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Generate orders for each day
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday

            # Determine base number of orders for the day
            # Weekends (Fri, Sat, Sun) are busier
            if day_of_week in [4, 5, 6]:  # Friday, Saturday, Sunday
                base_orders = random.randint(25, 40)
            else:  # Weekdays
                base_orders = random.randint(15, 25)

            # Add seasonal trend (gradually increasing over time)
            trend_factor = 1 + (day_offset / days) * 0.3  # 30% growth over period
            num_orders = int(base_orders * trend_factor)

            # Add some random variation
            num_orders = max(10, num_orders + random.randint(-5, 5))

            # Generate orders throughout the day
            for _ in range(num_orders):
                # Create realistic order times (lunch: 11am-2pm, dinner: 5pm-9pm)
                if random.random() < 0.4:  # 40% lunch orders
                    hour = random.randint(11, 14)
                else:  # 60% dinner orders
                    hour = random.randint(17, 21)

                minute = random.randint(0, 59)
                order_time = current_date.replace(
                    hour=hour,
                    minute=minute,
                    second=random.randint(0, 59)
                )

                # Create order
                order = Order.objects.create(
                    customer_name=self.generate_customer_name(),
                    table_number=str(random.randint(1, 25)),
                    status='FINISHED',
                    notes='Historical order',
                    processed_by=random.choice(cashier_users),
                    created_at=order_time
                )

                # Add items to order
                num_items = random.choices(
                    [1, 2, 3, 4],
                    weights=[0.3, 0.4, 0.2, 0.1]  # Most orders have 1-2 items
                )[0]

                # Always include at least one pizza
                if pizza_products:
                    pizza = random.choice(pizza_products)
                    quantity = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
                    OrderItem.objects.create(
                        order=order,
                        product=pizza,
                        product_name=pizza.name,
                        product_price=pizza.price,
                        quantity=quantity,
                        subtotal=pizza.price * quantity
                    )

                # Add additional items
                for _ in range(num_items - 1):
                    # Mix of beverages and sides
                    if random.random() < 0.6 and beverage_products:
                        product = random.choice(beverage_products)
                    elif side_products:
                        product = random.choice(side_products)
                    else:
                        product = random.choice(products)

                    quantity = random.choices([1, 2], weights=[0.8, 0.2])[0]
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        product_price=product.price,
                        quantity=quantity,
                        subtotal=product.price * quantity
                    )

                # Calculate order total
                order.calculate_total()

                # Create successful payment
                payment_method = random.choices(
                    ['CASH', 'ONLINE', 'CARD'],
                    weights=[0.5, 0.3, 0.2]
                )[0]

                Payment.objects.create(
                    order=order,
                    method=payment_method,
                    status='SUCCESS',
                    amount=order.total_amount,
                    reference_number=f'HIST-{order.order_number}',
                    processed_by=random.choice(cashier_users),
                    created_at=order_time + timedelta(minutes=random.randint(1, 5))
                )

                orders_created += 1
                total_revenue += order.total_amount

            # Progress indicator
            if (day_offset + 1) % 10 == 0:
                progress = ((day_offset + 1) / days) * 100
                self.stdout.write(f'  Progress: {progress:.0f}% ({day_offset + 1}/{days} days)')

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('Historical Sales Data Generation Complete!'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(f'  Days of data: {days}')
        self.stdout.write(f'  Orders created: {orders_created:,}')
        self.stdout.write(f'  Total revenue: ₱{total_revenue:,.2f}')
        self.stdout.write(f'  Average daily revenue: ₱{(total_revenue / days):,.2f}')
        self.stdout.write(f'  Average order value: ₱{(total_revenue / orders_created):,.2f}')
        self.stdout.write('')
        self.stdout.write('You can now test the forecasting at:')
        self.stdout.write('  http://127.0.0.1:8000/analytics/forecast/')
        self.stdout.write('')

    def get_or_create_users(self):
        """Get existing cashier users or create default ones"""
        cashier_users = list(User.objects.filter(role='CASHIER'))

        if not cashier_users:
            # Create default cashier if none exist
            self.stdout.write('Creating default cashier user...')
            cashier = User.objects.create(
                username='cashier1',
                first_name='Maria',
                last_name='Garcia',
                email='cashier1@fjcpizza.com',
                phone='555-0002',
                role='CASHIER',
            )
            cashier.set_password('cashier123')
            cashier.save()
            cashier_users.append(cashier)
            self.stdout.write('  Created default cashier: cashier1')

        return cashier_users

    def generate_customer_name(self):
        """Generate random customer name"""
        first_names = [
            'John', 'Jane', 'Michael', 'Emily', 'David', 'Sarah',
            'Robert', 'Lisa', 'James', 'Maria', 'Carlos', 'Ana',
            'Joseph', 'Linda', 'Thomas', 'Patricia', 'Daniel', 'Jennifer',
            'Mark', 'Jessica', 'Paul', 'Nancy', 'Steven', 'Karen',
            'Andrew', 'Betty', 'Joshua', 'Helen', 'Kenneth', 'Sandra'
        ]
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia',
            'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez',
            'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore',
            'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson', 'White',
            'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson'
        ]

        return f'{random.choice(first_names)} {random.choice(last_names)}'
