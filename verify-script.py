#!/usr/bin/env python3
# verify_installation.py
"""
Verify that the Sangram Tutor package is properly installed and accessible.
Run this script to check if all components can be imported correctly.
"""

import sys
import importlib
import os

def check_import(module_name):
    """Try to import a module and return whether it was successful."""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError as e:
        return False, str(e)

def main():
    """Check if the Sangram Tutor package is properly installed."""
    print("Verifying Sangram Tutor installation...")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    # Check if the package and its subpackages can be imported
    modules_to_check = [
        "sangram_tutor",
        "sangram_tutor.api",
        "sangram_tutor.db",
        "sangram_tutor.ml",
        "sangram_tutor.models",
        "sangram_tutor.utils",
    ]
    
    all_imports_successful = True
    for module in modules_to_check:
        result = check_import(module)
        if result is True:
            print(f"✓ {module} can be imported successfully")
        else:
            all_imports_successful = False
            print(f"✗ {module} import failed: {result[1]}")
    
    # Check main application module
    try:
        from sangram_tutor.main import app
        print("✓ Main application imported successfully")
    except ImportError as e:
        all_imports_successful = False
        print(f"✗ Main application import failed: {e}")
    
    # Summary
    if all_imports_successful:
        print("\n✅ All components can be imported successfully!")
        print("You're ready to run the application with: python -m sangram_tutor.main")
        return 0
    else:
        print("\n❌ Some components could not be imported.")
        print("Please check your installation and project structure.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
