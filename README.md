# 🍕 FJC Pizza - Sales & Inventory Management System

A modern, Django-powered Sales and Inventory Management System built for FJC Pizza, featuring a beautiful light mode design with yellow and blue accents, atomic reusable components, and role-based access control.

## 🎨 Design Philosophy

- **Modern Light Mode**: Clean, bright interface with yellow (#f59e0b) and blue (#3b82f6) brand colors
- **Atomic Design**: Reusable components organized as Atoms → Molecules → Organisms
- **Mobile-First**: Responsive design that works seamlessly on all devices
- **User-Centric UX**: Intuitive workflows optimized for speed and efficiency

## ✨ Features

### 🔐 Role-Based Access Control
- **Admin**: Full system access - manage products, users, view analytics, audit logs
- **Cashier**: POS interface - process orders, handle payments, manage order status
- **Customer**: Public kiosk - browse menu, place orders, track order status

### 📦 Product Management
- Complete CRUD operations for products
- Stock level tracking with low-stock alerts
- Image upload support
- Category organization
- Soft delete (archive) system

### 🛒 Order Processing
- Real-time order tracking
- Order status workflow: Pending → In Progress → Finished
- Support for both cash and online demo payments
- Customer-facing kiosk interface
- QR code ordering capability

### 💰 Payment System
- Cash payment processing
- Online payment simulation
- Automatic stock deduction on successful payment
- Payment history and receipts

### 📊 Analytics & Reporting
- Sales dashboard with key metrics
- Revenue tracking (daily, weekly, monthly)
- Top-selling products analysis
- Low-stock inventory alerts
- Cashier performance metrics

### 🔍 Audit Trail & Archive
- Complete action logging for transparency
- JSON snapshots of all changes
- Non-destructive data archiving
- Full audit history with user tracking

## 🛠 Tech Stack

- **Backend**: Django 5.2.8
- **Database**: SQLite (development) / MySQL (production)
- **Frontend**: Django Templates + Tailwind CSS (CDN)
- **JavaScript**: Alpine.js + HTMX for interactivity
- **Image Processing**: Pillow

## 📁 Project Structure

```
FJC-Pizza/
├── Documentation/           # Project documentation
│   ├── concept.md          # System concept and vision
│   ├── phase.md            # Development phases
│   └── schema.md           # Database schema
├── sales_inventory_system/
│   ├── accounts/           # User management & authentication
│   ├── analytics/          # Analytics & reporting
│   ├── orders/             # Order & payment processing
│   ├── products/           # Product inventory management
│   ├── sales_inventory/    # Main project settings
│   ├── system/             # Audit trail & archive
│   ├── static/             # Static files (CSS, JS, images)
│   │   ├── css/
│   │   └── js/
│   │       └── components/ # JavaScript components
│   ├── templates/          # HTML templates
│   │   ├── components/     # Reusable UI components
│   │   │   ├── atoms/      # Button, Badge, Input
│   │   │   ├── molecules/  # Card, ProductCard
│   │   │   └── organisms/  # Complex UI sections
│   │   ├── accounts/       # Login/logout templates
│   │   ├── dashboards/     # Admin & POS dashboards
│   │   ├── kiosk/          # Customer kiosk interface
│   │   ├── orders/         # Order management
│   │   ├── products/       # Product CRUD
│   │   ├── analytics/      # Analytics dashboard
│   │   └── system/         # Audit & archive
│   └── media/              # Uploaded files (product images)
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/property360-2/FJC-Pizza.git
   cd FJC-Pizza/sales_inventory_system
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**
   ```bash
   python manage.py migrate
   ```

4. **Create a superuser** (if not already created)
   ```bash
   python manage.py createsuperuser
   ```
   Or use the demo admin account:
   - Username: `admin`
   - Password: `admin123`

5. **Populate demo data** (Optional but recommended)
   ```bash
   python manage.py populate_demo_data
   ```
   This creates:
   - 16 sample products (pizzas, sides, drinks, desserts)
   - 4 sample orders with different statuses
   - 1 additional cashier user

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Admin/Cashier Login: http://localhost:8000/accounts/login/
   - Customer Kiosk: http://localhost:8000/kiosk/
   - Django Admin: http://localhost:8000/admin/

## 👥 User Roles & Access

### Admin User
- **Login**: `/accounts/login/`
- **Features**:
  - Full product management (add, edit, archive)
  - View all orders and analytics
  - Manage users and permissions
  - Access audit trail and archives
  - Configure system settings

### Cashier User
- **Login**: `/accounts/login/`
- **Features**:
  - POS interface for order processing
  - Accept cash payments
  - Update order status
  - View active orders

### Customer (No Login Required)
- **Access**: `/kiosk/`
- **Features**:
  - Browse product menu
  - Add items to cart
  - Place orders
  - Choose payment method (cash/online demo)
  - Track order status

## 🎨 Atomic Components

### Atoms (Basic Building Blocks)
- **Button** (`components/atoms/button.html`)
  - Types: primary, secondary, success, warning, danger, outline
  - Used throughout the system for consistent actions

- **Badge** (`components/atoms/badge.html`)
  - Types: success, warning, danger, info, pending
  - Order status, stock levels, payment status

- **Input** (`components/atoms/input.html`)
  - Text, number, textarea, select
  - Consistent form inputs with validation

### Molecules (Component Combinations)
- **Card** (`components/molecules/card.html`)
  - Reusable container with header, content, footer

- **Product Card** (`components/molecules/product_card.html`)
  - Displays product with image, price, stock, actions

### Organisms (Complex Sections)
- Dashboards, data tables, navigation bars
- Assembled from atoms and molecules

## 📊 Database Models

### User (Custom User Model)
- Extended Django User with role field (Admin/Cashier)
- Soft delete support via `is_archived`

### Product
- Name, description, price, stock, threshold
- Category and image support
- Low-stock detection

### Order
- Unique order number generation
- Customer info and table number
- Status tracking (Pending/In Progress/Finished/Cancelled)
- Total amount calculation

### OrderItem
- Links products to orders
- Quantity and price snapshots
- Automatic subtotal calculation

### Payment
- Payment method (Cash/Online)
- Status tracking
- Reference number for transactions

### AuditTrail
- User action logging
- JSON data snapshots
- Timestamp and IP tracking

### Archive
- Soft-deleted record storage
- Full data preservation
- Restore capability

## 🎯 Key Features Implementation

### Automatic Stock Management
- Stock automatically deducted when payment is successful
- Low-stock alerts when stock < threshold
- Real-time stock updates

### Order Lifecycle
1. Customer places order → Status: `PENDING`
2. Payment processed → Status: `IN_PROGRESS`, stock deducted
3. Order fulfilled → Status: `FINISHED`

### Audit Trail
- All CRUD operations logged automatically
- User, action, timestamp recorded
- Data snapshots for full history

## 🔧 Configuration

### Settings (`settings.py`)
- Custom User Model: `accounts.User`
- Static Files: Configured for CDN delivery
- Media Files: Product image uploads
- Templates: Global template directory

### URLs Structure
```
/                           → Home (redirects based on role)
/accounts/login/            → Login page
/accounts/logout/           → Logout
/dashboard/                 → Admin dashboard
/pos/                       → Cashier POS interface
/products/                  → Product management
/orders/                    → Order management
/analytics/dashboard/       → Analytics
/system/audit/              → Audit trail
/kiosk/                     → Customer kiosk
```

## 🎨 Brand Colors

- **Primary Yellow**: `#f59e0b` (fjc-yellow-500)
- **Primary Blue**: `#3b82f6` (fjc-blue-500)
- **Background**: Light gray (`#f9fafb`)
- **Text**: Dark gray (`#111827`)

## 📱 Responsive Design

- Mobile-first approach using Tailwind CSS
- Breakpoints:
  - `sm`: 640px (mobile)
  - `md`: 768px (tablet)
  - `lg`: 1024px (desktop)
  - `xl`: 1280px (large desktop)

## 🔐 Security Features

- Role-based access control
- Login required for admin/cashier functions
- CSRF protection on all forms
- User session management
- Password hashing

## 🚧 Future Enhancements

- Real payment gateway integration (PayMaya, GCash)
- Multi-branch inventory syncing
- WebSocket for real-time order updates
- Email/SMS notifications
- Advanced analytics with charts
- Inventory forecasting
- Customer loyalty program

## 📄 License

This project is developed for FJC Pizza as a custom sales and inventory management solution.

## 👨‍💻 Development

Built with precision following the atomic design pattern and modern Django best practices. The system emphasizes great UX/UI with a clean, modern light mode design featuring FJC Pizza's yellow and blue brand colors.

---

**FJC Pizza** - Delivering excellence, one slice at a time! 🍕
