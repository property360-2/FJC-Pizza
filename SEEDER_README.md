# FJC Pizza Data Seeder

Comprehensive data seeder for the FJC Pizza Sales & Inventory System with built-in validation and error checking.

## Features

✅ **Validation Checks**:
- Validates all required model files exist
- Checks if models can be imported
- Verifies database migrations are applied
- Prevents duplicate data creation

✅ **Comprehensive Data**:
- 4 demo users (1 admin, 3 cashiers)
- 23 products across 4 categories
- 10 sample orders with varied statuses
- Realistic test data for all features

✅ **Safe Execution**:
- Confirmation prompt before seeding
- Skips existing records
- Detailed progress output
- Error handling and rollback

## Prerequisites

1. **Python Environment**: Ensure you're in the correct directory
2. **Virtual Environment**: Activate if using one
3. **Database**: Migrations must be applied

## Usage

### Option 1: Standalone Python Script (Recommended)

```bash
# From the project root directory
python seed_data.py
```

### Option 2: Django Management Command

```bash
# Navigate to the sales_inventory_system directory
cd sales_inventory_system

# Run the management command
python manage.py populate_demo_data
```

## What Gets Created

### Users (4 total)

| Username | Password    | Role    | Name         |
|----------|-------------|---------|--------------|
| admin    | admin123    | ADMIN   | (superuser)  |
| cashier  | cashier123  | CASHIER | John Doe     |
| maria    | maria123    | CASHIER | Maria Santos |
| jose     | jose123     | CASHIER | Jose Reyes   |
| manager  | manager123  | ADMIN   | Ana Garcia   |

### Products (23 total)

- **8 Pizzas**: Margherita, Pepperoni, Hawaiian, Supreme, Four Cheese, BBQ Chicken, Veggie Supreme, Meat Lovers
- **6 Sides**: Garlic Bread, Chicken Wings, Mozzarella Sticks, French Fries, Onion Rings, Caesar Salad, Buffalo Wings
- **5 Drinks**: Coca-Cola, Sprite, Iced Tea, Water, Orange Juice
- **3 Desserts**: Chocolate Brownie, Tiramisu, Cheesecake
- **1 Low Stock Item**: Buffalo Wings (for testing alerts)

### Orders (10 total)

- **2 PENDING**: Awaiting payment confirmation
- **3 IN_PROGRESS**: Being prepared
- **5 FINISHED**: Completed orders
- Mixed payment methods (CASH and ONLINE)
- Timestamps spread across 10 hours

## Validation Process

The seeder performs these checks before running:

1. ✅ Django environment setup
2. ✅ Model files existence check:
   - `accounts/models.py`
   - `analytics/models.py`
   - `orders/models.py`
   - `products/models.py`
   - `system/models.py`
3. ✅ Model import validation
4. ✅ Database migration status
5. ✅ User confirmation

## Error Handling

If the seeder encounters errors:

- **Missing model files**: Lists which files are missing
- **Import errors**: Shows the problematic model
- **Unapplied migrations**: Prompts to run `python manage.py migrate`
- **Duplicate data**: Skips and reports existing records

## Sample Output

```
============================================================
🌱 FJC PIZZA DATA SEEDER
============================================================
✅ Django environment setup successful

🔍 Validating model files...
  ✅ Found: accounts/models.py
  ✅ Found: analytics/models.py
  ✅ Found: orders/models.py
  ✅ Found: products/models.py
  ✅ Found: system/models.py
✅ All model files found

🔍 Validating models...
  ✅ User model imported
  ✅ Product model imported
  ✅ Order, OrderItem, Payment models imported
  ✅ AuditTrail, Archive models imported
✅ All models validated successfully

🔍 Checking database migrations...
✅ All migrations applied

⚠️  This will add demo data to your database.
Continue? (y/N): y

🚀 Starting data seeding...

👥 Seeding users...
  ✅ Created: cashier (CASHIER)
  ✅ Created: maria (CASHIER)
  ✅ Created: jose (CASHIER)
  ✅ Created: manager (ADMIN)

📊 Users: 4 created, 0 skipped

🍕 Seeding products...
  ✅ Created: Margherita Pizza
  ✅ Created: Pepperoni Pizza
  ...

📊 Products: 23 created, 0 skipped, 1 low stock

📦 Seeding orders...
  ✅ Created: ORD-A1B2C3D4 (PENDING, CASH)
  ...

📊 Orders: 10 created, 0 already existed

============================================================
📊 DATABASE SUMMARY
============================================================

👥 Users: 5 total (2 admins, 3 cashiers)
🍕 Products: 23 total, 1 low stock
   Categories: Pizza, Sides, Drinks, Desserts
📦 Orders: 10 total
   - 2 pending
   - 3 in progress
   - 5 finished

============================================================
🔑 LOGIN CREDENTIALS
============================================================

Admin:
  Username: admin
  Password: admin123

Cashiers:
  cashier / cashier123
  maria / maria123
  jose / jose123

Manager:
  manager / manager123

============================================================

✅ Data seeding completed successfully!

💡 Tip: Run 'python manage.py runserver' to start the application
```

## Troubleshooting

### "No module named 'sales_inventory'"

Make sure you're running from the project root directory:
```bash
cd /path/to/FJC-Pizza
python seed_data.py
```

### "Unapplied migrations found"

Run migrations first:
```bash
cd sales_inventory_system
python manage.py migrate
```

### "Cannot import models"

Ensure Django is properly installed:
```bash
pip install -r requirements.txt
```

### Data Already Exists

The seeder will skip existing records and only create new ones. To completely reset:
```bash
# WARNING: This deletes all data!
cd sales_inventory_system
python manage.py flush
python manage.py migrate
cd ..
python seed_data.py
```

## Testing Workflows

After seeding, you can test:

1. **Guest Ordering**: Visit kiosk → Add items → Checkout
2. **Staff Payment Confirmation**: Login as cashier → Confirm pending payment
3. **POS Ordering**: Login as cashier → Click "New Order" → Create order
4. **User Management**: Login as admin → Manage Users → CRUD operations
5. **Low Stock Alerts**: Admin dashboard shows Buffalo Wings with low stock
6. **Analytics**: View sales data, top products, revenue metrics

## Next Steps

After successful seeding:

1. Start the development server:
   ```bash
   cd sales_inventory_system
   python manage.py runserver
   ```

2. Access the application:
   - Admin Panel: http://127.0.0.1:8000/admin/
   - Kiosk: http://127.0.0.1:8000/kiosk/
   - Login: http://127.0.0.1:8000/accounts/login/

3. Test the workflows with the provided credentials

## Support

For issues or questions:
- Check the main README.md
- Review error messages carefully
- Ensure all prerequisites are met
- Verify model files are intact
