#!/usr/bin/env python
"""
Comprehensive QA Test Suite for FJC-Pizza System
Validates data integrity, model relationships, and system consistency
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_inventory.settings')
django.setup()

from django.db.models import Count, Q
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

from accounts.models import User
from products.models import Product, Ingredient, RecipeItem, RecipeIngredient, StockTransaction, PhysicalCount, WasteLog, PrepBatch, VarianceRecord
from orders.models import Order, OrderItem, Payment
from system.models import AuditTrail


class QATest:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def test(self, name, condition, message=""):
        """Helper method to run and track tests"""
        if condition:
            self.passed += 1
            print(f"  [PASS] {name}")
        else:
            self.failed += 1
            print(f"  [FAIL] {name}")
            if message:
                print(f"         {message}")

    def warning(self, name, message=""):
        """Log a warning"""
        self.warnings += 1
        print(f"  [WARN] {name}")
        if message:
            print(f"         {message}")

    def section(self, title):
        """Print a test section header"""
        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}")

    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Passed:  {self.passed}")
        print(f"Failed:  {self.failed}")
        print(f"Warnings: {self.warnings}")
        total = self.passed + self.failed
        if total > 0:
            pass_rate = (self.passed / total) * 100
            print(f"Pass Rate: {pass_rate:.1f}%")
        print(f"{'='*60}\n")

        return self.failed == 0


class DataIntegrityTests(QATest):
    """Test data integrity and relationships"""

    def run_all(self):
        """Run all data integrity tests"""
        self.section("DATA INTEGRITY TESTS")

        self.test_user_data()
        self.test_product_data()
        self.test_ingredient_data()
        self.test_recipe_data()
        self.test_order_data()
        self.test_payment_data()
        self.test_stock_transactions()
        self.test_physical_counts()
        self.test_waste_logs()
        self.test_prep_batches()
        self.test_variance_records()

        return self.print_summary()

    def test_user_data(self):
        """Validate user data"""
        print("\n[User Model Validation]")

        user_count = User.objects.count()
        self.test("Users exist", user_count > 0, f"Found {user_count} users")

        admin_users = User.objects.filter(role='ADMIN')
        self.test("Admin users exist", admin_users.count() > 0, f"Found {admin_users.count()} admins")

        cashier_users = User.objects.filter(role='CASHIER')
        self.test("Cashier users exist", cashier_users.count() > 0, f"Found {cashier_users.count()} cashiers")

        invalid_roles = User.objects.exclude(role__in=['ADMIN', 'CASHIER'])
        self.test("All users have valid roles", invalid_roles.count() == 0,
                 f"Found {invalid_roles.count()} users with invalid roles")

    def test_product_data(self):
        """Validate product data"""
        print("\n[Product Model Validation]")

        product_count = Product.objects.count()
        self.test("Products exist", product_count > 0, f"Found {product_count} products")

        zero_price = Product.objects.filter(price__lte=0)
        self.test("All products have valid prices", zero_price.count() == 0,
                 f"Found {zero_price.count()} products with invalid prices")

        invalid_stock = Product.objects.filter(stock__lt=0)
        self.test("All products have non-negative stock", invalid_stock.count() == 0,
                 f"Found {invalid_stock.count()} products with negative stock")

    def test_ingredient_data(self):
        """Validate ingredient data"""
        print("\n[Ingredient Model Validation]")

        ingredient_count = Ingredient.objects.count()
        self.test("Ingredients exist", ingredient_count > 0, f"Found {ingredient_count} ingredients")

        invalid_cost = Ingredient.objects.filter(cost_per_unit__lte=0)
        self.test("All ingredients have valid cost", invalid_cost.count() == 0,
                 f"Found {invalid_cost.count()} ingredients with invalid cost")

        negative_stock = Ingredient.objects.filter(current_stock__lt=0)
        self.test("All ingredients have non-negative stock", negative_stock.count() == 0,
                 f"Found {negative_stock.count()} ingredients with negative stock")

    def test_recipe_data(self):
        """Validate recipe relationships"""
        print("\n[Recipe Model Validation]")

        recipe_count = RecipeItem.objects.count()
        self.test("Recipes exist", recipe_count > 0, f"Found {recipe_count} recipes")

        if recipe_count > 0:
            orphaned_recipes = RecipeItem.objects.filter(product__isnull=True)
            self.test("No orphaned recipes", orphaned_recipes.count() == 0,
                     f"Found {orphaned_recipes.count()} recipes without products")

            recipe_ingredients = RecipeIngredient.objects.count()
            self.test("Recipe ingredients exist", recipe_ingredients > 0,
                     f"Found {recipe_ingredients} recipe-ingredient relationships")

    def test_order_data(self):
        """Validate order data"""
        print("\n[Order Model Validation]")

        order_count = Order.objects.count()
        self.test("Orders exist", order_count > 0, f"Found {order_count} orders")

        if order_count > 0:
            invalid_amounts = Order.objects.filter(total_amount__lt=0)
            self.test("All orders have non-negative amounts", invalid_amounts.count() == 0,
                     f"Found {invalid_amounts.count()} orders with negative amounts")

            invalid_status = Order.objects.exclude(status__in=['PENDING', 'IN_PROGRESS', 'FINISHED', 'CANCELLED', 'EXPIRED'])
            self.test("All orders have valid status", invalid_status.count() == 0,
                     f"Found {invalid_status.count()} orders with invalid status")

    def test_payment_data(self):
        """Validate payment data"""
        print("\n[Payment Model Validation]")

        payment_count = Payment.objects.count()
        self.test("Payments exist", payment_count > 0, f"Found {payment_count} payments")

        if payment_count > 0:
            invalid_method = Payment.objects.exclude(method__in=['CASH', 'ONLINE'])
            self.test("All payments have valid methods", invalid_method.count() == 0,
                     f"Found {invalid_method.count()} payments with invalid methods")

            invalid_status = Payment.objects.exclude(status__in=['PENDING', 'SUCCESS', 'FAILED'])
            self.test("All payments have valid status", invalid_status.count() == 0,
                     f"Found {invalid_status.count()} payments with invalid status")

            negative_amounts = Payment.objects.filter(amount__lt=0)
            self.test("All payments have non-negative amounts", negative_amounts.count() == 0,
                     f"Found {negative_amounts.count()} payments with negative amounts")

    def test_stock_transactions(self):
        """Validate stock transactions"""
        print("\n[StockTransaction Model Validation]")

        transaction_count = StockTransaction.objects.count()
        self.test("Stock transactions exist", transaction_count > 0,
                 f"Found {transaction_count} transactions")

        if transaction_count > 0:
            invalid_type = StockTransaction.objects.exclude(
                transaction_type__in=['PURCHASE', 'DEDUCTION', 'ADJUSTMENT', 'WASTE', 'FREEBIE', 'PREP']
            )
            self.test("All transactions have valid type", invalid_type.count() == 0,
                     f"Found {invalid_type.count()} transactions with invalid type")

    def test_physical_counts(self):
        """Validate physical counts"""
        print("\n[PhysicalCount Model Validation]")

        count_count = PhysicalCount.objects.count()
        if count_count > 0:
            self.test("Physical counts exist", True, f"Found {count_count} counts")

            missing_ingredient = PhysicalCount.objects.filter(ingredient__isnull=True)
            self.test("All counts have ingredients", missing_ingredient.count() == 0,
                     f"Found {missing_ingredient.count()} counts without ingredients")

    def test_waste_logs(self):
        """Validate waste logs"""
        print("\n[WasteLog Model Validation]")

        waste_count = WasteLog.objects.count()
        if waste_count > 0:
            self.test("Waste logs exist", True, f"Found {waste_count} waste entries")

            invalid_type = WasteLog.objects.exclude(waste_type__in=['SPOILAGE', 'WASTE', 'FREEBIE', 'SAMPLE', 'OTHER'])
            self.test("All waste logs have valid type", invalid_type.count() == 0,
                     f"Found {invalid_type.count()} waste logs with invalid type")

    def test_prep_batches(self):
        """Validate prep batches"""
        print("\n[PrepBatch Model Validation]")

        batch_count = PrepBatch.objects.count()
        if batch_count > 0:
            self.test("Prep batches exist", True, f"Found {batch_count} batches")

            invalid_status = PrepBatch.objects.exclude(status__in=['PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'])
            self.test("All batches have valid status", invalid_status.count() == 0,
                     f"Found {invalid_status.count()} batches with invalid status")

    def test_variance_records(self):
        """Validate variance records"""
        print("\n[VarianceRecord Model Validation]")

        variance_count = VarianceRecord.objects.count()
        if variance_count > 0:
            self.test("Variance records exist", True, f"Found {variance_count} records")

            missing_ingredient = VarianceRecord.objects.filter(ingredient__isnull=True)
            self.test("All variance records have ingredients", missing_ingredient.count() == 0,
                     f"Found {missing_ingredient.count()} records without ingredients")


class RelationshipTests(QATest):
    """Test model relationships"""

    def run_all(self):
        """Run all relationship tests"""
        self.section("MODEL RELATIONSHIP TESTS")

        self.test_order_payment_relationships()
        self.test_order_item_relationships()
        self.test_recipe_ingredient_relationships()
        self.test_stock_transaction_references()

        return self.print_summary()

    def test_order_payment_relationships(self):
        """Test Order-Payment 1:1 relationship"""
        print("\n[Order-Payment Relationships]")

        orders_with_payments = Order.objects.filter(payment__isnull=False).count()
        orders_without_payments = Order.objects.filter(payment__isnull=True).count()

        self.test("Orders have associated payments", orders_without_payments == 0,
                 f"Found {orders_without_payments} orders without payments")

    def test_order_item_relationships(self):
        """Test Order-OrderItem relationships"""
        print("\n[Order-OrderItem Relationships]")

        orders_with_items = Order.objects.filter(items__isnull=False).distinct().count()
        orders_without_items = Order.objects.filter(items__isnull=True).count()

        self.test("Orders have items", orders_without_items <= 1 or orders_without_items == 0,
                 f"Found {orders_without_items} orders without items (expected ~0)")

    def test_recipe_ingredient_relationships(self):
        """Test RecipeItem-RecipeIngredient relationships"""
        print("\n[Recipe-Ingredient Relationships]")

        recipes = RecipeItem.objects.count()
        if recipes > 0:
            recipes_with_ingredients = RecipeItem.objects.filter(ingredients__isnull=False).distinct().count()
            self.test("Recipes have ingredients", recipes_with_ingredients > 0,
                     f"Found {recipes_with_ingredients} recipes with ingredients")

    def test_stock_transaction_references(self):
        """Test StockTransaction reference consistency"""
        print("\n[StockTransaction Reference Consistency]")

        transactions = StockTransaction.objects.count()
        if transactions > 0:
            deductions = StockTransaction.objects.filter(transaction_type='DEDUCTION')
            deductions_with_order = deductions.filter(reference_type='order', reference_id__isnull=False).count()

            self.test("Deduction transactions have order references",
                     deductions_with_order == deductions.count() or deductions.count() == 0,
                     f"Deductions: {deductions.count()}, With references: {deductions_with_order}")


class WebEndpointTests(QATest):
    """Test web application endpoints"""

    def run_all(self):
        """Run all endpoint tests"""
        self.section("WEB ENDPOINT TESTS")

        self.test_admin_site()
        self.test_database_connectivity()

        return self.print_summary()

    def test_admin_site(self):
        """Test Django admin site accessibility"""
        print("\n[Admin Site Access]")

        try:
            # Check if admin is configured
            from django.contrib.admin.sites import site
            self.test("Django admin is configured", len(site._registry) > 0,
                     f"Found {len(site._registry)} registered models")
        except Exception as e:
            self.test("Django admin access", False, str(e))

    def test_database_connectivity(self):
        """Test database connectivity"""
        print("\n[Database Connectivity]")

        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                self.test("Database connection works", result is not None)
        except Exception as e:
            self.test("Database connection", False, str(e))


def main():
    """Run all QA tests"""
    print("\n" + "="*60)
    print("FJC-PIZZA QA TEST SUITE")
    print("="*60)

    all_passed = True

    # Run data integrity tests
    integrity_tests = DataIntegrityTests()
    all_passed &= integrity_tests.run_all()

    # Run relationship tests
    relationship_tests = RelationshipTests()
    all_passed &= relationship_tests.run_all()

    # Run endpoint tests
    endpoint_tests = WebEndpointTests()
    all_passed &= endpoint_tests.run_all()

    # Final summary
    print("\n" + "="*60)
    if all_passed:
        print("ALL QA TESTS PASSED!")
    else:
        print("SOME QA TESTS FAILED - PLEASE REVIEW")
    print("="*60 + "\n")

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
