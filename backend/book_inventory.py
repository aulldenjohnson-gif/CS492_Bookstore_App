"""
book_inventory.py
Purpose: Store and update bookstore inventory
"""

# Inventory dictionary: Book ID -> [Title, Quantity]
inventory = {
    "B101": ["Harry Potter and the Sorcerer's Stone by J.K. Rowling", 12],
    "B102": ["The Hobbit by J.R.R. Tolkien", 7],
    "B103": ["To Kill a Mockingbird by Harper Lee", 5]
}

def get_inventory():
    """Return all books and their quantities"""
    return inventory

def show_inventory():
    """Show all books and their current quantities"""
    result = []
    for book_id in inventory:
        title, qty = inventory[book_id]
        result.append({"book_id": book_id, "title": title, "quantity": qty})
    return result

def add_delivery(book_id, amount):
    """Add new books delivered by supplier to the inventory"""
    if book_id in inventory:
        if amount > 0:
            inventory[book_id][1] += amount
            return {"success": True, "message": f"{amount} copies added to {inventory[book_id][0]}. New quantity: {inventory[book_id][1]}"}
        else:
            return {"success": False, "message": "Please enter a positive number for delivery."}
    else:
        return {"success": False, "message": "Book ID not found in inventory."}

def add_book(book_id, title, quantity):
    """Add a new book to inventory"""
    if book_id in inventory:
        return {"success": False, "message": "Book ID already exists."}
    inventory[book_id] = [title, quantity]
    return {"success": True, "message": f"Book '{title}' added to inventory."}
