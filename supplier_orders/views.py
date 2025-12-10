from django.http import JsonResponse, Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET

# Mock data (same as the Flask stub)
MOCK_ORDERS = [
    {"order_id":1001,"date":"2025-11-02","supplier":"Acme Books","items":[{"sku":"BK-001","title":"Intro to JS","qty":10,"price":12.5}],"total":125.0,"status":"received"},
    {"order_id":1002,"date":"2025-11-15","supplier":"Pages & Co","items":[{"sku":"BK-034","title":"Advanced CSS","qty":5,"price":22}],"total":110.0,"status":"shipped"},
    {"order_id":1003,"date":"2025-12-01","supplier":"Acme Books","items":[{"sku":"BK-002","title":"Python 101","qty":20,"price":15}],"total":300.0,"status":"processing"},
    {"order_id":1004,"date":"2025-12-03","supplier":"Global Texts","items":[{"sku":"BK-099","title":"Algorithms","qty":2,"price":45}],"total":90.0,"status":"pending"},
    {"order_id":1005,"date":"2025-11-28","supplier":"Pages & Co","items":[{"sku":"BK-076","title":"Design Patterns","qty":1,"price":55}],"total":55.0,"status":"cancelled"},
    {"order_id":1006,"date":"2025-10-10","supplier":"Novelty Distributors","items":[{"sku":"BK-121","title":"Modern Fiction","qty":12,"price":8}],"total":96.0,"status":"received"},
    {"order_id":1007,"date":"2025-09-07","supplier":"Acme Books","items":[{"sku":"BK-200","title":"Databases","qty":4,"price":30}],"total":120.0,"status":"received"},
    {"order_id":1008,"date":"2025-12-04","supplier":"Global Texts","items":[{"sku":"BK-132","title":"Networks","qty":3,"price":40}],"total":120.0,"status":"shipped"},
    {"order_id":1009,"date":"2025-11-21","supplier":"Pages & Co","items":[{"sku":"BK-140","title":"UX Basics","qty":7,"price":18}],"total":126.0,"status":"processing"},
    {"order_id":1010,"date":"2025-11-30","supplier":"Novelty Distributors","items":[{"sku":"BK-150","title":"Poetry","qty":6,"price":10}],"total":60.0,"status":"pending"},
    {"order_id":1011,"date":"2025-12-05","supplier":"Acme Books","items":[{"sku":"BK-170","title":"Machine Learning","qty":2,"price":80}],"total":160.0,"status":"processing"},
    {"order_id":1012,"date":"2025-12-07","supplier":"Pages & Co","items":[{"sku":"BK-177","title":"Cloud Eng","qty":1,"price":95}],"total":95.0,"status":"pending"}
]


def supplier_history_page(request):
    """Render the supplier order history template."""
    return render(request, 'supplier_orders/supplier_order_history.html')


@require_GET
def list_suppliers(request):
    suppliers = sorted(list({o['supplier'] for o in MOCK_ORDERS}))
    return JsonResponse({"data": suppliers})


@require_GET
def list_orders(request):
    # Query params
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    try:
        page_size = int(request.GET.get('pageSize', '25'))
    except ValueError:
        page_size = 25

    supplier = request.GET.get('supplier')
    status = request.GET.get('status')
    q = request.GET.get('q', '').lower()
    sort = request.GET.get('sort', '')

    data = MOCK_ORDERS[:]
    if supplier:
        data = [o for o in data if o['supplier'].lower() == supplier.lower()]
    if status:
        data = [o for o in data if o['status'].lower() == status.lower()]
    if q:
        def matches(o):
            hay = ' '.join([str(o['order_id']), o['supplier'], o['date'], ' '.join([i['sku']+' '+i['title'] for i in o['items']])]).lower()
            return q in hay
        data = [o for o in data if matches(o)]

    if sort:
        reverse = sort.startswith('-')
        key = sort.lstrip('-')
        if key in ('date', 'total', 'status'):
            data.sort(key=lambda x: x.get(key, ''), reverse=reverse)

    total = len(data)
    start = (page - 1) * page_size
    end = start + page_size
    page_data = data[start:end]
    return JsonResponse({"total": total, "page": page, "pageSize": page_size, "data": page_data})


@require_GET
def get_order(request, order_id):
    for o in MOCK_ORDERS:
        if o['order_id'] == int(order_id):
            return JsonResponse(o)
    raise Http404()
