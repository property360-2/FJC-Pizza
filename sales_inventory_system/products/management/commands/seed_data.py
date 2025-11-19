"""
Management command to seed the database with sample data
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from products.models import (
    Ingredient, Product, RecipeItem, RecipeIngredient
)
from accounts.models import User as CustomUser

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with sample pizza restaurant data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('[*] Starting data seeding...'))

        # Create users
        self.create_users()

        # Create ingredients
        ingredients = self.create_ingredients()

        # Create products
        self.create_products(ingredients)

        self.stdout.write(self.style.SUCCESS('[OK] Data seeding completed successfully!'))

    def create_users(self):
        """Create sample users"""
        self.stdout.write('Creating users...')

        users_data = [
            {
                'username': 'admin',
                'email': 'admin@fjcpizza.com',
                'password': 'admin123',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'ADMIN'
            },
            {
                'username': 'cashier',
                'email': 'cashier@fjcpizza.com',
                'password': 'cashier123',
                'first_name': 'Cashier',
                'last_name': 'User',
                'role': 'CASHIER'
            },
        ]

        for user_data in users_data:
            if not User.objects.filter(username=user_data['username']).exists():
                User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    role=user_data['role']
                )
                self.stdout.write(f"  [+] Created user: {user_data['username']}")

    def create_ingredients(self):
        """Create ingredients"""
        self.stdout.write('Creating ingredients...')

        ingredients_data = [
            # Bases
            {'name': 'Pizza Dough', 'unit': 'kg', 'cost': 15.00, 'stock': 50, 'min': 10, 'variance': 5},
            {'name': 'Tomato Sauce', 'unit': 'L', 'cost': 85.00, 'stock': 20, 'min': 5, 'variance': 10},

            # Cheese & Dairy
            {'name': 'Mozzarella Cheese', 'unit': 'kg', 'cost': 320.00, 'stock': 30, 'min': 5, 'variance': 8},
            {'name': 'Parmesan Cheese', 'unit': 'kg', 'cost': 450.00, 'stock': 10, 'min': 2, 'variance': 5},
            {'name': 'Cheddar Cheese', 'unit': 'kg', 'cost': 280.00, 'stock': 15, 'min': 3, 'variance': 8},

            # Meats
            {'name': 'Pepperoni', 'unit': 'kg', 'cost': 400.00, 'stock': 20, 'min': 5, 'variance': 5},
            {'name': 'Italian Sausage', 'unit': 'kg', 'cost': 350.00, 'stock': 15, 'min': 3, 'variance': 5},
            {'name': 'Bacon', 'unit': 'kg', 'cost': 380.00, 'stock': 12, 'min': 2, 'variance': 5},
            {'name': 'Ham', 'unit': 'kg', 'cost': 320.00, 'stock': 18, 'min': 3, 'variance': 5},
            {'name': 'Chicken Breast', 'unit': 'kg', 'cost': 250.00, 'stock': 25, 'min': 5, 'variance': 8},

            # Vegetables
            {'name': 'Onion', 'unit': 'kg', 'cost': 25.00, 'stock': 40, 'min': 10, 'variance': 10},
            {'name': 'Bell Pepper', 'unit': 'kg', 'cost': 50.00, 'stock': 30, 'min': 5, 'variance': 10},
            {'name': 'Mushroom', 'unit': 'kg', 'cost': 60.00, 'stock': 25, 'min': 5, 'variance': 10},
            {'name': 'Olive', 'unit': 'kg', 'cost': 200.00, 'stock': 15, 'min': 3, 'variance': 5},
            {'name': 'Pineapple', 'unit': 'kg', 'cost': 80.00, 'stock': 20, 'min': 5, 'variance': 10},
            {'name': 'Spinach', 'unit': 'kg', 'cost': 45.00, 'stock': 12, 'min': 3, 'variance': 10},
            {'name': 'Garlic', 'unit': 'kg', 'cost': 120.00, 'stock': 8, 'min': 2, 'variance': 5},
            {'name': 'Tomato', 'unit': 'kg', 'cost': 50.00, 'stock': 25, 'min': 5, 'variance': 10},

            # Toppings & Extras
            {'name': 'Extra Virgin Olive Oil', 'unit': 'L', 'cost': 400.00, 'stock': 5, 'min': 1, 'variance': 5},
            {'name': 'Oregano', 'unit': 'kg', 'cost': 150.00, 'stock': 3, 'min': 1, 'variance': 5},
            {'name': 'Fresh Basil', 'unit': 'kg', 'cost': 100.00, 'stock': 5, 'min': 1, 'variance': 10},

            # Dessert Ingredients
            {'name': 'Cream Cheese', 'unit': 'kg', 'cost': 380.00, 'stock': 8, 'min': 2, 'variance': 5},
            {'name': 'Eggs', 'unit': 'pcs', 'cost': 8.00, 'stock': 200, 'min': 50, 'variance': 10},
            {'name': 'Sugar', 'unit': 'kg', 'cost': 35.00, 'stock': 30, 'min': 10, 'variance': 10},
            {'name': 'Chocolate', 'unit': 'kg', 'cost': 350.00, 'stock': 10, 'min': 2, 'variance': 5},
            {'name': 'Vanilla Extract', 'unit': 'L', 'cost': 500.00, 'stock': 1, 'min': 0.5, 'variance': 5},

            # Beverages
            {'name': 'Coca Cola Syrup', 'unit': 'L', 'cost': 120.00, 'stock': 15, 'min': 5, 'variance': 10},
            {'name': 'Sprite Syrup', 'unit': 'L', 'cost': 120.00, 'stock': 12, 'min': 3, 'variance': 10},
            {'name': 'Iced Tea Powder', 'unit': 'kg', 'cost': 180.00, 'stock': 5, 'min': 1, 'variance': 10},
            {'name': 'Coffee Beans', 'unit': 'kg', 'cost': 400.00, 'stock': 4, 'min': 1, 'variance': 5},
            {'name': 'Milk', 'unit': 'L', 'cost': 50.00, 'stock': 20, 'min': 5, 'variance': 10},
        ]

        ingredients = {}
        for ing_data in ingredients_data:
            ingredient, created = Ingredient.objects.get_or_create(
                name=ing_data['name'],
                defaults={
                    'unit': ing_data['unit'],
                    'cost_per_unit': Decimal(str(ing_data['cost'])),
                    'current_stock': Decimal(str(ing_data['stock'])),
                    'min_stock': Decimal(str(ing_data['min'])),
                    'variance_allowance': Decimal(str(ing_data['variance'])),
                    'is_active': True
                }
            )
            ingredients[ing_data['name']] = ingredient
            if created:
                self.stdout.write(f"  [+] Created ingredient: {ing_data['name']}")

        return ingredients

    def create_products(self, ingredients):
        """Create products with recipes"""
        self.stdout.write('Creating products and recipes...')

        products_data = [
            {
                'name': 'Margherita Pizza',
                'description': 'Classic pizza with tomato sauce, mozzarella, and fresh basil',
                'category': 'Pizza',
                'price': 199.00,
                'stock': 50,
                'threshold': 5,
                'recipe': [
                    ('Pizza Dough', '0.4'),
                    ('Tomato Sauce', '0.2'),
                    ('Mozzarella Cheese', '0.15'),
                    ('Fresh Basil', '0.01'),
                    ('Olive Oil', '0.05'),
                ]
            },
            {
                'name': 'Pepperoni Pizza',
                'description': 'Loaded with pepperoni slices and melted mozzarella',
                'category': 'Pizza',
                'price': 249.00,
                'stock': 45,
                'threshold': 5,
                'recipe': [
                    ('Pizza Dough', '0.4'),
                    ('Tomato Sauce', '0.2'),
                    ('Mozzarella Cheese', '0.15'),
                    ('Pepperoni', '0.1'),
                    ('Olive Oil', '0.05'),
                ]
            },
            {
                'name': 'Hawaiian Pizza',
                'description': 'Tropical pizza with ham and pineapple',
                'category': 'Pizza',
                'price': 269.00,
                'stock': 35,
                'threshold': 5,
                'recipe': [
                    ('Pizza Dough', '0.4'),
                    ('Tomato Sauce', '0.2'),
                    ('Mozzarella Cheese', '0.15'),
                    ('Ham', '0.08'),
                    ('Pineapple', '0.1'),
                ]
            },
            {
                'name': 'Veggie Supreme Pizza',
                'description': 'Fresh vegetables: peppers, onions, mushrooms, olives',
                'category': 'Pizza',
                'price': 239.00,
                'stock': 40,
                'threshold': 5,
                'recipe': [
                    ('Pizza Dough', '0.4'),
                    ('Tomato Sauce', '0.2'),
                    ('Mozzarella Cheese', '0.15'),
                    ('Bell Pepper', '0.08'),
                    ('Onion', '0.06'),
                    ('Mushroom', '0.08'),
                    ('Olive', '0.04'),
                ]
            },
            {
                'name': 'Meat Lovers Pizza',
                'description': 'Loaded with pepperoni, sausage, ham, and bacon',
                'category': 'Pizza',
                'price': 299.00,
                'stock': 30,
                'threshold': 5,
                'recipe': [
                    ('Pizza Dough', '0.4'),
                    ('Tomato Sauce', '0.2'),
                    ('Mozzarella Cheese', '0.15'),
                    ('Pepperoni', '0.06'),
                    ('Italian Sausage', '0.06'),
                    ('Ham', '0.05'),
                    ('Bacon', '0.05'),
                ]
            },
            {
                'name': 'BBQ Chicken Pizza',
                'description': 'Grilled chicken with BBQ sauce and red onions',
                'category': 'Pizza',
                'price': 279.00,
                'stock': 32,
                'threshold': 5,
                'recipe': [
                    ('Pizza Dough', '0.4'),
                    ('Chicken Breast', '0.15'),
                    ('Mozzarella Cheese', '0.12'),
                    ('Onion', '0.05'),
                    ('Cheddar Cheese', '0.03'),
                ]
            },
            {
                'name': 'Cheesecake',
                'description': 'Creamy New York style cheesecake',
                'category': 'Dessert',
                'price': 139.00,
                'stock': 32,
                'threshold': 3,
                'recipe': [
                    ('Cream Cheese', '0.3'),
                    ('Eggs', '4'),
                    ('Sugar', '0.15'),
                    ('Vanilla Extract', '0.01'),
                ]
            },
            {
                'name': 'Chocolate Cake',
                'description': 'Rich chocolate cake with chocolate frosting',
                'category': 'Dessert',
                'price': 129.00,
                'stock': 25,
                'threshold': 3,
                'recipe': [
                    ('Chocolate', '0.3'),
                    ('Eggs', '5'),
                    ('Sugar', '0.2'),
                    ('Milk', '0.15'),
                ]
            },
            {
                'name': 'Coca Cola',
                'description': 'Cold Coca Cola soft drink',
                'category': 'Beverage',
                'price': 49.00,
                'stock': 100,
                'threshold': 20,
                'recipe': [
                    ('Coca Cola Syrup', '0.25'),
                ]
            },
            {
                'name': 'Sprite',
                'description': 'Refreshing lemon-lime soft drink',
                'category': 'Beverage',
                'price': 49.00,
                'stock': 90,
                'threshold': 20,
                'recipe': [
                    ('Sprite Syrup', '0.25'),
                ]
            },
            {
                'name': 'Iced Tea',
                'description': 'Cold refreshing iced tea',
                'category': 'Beverage',
                'price': 39.00,
                'stock': 80,
                'threshold': 15,
                'recipe': [
                    ('Iced Tea Powder', '0.02'),
                ]
            },
            {
                'name': 'Espresso',
                'description': 'Strong Italian espresso coffee',
                'category': 'Beverage',
                'price': 69.00,
                'stock': 60,
                'threshold': 10,
                'recipe': [
                    ('Coffee Beans', '0.01'),
                ]
            },
            {
                'name': 'Capuccino',
                'description': 'Creamy cappuccino with milk foam',
                'category': 'Beverage',
                'price': 89.00,
                'stock': 55,
                'threshold': 10,
                'recipe': [
                    ('Coffee Beans', '0.015'),
                    ('Milk', '0.1'),
                ]
            },
        ]

        for prod_data in products_data:
            product, created = Product.objects.get_or_create(
                name=prod_data['name'],
                defaults={
                    'description': prod_data['description'],
                    'category': prod_data['category'],
                    'price': Decimal(str(prod_data['price'])),
                    'stock': prod_data['stock'],
                    'threshold': prod_data['threshold'],
                    'is_archived': False
                }
            )

            if created:
                self.stdout.write(f"  [+] Created product: {prod_data['name']}")

                # Create recipe
                if prod_data.get('recipe'):
                    recipe_item, _ = RecipeItem.objects.get_or_create(product=product)

                    for ing_name, qty in prod_data['recipe']:
                        ingredient = ingredients.get(ing_name)
                        if ingredient:
                            RecipeIngredient.objects.get_or_create(
                                recipe=recipe_item,
                                ingredient=ingredient,
                                defaults={'quantity': Decimal(qty)}
                            )

                    self.stdout.write(f"      [*] Recipe with {len(prod_data['recipe'])} ingredients")
