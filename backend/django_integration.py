"""
Django Model Integration for Supplier Orders
Provides functions to sync Flask supplier order operations with Django models
"""

import os
import sys
import django

# Determine the root directory
# When running in PyInstaller, __file__ might be in the bundle
if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
    # Running in PyInstaller bundle
    root_dir = sys._MEIPASS
else:
    # Running in normal development mode
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(backend_dir)

# Ensure root directory is in path
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Also add bundle root if available
if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
    if sys._MEIPASS not in sys.path:
        sys.path.insert(0, sys._MEIPASS)

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore_settings')
django.setup()

from supplier_orders.models import SupplierOrder, SupplierOrderItem, Book, Supplier
from datetime import date


def sync_order_to_django(po_id, supplier_name, po_date, items, total, status='pending'):
    """
    Sync a supplier order from Flask to Django models.
    Creates or updates a Django SupplierOrder record.
    """
    try:
        # Get or create supplier
        supplier, created = Supplier.objects.get_or_create(
            name=supplier_name,
            defaults={'contact_email': '', 'contact_phone': '', 'address': ''}
        )
        
        # Create or update order number
        order_number = f"ORD-{po_id}"
        
        # Create or update the order
        order, created = SupplierOrder.objects.update_or_create(
            order_number=order_number,
            defaults={
                'supplier': supplier,
                'total': total,
                'status': status,
            }
        )
        
        return {
            'success': True,
            'message': f'Order synced to database',
            'order_id': order.id,
            'created': created
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error syncing order: {str(e)}'
        }


def receive_and_update_inventory(po_id, supplier_name, items, po_date=None):
    """
    Mark a supplier order as received and update Django Book inventory.
    This bridges Flask supplier_orders with Django models.
    """
    try:
        # Get or create supplier
        supplier, _ = Supplier.objects.get_or_create(
            name=supplier_name,
            defaults={'contact_email': '', 'contact_phone': '', 'address': ''}
        )
        
        # Get or create the order
        order_number = f"ORD-{po_id}"
        order, _ = SupplierOrder.objects.get_or_create(
            order_number=order_number,
            defaults={
                'supplier': supplier,
                'total': 0,
                'status': 'pending'
            }
        )
        
        # Mark as received
        order.status = 'received'
        order.received_date = po_date or date.today()
        order.save()
        
        # Update inventory for each item
        inventory_updates = []
        errors = []
        
        if not items:
            return {
                'success': True,
                'message': f'Order {order_number} marked as received but no items to inventory',
                'order_id': order.id,
                'status': order.status,
                'inventory_updates': [],
                'errors': None
            }
        
        for item in items:
            try:
                # Item could be dict or object with various field names
                if isinstance(item, dict):
                    # Try multiple possible field names for book identifier
                    sku = item.get('sku') or item.get('book_id') or item.get('isbn') or item.get('id')
                    title = item.get('title') or item.get('name') or f"Book {sku}"
                    quantity = item.get('quantity') or item.get('qty') or 0
                    price = item.get('price') or item.get('unit_price') or 0.0
                else:
                    # Handle object attributes
                    sku = getattr(item, 'sku', None) or getattr(item, 'book_id', None) or getattr(item, 'id', None)
                    title = getattr(item, 'title', None) or getattr(item, 'name', f"Book {sku}")
                    quantity = getattr(item, 'quantity', 0) or getattr(item, 'qty', 0)
                    price = getattr(item, 'price', 0) or getattr(item, 'unit_price', 0)
                
                # Skip items without valid identifiers
                if not sku:
                    errors.append({
                        'item': str(item),
                        'error': 'No valid SKU/book_id found in item'
                    })
                    continue
                
                # Convert quantity to int
                try:
                    quantity = int(quantity) if quantity else 0
                except (ValueError, TypeError):
                    quantity = 0
                
                if quantity <= 0:
                    continue
                
                # Use update_or_create to handle both cases atomically and prevent race conditions.
                # It ensures the book exists with the correct title and price before we adjust quantity.
                book, created = Book.objects.update_or_create(
                    sku=str(sku),
                    defaults={
                        'title': str(title),
                        'price': float(price) if price else 0.0,
                        'quantity': 0  # Default quantity to 0, we will add to it below
                    }
                )

                # Now, add the received quantity to the book's current quantity.
                # This correctly handles both new books (0 + qty) and existing ones (current_qty + qty).
                book.quantity += quantity
                book.save()
                
                inventory_updates.append({
                    'sku': str(sku),
                    'title': book.title,
                    'quantity_added': quantity,
                    'new_total': book.quantity,
                    'created': created
                })
                
            except Exception as e:
                errors.append({
                    'item': str(item),
                    'error': f'{type(e).__name__}: {str(e)}'
                })
        
        return {
            'success': True,
            'message': f'Order {order_number} marked as received and inventory updated',
            'order_id': order.id,
            'status': order.status,
            'inventory_updates': inventory_updates,
            'errors': errors if errors else None
        }
        
    except Exception as e:
        import traceback
        return {
            'success': False,
            'message': f'Error processing order: {str(e)}',
            'traceback': traceback.format_exc()
        }


def cancel_and_sync_order(po_id):
    """
    Cancel a supplier order and sync to Django models.
    """
    try:
        order_number = f"ORD-{po_id}"
        
        # Get the order
        try:
            order = SupplierOrder.objects.get(order_number=order_number)
        except SupplierOrder.DoesNotExist:
            # Order doesn't exist in Django yet, just return success
            return {
                'success': True,
                'message': f'Order not found in database (may be new order)'
            }
        
        # Check if can be cancelled
        if order.status == 'received':
            return {
                'success': False,
                'message': 'Cannot cancel a received order'
            }
        
        if order.status == 'cancelled':
            return {
                'success': False,
                'message': 'Order is already cancelled'
            }
        
        # Cancel the order
        order.status = 'cancelled'
        order.save()
        
        return {
            'success': True,
            'message': f'Order {order_number} cancelled',
            'order_id': order.id,
            'status': order.status
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error cancelling order: {str(e)}'
        }


def get_book_inventory():
    """
    Get current book inventory from Django models.
    """
    try:
        books = Book.objects.all().values(
            'sku', 'title', 'quantity', 'price', 'updated_at'
        )
        return {
            'success': True,
            'books': list(books)
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error retrieving inventory: {str(e)}'
        }


def update_book_quantity(sku, quantity_change):
    """
    Update a book's quantity directly.
    """
    try:
        book = Book.objects.get(sku=sku)
        book.quantity += quantity_change
        book.save()
        
        return {
            'success': True,
            'message': f'Updated {sku} to {book.quantity} units',
            'quantity': book.quantity
        }
    except Book.DoesNotExist:
        return {
            'success': False,
            'message': f'Book with SKU {sku} not found'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error updating quantity: {str(e)}'
        }

def get_all_inventory():
    """
    Retrieve all books and their current inventory quantities from the Django database.
    Returns a list of dictionaries with book information.
    """
    try:
        books = Book.objects.all().order_by('sku')
        inventory_list = []
        
        for book in books:
            inventory_list.append({
                'book_id': book.sku,
                'title': book.title,
                'quantity': book.quantity,
                'sku': book.sku,
                'author': book.author if hasattr(book, 'author') else 'Unknown'
            })
        
        return inventory_list
    except Exception as e:
        return {
            'success': False,
            'message': f'Error retrieving inventory: {str(e)}'
        }