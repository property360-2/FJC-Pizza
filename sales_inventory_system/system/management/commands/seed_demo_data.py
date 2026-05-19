import random
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db import transaction

# Import custom models using absolute package prefixes
from sales_inventory_system.accounts.models import User
from sales_inventory_system.products.models import Product, Ingredient, RecipeItem, RecipeIngredient, StockTransaction
from sales_inventory_system.orders.models import Order, OrderItem, Payment


class Command(BaseCommand):
    """
    Management command to seed realistic mock data for FJC Pizza.
    Populates ingredients, products, BOM/recipes, and 60 days of historical sales
    with weekly seasonal variations for Holt-Winters forecasting demonstration.
    """
    help = 'Seeds FJC Pizza database with mock ingredients, products, recipes, and 60 days of transaction history.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing products, ingredients, orders, and payments before seeding',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("[+] Preparing to seed FJC Pizza database..."))

        if options['clear']:
            self.stdout.write(self.style.WARNING("[-] Clearing existing database records..."))
            self.clear_database()

        try:
            with transaction.atomic():
                self.seed_users()
                ingredients = self.seed_ingredients()
                products = self.seed_products()
                self.seed_recipes(products, ingredients)
                self.seed_historical_sales(products)
                
            self.stdout.write(self.style.SUCCESS("\n[SUCCESS] Database successfully seeded with 60 days of seasonal historical sales!"))
            self.stdout.write(self.style.SUCCESS("[INFO] Run 'python manage.py runserver' and visit '/analytics/forecast/' to view the predictive chart!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[ERROR] Error during seeding: {e}"))
            import traceback
            traceback.print_exc()

    def clear_database(self):
        """Clean all transactional and inventory tables safely"""
        Payment.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        StockTransaction.objects.all().delete()
        RecipeIngredient.objects.all().delete()
        RecipeItem.objects.all().delete()
        Product.objects.all().delete()
        Ingredient.objects.all().delete()
        # Keep superusers, but delete non-superuser seed users
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.SUCCESS("[SUCCESS] Database tables cleared successfully."))

    def seed_users(self):
        """Seed Cashiers and Administrators"""
        self.stdout.write("Seeding personnel users...")
        
        users_data = [
            {
                'username': 'cashier',
                'email': 'cashier@fjcpizza.com',
                'password': 'cashier123',
                'first_name': 'John',
                'last_name': 'Doe',
                'phone': '+63 917 123 4567',
                'role': 'CASHIER'
            },
            {
                'username': 'maria',
                'email': 'maria@fjcpizza.com',
                'password': 'maria123',
                'first_name': 'Maria',
                'last_name': 'Santos',
                'phone': '+63 918 234 5678',
                'role': 'CASHIER'
            },
            {
                'username': 'jose',
                'email': 'jose@fjcpizza.com',
                'password': 'jose123',
                'first_name': 'Jose',
                'last_name': 'Reyes',
                'phone': '+63 919 345 6789',
                'role': 'CASHIER'
            },
            {
                'username': 'manager',
                'email': 'manager@fjcpizza.com',
                'password': 'manager123',
                'first_name': 'Ana',
                'last_name': 'Garcia',
                'phone': '+63 920 456 7890',
                'role': 'ADMIN'
            },
        ]

        for user_data in users_data:
            if not User.objects.filter(username=user_data['username']).exists():
                User.objects.create_user(**user_data)
                self.stdout.write(f"  [Created] User: {user_data['username']} ({user_data['role']})")
            else:
                self.stdout.write(f"  [Skipped] User {user_data['username']} already exists.")

    def seed_ingredients(self):
        """Seed Raw Ingredients and Stock Levels"""
        self.stdout.write("\nSeeding inventory ingredients...")
        
        ingredients_data = [
            {'name': 'Pizza Dough Ball', 'description': 'Standard 12-inch hand-stretched dough base', 'unit': 'pcs', 'current_stock': Decimal('150.00'), 'min_stock': Decimal('30.00')},
            {'name': 'Tomato Sauce Blend', 'description': 'Signature seasoned pizza marinara sauce', 'unit': 'ml', 'current_stock': Decimal('25000.00'), 'min_stock': Decimal('5000.00')},
            {'name': 'Mozzarella Cheese', 'description': 'Premium shredded mozzarella cheese', 'unit': 'g', 'current_stock': Decimal('30000.00'), 'min_stock': Decimal('6000.00')},
            {'name': 'Pepperoni Slices', 'description': 'Spicy cured beef and pork pepperoni slices', 'unit': 'pcs', 'current_stock': Decimal('12000.00'), 'min_stock': Decimal('2000.00')},
            {'name': 'Sweet Pineapple Tidbits', 'description': 'Canned sweet pineapple chunks in juice', 'unit': 'g', 'current_stock': Decimal('10000.00'), 'min_stock': Decimal('2000.00')},
            {'name': 'Smoked Ham Slices', 'description': 'Thinly sliced premium smoked ham squares', 'unit': 'pcs', 'current_stock': Decimal('5000.00'), 'min_stock': Decimal('1000.00')},
            {'name': 'Fresh Basil Leaves', 'description': 'Aromatic organic sweet basil leaves', 'unit': 'g', 'current_stock': Decimal('1500.00'), 'min_stock': Decimal('300.00')},
            {'name': 'Extra Virgin Olive Oil', 'description': 'Pure cold-pressed olive oil drizzle', 'unit': 'ml', 'current_stock': Decimal('5000.00'), 'min_stock': Decimal('1000.00')},
        ]

        ingredients = {}
        for ing_data in ingredients_data:
            ing, created = Ingredient.objects.get_or_create(name=ing_data['name'], defaults=ing_data)
            if created:
                self.stdout.write(f"  [Created] Ingredient: {ing.name}")
                # Log initial purchase transaction to inventory logs
                StockTransaction.objects.create(
                    ingredient=ing,
                    transaction_type='PURCHASE',
                    quantity=ing.current_stock,
                    notes='Initial seeding purchase.'
                )
            else:
                self.stdout.write(f"  [Skipped] Ingredient {ing.name} already exists.")
            ingredients[ing.name] = ing
        return ingredients

    def seed_products(self):
        """Seed Menu Products"""
        self.stdout.write("\nSeeding menu products...")
        
        products_data = [
            # Pizzas
            {'name': 'Margherita Pizza', 'description': 'Classic style with tomato sauce, premium mozzarella, fresh basil, and extra virgin olive oil.', 'price': Decimal('299.00'), 'stock': 40, 'threshold': 10, 'category': 'Pizza', 'requires_bom': True},
            {'name': 'Pepperoni Pizza', 'description': 'All-time favorite loaded with pepperoni slices and double mozzarella cheese.', 'price': Decimal('349.00'), 'stock': 45, 'threshold': 10, 'category': 'Pizza', 'requires_bom': True},
            {'name': 'Hawaiian Pizza', 'description': 'Perfect blend of sweet pineapple tidbits, smoked ham slices, and premium mozzarella.', 'price': Decimal('329.00'), 'stock': 35, 'threshold': 10, 'category': 'Pizza', 'requires_bom': True},
            {'name': 'Supreme Pizza', 'description': 'All-in-one feast of pepperoni, Italian sausage, bell peppers, onions, and black olives.', 'price': Decimal('399.00'), 'stock': 25, 'threshold': 8, 'category': 'Pizza', 'requires_bom': False},
            {'name': 'Four Cheese Pizza', 'description': 'Cheese overload with mozzarella, cheddar, parmesan, and cream cheese.', 'price': Decimal('379.00'), 'stock': 30, 'threshold': 8, 'category': 'Pizza', 'requires_bom': False},

            # Sides
            {'name': 'Garlic Bread', 'description': 'Warm, toasted bread with rich garlic butter and Italian herbs.', 'price': Decimal('89.00'), 'stock': 80, 'threshold': 15, 'category': 'Sides', 'requires_bom': False},
            {'name': 'Chicken Wings (6pcs)', 'description': 'Crispy golden fried chicken wings glazed in sweet honey BBQ sauce.', 'price': Decimal('199.00'), 'stock': 50, 'threshold': 12, 'category': 'Sides', 'requires_bom': False},
            {'name': 'Mozzarella Sticks', 'description': 'Gooey, deep-fried mozzarella fingers served with dipping marinara sauce.', 'price': Decimal('149.00'), 'stock': 60, 'threshold': 15, 'category': 'Sides', 'requires_bom': False},
            {'name': 'French Fries', 'description': 'Crispy, salted classic French fries.', 'price': Decimal('79.00'), 'stock': 100, 'threshold': 20, 'category': 'Sides', 'requires_bom': False},

            # Drinks
            {'name': 'Coca-Cola (500ml)', 'description': 'Ice-cold carbonated Coca-Cola.', 'price': Decimal('49.00'), 'stock': 150, 'threshold': 30, 'category': 'Drinks', 'requires_bom': False},
            {'name': 'Sprite (500ml)', 'description': 'Ice-cold lemon-lime flavored Sprite.', 'price': Decimal('49.00'), 'stock': 130, 'threshold': 30, 'category': 'Drinks', 'requires_bom': False},
            {'name': 'Iced Tea (500ml)', 'description': 'Signature sweet red house iced tea.', 'price': Decimal('39.00'), 'stock': 120, 'threshold': 25, 'category': 'Drinks', 'requires_bom': False},
            {'name': 'Bottled Water (500ml)', 'description': 'Pure mineral drinking water.', 'price': Decimal('29.00'), 'stock': 200, 'threshold': 40, 'category': 'Drinks', 'requires_bom': False},

            # Desserts
            {'name': 'Chocolate Brownie', 'description': 'Warm fudge chocolate brownie with rich chocolate chips.', 'price': Decimal('129.00'), 'stock': 30, 'threshold': 8, 'category': 'Desserts', 'requires_bom': False},
            {'name': 'Tiramisu Slice', 'description': 'Traditional Italian coffee-flavored dessert layer cake.', 'price': Decimal('149.00'), 'stock': 20, 'threshold': 5, 'category': 'Desserts', 'requires_bom': False},
        ]

        products = {}
        for p_data in products_data:
            prod, created = Product.objects.get_or_create(name=p_data['name'], defaults=p_data)
            if created:
                self.stdout.write(f"  [Created] Product: {prod.name} ({prod.category})")
            else:
                self.stdout.write(f"  [Skipped] Product {prod.name} already exists.")
            products[prod.name] = prod
        return products

    def seed_recipes(self, products, ingredients):
        """Set up Recipes / Bills of Materials (BOM) for products"""
        self.stdout.write("\nSetting up Bill of Materials (BOM) & Recipes...")

        # Margherita Recipe setup
        m_pizza = products.get('Margherita Pizza')
        if m_pizza:
            recipe, created = RecipeItem.objects.get_or_create(product=m_pizza)
            if created:
                RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredients['Pizza Dough Ball'], quantity=Decimal('1.000'))
                RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredients['Tomato Sauce Blend'], quantity=Decimal('120.000'))
                RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredients['Mozzarella Cheese'], quantity=Decimal('150.000'))
                RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredients['Fresh Basil Leaves'], quantity=Decimal('10.000'))
                RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredients['Extra Virgin Olive Oil'], quantity=Decimal('15.000'))
                self.stdout.write("  [Mapped] Recipe for Margherita Pizza")

        # Pepperoni Recipe setup
        p_pizza = products.get('Pepperoni Pizza')
        if p_pizza:
            recipe, created = RecipeItem.objects.get_or_create(product=p_pizza)
            if created:
                RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredients['Pizza Dough Ball'], quantity=Decimal('1.000'))
                RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredients['Tomato Sauce Blend'], quantity=Decimal('100.000'))
                RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredients['Mozzarella Cheese'], quantity=Decimal('180.000'))
                RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredients['Pepperoni Slices'], quantity=Decimal('35.000'))
                self.stdout.write("  [Mapped] Recipe for Pepperoni Pizza")

        # Hawaiian Recipe setup
        h_pizza = products.get('Hawaiian Pizza')
        if h_pizza:
            recipe, created = RecipeItem.objects.get_or_create(product=h_pizza)
            if created:
                RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredients['Pizza Dough Ball'], quantity=Decimal('1.000'))
                RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredients['Tomato Sauce Blend'], quantity=Decimal('100.000'))
                RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredients['Mozzarella Cheese'], quantity=Decimal('140.000'))
                RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredients['Smoked Ham Slices'], quantity=Decimal('12.000'))
                RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredients['Sweet Pineapple Tidbits'], quantity=Decimal('80.000'))
                self.stdout.write("  [Mapped] Recipe for Hawaiian Pizza")

    def seed_historical_sales(self, products):
        """Seed 60 days of historical sales with dynamic weekly seasonality wave"""
        self.stdout.write("\nSeeding historical transactions (last 60 days) with weekly seasonality waves...")

        # Find or use cashier/admin accounts to process orders
        cashier = User.objects.filter(role='CASHIER').first() or User.objects.filter(is_superuser=True).first()
        
        product_list = list(products.values())
        customers = [
            'Juan dela Cruz', 'Maria Clara', 'Andres Bonifacio', 'Jose Rizal',
            'Leonor Rivera', 'Emilio Aguinaldo', 'Gabriela Silang', 'Melchora Aquino',
            'Antonio Luna', 'Apolinario Mabini', 'Gregorio del Pilar', 'Diego Silang',
            'Cardo Dalisay', 'Alyana Arevalo', 'Victor Magtanggol', 'Lola Flora'
        ]

        total_orders_created = 0
        base_date = timezone.now().date()

        # Iterate backwards 60 days to seed transactions day-by-day
        for days_ago in range(60, -1, -1):
            target_date = base_date - timedelta(days=days_ago)
            day_of_week = target_date.weekday()  # Monday is 0, Sunday is 6

            # Define seasonality multipliers: Peak sales on Friday (4), Saturday (5), Sunday (6)
            if day_of_week in [4, 5, 6]:
                # Weekends: High volume
                order_count = random.randint(12, 18)
                volume_multiplier = 1.6
            elif day_of_week in [0, 1]:
                # Mon/Tue: Low volume
                order_count = random.randint(4, 7)
                volume_multiplier = 0.8
            else:
                # Midweek (Wed/Thu): Average volume
                order_count = random.randint(7, 11)
                volume_multiplier = 1.1

            # Seed the calculated number of orders for the day
            for i in range(order_count):
                customer = random.choice(customers)
                table = f"T{random.randint(1, 10):02d}" if random.random() < 0.75 else "Takeout"
                
                # Assign randomized transaction timestamp
                hour = random.randint(11, 21)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                created_at = timezone.make_aware(
                    timezone.datetime(target_date.year, target_date.month, target_date.day, hour, minute, second)
                )

                # Determine order states
                # Almost all past orders are FINISHED, but today's can have active states
                if days_ago == 0 and i == 0:
                    status = 'PENDING'
                    payment_status = 'PENDING'
                    payment_method = 'CASH'
                elif days_ago == 0 and i == 1:
                    status = 'IN_PROGRESS'
                    payment_status = 'SUCCESS'
                    payment_method = 'ONLINE'
                else:
                    status = 'FINISHED'
                    payment_status = 'SUCCESS'
                    payment_method = 'ONLINE' if random.random() < 0.4 else 'CASH'

                # Create Order
                order = Order.objects.create(
                    customer_name=customer,
                    table_number=table if table != "Takeout" else "",
                    status=status,
                    processed_by=cashier,
                    notes='No onions' if random.random() < 0.1 else '',
                )

                # Create between 1 to 4 line items per order
                line_item_count = random.randint(1, 3)
                selected_products = random.sample(product_list, line_item_count)
                
                for product in selected_products:
                    # Apply weekend bias for higher quantities
                    quantity = random.randint(1, 2)
                    if volume_multiplier > 1.2 and random.random() < 0.3:
                        quantity += 1
                        
                    item = OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        product_price=product.price,
                        quantity=quantity,
                        subtotal=product.price * quantity,
                    )
                    OrderItem.objects.filter(pk=item.pk).update(created_at=created_at)

                # Update the order's accumulated total (calls save internally)
                order.calculate_total()

                # Create Payment
                payment = Payment.objects.create(
                    order=order,
                    method=payment_method,
                    status=payment_status,
                    amount=order.total_amount,
                    processed_by=cashier,
                )

                # Force historic dates using direct SQL updates to bypass auto_now_add
                Order.objects.filter(pk=order.pk).update(created_at=created_at)
                Payment.objects.filter(pk=payment.pk).update(created_at=created_at)

                total_orders_created += 1

        self.stdout.write(f"  [SUCCESS] Created {total_orders_created} completed historical orders across the last 60 days.")
