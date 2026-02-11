import csv
import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from sales_inventory_system.products.models import Product, Ingredient, StockTransaction, PhysicalCount, WasteLog, RecipeIngredient
from sales_inventory_system.orders.models import Order, OrderItem, Payment
from sales_inventory_system.accounts.models import User

class Command(BaseCommand):
    help = 'Export all business data to CSV files for Power BI analysis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='bi_exports',
            help='Directory to save CSV files'
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            self.stdout.write(f"Created directory: {output_dir}")

        self.stdout.write("🚀 Starting Data Export for Power BI...")

        self.export_orders(output_dir)
        self.export_products(output_dir)
        self.export_ingredients(output_dir)
        self.export_stock_transactions(output_dir)
        self.export_waste_logs(output_dir)
        self.export_physical_counts(output_dir)
        self.export_users(output_dir)
        self.export_recipes(output_dir)

        self.stdout.write(self.style.SUCCESS(f"\n✅ All exports completed! Files saved in: {os.path.abspath(output_dir)}"))

    def export_orders(self, output_dir):
        self.stdout.write("  Exporting Orders & Items...")
        file_path = os.path.join(output_dir, 'fact_sales.csv')
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Order_ID', 'Order_Number', 'Customer', 'Table', 'Status', 
                'Total_Amount', 'Order_Date', 'Processed_By_Username',
                'Item_Product', 'Item_Category', 'Item_Quantity', 'Item_Price', 'Item_Subtotal'
            ])
            
            items = OrderItem.objects.select_related('order', 'order__processed_by', 'product').all()
            for item in items:
                writer.writerow([
                    item.order.id,
                    item.order.order_number,
                    item.order.customer_name,
                    item.order.table_number,
                    item.order.status,
                    item.order.total_amount,
                    item.order.created_at.isoformat(),
                    item.order.processed_by.username if item.order.processed_by else 'N/A',
                    item.product_name,
                    item.product.category if item.product else 'N/A',
                    item.quantity,
                    item.product_price,
                    item.subtotal
                ])

    def export_products(self, output_dir):
        self.stdout.write("  Exporting Products...")
        file_path = os.path.join(output_dir, 'dim_products.csv')
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Name', 'Category', 'Price', 'Stock', 'Threshold', 'Requires_BOM', 'Is_Archived'])
            
            for p in Product.objects.all():
                writer.writerow([p.id, p.name, p.category, p.price, p.stock, p.threshold, p.requires_bom, p.is_archived])

    def export_ingredients(self, output_dir):
        self.stdout.write("  Exporting Ingredients...")
        file_path = os.path.join(output_dir, 'dim_ingredients.csv')
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Name', 'Unit', 'Current_Stock', 'Min_Stock', 'Variance_Allowance', 'Is_Active'])
            
            for i in Ingredient.objects.all():
                writer.writerow([i.id, i.name, i.unit, i.current_stock, i.min_stock, i.variance_allowance, i.is_active])

    def export_stock_transactions(self, output_dir):
        self.stdout.write("  Exporting Stock Transactions...")
        file_path = os.path.join(output_dir, 'fact_stock_transactions.csv')
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Ingredient_Name', 'Type', 'Quantity', 'Reference_Type', 'Reference_ID', 'Date', 'Recorded_By'])
            
            for t in StockTransaction.objects.select_related('ingredient', 'recorded_by').all():
                writer.writerow([
                    t.id, 
                    t.ingredient.name, 
                    t.transaction_type, 
                    t.quantity, 
                    t.reference_type, 
                    t.reference_id, 
                    t.created_at.isoformat(), 
                    t.recorded_by.username if t.recorded_by else 'System'
                ])

    def export_waste_logs(self, output_dir):
        self.stdout.write("  Exporting Waste Logs...")
        file_path = os.path.join(output_dir, 'fact_waste.csv')
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Ingredient_Name', 'Type', 'Quantity', 'Reason', 'Date', 'Reported_By'])
            
            for w in WasteLog.objects.select_related('ingredient', 'reported_by').all():
                writer.writerow([
                    w.id,
                    w.ingredient.name,
                    w.waste_type,
                    w.quantity,
                    w.reason,
                    w.waste_date.isoformat(),
                    w.reported_by.username if w.reported_by else 'N/A'
                ])

    def export_physical_counts(self, output_dir):
        self.stdout.write("  Exporting Physical Counts...")
        file_path = os.path.join(output_dir, 'fact_inventory_counts.csv')
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Ingredient_Name', 'Physical_Qty', 'Theoretical_Qty', 'Variance', 'Date', 'Counted_By'])
            
            for c in PhysicalCount.objects.select_related('ingredient', 'counted_by').all():
                writer.writerow([
                    c.id,
                    c.ingredient.name,
                    c.physical_quantity,
                    c.theoretical_quantity,
                    c.variance_quantity,
                    c.count_date.isoformat(),
                    c.counted_by.username if c.counted_by else 'N/A'
                ])

    def export_users(self, output_dir):
        self.stdout.write("  Exporting Users...")
        file_path = os.path.join(output_dir, 'dim_users.csv')
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Username', 'Role', 'Email', 'Date_Joined'])
            
            for u in User.objects.all():
                writer.writerow([u.username, u.role, u.email, u.date_joined.isoformat()])

    def export_recipes(self, output_dir):
        """Export Recipes (BOM) to allow Power BI to calculate theoretical usage"""
        self.stdout.write("  Exporting Recipes (BOM)...")
        file_path = os.path.join(output_dir, 'dim_recipes.csv')
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Product_Name', 'Ingredient_Name', 'Quantity_Required'])
            
            for ri in RecipeIngredient.objects.select_related('recipe__product', 'ingredient').all():
                writer.writerow([
                    ri.recipe.product.name,
                    ri.ingredient.name,
                    ri.quantity
                ])
