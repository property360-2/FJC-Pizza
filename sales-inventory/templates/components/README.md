# Component Library Documentation

## Phase 8: Component Refinement & Reusability

This directory contains the complete implementation of the **Atomic Design Pattern** for the FJC Pizza Sales & Inventory Management System.

## 📁 Structure

```
components/
├── atoms/          # Basic building blocks (buttons, inputs, badges, etc.)
├── molecules/      # Combinations of atoms (product cards, cart items, etc.)
└── organisms/      # Complex components (product grids, tables, sidebars, etc.)
```

## 🎨 Design Philosophy

### Atomic Design Pattern

Following Brad Frost's Atomic Design methodology:

1. **Atoms** - The smallest, most basic components
   - Cannot be broken down further without losing meaning
   - Examples: buttons, inputs, badges, spinners

2. **Molecules** - Simple groups of atoms functioning together
   - Created by combining 2-3 atoms
   - Examples: product card, cart item, stat card

3. **Organisms** - Complex components made of molecules and atoms
   - Form distinct sections of the interface
   - Examples: product grid, cart sidebar, dashboard stats

## 📚 Component Usage

### Atoms

#### Button
```django
{% include "components/atoms/button.html" with
   type="primary"
   size="md"
   text="Click Me"
   icon="bi-check"
   attrs="@click='handleClick()'"
%}
```

**Parameters:**
- `type`: primary|secondary|success|danger|warning|info|outline-primary|outline-secondary|outline-danger (default: primary)
- `size`: sm|md|lg (default: md)
- `text`: Button text (required)
- `icon`: Bootstrap icon class (optional)
- `attrs`: Additional HTML attributes like Alpine.js directives (optional)
- `disabled`: true|false (optional)
- `fullwidth`: true|false (optional)

#### Badge
```django
{% include "components/atoms/badge.html" with
   type="success"
   text="Active"
   icon="bi-check-circle"
%}
```

**Parameters:**
- `type`: primary|secondary|success|danger|warning|info|light|dark (default: primary)
- `text`: Badge text (required)
- `icon`: Bootstrap icon class (optional)

#### Input
```django
{% include "components/atoms/input.html" with
   type="text"
   name="username"
   label="Username"
   placeholder="Enter username"
   required=True
%}
```

**Parameters:**
- `type`: text|email|password|number|search|tel|url|date|time (default: text)
- `name`: Input name attribute (required)
- `label`: Label text (optional)
- `placeholder`: Placeholder text (optional)
- `required`: true|false (optional)

#### Spinner
```django
{% include "components/atoms/spinner.html" with
   type="border"
   color="primary"
   size="md"
   centered=True
%}
```

**Parameters:**
- `type`: border|grow (default: border)
- `color`: primary|secondary|success|danger|warning|info|light|dark (default: primary)
- `size`: sm|md|lg (default: md)
- `centered`: true|false - wrap in centered container (optional)

#### Alert
```django
{% include "components/atoms/alert.html" with
   type="success"
   text="Operation completed!"
   icon="bi-check-circle"
   dismissible=True
%}
```

**Parameters:**
- `type`: primary|secondary|success|danger|warning|info|light|dark (default: info)
- `text`: Alert message text (required)
- `icon`: Bootstrap icon class (optional)
- `dismissible`: true|false (optional)

### Molecules

#### Product Card - Kiosk
```django
<!-- Requires Alpine.js data context -->
<div x-data="{
    products: [...],
    addToCart: function(product) { ... }
}">
    <template x-for="product in products" :key="product.id">
        <div class="col-md-6 col-lg-4">
            {% include "components/molecules/product-card-kiosk.html" %}
        </div>
    </template>
</div>
```

**Expected Alpine.js data:**
- `product.id`, `product.name`, `product.price`, `product.image_url`
- `product.is_low_stock`, `product.is_out_of_stock`
- Method: `addToCart(product)`

#### Product Card - POS
```django
<div x-data="{
    filteredProducts: [...],
    addToCart: function(product) { ... }
}">
    <template x-for="product in filteredProducts" :key="product.id">
        <div class="col-md-4">
            {% include "components/molecules/product-card-pos.html" %}
        </div>
    </template>
</div>
```

**Expected Alpine.js data:**
- `product.id`, `product.name`, `product.price`, `product.stock`
- `product.is_low_stock`, `product.is_out_of_stock`
- Method: `addToCart(product)`

#### Cart Item
```django
<div x-data="{
    cart: [...],
    increaseQty: function(index) { ... },
    decreaseQty: function(index) { ... },
    removeFromCart: function(index) { ... }
}">
    <div class="list-group">
        <template x-for="(item, index) in cart" :key="index">
            {% include "components/molecules/cart-item.html" %}
        </template>
    </div>
</div>
```

**Expected Alpine.js data:**
- `item.name`, `item.price`, `item.qty`
- Methods: `increaseQty(index)`, `decreaseQty(index)`, `removeFromCart(index)`

