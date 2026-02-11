import csv
import os
import random
from datetime import datetime, timedelta

# Create directory
output_dir = 'bi_exports'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print(f"🚀 Generating Mock BI Data for FJC Pizza...")

# 1. Fact Sales
products = [
    ('Margherita Pizza', 'Pizzas', 299.00),
    ('Pepperoni Pizza', 'Pizzas', 349.00),
    ('Hawaiian Pizza', 'Pizzas', 329.00),
    ('Four Cheese Pizza', 'Pizzas', 379.00),
    ('Buffalo Wings', 'Sides', 199.00),
    ('Coca-Cola', 'Drinks', 49.00),
]
cashiers = ['maria', 'jose', 'john']

with open(os.path.join(output_dir, 'fact_sales.csv'), 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Order_ID', 'Order_Number', 'Customer', 'Table', 'Status', 'Total_Amount', 'Order_Date', 'Processed_By_Username', 'Item_Product', 'Item_Category', 'Item_Quantity', 'Item_Price', 'Item_Subtotal'])
    
    start_date = datetime.now() - timedelta(days=90)
    for i in range(500): # 500 sales items
        order_id = i // 2
        order_date = start_date + timedelta(days=random.randint(0, 90), hours=random.randint(10, 21))
        prod_name, cat, price = random.choice(products)
        qty = random.randint(1, 3)
        subtotal = price * qty
        writer.writerow([order_id, f"ORD-{order_id:04d}", f"Customer {i}", random.randint(1, 15), 'FINISHED', subtotal, order_date.isoformat(), random.choice(cashiers), prod_name, cat, qty, price, subtotal])

# 2. Fact Waste
ingredients = ['Dough', 'Cheese', 'Tomato Sauce', 'Pepperoni', 'Pineapple']
with open(os.path.join(output_dir, 'fact_waste.csv'), 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['ID', 'Ingredient_Name', 'Type', 'Quantity', 'Reason', 'Date', 'Reported_By'])
    for i in range(50):
        writer.writerow([i, random.choice(ingredients), random.choice(['SPOILAGE', 'WASTE']), random.uniform(0.5, 5.0), 'Accident', (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(), 'admin'])

# 3. Dim Recipes (BOM)
with open(os.path.join(output_dir, 'dim_recipes.csv'), 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Product_Name', 'Ingredient_Name', 'Quantity_Required'])
    writer.writerow(['Margherita Pizza', 'Dough', 300])
    writer.writerow(['Margherita Pizza', 'Cheese', 150])
    writer.writerow(['Pepperoni Pizza', 'Dough', 300])
    writer.writerow(['Pepperoni Pizza', 'Pepperoni', 50])

print(f"✅ Mock reports generated in {output_dir}")
