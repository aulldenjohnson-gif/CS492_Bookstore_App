"""Launcher for Bookstore Management System

This script opens the `Bookstore_Management_System.html` file (created alongside
this script) in the user's default web browser. The original HTML content was
previously stored in this .py file which caused syntax errors when running
Python; the HTML has been moved into the `.html` file and this script is a
small, valid Python launcher.
"""

from pathlib import Path
import webbrowser
import sys


def main():
    html_path = Path(__file__).with_suffix('.html')
    if not html_path.exists():
        print(f"Error: '{html_path.name}' not found in {html_path.parent}")
        print("If you want a Python program instead, replace this file with valid code.")
        sys.exit(1)

    print(f"Opening '{html_path.name}' in your default web browser...")
    webbrowser.open_new_tab(html_path.as_uri())


if __name__ == '__main__':
    main()