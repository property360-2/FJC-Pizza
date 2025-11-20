# FJC Pizza - Comprehensive Data Seeder Guide

## Overview
A complete Django management command that seeds realistic test data for the entire FJC Pizza sales & inventory system. The seeder populates all models across all apps with interconnected, realistic data.

## File Location
```
sales_inventory_system/products/management/commands/seed_data.py
```

## What Gets Seeded

### 1. **Accounts (Users)**
- **1 Admin User**
  - Username: `admin`
  - Password: `admin123`
  - Email: `admin@fjcpizza.com`
  - Role: ADMIN with full permissions

- **4 Cashier Users**
  - Names: Maria Garcia, John Smith, Sarah Johnson, Carlos Martinez
  - Usernames: `cashier1`, `cashier2`, `cashier3`, `cashier4`
  - Password: `cashier123` (for all)
  - Emails: `cashier1@fjcpizza.com`, etc.

### 2. **Products (8 Items)**
**Pizzas (4):**
- Margherita Pizza - $12.99
- Pepperoni Pizza - $14.99
- Vegetarian Pizza - $13.99
- Supreme Pizza - $16.99

**Beverages (2):**
- Cola - $2.99
- Lemonade - $3.49

**Sides (2):**
- Garlic Bread - $4.99
- Caesar Salad - $7.99

### 3. **Ingredients (12 Raw Materials)**
- Pizza Flour (50 kg @ $2.50/kg)
- Mozzarella Cheese (30 kg @ $8.00/kg)
- Tomato Sauce (25 L @ $3.50/L)
- Pepperoni (10 kg @ $12.00/kg)
- Fresh Basil (500 g @ $0.05/g)
- Olive Oil (20 L @ $15.00/L)
- Mushrooms (8 kg @ $4.00/kg)
- Bell Peppers (6 kg @ $3.50/kg)
- Onions (15 kg @ $1.50/kg)
- Yeast (200 g @ $0.20/g)
- Salt (10 kg @ $0.50/kg)
- Water (100 L @ $0.20/L)

### 4. **Recipes/BOM (8 Complete Recipes)**
Every product has a complete bill of materials with specific ingredient quantities:

**Pizzas (4):**
- **Margherita**: Flour, Tomato Sauce, Cheese, Basil, Olive Oil, Yeast, Salt, Water
- **Pepperoni**: Flour, Tomato Sauce, Cheese, Pepperoni, Olive Oil, Yeast, Salt, Water
- **Vegetarian**: Flour, Tomato Sauce, Cheese, Mushrooms, Peppers, Onions, Olive Oil, Yeast, Salt, Water
- **Supreme**: Flour, Tomato Sauce, Cheese, Pepperoni, Mushrooms, Peppers, Onions, Olive Oil, Yeast, Salt, Water

**Sides (2):**
- **Garlic Bread**: Flour, Olive Oil, Salt, Water, Yeast
- **Caesar Salad**: Onions, Bell Peppers, Olive Oil, Salt

**Beverages (2):**
- **Cola**: Water, Salt (simplified BOM)
- **Lemonade**: Water, Salt (simplified BOM)

### 5. **Stock Management Data**
- **Stock Transactions**: 36-60 transactions (3-5 per ingredient)
  - Types: PURCHASE, ADJUSTMENT, WASTE, PREP
  - Spread over past 30 days

- **Physical Counts**: 12-24 records (1-2 per ingredient)
  - Variance simulation: ±5% tolerance

- **Variance Records**: 12-24 records per ingredient
  - Analyzes theoretical vs actual usage
  - Checks tolerance compliance

- **Waste Logs**: ~10-15 entries (for 6 sample ingredients)
  - Types: SPOILAGE, WASTE, FREEBIE, SAMPLE

- **Prep Batches**: 8-24 batches (1-3 per product recipe)
  - Status variations: PLANNED, IN_PROGRESS, COMPLETED, CANCELLED

### 6. **Orders & Payments**
- **20-30 Customer Orders** (randomly distributed over past 30 days)
  - Random customer names
  - Table numbers (1-20)
  - Status: PENDING, IN_PROGRESS, FINISHED, CANCELLED
  - 1-4 items per order
  - Automatic total calculation

