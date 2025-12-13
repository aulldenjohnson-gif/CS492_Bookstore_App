from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
import json
from .models import Supplier, SupplierOrder, SupplierOrderItem


@require_http_methods(["GET"])
def supplier_history_page(request):
    """Render the supplier order history UI page."""
    return render(request, 'supplier_orders/supplier_order_history.html')


@require_http_methods(["GET"])
def list_suppliers(request):
    """Return list of all suppliers for dropdown."""
    suppliers = Supplier.objects.values_list('name', flat=True).order_by('name')
    return JsonResponse({"data": list(suppliers)})


@require_http_methods(["GET"])
@csrf_exempt
def list_orders(request):
    """Return paginated, filtered supplier orders."""
    page_num = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('pageSize', 25))
    supplier_filter = request.GET.get('supplier', '').strip()
    status_filter = request.GET.get('status', '').strip()
    search_q = request.GET.get('q', '').strip().lower()
    sort_by = request.GET.get('sort', '')

    # Start with all orders
    queryset = SupplierOrder.objects.select_related('supplier').prefetch_related('items')

    # Apply filters
    if supplier_filter:
        queryset = queryset.filter(supplier__name__iexact=supplier_filter)
    if status_filter:
        queryset = queryset.filter(status__iexact=status_filter)
    if search_q:
        queryset = queryset.filter(
            Q(order_number__icontains=search_q) |
            Q(supplier__name__icontains=search_q) |
            Q(items__sku__icontains=search_q) |
            Q(items__title__icontains=search_q)
        ).distinct()

    # Apply sorting
    if sort_by:
        reverse = sort_by.startswith('-')
        key = sort_by.lstrip('-')
        if key in ('date', 'total', 'status'):
            queryset = queryset.order_by(f"{'-' if reverse else ''}{key}")

    # Paginate
    total = queryset.count()
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page_num)

    # Build response with serialized orders
    orders_data = []
    for order in page_obj:
        items = [
            {
                'sku': item.sku,
                'title': item.title,
                'qty': item.quantity,
                'price': float(item.price)
            }
            for item in order.items.all()
        ]
        orders_data.append({
            'order_id': order.id,
            'order_number': order.order_number,
            'date': order.date.isoformat(),
            'supplier': order.supplier.name,
            'items': items,
            'total': float(order.total),
            'status': order.status,
            'tracking': order.tracking_number,
            'expected_date': order.expected_date.isoformat() if order.expected_date else None,
            'received_date': order.received_date.isoformat() if order.received_date else None,
            'notes': order.notes,
        })

    return JsonResponse({
        'total': total,
        'page': page_num,
        'pageSize': page_size,
        'data': orders_data
    })


@require_http_methods(["GET"])
def get_order(request, order_id):
    """Return a single order by ID."""
    try:
        order = SupplierOrder.objects.select_related('supplier').prefetch_related('items').get(id=order_id)
    except SupplierOrder.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)

    items = [
        {
            'sku': item.sku,
            'title': item.title,
            'qty': item.quantity,
            'price': float(item.price)
        }
        for item in order.items.all()
    ]

    return JsonResponse({
        'order_id': order.id,
        'order_number': order.order_number,
        'date': order.date.isoformat(),
        'supplier': order.supplier.name,
        'items': items,
        'total': float(order.total),
        'status': order.status,
        'tracking': order.tracking_number,
        'expected_date': order.expected_date.isoformat() if order.expected_date else None,
        'received_date': order.received_date.isoformat() if order.received_date else None,
        'notes': order.notes,
    })


@require_http_methods(["POST"])
@csrf_exempt
def create_order(request):
    """Create a new supplier order."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    supplier_name = data.get('supplier')
    items = data.get('items', [])
    expected_date = data.get('expected_date')
    notes = data.get('notes', '')

    if not supplier_name or not items:
        return JsonResponse({'error': 'Missing supplier or items'}, status=400)

    try:
        supplier = Supplier.objects.get(name=supplier_name)
    except Supplier.DoesNotExist:
        return JsonResponse({'error': 'Supplier not found'}, status=404)

    # Generate order number
    last_order = SupplierOrder.objects.order_by('-id').first()
    next_id = (last_order.id + 1) if last_order else 1001
    order_number = f"ORD-{next_id}"

    # Calculate total
    total = sum(float(item['price']) * int(item['qty']) for item in items)

    # Create order
    order = SupplierOrder.objects.create(
        order_number=order_number,
        supplier=supplier,
        total=total,
        expected_date=expected_date,
        notes=notes
    )

    # Create order items
    for item in items:
        SupplierOrderItem.objects.create(
            order=order,
            sku=item['sku'],
            title=item['title'],
            quantity=int(item['qty']),
            price=float(item['price'])
        )

    return JsonResponse({
        'order_id': order.id,
        'order_number': order.order_number,
        'status': 'created'
    }, status=201)


@require_http_methods(["PUT"])
@csrf_exempt
def update_order(request, order_id):
    """Update an existing supplier order."""
    try:
        order = SupplierOrder.objects.get(id=order_id)
    except SupplierOrder.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    # Update allowed fields
    if 'status' in data:
        order.status = data['status']
    if 'tracking_number' in data:
        order.tracking_number = data['tracking_number']
    if 'received_date' in data:
        order.received_date = data['received_date']
    if 'notes' in data:
        order.notes = data['notes']

    order.save()
    return JsonResponse({'status': 'updated'})
