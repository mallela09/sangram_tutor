# test_imports.py
print("Testing imports...")

try:
    from api.auth import router as auth_router
    print("✅ Successfully imported auth_router")
except ImportError as e:
    print(f"❌ Failed to import auth_router: {e}")

try:
    from api.users import router as users_router
    print("✅ Successfully imported users_router")
except ImportError as e:
    print(f"❌ Failed to import users_router: {e}")

try:
    from api.learning import router as learning_router
    print("✅ Successfully imported learning_router")
except ImportError as e:
    print(f"❌ Failed to import learning_router: {e}")

try:
    from api.analytics import router as analytics_router
    print("✅ Successfully imported analytics_router")
except ImportError as e:
    print(f"❌ Failed to import analytics_router: {e}")

try:
    from db.session import get_db, engine
    print("✅ Successfully imported database session components")
except ImportError as e:
    print(f"❌ Failed to import database session components: {e}")

print("Import tests completed.")