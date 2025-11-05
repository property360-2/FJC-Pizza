# Atomic Design Component Structure

This directory contains frontend components organized using the Atomic Design methodology.

## Structure

### Atoms (`atoms/`)
Basic building blocks - smallest reusable components:
- `button.atom.js` - Button variations
- `input.atom.js` - Form inputs
- `badge.atom.js` - Status badges
- `modal.atom.js` - Modal dialog base
- `spinner.atom.js` - Loading indicators
- `toast.atom.js` - Notification toasts

### Molecules (`molecules/`)
Combinations of atoms creating functional units:
- `kiosk-product-card.mol.js` - Product display card for kiosk
- `cart-line-item.mol.js` - Cart item with quantity controls
- `order-row.mol.js` - Order list item for POS
- `product-card.mol.js` - Product card for admin
- `stock-adjust-form.mol.js` - Stock adjustment modal
- `payment-modal.mol.js` - Payment confirmation

### Organisms (`organisms/`)
Complex components composed of molecules and atoms:
- `kiosk-product-grid.org.js` - Product grid for kiosk
- `cart-sidebar.org.js` - Shopping cart sidebar
- `pos-order-table.org.js` - POS order management table
- `dashboard-grid.org.js` - Analytics dashboard layout
- `product-table.org.js` - Admin product management
- `user-table.org.js` - Admin user management

## Usage

Components will use:
- **HTMX** for AJAX interactions
- **Alpine.js** for lightweight reactivity
- **Bootstrap 5** for styling (via CDN)

## Naming Convention

- Files: `component-name.{atom|mol|org}.js`
- Each component exports an `init(element)` function
- Components emit custom events for inter-component communication
