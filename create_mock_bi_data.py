import csv
import os
import random
from datetime import datetime, timedelta

# Create directory
output_dir = 'bi_exports'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print(f"🚀 Generating FULL COMPREHENSIVE Mock BI Data for FJC Pizza...")

# --- 1. Dim Products ---
product_list = [
    (1, 'Margherita Pizza', 'Pizzas', 299.00, 50, 10, True, False),
    (2, 'Pepperoni Pizza', 'Pizzas', 349.00, 45, 10, True, False),
    (3, 'Hawaiian Pizza', 'Pizzas', 329.00, 40, 10, True, False),
    (4, 'Four Cheese Pizza', 'Pizzas', 379.00, 30, 10, True, False),
    (5, 'Garlic Bread', 'Sides', 89.00, 100, 20, False, False),
    (6, 'Chicken Wings (6pcs)', 'Sides', 199.00, 60, 15, False, False),
    (7, 'Coca-Cola (500ml)', 'Drinks', 49.00, 200, 50, False, False),
    (8, 'Iced Tea (500ml)', 'Drinks', 39.00, 150, 40, False, False),
]

with open(os.path.join(output_dir, 'dim_products.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['ID', 'Name', 'Category', 'Price', 'Stock', 'Threshold', 'Requires_BOM', 'Is_Archived'])
    for p in product_list:
        writer.writerow(p)

# --- 2. Dim Ingredients ---
ingredient_list = [
    (1, 'Pizza Dough', 'pcs', 150, 20, 5, True),
    (2, 'Tomato Sauce', 'ml', 5000, 1000, 5, True),
    (3, 'Mozzarella Cheese', 'g', 8000, 2000, 5, True),
    (4, 'Pepperoni Slices', 'g', 3000, 500, 5, True),
    (5, 'Pineapple Tidbits', 'g', 2000, 500, 5, True),
    (6, 'Ham', 'g', 3000, 500, 5, True),
]

with open(os.path.join(output_dir, 'dim_ingredients.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['ID', 'Name', 'Unit', 'Current_Stock', 'Min_Stock', 'Variance_Allowance', 'Is_Active'])
    for ing in ingredient_list:
        writer.writerow(ing)

# --- 3. Dim Users ---
user_list = [
    ('admin', 'ADMIN', 'admin@fjcpizza.com', '2025-01-01T08:00:00'),
    ('cashier_maria', 'CASHIER', 'maria@fjcpizza.com', '2025-01-10T09:00:00'),
    ('cashier_jose', 'CASHIER', 'jose@fjcpizza.com', '2025-01-12T09:00:00'),
]

with open(os.path.join(output_dir, 'dim_users.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Username', 'Role', 'Email', 'Date_Joined'])
    for u in user_list:
        writer.writerow(u)

# --- 4. Dim Recipes (BOM) ---
recipe_list = [
    ('Margherita Pizza', 'Pizza Dough', 1),
    ('Margherita Pizza', 'Tomato Sauce', 100),
    ('Margherita Pizza', 'Mozzarella Cheese', 150),
    ('Pepperoni Pizza', 'Pizza Dough', 1),
    ('Pepperoni Pizza', 'Tomato Sauce', 100),
    ('Pepperoni Pizza', 'Mozzarella Cheese', 150),
    ('Pepperoni Pizza', 'Pepperoni Slices', 50),
    ('Hawaiian Pizza', 'Pizza Dough', 1),
    ('Hawaiian Pizza', 'Tomato Sauce', 100),
    ('Hawaiian Pizza', 'Mozzarella Cheese', 150),
    ('Hawaiian Pizza', 'Pineapple Tidbits', 60),
    ('Hawaiian Pizza', 'Ham', 60),
]

with open(os.path.join(output_dir, 'dim_recipes.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Product_Name', 'Ingredient_Name', 'Quantity_Required'])
    for r in recipe_list:
        writer.writerow(r)

# --- 5. Fact Sales ---
with open(os.path.join(output_dir, 'fact_sales.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Order_ID', 'Order_Number', 'Customer', 'Table', 'Status', 'Total_Amount', 'Order_Date', 'Processed_By_Username', 'Item_Product', 'Item_Category', 'Item_Quantity', 'Item_Price', 'Item_Subtotal'])
    
    start_date = datetime.now() - timedelta(days=90)
    for i in range(1, 401): # 400 sales items
        order_id = (i + 1) // 2
        order_date = start_date + timedelta(days=random.randint(0, 89), hours=random.randint(10, 21), minutes=random.randint(0, 59))
        p_id, p_name, p_cat, p_price, _, _, _, _ = random.choice(product_list)
        qty = random.randint(1, 2)
        subtotal = p_price * qty
        writer.writerow([order_id, f"ORD-{order_id:05d}", f"Customer {order_id}", f"T{random.randint(1, 10)}", 'FINISHED', subtotal, order_date.isoformat(), random.choice(['cashier_maria', 'cashier_jose']), p_name, p_cat, qty, p_price, subtotal])

# --- 6. Fact Stock Transactions ---
with open(os.path.join(output_dir, 'fact_stock_transactions.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['ID', 'Ingredient_Name', 'Type', 'Quantity', 'Reference_Type', 'Reference_ID', 'Date', 'Recorded_By'])
    for i in range(1, 101):
        writer.writerow([i, random.choice(ingredient_list)[1], 'DEDUCTION', random.uniform(1, 5), 'order', random.randint(1, 200), (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(), 'admin'])

# --- 7. Fact Waste ---
with open(os.path.join(output_dir, 'fact_waste.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['ID', 'Ingredient_Name', 'Type', 'Quantity', 'Reason', 'Date', 'Reported_By'])
    for i in range(1, 41):
        writer.writerow([i, random.choice(ingredient_list)[1], random.choice(['SPOILAGE', 'WASTE']), round(random.uniform(0.1, 2.0), 2), 'Damaged/Expired', (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(), 'admin'])

# --- 8. Fact Inventory Counts ---
with open(os.path.join(output_dir, 'fact_inventory_counts.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['ID', 'Ingredient_Name', 'Physical_Qty', 'Theoretical_Qty', 'Variance', 'Date', 'Counted_By'])
    for i in range(1, 21):
        theo = random.uniform(100, 500)
        phys = theo * random.uniform(0.95, 1.02)
        writer.writerow([i, random.choice(ingredient_list)[1], round(phys, 2), round(theo, 2), round(phys - theo, 2), (datetime.now() - timedelta(days=7 * i)).isoformat(), 'admin'])

print(f"✅ ALL 8 COMPREHENSIVE reports generated in '{output_dir}'")
print(f"FILES READY FOR POWER BI:")
for file in os.listdir(output_dir):
    print(f" - {file}")