#### Stat Card
```django
{% include "components/molecules/stat-card.html" with
   title="Total Sales"
   value="$12,345.67"
   icon="bi-currency-dollar"
   color="success"
   trend="+12.5%"
%}
```

**Parameters:**
- `title`: Card title (required)
- `value`: Main value to display (required)
- `icon`: Bootstrap icon class (optional)
- `color`: primary|secondary|success|danger|warning|info (default: primary)
- `trend`: Trend indicator like "+12%" or "-5%" (optional)

### Organisms

#### Product Grid - Kiosk
```django
<div x-data="kioskApp()">
    {% include "components/organisms/product-grid-kiosk.html" %}
</div>
```

**Required Alpine.js data:**
- `products`: Array of product objects
- `loading`: Boolean loading state
- `addToCart(product)`: Function

#### Product Grid - POS
```django
<div x-data="posApp()">
    {% include "components/organisms/product-grid-pos.html" %}
</div>
```

**Required Alpine.js data:**
- `filteredProducts`: Array of filtered products
- `loading`: Boolean loading state
- `search`: Search query string
- `searchProducts()`: Search function
- `addToCart(product)`: Function

#### Cart Sidebar
```django
<div x-data="posApp()">
    {% include "components/organisms/cart-sidebar.html" %}
</div>
```

**Required Alpine.js data:**
- `cart`: Array of cart items
- `cartTotal`: Computed total amount
- `clearCart()`, `processPayment()`: Functions
- Methods from cart-item molecule

#### Product Table - Admin
```django
{% include "components/organisms/product-table-admin.html" with
   products=products
   search_query=search_query
%}
```

**Required Django context:**
- `products`: QuerySet or list of Product objects
- `search_query`: Current search query (optional)

#### Dashboard Stats
```django
<!-- With Alpine.js -->
<div x-data="dashboardApp()">
    {% include "components/organisms/dashboard-stats.html" %}
</div>

<!-- Or with Django context -->
{% include "components/organisms/dashboard-stats.html" with stats=stats %}
```

**Required data:**
- `stats.total_sales`, `stats.total_orders`
- `stats.low_stock_count`, `stats.active_products`

## 🎯 Best Practices

### 1. Consistency
- Always use the component library instead of writing custom HTML
- Maintain consistent parameter naming across components
- Follow the established color scheme

### 2. Reusability
- Components are designed to be technology-agnostic
- Can work with Alpine.js, HTMX, or vanilla JavaScript
- Support both client-side and server-side rendering

### 3. Accessibility
- All components include proper ARIA attributes
- Keyboard navigation is supported
- Color contrast meets WCAG standards
- Reduced motion preferences are respected

### 4. Performance
- Components use CSS-only animations where possible
- Minimal JavaScript dependencies
- Optimized for fast rendering

## 🔧 Customization

### CSS Variables
Customize the theme by overriding CSS variables in `components.css`:

```css
:root {
    --primary-color: #0d6efd;
    --success-color: #198754;
    --danger-color: #dc3545;
    --border-radius: 0.375rem;
    --transition-speed: 0.2s;
}
```

### Component Extensions
To create custom variations:

1. Create a new file in the appropriate directory (atoms/molecules/organisms)
2. Include existing components as building blocks
3. Add custom styling in `components.css`
4. Document the new component in this README

## 📊 Component Preview

Access the live component preview at: `/dashboard/components/`

This page showcases all components with various configurations and states.

## 🔄 Migration Guide

### Converting Inline HTML to Components

**Before:**
```django
<button class="btn btn-primary" @click="handleClick()">
    <i class="bi-check"></i> Save
</button>
```

**After:**
```django
{% include "components/atoms/button.html" with
   type="primary"
   text="Save"
   icon="bi-check"
   attrs="@click='handleClick()'"
%}
```

### Benefits
- Consistent styling across the application
- Easier maintenance and updates
- Better code reusability
- Improved accessibility

## 📝 Contributing

When adding new components:

1. Follow the Atomic Design hierarchy
2. Document all parameters and usage
3. Add examples to the component preview page
4. Update this README with new component details
5. Ensure accessibility standards are met
6. Test with Alpine.js and Django template contexts

## 🚀 Future Enhancements

Potential improvements for future phases:

- [ ] Add more complex organisms (data tables with sorting/filtering)
- [ ] Implement HTMX-specific components
- [ ] Create form validation components
- [ ] Add animation presets library
- [ ] Build a component generator CLI tool
- [ ] Add unit tests for component rendering

## 📖 Resources

- [Atomic Design Methodology](https://atomicdesign.bradfrost.com/)
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.3/)
- [Alpine.js Documentation](https://alpinejs.dev/)
- [Bootstrap Icons](https://icons.getbootstrap.com/)

---

**Version:** Phase 8 - Component Refinement & Reusability
**Last Updated:** November 2025
**Maintained By:** FJC Pizza Development Team
