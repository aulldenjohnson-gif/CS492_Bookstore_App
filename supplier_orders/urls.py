from django.urls import path
from . import views

app_name = 'supplier_orders'

urlpatterns = [
    path('supplier-order-history/', views.supplier_history_page, name='supplier_history_page'),
    # API endpoints
    path('api/suppliers', views.list_suppliers, name='api_suppliers'),
    path('api/supplier-orders', views.list_orders, name='api_supplier_orders'),
    path('api/supplier-orders/<int:order_id>', views.get_order, name='api_supplier_order_detail'),
]
