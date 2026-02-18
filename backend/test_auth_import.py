"""
Quick test to verify auth imports work correctly
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing auth imports...")

try:
    from auth.auth_routes import auth_router, initialize_auth
    print("✅ auth_routes imported successfully")
    
    from auth.user_manager import UserManager
    print("✅ user_manager imported successfully")
    
    from auth.jwt_handler import jwt_handler
    print("✅ jwt_handler imported successfully")
    
    from auth.dependencies import get_current_user
    print("✅ dependencies imported successfully")
    
    print("\n🎉 All auth imports successful!")
    print("✅ Backend should start without ModuleNotFoundError")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
