Supplier Order History — Integration Notes

Purpose
- Provide guidance to integrate the `supplier_order_history.html` UI into your existing Bookstore app and wire it to backend endpoints.

Static UI placement
- Copy `supplier_order_history.html` and the `assets` folder into the folder where your app serves static files (e.g., `static/` or `public/`).
- Ensure the relative paths remain: `assets/css/supplier_order_history.css` and `assets/js/supplier_order_history.js`.
- If your app uses templates, convert `supplier_order_history.html` into your template engine (Jinja2, EJS, etc.) and replace any static mock data with API calls.

Navigation
- Add a link to your main nav/component so staff can open the page. Example HTML snippet to add to your nav:

```html
<li><a href="/supplier-order-history">Supplier Orders</a></li>
```

Backend wiring
- Use the API spec in `API_supplier_orders.md`.
- On page load, call `GET /api/suppliers` to populate the supplier dropdown.
- Replace the `mockOrders` in `assets/js/supplier_order_history.js` with a network call to `GET /api/supplier-orders` (pass `page`, `pageSize`, `supplier`, `status`, `q`).
- For showing details, call `GET /api/supplier-orders/:orderId` if you prefer fresh data per view.

Example client fetch (replace mockOrders usage):

```js
// fetch page 1
fetch('/api/supplier-orders?page=1&pageSize=25')
  .then(r=>r.json())
  .then(data=>{ orders = data.data; /* update UI */ });
```

Authentication & Roles
- Protect POST/PUT endpoints with auth (only purchasers/admins should create or update supplier orders).
- On the front-end, hide or disable actions for users without the required role.

Database
- Minimal tables: `suppliers`, `supplier_orders`, `supplier_order_items` (see `README_supplier_history.md` for suggested schema).

Running the provided Flask stub
- A minimal Flask stub is supplied at `supplier_orders_api_stub.py` to help local integration and testing (mock data). See `README_supplier_history.md` for run instructions.

Next steps you may want me to do for you
- Integrate this UI into `Bookstore_Management_System.py` (if it is a Flask app) by adding routes and templates.
- Convert UI to use your app's template engine and authentication.
- Implement persistent backend (DB) and tests.
