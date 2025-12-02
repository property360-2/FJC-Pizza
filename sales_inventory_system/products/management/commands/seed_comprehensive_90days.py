"""
Comprehensive 90-Day Historical Data Seeder for FJC-Pizza
Generates realistic business data across all models for a 90-day period
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from decimal import Decimal
import random
import string

from sales_inventory_system.accounts.models import User
from sales_inventory_system.products.models import Product, Ingredient, RecipeItem, RecipeIngredient, StockTransaction, PhysicalCount, WasteLog, PrepBatch, VarianceRecord
from sales_inventory_system.orders.models import Order, OrderItem, Payment
from sales_inventory_system.system.models import AuditTrail


class Command(BaseCommand):
    help = 'Seed comprehensive 90-day historical data across all models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to seed (default: 90)'
        )
        parser.add_argument(
            '--clear-data',
            action='store_true',
            help='Delete seeded data before starting'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output with progress tracking'
        )

    def handle(self, *args, **options):
        days = options['days']
        verbose = options['verbose']
        clear_data = options['clear_data']

        self.stdout.write(f'Starting comprehensive {days}-day data seeding...')

        try:
            with transaction.atomic():
                # Clear existing seeded data if requested
                if clear_data:
                    self._clear_data()

                # Get or create users
                users = self._get_or_create_users()
                admin_user = users['admin']
                cashier_users = users['cashiers']

                # Get products
                products = self._get_products()
                if not products:
                    self.stdout.write(self.style.WARNING('No products found. Creating demo products...'))
                    self._create_demo_products()
                    products = self._get_products()

                # Get or create ingredients
                ingredients = self._get_or_create_ingredients()

                # Setup recipes
                self._setup_recipes(products, ingredients)

                # Generate 90 days of data
                start_date = timezone.now() - timedelta(days=days)

                for day_offset in range(days):
                    current_date = start_date + timedelta(days=day_offset)
                    is_weekend = current_date.weekday() >= 5

                    if verbose and day_offset % 7 == 0:
                        self.stdout.write(f'  Processing day {day_offset}/{days}...')

                    # Generate orders for this day
                    self._generate_daily_data(
                        current_date, is_weekend, products, cashier_users, admin_user
                    )

                    # Generate waste logs
                    self._generate_waste_logs(current_date, ingredients, admin_user)

                    # Every 14 days: physical counts and variance records
                    if day_offset % 14 == 0 and day_offset > 0:
                        self._generate_physical_counts(current_date, ingredients, admin_user)
                        self._generate_variance_records(current_date, ingredients, admin_user)

                    # Every 7 days: prep batches
                    if day_offset % 7 == 0:
                        self._generate_prep_batches(current_date, products, admin_user)

                self._print_summary(days)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during seeding: {str(e)}'))
            raise

    def _clear_data(self):
        """Clear previously seeded data"""
        self.stdout.write('Clearing previous seeded data...')
        Order.objects.all().delete()
        OrderItem.objects.all().delete()
        Payment.objects.all().delete()
        StockTransaction.objects.all().delete()
        PhysicalCount.objects.all().delete()
        WasteLog.objects.all().delete()
        PrepBatch.objects.all().delete()
        VarianceRecord.objects.all().delete()
        AuditTrail.objects.all().delete()

    def _get_or_create_users(self):
        """Get or create admin and cashier users"""
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@fjcpizza.com',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True
            }
        )

        cashier_names = [
            ('maria', 'Maria Santos'),
            ('jose', 'Jose Garcia'),
            ('john', 'John Smith'),
        ]

        cashiers = []
        for username, name in cashier_names:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@fjcpizza.com',
                    'first_name': name.split()[0],
                    'last_name': name.split()[1],
                    'role': 'CASHIER'
                }
            )
            cashiers.append(user)

        return {'admin': admin, 'cashiers': cashiers}

    def _get_products(self):
        """Get existing products"""
        return list(Product.objects.all())

    def _create_demo_products(self):
        """Create demo products if none exist"""
        demo_products = [
            {'name': 'Margherita Pizza', 'price': Decimal('12.99'), 'category': 'Pizzas', 'stock': 100},
            {'name': 'Pepperoni Pizza', 'price': Decimal('14.99'), 'category': 'Pizzas', 'stock': 100},
            {'name': 'Vegetarian Pizza', 'price': Decimal('13.99'), 'category': 'Pizzas', 'stock': 100},
            {'name': 'Chicken Wings', 'price': Decimal('8.99'), 'category': 'Sides', 'stock': 150},
            {'name': 'Caesar Salad', 'price': Decimal('7.99'), 'category': 'Salads', 'stock': 80},
            {'name': 'Garlic Bread', 'price': Decimal('4.99'), 'category': 'Sides', 'stock': 120},
            {'name': 'Coca Cola', 'price': Decimal('2.99'), 'category': 'Drinks', 'stock': 200},
            {'name': 'Sprite', 'price': Decimal('2.99'), 'category': 'Drinks', 'stock': 200},
        ]

        for product_data in demo_products:
            Product.objects.get_or_create(
                name=product_data['name'],
                defaults={
                    'price': product_data['price'],
                    'category': product_data['category'],
                    'stock': product_data['stock'],
                    'description': f'{product_data["name"]} from FJC Pizza'
                }
            )

    def _get_or_create_ingredients(self):
        """Get or create ingredients for recipes"""
        ingredients_data = [
            {'name': 'Pizza Dough', 'unit': 'g', 'cost_per_unit': Decimal('0.50'), 'current_stock': Decimal('50000')},
            {'name': 'Tomato Sauce', 'unit': 'ml', 'cost_per_unit': Decimal('0.10'), 'current_stock': Decimal('10000')},
            {'name': 'Mozzarella Cheese', 'unit': 'g', 'cost_per_unit': Decimal('0.20'), 'current_stock': Decimal('20000')},
            {'name': 'Pepperoni', 'unit': 'g', 'cost_per_unit': Decimal('0.80'), 'current_stock': Decimal('5000')},
            {'name': 'Fresh Basil', 'unit': 'g', 'cost_per_unit': Decimal('0.05'), 'current_stock': Decimal('1000')},
            {'name': 'Olive Oil', 'unit': 'ml', 'cost_per_unit': Decimal('0.15'), 'current_stock': Decimal('5000')},
            {'name': 'Mushrooms', 'unit': 'g', 'cost_per_unit': Decimal('0.25'), 'current_stock': Decimal('3000')},
            {'name': 'Bell Peppers', 'unit': 'g', 'cost_per_unit': Decimal('0.15'), 'current_stock': Decimal('5000')},
            {'name': 'Onions', 'unit': 'g', 'cost_per_unit': Decimal('0.08'), 'current_stock': Decimal('8000')},
            {'name': 'Chicken', 'unit': 'g', 'cost_per_unit': Decimal('1.20'), 'current_stock': Decimal('10000')},
            {'name': 'Lettuce', 'unit': 'g', 'cost_per_unit': Decimal('0.10'), 'current_stock': Decimal('5000')},
            {'name': 'Croutons', 'unit': 'g', 'cost_per_unit': Decimal('0.30'), 'current_stock': Decimal('2000')},
            {'name': 'Caesar Dressing', 'unit': 'ml', 'cost_per_unit': Decimal('0.20'), 'current_stock': Decimal('3000')},
        ]

        ingredients = {}
        for data in ingredients_data:
            ingredient, _ = Ingredient.objects.get_or_create(
                name=data['name'],
                defaults={
                    'unit': data['unit'],
                    'cost_per_unit': data['cost_per_unit'],
                    'current_stock': data['current_stock'],
                    'min_stock': Decimal('1000'),
                    'variance_allowance': Decimal('5'),
                    'is_active': True
                }
            )
            ingredients[data['name']] = ingredient

        return ingredients

    def _setup_recipes(self, products, ingredients):
        """Setup recipe relationships between products and ingredients"""
        # Map of product names to ingredient recipes
        recipes = {
            'Margherita Pizza': {
                'Pizza Dough': Decimal('300'),
                'Tomato Sauce': Decimal('100'),
                'Mozzarella Cheese': Decimal('150'),
                'Fresh Basil': Decimal('10'),
            },
            'Pepperoni Pizza': {
                'Pizza Dough': Decimal('300'),
                'Tomato Sauce': Decimal('100'),
                'Mozzarella Cheese': Decimal('150'),
                'Pepperoni': Decimal('80'),
            },
            'Vegetarian Pizza': {
                'Pizza Dough': Decimal('300'),
                'Tomato Sauce': Decimal('100'),
                'Mozzarella Cheese': Decimal('150'),
                'Bell Peppers': Decimal('50'),
                'Mushrooms': Decimal('50'),
                'Onions': Decimal('30'),
            },
            'Caesar Salad': {
                'Lettuce': Decimal('150'),
                'Croutons': Decimal('30'),
                'Caesar Dressing': Decimal('50'),
                'Mozzarella Cheese': Decimal('30'),
            },
        }

        for product in products:
            if product.name in recipes:
                recipe, _ = RecipeItem.objects.get_or_create(
                    product=product,
                    defaults={'created_by': None}
                )

                for ingredient_name, quantity in recipes[product.name].items():
                    if ingredient_name in ingredients:
                        RecipeIngredient.objects.get_or_create(
                            recipe=recipe,
                            ingredient=ingredients[ingredient_name],
                            defaults={'quantity': quantity}
                        )

    def _generate_daily_data(self, date, is_weekend, products, cashier_users, admin_user):
        """Generate orders and related data for a day"""
        # Determine number of orders based on weekday/weekend
        if is_weekend:
            num_orders = random.randint(20, 32)
        else:
            num_orders = random.randint(12, 18)

        for _ in range(num_orders):
            # Create order
            order_num = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            status = random.choices(['FINISHED', 'CANCELLED', 'PENDING'], weights=[75, 15, 10])[0]

            order = Order.objects.create(
                order_number=f'ORD-{order_num}',
                customer_name=random.choice(['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Williams', 'Carlos Lopez']),
                processed_by=random.choice(cashier_users),
                table_number=str(random.randint(1, 20)),
                status=status,
                notes='Customer order',
                total_amount=Decimal('0')
            )
            order.created_at = date + timedelta(hours=random.randint(9, 21), minutes=random.randint(0, 59))
            order.save(update_fields=['created_at'])

            # Add items to order
            num_items = random.randint(1, 5)
            total = Decimal('0')

            for _ in range(num_items):
                if not products:
                    continue

                product = random.choice(products)
                quantity = random.randint(1, 3)
                item_total = product.price * quantity
                total += item_total

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    product_name=product.name,
                    product_price=product.price
                )

                # Create stock transactions for deductions
                self._create_stock_transactions_for_order_item(order, product, quantity, admin_user)

            # Update order total
            order.total_amount = total
            order.save(update_fields=['total_amount'])

            # Create payment
            payment_status = 'SUCCESS' if status == 'FINISHED' else ('FAILED' if status == 'CANCELLED' else 'PENDING')
            Payment.objects.create(
                order=order,
                amount=total,
                method=random.choice(['CASH', 'ONLINE']),
                status=payment_status
            )

    def _create_stock_transactions_for_order_item(self, order, product, quantity, user):
        """Create stock transactions for order items (ingredient deductions)"""
        try:
            recipe = RecipeItem.objects.get(product=product)
            ingredients = recipe.ingredients.all()

            for recipe_ingredient in ingredients:
                total_quantity = recipe_ingredient.quantity * quantity
                StockTransaction.objects.create(
                    ingredient=recipe_ingredient.ingredient,
                    transaction_type='DEDUCTION',
                    quantity=total_quantity,
                    reference_type='order',
                    reference_id=order.id,
                    recorded_by=user
                )
        except RecipeItem.DoesNotExist:
            # No recipe for this product, skip deductions
            pass

    def _generate_waste_logs(self, date, ingredients, user):
        """Generate waste logs (2-3 times per week)"""
        if random.random() < 0.3:  # ~30% chance each day
            num_waste_entries = random.randint(1, 2)

            for _ in range(num_waste_entries):
                if not ingredients:
                    continue

                ingredient = random.choice(list(ingredients.values()))
                waste_type = random.choices(
                    ['SPOILAGE', 'WASTE', 'FREEBIE', 'SAMPLE', 'OTHER'],
                    weights=[50, 30, 15, 4, 1]
                )[0]

                reasons = {
                    'SPOILAGE': 'Expired ingredients found during inventory',
                    'WASTE': 'Accidentally spilled during prep',
                    'FREEBIE': 'Given as complimentary sample to customer',
                    'SAMPLE': 'Testing batch quality',
                    'OTHER': 'Damaged during storage'
                }

                WasteLog.objects.create(
                    ingredient=ingredient,
                    waste_type=waste_type,
                    quantity=Decimal(str(round(random.uniform(1, 10), 3))),
                    reason=reasons.get(waste_type, 'Miscellaneous waste'),
                    waste_date=date + timedelta(hours=random.randint(9, 18)),
                    reported_by=user
                )

    def _generate_physical_counts(self, date, ingredients, user):
        """Generate physical inventory counts (bi-weekly)"""
        for ingredient in ingredients.values():
            physical_qty = ingredient.current_stock * Decimal(str(round(random.uniform(0.95, 1.05), 2)))

            PhysicalCount.objects.create(
                ingredient=ingredient,
                physical_quantity=physical_qty,
                theoretical_quantity=ingredient.current_stock,
                count_date=date,
                notes=f'Regular inventory count for {ingredient.name}',
                counted_by=user
            )

    def _generate_variance_records(self, date, ingredients, user):
        """Generate variance records for inventory analysis"""
        for ingredient in ingredients.values():
            variance_qty = ingredient.current_stock * Decimal(str(round(random.uniform(-0.05, 0.05), 2)))
            variance_pct = (variance_qty / ingredient.current_stock * 100) if ingredient.current_stock > 0 else Decimal('0')

            VarianceRecord.objects.create(
                ingredient=ingredient,
                period_start=date - timedelta(days=14),
                period_end=date,
                theoretical_used=ingredient.current_stock,
                actual_used=ingredient.current_stock - variance_qty,
                variance_quantity=variance_qty,
                variance_percentage=variance_pct,
                within_tolerance=abs(variance_pct) <= ingredient.variance_allowance
            )

    def _generate_prep_batches(self, date, products, user):
        """Generate prep batch operations (weekly)"""
        products_with_recipes = [p for p in products if hasattr(p, 'recipe')]

        for product in products_with_recipes[:2]:  # Up to 2 products per week
            try:
                recipe = RecipeItem.objects.get(product=product)

                status = random.choices(['COMPLETED', 'IN_PROGRESS', 'PLANNED'], weights=[80, 10, 10])[0]
                batch_start = date if status != 'PLANNED' else None
                batch_end = date if status == 'COMPLETED' else None

                PrepBatch.objects.create(
                    recipe=recipe,
                    name=f'{product.name} Batch {random.randint(1, 999)}',
                    quantity_produced=random.randint(10, 50),
                    status=status,
                    prep_start=batch_start,
                    prep_end=batch_end,
                    prepared_by=user if status != 'PLANNED' else None
                )
            except RecipeItem.DoesNotExist:
                pass

    def _print_summary(self, days):
        """Print data seeding summary"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('[OK] Comprehensive 90-Day Seeding Complete!'))
        self.stdout.write('='*60)

        self.stdout.write(f'Orders: {Order.objects.count()}')
        self.stdout.write(f'Order Items: {OrderItem.objects.count()}')
        self.stdout.write(f'Payments: {Payment.objects.count()}')
        self.stdout.write(f'Stock Transactions: {StockTransaction.objects.count()}')
        self.stdout.write(f'Physical Counts: {PhysicalCount.objects.count()}')
        self.stdout.write(f'Variance Records: {VarianceRecord.objects.count()}')
        self.stdout.write(f'Waste Logs: {WasteLog.objects.count()}')
        self.stdout.write(f'Prep Batches: {PrepBatch.objects.count()}')
        self.stdout.write('='*60 + '\n')
