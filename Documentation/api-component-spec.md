# Sales & Inventory Management System — API Contract & Frontend Component Hierarchy

**Source of truth:** Aligns precisely with `concept.md` and `phase.md` (Django + MySQL + CDN Frontend using Atomic Design). Mirrors route ideas from `schema.md` where compatible. Authentication is **session-based**; roles are **ADMIN** and **CASHIER**. Public Kiosk requires **no login**.

---

## 1) API CONTRACT (Routes + Methods)

**Base URL:** `/api`
**Authentication:** Django Sessions (CSRF required for unsafe methods).
**Roles:** `ADMIN`, `CASHIER`.
**Common Status Codes:** `200 OK`, `201 Created`, `204 No Content`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `422 Unprocessable Entity`, `500 Internal Server Error`.

### 1.1 Auth & Session

* `POST /auth/login`

  * **Body:** `{ "username": string, "password": string }`
  * **Response 200:** `{ "id": int, "username": string, "role": "ADMIN"|"CASHIER" }`
  * **Notes:** Sets session cookie. Requires CSRF token.

* `POST /auth/logout`

  * **Response 204**

* `GET /auth/me`

  * **Response 200:** `{ "id": int, "username": string, "role": "ADMIN"|"CASHIER", "is_active": bool }`

### 1.2 Users (Admin only)

* `GET /users`

  * **Auth:** ADMIN
  * **Query:** `q` (search), `is_active` (bool), `role`
  * **Response 200:** `{ "results": [ { "id": int, "username": string, "role": "ADMIN"|"CASHIER", "is_active": bool } ], "count": int, "next": string|null }`

* `POST /users`

  * **Auth:** ADMIN
  * **Body:** `{ "username": string, "password": string, "role": "ADMIN"|"CASHIER", "is_active": bool }`
  * **Response 201:** user object

* `GET /users/{id}` / `PATCH /users/{id}`

  * **Auth:** ADMIN
  * **PATCH Body (any):** `{ "password"?: string, "role"?: "ADMIN"|"CASHIER", "is_active"?: bool }`

* `POST /users/{id}/activate` → `{ "is_active": true }`
  `POST /users/{id}/deactivate` → `{ "is_active": false }`

### 1.3 Products & Inventory

* `GET /products`

  * **Auth:** ADMIN or CASHIER
  * **Query:** `archived` (bool, default `false`), `low_stock` (bool), `q` (search), `page`, `page_size`
  * **Response 200:** `{ "results": [ Product ], "count": int }`

* `POST /products`

  * **Auth:** ADMIN
  * **Body:** `{ "name": string, "price": number, "stock": int, "threshold": int, "image_url"?: string }`
  * **Response 201:** `Product`

* `GET /products/{id}` / `PATCH /products/{id}`

  * **Auth:** ADMIN
  * **PATCH Body (any):** `{ "name"?: string, "price"?: number, "stock"?: int, "threshold"?: int, "image_url"?: string }`

* `POST /products/{id}/archive` → sets `is_archived = true`
  `POST /products/{id}/unarchive` → sets `is_archived = false`

* `POST /products/{id}/stock_adjust`

  * **Auth:** ADMIN
  * **Body:** `{ "delta": int, "reason"?: string }`
  * **Response 200:** `{ "id": int, "stock_before": int, "stock_after": int }`

**Product object**

```json
{
  "id": 12,
  "name": "Iced Latte",
  "price": 120.00,
  "stock": 45,
  "threshold": 10,
  "is_archived": false,
  "image_url": "https://cdn.example/p12.jpg",
  "created_at": "2025-11-01T08:00:00Z",
  "updated_at": "2025-11-04T10:12:00Z"
}
```

### 1.4 Orders & Items

**Statuses:** `PENDING` → `IN_PROGRESS` → `FINISHED` (with optional `CANCELLED`).

* `GET /orders`

  * **Auth:** ADMIN or CASHIER
  * **Query:** `status`, `from`, `to`, `page`, `q` (order_no)
  * **Response 200:** `{ "results": [ OrderSummary ], "count": int }`

* `GET /orders/{id}`

  * **Auth:** ADMIN or CASHIER
  * **Response 200:** `Order` (with items + payment summary)

* `POST /orders` (Server-side creates from Kiosk checkout or POS)

  * **Auth:** Public (Kiosk session) **or** CASHIER (POS)
  * **Body:** `{ "items": [ { "product_id": int, "qty": int } ], "payment_method": "CASH"|"ONLINE_DEMO" }`
  * **Response 201:** `{ "order_id": int, "order_no": string, "status": "PENDING" }`

