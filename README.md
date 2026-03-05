# 🍕 FJC Pizza Sales & Inventory Management System

> **IMPORTANT NOTICE**
> This system is proudly made by **Jun Alvior**.
> ⚠️ **Ownership & Permissions**: This software and its related documentation are the intellectual property of Jun Alvior. It **cannot be used, modified, or distributed** by others without explicit written permission from the owner.

---

## 🚀 Overview

FJC Pizza is a high-performance Sales & Inventory Management System designed to streamline restaurant operations, from order processing to real-time inventory tracking and business intelligence.

### Key Features
- **POS & Order Management**: Seamless order processing for cashiers and customers.
- **Real-time Inventory**: Automatic stock deduction and low-stock alerts.
- **Advanced Analytics**: Sales forecasting and business intelligence reports.
- **Audit Trail**: Complete log of all system activities for accountability.
- **Secure Authentication**: Role-based access control for Admins, Managers, and Cashiers.

---

## 💻 Local Setup Guide

This system is optimized for local development using **SQLite**.

### 1. Prerequisites
- Python 3.10+
- Virtual Environment (Recommended)

### 2. Environment Configuration
Create a `.env` file in the root directory (or use the provided `.env.example`).
For local development, ensure the PostgreSQL settings are commented out to use SQLite defaults.

```bash
DEBUG=True
SECRET_KEY=your-secret-key-here
# DATABASE_URL= (Leave empty for SQLite)
```

### 3. Installation & Database Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
cd sales_inventory_system
python manage.py migrate

# Seed demo data (Users, Products, Orders)
cd ..
python seed_data.py
```

### 4. Running the Application
```bash
cd sales_inventory_system
python manage.py runserver
```
Access the system at: `http://127.0.0.1:8000`

---

## 🔑 Demo Credentials

Use these accounts to explore the system after running the seeder:

| Role | Username | Password |
| :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` |
| **Manager** | `manager` | `manager123` |
| **Cashier** | `cashier` | `cashier123` |

---

## 📚 Documentation

For detailed guides, please refer to the [Documentation Directory](./Documentation/):
- [Business Overview](./Documentation/01-BUSINESS-OVERVIEW.md)
- [System Architecture](./Documentation/02-SYSTEM-ARCHITECTURE.md)
- [User Workflows](./Documentation/03-USER-ROLES-WORKFLOWS.md)
- [Full Feature List](./Documentation/04-FEATURES-FUNCTIONALITY.md)

---

Developed with ❤️ by **Jun Alvior**
