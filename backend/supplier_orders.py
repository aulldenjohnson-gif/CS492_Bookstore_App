"""
supplier_orders.py
Purpose: Manage supplier purchase order history and tracking
"""

from datetime import datetime

class SupplierOrder:
    """
    Represents a supplier purchase order.
    """

    def __init__(self, po_id, supplier_name, po_date, items, total):
        self.po_id = po_id
        self.supplier_name = supplier_name
        self.po_date = po_date
        self.items = items
        self.total = total
        self.status = "Pending"
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def mark_received(self):
        """Mark the order as received"""
        self.status = "Received"
        return True

    def to_dict(self):
        """Convert order to dictionary for JSON serialization"""
        return {
            "po_id": self.po_id,
            "supplier_name": self.supplier_name,
            "po_date": self.po_date,
            "items": self.items,
            "total": self.total,
            "status": self.status,
            "created_at": self.created_at
        }


class SupplierOrderManager:
    """
    Manages supplier purchase orders and their history.
    """

    def __init__(self):
        self.orders = {}
        self.next_po_id = 5001

    def create_order(self, supplier_name, po_date, items, total):
        """Create a new supplier purchase order"""
        po_id = self.next_po_id
        self.next_po_id += 1
        order = SupplierOrder(po_id, supplier_name, po_date, items, total)
        self.orders[po_id] = order
        return {
            "success": True,
            "message": f"Purchase order {po_id} created for {supplier_name}",
            "po_id": po_id,
            "order": order.to_dict()
        }

    def get_all_orders(self):
        """Get all supplier purchase orders"""
        return [order.to_dict() for order in self.orders.values()]

    def get_order(self, po_id):
        """Get a specific purchase order by ID"""
        if po_id not in self.orders:
            return {"success": False, "message": "Order not found"}
        return {
            "success": True,
            "order": self.orders[po_id].to_dict()
        }

    def mark_order_received(self, po_id):
        """Mark a purchase order as received"""
        if po_id not in self.orders:
            return {"success": False, "message": "Order not found"}
        
        order = self.orders[po_id]
        order.mark_received()
        return {
            "success": True,
            "message": f"Order {po_id} marked as received",
            "order": order.to_dict()
        }

    def get_pending_orders(self):
        """Get all pending orders"""
        pending = [order.to_dict() for order in self.orders.values() if order.status == "Pending"]
        return pending

    def get_received_orders(self):
        """Get all received orders"""
        received = [order.to_dict() for order in self.orders.values() if order.status == "Received"]
        return received


# Global supplier order manager instance
supplier_manager = SupplierOrderManager()


# API functions for Flask integration
def create_order(supplier_name, po_date, items, total):
    """Create a new supplier purchase order"""
    return supplier_manager.create_order(supplier_name, po_date, items, total)


def get_all_orders():
    """Get all supplier purchase orders"""
    return supplier_manager.get_all_orders()


def get_order(po_id):
    """Get a specific purchase order"""
    return supplier_manager.get_order(po_id)


def mark_order_received(po_id):
    """Mark a purchase order as received"""
    return supplier_manager.mark_order_received(po_id)


def get_pending_orders():
    """Get all pending orders"""
    return supplier_manager.get_pending_orders()


def get_received_orders():
    """Get all received orders"""
    return supplier_manager.get_received_orders()