* `POST /orders/{id}/mark_in_progress`

  * **Auth:** CASHIER or ADMIN
  * **Response 200:** `{ "status": "IN_PROGRESS" }`

* `POST /orders/{id}/finish`

  * **Auth:** CASHIER or ADMIN
  * **Response 200:** `{ "status": "FINISHED" }`

* `POST /orders/{id}/cancel`

  * **Auth:** CASHIER or ADMIN
  * **Response 200:** `{ "status": "CANCELLED" }` (stock restoration occurs if previously deducted)

**OrderSummary object**

```json
{
  "id": 101,
  "order_no": "K-20251105-00101",
  "status": "PENDING",
  "total": 540.00,
  "item_count": 3,
  "created_at": "2025-11-05T02:11:00Z"
}
```

**Order (detailed)**

```json
{
  "id": 101,
  "order_no": "K-20251105-00101",
  "status": "IN_PROGRESS",
  "items": [
    { "product_id": 12, "name": "Iced Latte", "price": 120.00, "qty": 2, "subtotal": 240.00 },
    { "product_id": 8,  "name": "Brownie",    "price": 150.00, "qty": 2, "subtotal": 300.00 }
  ],
  "payment": { "id": 9001, "method": "CASH", "status": "SUCCESS" },
  "totals": { "gross": 540.00 },
  "created_at": "2025-11-05T02:11:00Z"
}
```

### 1.5 Payments

**Payment status:** `PENDING`, `SUCCESS`, `FAILED`.

* `POST /payments`

  * **Auth:** CASHIER or Public (Kiosk Online Demo)
  * **Body:** `{ "order_id": int, "method": "CASH"|"ONLINE_DEMO" }`
  * **Response 201:** `Payment`

* `POST /payments/{id}/mark_success` (Cash)

  * **Auth:** CASHIER or ADMIN
  * **Action:** Sets `Payment.status = SUCCESS`, triggers **inventory deduction** and order → `IN_PROGRESS`.

* `POST /payments/{id}/simulate_online_success` (Demo)

  * **Auth:** Public (kiosk session that created the payment) or server-side after redirect
  * **Action:** Same as above; demo path to success.

**Payment object**

```json
{
  "id": 9001,
  "order_id": 101,
  "method": "CASH",
  "status": "SUCCESS",
  "amount": 540.00,
  "processed_at": "2025-11-05T02:12:10Z"
}
```

### 1.6 Kiosk Cart (Session-based, no login)

* `GET /kiosk/cart`

  * **Auth:** Public (session cookie)
  * **Response 200:** `{ "items": [ { "product_id": int, "name": string, "price": number, "qty": int, "subtotal": number } ], "total_qty": int, "total_amount": number }`

* `POST /kiosk/cart/items`

  * **Body:** `{ "product_id": int, "qty": int }` (qty can be +/−)
  * **Response 200:** Updated cart object

* `PATCH /kiosk/cart/items/{product_id}`

  * **Body:** `{ "qty": int }`

* `DELETE /kiosk/cart/items/{product_id}` → 204

* `DELETE /kiosk/cart` (clear) → 204

* `POST /kiosk/checkout`

  * **Body:** `{ "payment_method": "CASH"|"ONLINE_DEMO" }`
  * **Response 201:** `{ "order_id": int, "order_no": string, "status": "PENDING" }`

* `GET /kiosk/orders/{order_no}/status`

  * **Response 200:** `{ "order_no": string, "status": "PENDING"|"IN_PROGRESS"|"FINISHED"|"CANCELLED" }`

### 1.7 Analytics (Admin)

* `GET /analytics/sales`

  * **Auth:** ADMIN
  * **Query:** `granularity` = `daily|weekly|monthly`, `from`, `to`
  * **Response 200:** `{ "series": [ { "period": "2025-11-01", "total": 12450.00 } ], "meta": { "from": "...", "to": "..." } }`

* `GET /analytics/top_products`

  * **Auth:** ADMIN
  * **Query:** `limit` (default 10), `from`, `to`
  * **Response 200:** `[ { "product_id": int, "name": string, "qty_sold": int, "revenue": number } ]`

* `GET /analytics/cashier_performance`

  * **Auth:** ADMIN
  * **Query:** `from`, `to`
  * **Response 200:** `[ { "cashier_id": int, "username": string, "orders": int, "revenue": number } ]`

* `GET /analytics/inventory_summary`

  * **Auth:** ADMIN
  * **Response 200:** `{ "low_stock": [ { "product_id": int, "name": string, "stock": int, "threshold": int } ], "counts": { "active": int, "archived": int } }`

