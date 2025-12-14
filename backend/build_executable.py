"""
Build script to create a standalone executable for the Bookstore Management System
"""
import PyInstaller.__main__
import os
import shutil
import time

# Get paths
backend_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(backend_dir, '..'))
dist_dir = os.path.join(backend_dir, 'dist')
build_dir = os.path.join(backend_dir, 'build')
source_file = os.path.join(repo_root, 'Bookstore_Management_System.html')

# Clean previous builds with retry logic
def remove_dir(path, retries=3):
    for attempt in range(retries):
        try:
            if os.path.exists(path):
                shutil.rmtree(path)
            return True
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                print(f"Warning: Could not remove {path}: {e}")
                return False
    return False

remove_dir(dist_dir)
remove_dir(build_dir)

# PyInstaller arguments
args = [
    'app.py',
    '--name=BookstoreApp',
    '--onefile',  # Create single executable
    '--console',  # Show console window so user can see server is running
    '--add-data=templates:templates',  # Include templates folder
    f'--add-data={source_file}:.',  # Include HTML file
    '--add-data=../supplier_orders:supplier_orders',  # Include entire supplier_orders app
    '--add-data=../instance/bookstore_supplier.db:instance', # Include Django DB
    '--add-data=../bookstore_settings.py:.', # Include Django settings module
    '--hidden-import=flask',
    '--hidden-import=flask_login',
    '--hidden-import=flask_sqlalchemy',
    '--hidden-import=werkzeug',
    '--hidden-import=django',
    '--hidden-import=supplier_orders',
    '--hidden-import=supplier_orders.models',
    '--hidden-import=supplier_orders.apps',
    '--hidden-import=supplier_orders.admin',
    f'--distpath={dist_dir}',
    f'--workpath={build_dir}',
]

print("Building standalone executable...")
print(f"Output directory: {dist_dir}")
PyInstaller.__main__.run(args)

print("\n[BUILD COMPLETE]")
print(f"Executable location: {os.path.join(dist_dir, 'BookstoreApp.exe')}")
print("\nTo run the app:")
print(f"  cd {dist_dir}")
print("  BookstoreApp.exe")
print("\nThen open: http://127.0.0.1:5000/login")
