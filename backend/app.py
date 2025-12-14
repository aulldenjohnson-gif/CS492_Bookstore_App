from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from models import db, User
from werkzeug.exceptions import HTTPException
import logging
import os
import sys
import book_inventory
import order_cancellation
import supplier_orders_manager as supplier_orders
# Note: django_integration is imported lazily to avoid startup issues
import webbrowser
import threading
import time
import subprocess

# Add parent directory to path for PyInstaller bundles and development
backend_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(backend_dir, '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# If running in PyInstaller bundle, add the bundle root to path as well
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    if sys._MEIPASS not in sys.path:
        sys.path.insert(0, sys._MEIPASS)

def get_resource_path(resource_name):
    """Get the path to a resource file, handling both PyInstaller bundles and regular installations"""
    # Check if running inside a PyInstaller bundle
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running in PyInstaller bundle
        return os.path.join(sys._MEIPASS, resource_name)
    else:
        # Running in development
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(backend_dir, '..'))
        return os.path.join(repo_root, resource_name)

def create_app(test_config=None):
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(backend_dir, '..'))

    # Serve static files from the repository root (keeps current frontend in place)
    # Use absolute paths so the app works no matter what the current working directory is.
    app = Flask(
        __name__,
        root_path=backend_dir,
        static_folder=repo_root,
        template_folder=os.path.join(backend_dir, 'templates'),
    )
    app.config['SECRET_KEY'] = os.environ.get('BOOKSTORE_SECRET', 'dev-secret')
    # Use the Flask instance folder for a single canonical sqlite DB file so
    # the path is consistent regardless of the current working directory.
    # Ensure the instance folder exists and use an absolute path to the DB.
    os.makedirs(app.instance_path, exist_ok=True)

    # Log uncaught exceptions to a file so 500 errors are diagnosable even when
    # console output is not visible.
    log_path = os.path.join(app.instance_path, 'server_errors.log')
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

    db_path = os.path.join(app.instance_path, 'bookstore.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)

    class UserLogin(UserMixin):
        def __init__(self, user):
            self.id = user.id
            self.username = user.username
            self.role = user.role

    @login_manager.user_loader
    def load_user(user_id):
        u = User.query.get(int(user_id))
        if not u:
            return None
        return UserLogin(u)

    def role_required(role):
        def decorator(f):
            from functools import wraps
            @wraps(f)
            def wrapped(*args, **kwargs):
                if not current_user.is_authenticated:
                    return redirect(url_for('login'))
                if current_user.role != role:
                    return ("Forbidden", 403)
                return f(*args, **kwargs)
            return wrapped
        return decorator

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('app_ui'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'GET':
            return render_template('login.html')
        data = request.form
        username = data.get('username')
        password = data.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(UserLogin(user))
            # Explicitly redirect to the app_ui route
            return redirect(url_for('app_ui'))
        return render_template('login.html', error='Invalid username or password')

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc):
        # Let Flask handle normal HTTP errors (404, 403, etc.)
        if isinstance(exc, HTTPException):
            return exc
        app.logger.exception('Unhandled exception during request')
        return ("Internal Server Error", 500)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        # Simple open registration that creates users with role 'cashier' by default.
        # For production, restrict this or require admin approval.
        if request.method == 'GET':
            return render_template('register.html')
        data = request.form
        username = data.get('username')
        password = data.get('password')
        # Default role is cashier to avoid accidental admin creation
        role = data.get('role') or 'cashier'
        if not username or not password:
            return render_template('register.html', error='Missing username or password')
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already exists')
        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    # Simple API endpoints
    @app.route('/api/inventory', methods=['GET'])
    @login_required
    def api_inventory():
        # Return current inventory from Django database (where supplier orders update it)
        try:
            import django_integration
            inventory_data = django_integration.get_all_inventory()
            return jsonify(inventory_data)
        except Exception as e:
            app.logger.error(f"Error fetching Django inventory: {str(e)}")
            # Fallback to Flask inventory if Django fails
            return jsonify(book_inventory.show_inventory())

    @app.route('/api/inventory/low-stock', methods=['GET'])
    @login_required
    def api_low_stock():
        """Check for low stock items based on threshold"""
        threshold = request.args.get('threshold', 5, type=int)
        inventory_data = book_inventory.show_inventory()
        low_stock_items = [item for item in inventory_data if item['quantity'] <= threshold]
        return jsonify({
            'threshold': threshold,
            'low_stock_count': len(low_stock_items),
            'items': low_stock_items
        })

    @app.route('/api/inventory/add-delivery', methods=['POST'])
    @login_required
    def api_add_delivery():
        data = request.get_json() or {}
        book_id = data.get('book_id')
        amount = data.get('amount')
        result = book_inventory.add_delivery(book_id, amount)
        return jsonify(result), 200 if result.get('success') else 400

    @app.route('/api/inventory/add-book', methods=['POST'])
    @login_required
    def api_add_book():
        data = request.get_json() or {}
        book_id = data.get('book_id')
        title = data.get('title')
        quantity = data.get('quantity', 0)
        result = book_inventory.add_book(book_id, title, quantity)
        return jsonify(result), 200 if result.get('success') else 400

    @app.route('/api/orders', methods=['GET', 'POST'])
    @login_required
    def api_orders():
        if request.method == 'GET':
            # Return all orders
            return jsonify(order_cancellation.get_all_orders())
        else:
            # POST: Create a new order
            data = request.get_json() or {}
            customer_name = data.get('customer_name')
            items = data.get('items', [])
            if customer_name:
                result = order_cancellation.create_order(customer_name, items)
                return jsonify(result), 200 if result.get('success') else 400
            else:
                # Accept generic order payload
                payload = data
                return jsonify({'status':'ok','order':payload}), 201

    @app.route('/api/orders/<int:order_id>/cancel', methods=['POST'])
    @login_required
    def api_cancel_order(order_id):
        result = order_cancellation.cancel_order(order_id)
        return jsonify(result), 200 if result.get('success') else 400

    @app.route('/api/supplier-orders', methods=['GET', 'POST'])
    @login_required
    def api_supplier_orders():
        if request.method == 'GET':
            # Return all supplier purchase orders
            orders = supplier_orders.get_all_orders()
            return jsonify({'orders': orders}), 200
        else:
            # POST: Create a new supplier purchase order
            data = request.get_json() or {}
            supplier_name = data.get('supplier_name')
            po_date = data.get('po_date')
            items = data.get('items', [])
            total = data.get('total', 0)
            
            if supplier_name and po_date:
                result = supplier_orders.create_order(supplier_name, po_date, items, total)
                return jsonify(result), 200 if result.get('success') else 400
            else:
                return jsonify({'success': False, 'message': 'Missing supplier_name or po_date'}), 400

    @app.route('/api/supplier-orders/<int:po_id>/receive', methods=['POST'])
    @login_required
    def api_receive_supplier_order(po_id):
        """Mark a supplier order as received and update inventory"""
        result = supplier_orders.mark_order_received(po_id)
        
        if result.get('success'):
            # Get the order details
            order = result.get('order', {})
            items = order.get('items', [])
            supplier_name = order.get('supplier_name', 'Unknown Supplier')
            
            app.logger.info(f"Receiving order {po_id} from {supplier_name} with {len(items)} items: {items}")
            
            # Update Django inventory (lazy import to avoid startup issues)
            try:
                import django_integration
                django_result = django_integration.receive_and_update_inventory(
                    po_id=po_id,
                    supplier_name=supplier_name,
                    items=items
                )
                
                # Merge results
                result['django_sync'] = django_result
                if django_result.get('inventory_updates'):
                    result['inventory_updates'] = django_result['inventory_updates']
                if django_result.get('errors'):
                    result['inventory_errors'] = django_result['errors']
                
                app.logger.info(f"Received supplier order {po_id}. Django sync result: {django_result}")
            except Exception as e:
                app.logger.error(f"Django sync failed for order {po_id}: {str(e)}", exc_info=True)
                # Order is still marked as received in Flask, even if Django sync fails
        
        return jsonify(result), 200 if result.get('success') else 400

    @app.route('/api/supplier-orders/<int:po_id>/cancel', methods=['POST'])
    @login_required
    def api_cancel_supplier_order(po_id):
        """Cancel a supplier order"""
        result = supplier_orders.cancel_order(po_id)
        
        if result.get('success'):
            # Sync cancellation to Django (lazy import to avoid startup issues)
            try:
                import django_integration
                django_result = django_integration.cancel_and_sync_order(po_id)
                result['django_sync'] = django_result
                app.logger.info(f"Cancelled supplier order {po_id}. Django sync: {django_result}")
            except Exception as e:
                app.logger.warning(f"Django sync failed for order {po_id}: {str(e)}")
                # Order is still cancelled in Flask, even if Django sync fails
        
        return jsonify(result), 200 if result.get('success') else 400

    @app.route('/api/supplier-orders/pending', methods=['GET'])
    @login_required
    def api_pending_supplier_orders():
        """Get all pending supplier orders"""
        orders = supplier_orders.get_pending_orders()
        return jsonify({'orders': orders}), 200

    @app.route('/api/supplier-orders/received', methods=['GET'])
    @login_required
    def api_received_supplier_orders():
        """Get all received supplier orders"""
        orders = supplier_orders.get_received_orders()
        return jsonify({'orders': orders}), 200

    # Admin-only endpoint example
    @app.route('/admin/users')
    @login_required
    @role_required('admin')
    def admin_users():
        users = User.query.all()
        return render_template('admin_users.html', users=users)

    @app.route('/app')
    @login_required
    def app_ui():
        from flask import Response
        
        # Use the helper function to get resource path (handles PyInstaller bundles)
        html_path = get_resource_path('Bookstore_Management_System.html')
        
        # Also try alternative paths as fallback
        paths_to_try = [
            html_path,
            os.path.join(os.getcwd(), 'Bookstore_Management_System.html'),
            os.path.join(os.path.dirname(sys.executable), 'Bookstore_Management_System.html'),
            os.path.join(app.static_folder, 'Bookstore_Management_System.html'),
        ]
        
        found_path = None
        for path in paths_to_try:
            if os.path.exists(path):
                found_path = path
                break
        
        if found_path:
            try:
                with open(found_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return Response(content, mimetype='text/html')
            except Exception as e:
                app.logger.error(f"Error reading HTML file {found_path}: {str(e)}")
                return f"Error reading HTML file: {str(e)}", 500
        
        # If we get here, file was not found in any location
        app.logger.error(f"HTML file not found. Tried paths: {paths_to_try}")
        return f"File not found. Tried: {', '.join(paths_to_try)}", 500

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        
        # Seed default users if they don't exist
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', role='admin')
            admin.set_password('adminpass')
            db.session.add(admin)
        
        if not User.query.filter_by(username='cashier').first():
            cashier = User(username='cashier', role='cashier')
            cashier.set_password('cashierpass')
            db.session.add(cashier)
        
        try:
            db.session.commit()
        except:
            db.session.rollback()
    
    print("\n" + "="*60)
    print("BOOKSTORE MANAGEMENT SYSTEM")
    print("="*60)
    print("\nServer starting on http://127.0.0.1:5000")
    print("\nOpening login page in your browser...")
    print("If browser does not open, manually visit:")
    print("  http://127.0.0.1:5000/login")
    print("\nLogin credentials:")
    print("  Username: admin")
    print("  Password: adminpass")
    print("\nPress CTRL+C to stop the server")
    print("="*60 + "\n")
    
    # Open browser in a separate thread after server starts
    def open_browser():
        time.sleep(3)  # Wait 3 seconds for server to fully start
        try:
            # Try multiple methods to open the browser
            if sys.platform == 'win32':
                os.startfile('http://127.0.0.1:5000/login')
            else:
                webbrowser.open('http://127.0.0.1:5000/login')
        except Exception as e:
            print(f"\nNote: Could not auto-open browser")
            print(f"Please manually open: http://127.0.0.1:5000/login\n")
    
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Run without the reloader in this environment to avoid issues with background execution
    app.run(debug=False)