### 1.8 Audit Trail & Archive (Admin)

* `GET /audit`

  * **Auth:** ADMIN
  * **Query:** `entity` (e.g., `product|order|payment|user`), `ref_id`, `actor_id`, `from`, `to`, `page`
  * **Response 200:** `[ AuditEntry ]`

* `GET /archive`

  * **Auth:** ADMIN
  * **Query:** `entity`, `ref_id`, `page`
  * **Response 200:** `[ ArchiveEntry ]`

* `POST /archive/{entity}/{ref_id}/restore`

  * **Auth:** ADMIN
  * **Response 200:** `{ "restored": true, "entity": string, "ref_id": int }`

**AuditEntry**

```json
{ "id": 501,
  "actor_id": 2,
  "actor": "admin1",
  "entity": "product",
  "action": "UPDATE",
  "ref_id": 12,
  "timestamp": "2025-11-05T02:13:00Z",
  "diff": { "stock": { "from": 20, "to": 45 } }
}
```

**ArchiveEntry**

```json
{ "id": 88,
  "entity": "product",
  "ref_id": 9,
  "snapshot": { /* JSON of original data */ },
  "archived_by": 1,
  "archived_at": "2025-11-02T06:30:00Z" }
```

### 1.9 System/Utility

* `GET /health` → `{ "ok": true }`
* `GET /csrf` → `{ "csrfToken": string }`

### 1.10 Pagination & Filtering Conventions

* `page` (1-based), `page_size` (default 20, max 100)
* Date filters are ISO8601 strings (`YYYY-MM-DD` or full timestamps)
* Search param `q` does case-insensitive contains on sensible fields

### 1.11 Security & Side Effects

* **RBAC:**

  * ADMIN → all endpoints
  * CASHIER → POS-related reads/writes (`orders`, `payments`, product reads)
  * Public → kiosk cart + checkout + order status
* **Inventory deduction:** occurs **only** when `Payment.status` transitions to `SUCCESS`.
* **Soft archive:** products hidden from POS/Kiosk when `is_archived = true`.
* **Audit signals:** trigger automatically on Product CRUD, stock adjust, Payment processing, User changes.

---

## 2) UI ROUTES (Server-rendered pages)

* `/login` (Public) → login form
* `/logout` (Authed) → ends session, redirect to `/login`
* `/admin/products/` (ADMIN) → inventory management UI
* `/admin/users/` (ADMIN) → user management
* `/pos/` (CASHIER, ADMIN) → cashier POS panel
* `/kiosk/` (Public) → product grid + cart
* `/kiosk/checkout/` (Public) → checkout + demo payment
* `/kiosk/order/{order_no}/` (Public) → order status page (auto-refresh)
* `/dashboard/` (ADMIN) → analytics & charts
* `/audit/` (ADMIN) → audit viewer
* `/archive/` (ADMIN) → archive viewer

---

## 3) FRONTEND COMPONENT HIERARCHY (Atomic Design)

**Stack:** TailwindCSS via CDN, minimal JS (HTMX/Alpine recommended), organized under `/static/js/components/{atoms|molecules|organisms}/` and `/static/css/`.

### 3.1 Shared Atoms (Generic)

* **ButtonAtom** — size/variant props via `data-variant="primary|secondary|danger"`.
* **InputAtom** — text/number inputs with error state.
* **BadgeAtom** — status display (e.g., `PENDING`, `IN_PROGRESS`, `FINISHED`).
* **IconAtom** — inline SVG wrapper.
* **ModalAtom** — basic modal shell.
* **SpinnerAtom** — loading indicator.
* **PaginationAtom** — previous/next controls.
* **ToastAtom** — transient notifications.

### 3.2 Kiosk Components

* **Atoms:** `QuantityStepperAtom`, `PriceTagAtom`, `AddToCartButtonAtom` (posts to `/api/kiosk/cart/items`).
* **Molecules:**

  * `KioskProductCard` — displays name, price, image, threshold-based badge.
  * `CartLineItem` — product row with qty steppers and subtotal.
* **Organisms:**

  * `KioskProductGrid` — fetches from `/api/products?archived=false` (filters out low-stock if desired).
  * `CartSidebar` — shows session cart from `/api/kiosk/cart`.
  * `CheckoutForm` — posts to `/api/kiosk/checkout`; branches to cash or demo.
  * `OrderStatusPanel` — polls `/api/kiosk/orders/{order_no}/status`.
* **Pages:** `/kiosk/`, `/kiosk/checkout/`, `/kiosk/order/{order_no}/`.

