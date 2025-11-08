"""
Management command to populate the database with demo data for FJC Pizza
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from accounts.models import User
from products.models import Product
from orders.models import Order, OrderItem, Payment
from system.models import AuditTrail


class Command(BaseCommand):
    help = 'Populate database with demo data for FJC Pizza'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting demo data population...'))

        with transaction.atomic():
            # Create users
            self.create_users()

            # Create products
            self.create_products()

            # Create sample orders
            self.create_orders()

        self.stdout.write(self.style.SUCCESS('✅ Demo data created successfully!'))
        self.stdout.write(self.style.SUCCESS('\nLogin credentials:'))
        self.stdout.write('  Admin: username=admin, password=admin123')
        self.stdout.write('  Cashier: username=cashier, password=cashier123')

    def create_users(self):
        """Create demo users"""
        # Create cashier user
        if not User.objects.filter(username='cashier').exists():
            cashier = User.objects.create_user(
                username='cashier',
                email='cashier@fjcpizza.com',
                password='cashier123',
                first_name='John',
                last_name='Doe',
                role='CASHIER'
            )
            self.stdout.write(f'  ✓ Created cashier user: {cashier.username}')

    def create_products(self):
        """Create demo pizza products"""
        products_data = [
            # Pizzas
            {
                'name': 'Margherita Pizza',
                'description': 'Classic pizza with tomato sauce, mozzarella, and fresh basil',
                'price': Decimal('299.00'),
                'stock': 50,
                'threshold': 10,
                'category': 'Pizza'
            },
            {
                'name': 'Pepperoni Pizza',
                'description': 'Loaded with pepperoni slices and mozzarella cheese',
                'price': Decimal('349.00'),
                'stock': 45,
                'threshold': 10,
                'category': 'Pizza'
            },
            {
                'name': 'Hawaiian Pizza',
                'description': 'Ham, pineapple, and mozzarella cheese',
                'price': Decimal('329.00'),
                'stock': 40,
                'threshold': 10,
                'category': 'Pizza'
            },
            {
                'name': 'Supreme Pizza',
                'description': 'Loaded with pepperoni, sausage, bell peppers, onions, and olives',
                'price': Decimal('399.00'),
                'stock': 35,
                'threshold': 10,
                'category': 'Pizza'
            },
            {
                'name': 'Four Cheese Pizza',
                'description': 'Mozzarella, parmesan, gouda, and cheddar cheese blend',
                'price': Decimal('379.00'),
                'stock': 30,
                'threshold': 10,
                'category': 'Pizza'
            },
            {
                'name': 'BBQ Chicken Pizza',
                'description': 'Grilled chicken, BBQ sauce, onions, and mozzarella',
                'price': Decimal('389.00'),
                'stock': 25,
                'threshold': 10,
                'category': 'Pizza'
            },

            # Sides
            {
                'name': 'Garlic Bread',
                'description': 'Toasted bread with garlic butter and herbs',
                'price': Decimal('89.00'),
                'stock': 100,
                'threshold': 20,
                'category': 'Sides'
            },
            {
                'name': 'Chicken Wings (6pcs)',
                'description': 'Crispy chicken wings with your choice of sauce',
                'price': Decimal('199.00'),
                'stock': 60,
                'threshold': 15,
                'category': 'Sides'
            },
            {
                'name': 'Mozzarella Sticks',
                'description': 'Breaded mozzarella sticks with marinara sauce',
                'price': Decimal('149.00'),
                'stock': 75,
                'threshold': 15,
                'category': 'Sides'
            },
            {
                'name': 'French Fries',
                'description': 'Crispy golden french fries',
                'price': Decimal('79.00'),
                'stock': 120,
                'threshold': 25,
                'category': 'Sides'
            },

            # Drinks
            {
                'name': 'Coca-Cola (500ml)',
                'description': 'Ice-cold Coca-Cola',
                'price': Decimal('49.00'),
                'stock': 200,
                'threshold': 50,
                'category': 'Drinks'
            },
            {
                'name': 'Sprite (500ml)',
                'description': 'Refreshing lemon-lime soda',
                'price': Decimal('49.00'),
                'stock': 180,
                'threshold': 50,
                'category': 'Drinks'
            },
            {
                'name': 'Iced Tea (500ml)',
                'description': 'Fresh brewed iced tea',
                'price': Decimal('39.00'),
                'stock': 150,
                'threshold': 40,
                'category': 'Drinks'
            },
            {
                'name': 'Bottled Water (500ml)',
                'description': 'Pure mineral water',
                'price': Decimal('29.00'),
                'stock': 300,
                'threshold': 75,
                'category': 'Drinks'
            },

            # Desserts
            {
                'name': 'Chocolate Brownie',
                'description': 'Warm chocolate brownie with vanilla ice cream',
                'price': Decimal('129.00'),
                'stock': 40,
                'threshold': 10,
                'category': 'Desserts'
            },
            {
                'name': 'Tiramisu',
                'description': 'Classic Italian coffee-flavored dessert',
                'price': Decimal('149.00'),
                'stock': 30,
                'threshold': 8,
                'category': 'Desserts'
            },
        ]

        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults=product_data
            )
            if created:
                self.stdout.write(f'  ✓ Created product: {product.name}')

    def create_orders(self):
        """Create sample orders for demonstration"""
        admin = User.objects.get(username='admin')
        products = list(Product.objects.all())  # Get all products

        if not products or len(products) < 4:
            self.stdout.write(self.style.WARNING('  ⚠ Not enough products found, skipping order creation'))
            return

        # Create completed order (online payment)
        order1 = Order.objects.create(
            customer_name='Alice Johnson',
            table_number='T01',
            status='FINISHED',
            notes='Extra napkins please'
        )

        OrderItem.objects.create(
            order=order1,
            product=products[0],
            quantity=2
        )
        if len(products) > 6:
            OrderItem.objects.create(
                order=order1,
                product=products[6],
                quantity=1
            )

        order1.calculate_total()

        Payment.objects.create(
            order=order1,
            method='ONLINE',
            status='SUCCESS',
            amount=order1.total_amount,
            processed_by=admin
        )

        self.stdout.write(f'  ✓ Created order: {order1.order_number} (FINISHED)')

        # Create in-progress order (cash payment confirmed)
        order2 = Order.objects.create(
            customer_name='Bob Smith',
            table_number='T02',
            status='IN_PROGRESS'
        )

        OrderItem.objects.create(
            order=order2,
            product=products[1],
            quantity=1
        )
        if len(products) > 7:
            OrderItem.objects.create(
                order=order2,
                product=products[7],
                quantity=1
            )

        order2.calculate_total()

        Payment.objects.create(
            order=order2,
            method='CASH',
            status='SUCCESS',
            amount=order2.total_amount,
            processed_by=admin
        )

        self.stdout.write(f'  ✓ Created order: {order2.order_number} (IN_PROGRESS)')

        # Create pending order (waiting for cash payment)
        order3 = Order.objects.create(
            customer_name='Carol Williams',
            table_number='T03',
            status='PENDING'
        )

        OrderItem.objects.create(
            order=order3,
            product=products[2],
            quantity=1
        )
        if len(products) > 10:
            OrderItem.objects.create(
                order=order3,
                product=products[10],
                quantity=2
            )

        order3.calculate_total()

        Payment.objects.create(
            order=order3,
            method='CASH',
            status='PENDING',
            amount=order3.total_amount
        )

        self.stdout.write(f'  ✓ Created order: {order3.order_number} (PENDING)')

        # Create another completed order
        order4 = Order.objects.create(
            customer_name='David Brown',
            table_number='T04',
            status='FINISHED'
        )

        OrderItem.objects.create(
            order=order4,
            product=products[3],
            quantity=1
        )
        if len(products) > 8:
            OrderItem.objects.create(
                order=order4,
                product=products[8],
                quantity=1
            )
        if len(products) > 11:
            OrderItem.objects.create(
                order=order4,
                product=products[11],
                quantity=2
            )

        order4.calculate_total()

        Payment.objects.create(
            order=order4,
            method='ONLINE',
            status='SUCCESS',
            amount=order4.total_amount,
            processed_by=admin
        )

        self.stdout.write(f'  ✓ Created order: {order4.order_number} (FINISHED)')
