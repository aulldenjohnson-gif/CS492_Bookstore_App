# Django Supplier Orders App — Setup Instructions

## Files Created

```
supplier_orders/
  ├── migrations/
  │   └── __init__.py
  ├── static/
  │   └── supplier_orders/
  │       ├── css/supplier_order_history.css
  │       └── js/supplier_order_history.js
  ├── templates/
  │   └── supplier_orders/
  │       └── supplier_order_history.html
  ├── __init__.py
  ├── admin.py (fully configured)
  ├── apps.py
  ├── models.py (Supplier, SupplierOrder, SupplierOrderItem)
  ├── urls.py (API endpoints)
  └── views.py (list, detail, create, update orders)
```

## Integration Steps

### 1. Add `supplier_orders` to Django INSTALLED_APPS

Edit your Django settings file (e.g., `settings.py`):

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # ... other apps
    'supplier_orders',  # ← Add this
]
```

### 2. Include supplier_orders URLs in main project

Edit your main `urls.py`:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('supplier-orders/', include('supplier_orders.urls')),  # ← Add this
    # ... other paths
]
```

### 3. Run migrations

```bash
python manage.py makemigrations supplier_orders
python manage.py migrate supplier_orders
```

### 4. Collect static files (production)

```bash
python manage.py collectstatic
```

### 5. Access the page

- **UI page:** `http://localhost:8000/supplier-orders/supplier-order-history/`
- **Admin:** `http://localhost:8000/admin/supplier_orders/`

## API Endpoints

All endpoints are under `/supplier-orders/api/`:

- `GET /api/suppliers/` — list all suppliers
- `GET /api/supplier-orders/?page=1&pageSize=25&supplier=X&status=Y&q=search&sort=date` — paginated, filtered orders
- `GET /api/supplier-orders/<id>/` — single order detail
- `POST /api/supplier-orders/create/` — create new order
- `PUT /api/supplier-orders/<id>/update/` — update order status/tracking

## Adding Mock Data (optional)

To add sample data to test the UI:

```bash
python manage.py shell
```

Then in the shell:

```python
from supplier_orders.models import Supplier, SupplierOrder, SupplierOrderItem
from datetime import date

# Create suppliers
acme = Supplier.objects.create(name='Acme Books', contact_email='sales@acme.com')
pages = Supplier.objects.create(name='Pages & Co', contact_email='orders@pages.com')

# Create orders
order = SupplierOrder.objects.create(
    order_number='ORD-1001',
    supplier=acme,
    total=125.00,
    status='received'
)

# Add items
SupplierOrderItem.objects.create(
    order=order,
    sku='BK-001',
    title='Intro to JS',
    quantity=10,
    price=12.50
)
```

## Features

✓ Full CRUD operations (create, read, update orders)
✓ Filter by supplier, status, date range
✓ Search by order number, SKU, title
✓ Export to CSV
✓ Django Admin integration with inline items
✓ Order pagination
✓ Responsive design