**Contracts:**

* `AddToCartButtonAtom`

  * **Inputs (data-attrs):** `data-product-id`, `data-qty-default` (optional)
  * **Action:** `hx-post="/api/kiosk/cart/items"` with `{ product_id, qty }`
  * **Success event:** dispatch `cart:updated` with `{ total_qty, total_amount }`

### 3.3 POS (Cashier) Components

* **Atoms:** `StatusBadgeAtom`, `ActionButtonAtom`, `SearchInputAtom`.
* **Molecules:**

  * `OrderRow` — shows order_no, item_count, total, status, actions.
  * `PaymentModal` — cash payment confirm → posts `/api/payments/{id}/mark_success`.
  * `OrderDetailCard` — expanded view of items.
* **Organisms:**

  * `POSOrderTable` — lists active orders from `/api/orders?status=PENDING|IN_PROGRESS` with polling.
  * `OrderQueuePanel` — kanban-like swimlanes (optional enhancement).
* **Page:** `/pos/`.

**Contracts:**

* `PaymentModal`

  * **Inputs:** `data-order-id`, `data-amount`
  * **Action:** `hx-post="/api/payments"` → then `hx-post /api/payments/{id}/mark_success`
  * **Side-effect:** triggers inventory deduction; emits `order:updated`.

### 3.4 Admin — Inventory & Users

* **Atoms:** `FormLabelAtom`, `NumberInputAtom`, `ArchiveToggleAtom`.
* **Molecules:**

  * `ProductCard` — quick edit for price/stock; archive switch.
  * `StockAdjustForm` — `hx-post "/api/products/{id}/stock_adjust"`.
  * `UserRow` — username, role, active state.
* **Organisms:**

  * `ProductTable` — sortable table; bulk archive.
  * `UserTable` — with activate/deactivate actions.
* **Pages:** `/admin/products/`, `/admin/users/`.

### 3.5 Admin — Analytics & System

* **Atoms:** `StatCardAtom` (value, label, trend), `DateRangePickerAtom`.
* **Molecules:** `ChartWidget` (Chart.js/ApexCharts via CDN), `TopProductsTable`.
* **Organisms:** `DashboardGrid` — assembles KPI cards + charts + low-stock list.
* **Page:** `/dashboard/`.

### 3.6 Audit & Archive

* **Molecules:** `AuditLogRow`, `ArchiveRecordRow`.
* **Organisms:** `AuditTable` (filters + pagination), `ArchiveTable` (restore buttons hitting `/api/archive/{entity}/{ref_id}/restore`).
* **Pages:** `/audit/`, `/archive/`.

---

## 4) File & Naming Conventions

```
/static/
  js/
    components/
      atoms/
        button.atom.js
        input.atom.js
        badge.atom.js
        ...
      molecules/
        kiosk-product-card.mol.js
        cart-line-item.mol.js
        order-row.mol.js
        stock-adjust-form.mol.js
      organisms/
        kiosk-product-grid.org.js
        cart-sidebar.org.js
        pos-order-table.org.js
        dashboard-grid.org.js
  css/
    components.css
```

* **Atoms** expose simple `init(el)` to attach behaviors.
* **Molecules/Organisms** can fetch via HTMX (`hx-get`, `hx-post`), and broadcast custom events (e.g., `cart:updated`, `order:updated`).
* **Accessibility:** buttons and inputs include ARIA labels; modals trap focus.

---

## 5) Data Flow & State

* **Kiosk cart** state is server-side (session); UI mirrors via `/api/kiosk/cart`. Optionally cache in `localStorage` for snappy redraws and reconcile on page load.
* **POS polling** uses `hx-get` with `hx-trigger="every 3s"` on `/api/orders?status=PENDING,IN_PROGRESS`.
* **Analytics** fetch on date change; debounce to avoid heavy queries.
* **Audit hooks** are server-side; UI is read-only with filters.

---

## 6) Error & Loading Patterns

* Use `SpinnerAtom` while `hx-request` is in-flight.
* Map server errors to `ToastAtom` with concise messages.
* Validation errors return `422` with `{ field: message }`; render inline next to fields.

---

## 7) Enums & Constraints (for reference)

* **Order.status:** `PENDING | IN_PROGRESS | FINISHED | CANCELLED`
* **Payment.status:** `PENDING | SUCCESS | FAILED`
* **User.role:** `ADMIN | CASHIER`
* **Product:** `stock >= 0`, `threshold >= 0`, `price >= 0`
* **Archive:** soft-delete equivalent; archived products excluded from Kiosk/POS queries.

---

