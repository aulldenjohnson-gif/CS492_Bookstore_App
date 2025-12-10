# Supplier Orders API — Spec

This document describes the recommended API endpoints for the Supplier Order History UI.

Base: `/api/supplier-orders`

- GET `/api/supplier-orders`
  - Query params:
    - `page` (int) — page number (default 1)
    - `pageSize` (int) — items per page (default 25)
    - `supplier` (string) — supplier name filter
    - `status` (string) — status filter (pending, processing, shipped, received, cancelled)
    - `q` (string) — search across order_id, supplier, SKU, title
    - `sort` (string) — `date|total|status` optionally prefixed with `-` for desc
  - Response:
    - `total` (int), `page` (int), `pageSize` (int), `data` (array of order objects)

- GET `/api/supplier-orders/:orderId`
  - Response: full order object including `items` array, shipping info, supplier contact

- POST `/api/supplier-orders` (create new order)
  - Body: supplier, items [{sku, qty, price}], expected_date, note
  - Response: created order

- PUT `/api/supplier-orders/:orderId` (update)
  - Body: fields to update (status, tracking, received_date, notes)
  - Response: updated order

- GET `/api/suppliers` — list suppliers for dropdown

Order object (example):
{
  "order_id": 1001,
  "date": "2025-12-01",
  "supplier": "Acme Books",
  "items": [ { "sku":"BK-002","title":"Python 101","qty":20,"price":15 } ],
  "total": 300.00,
  "status": "processing",
  "tracking": "",
  "notes": "",
  "expected_date": "2025-12-07",
  "received_date": null
}

Security: require authenticated users with appropriate role (purchasing or admin) on endpoints that create/update orders.

Pagination & performance: return counts and use offsets or cursor-based paging for large datasets.