- **Payments** (for completed/in-progress orders)
  - Methods: CASH or ONLINE
  - Status: SUCCESS or PENDING
  - Reference numbers auto-generated

### 7. **Audit Trails**
- **30 Audit Log Entries**
  - Actions: CREATE, UPDATE, DELETE, ARCHIVE, RESTORE
  - Covers all major models: Product, Order, Payment, Ingredient, Recipe

## How to Run

### Option 1: Run from Django Management Command
```bash
# Navigate to project root
cd C:\Users\Administrator\Desktop\projects\FJC-Pizza

# Run the seeder
python manage.py seed_data

# Expected output:
# Starting comprehensive data seeding...
# Creating users...
# Created admin user: admin
# Created cashier: cashier1
# ...
# ✓ Data seeding completed successfully!
```

### Option 2: Run from Interactive Shell
```bash
python manage.py shell
>>> from products.management.commands.seed_data import Command
>>> cmd = Command()
>>> cmd.handle()
```

## Data Characteristics

### Realistic Features
✓ **Interconnected Data**: Products link to recipes, recipes link to ingredients, orders link to products
✓ **Time Distributed**: Data spread over 30 days with realistic timestamps
✓ **Variance Simulation**: Stock counts include realistic variance for testing reports
✓ **User Assignments**: Orders processed by actual cashiers, ingredients managed by admin
✓ **Complete Workflow**: From raw ingredients → recipes → products → orders → payments

### Volume
- **Total Records Created**: ~200+ records across all models
- **Users**: 5
- **Products**: 8
- **Ingredients**: 12
- **Recipes**: 4
- **Orders**: 20-30
- **Transaction Records**: 100+
- **Audit Logs**: 30

## Key Use Cases

### Testing Features
1. **Order Management**: Test order creation, payment processing, status workflow
2. **Inventory Tracking**: Test ingredient stock levels, variance analysis, physical counts
3. **Reporting**: Test sales reports, inventory reports, waste tracking
4. **User Management**: Test role-based access (admin vs cashier)
5. **Audit Trail**: Test audit logging and compliance tracking
6. **Recipe Management**: Test BOM functionality, cost calculations

### Dashboard Analytics
- Order trends over 30 days
- Product performance
- Ingredient variance analysis
- Waste tracking and cost analysis
- User activity logs

## Running Tests with Seeded Data

```bash
# Run tests with seeded data
python manage.py test --keepdb

# The seeded data persists between test runs when using --keepdb
```

## Clearing and Re-Seeding

To reset all data:
```bash
# Delete all data (careful!)
python manage.py flush

# Re-seed fresh data
python manage.py seed_data
```

Or to keep specific data:
```bash
# The seeder uses get_or_create, so running it again won't duplicate data
# but won't create new batches of orders or transactions either
```

## Extending the Seeder

To add more data, edit the methods in `seed_data.py`:
1. `create_users()` - Add more users
2. `create_ingredients()` - Add more raw materials
3. `create_products()` - Add more menu items
4. `create_recipes()` - Add more BOMs
5. `create_orders()` - Increase order volume
6. Any method can be modified to customize data

## Notes

- All timestamps are automatically set to appropriate dates
- Passwords are hardcoded for demo purposes (change in production!)
- The seeder is idempotent - running it multiple times won't create duplicates
- Order numbers are auto-generated with UUID
- Product prices and ingredient costs are realistic for a pizza restaurant

## Testing Checklist

After running the seeder, verify:
- [ ] Admin can login with admin/admin123
- [ ] Cashiers can login with their credentials
- [ ] 8 products appear in the system
- [ ] 12 ingredients are available
- [ ] 4 pizza recipes with complete BOMs exist
- [ ] 20+ orders exist in the system
- [ ] Orders have associated payments
- [ ] Stock transactions are logged
- [ ] Waste logs show various waste types
- [ ] Audit trail has entries for actions
- [ ] Physical counts show variance data
