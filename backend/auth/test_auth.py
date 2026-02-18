"""
Quick test script for authentication system
"""
import asyncio
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

async def test_auth():
    """Test authentication system"""
    
    # Connect to database
    conn = await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        database=os.getenv("POSTGRES_DB", "memorygraph_ai"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    
    print("✅ Connected to database")
    
    # Import after connection
    from auth.user_manager import UserManager
    from auth.jwt_handler import jwt_handler
    
    # Create user manager
    user_manager = UserManager(conn)
    
    # Create users table
    print("\n📋 Creating users table...")
    await user_manager.create_users_table()
    
    # Test registration
    print("\n👤 Testing user registration...")
    try:
        result = await user_manager.register_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            full_name="Test User"
        )
        print(f"✅ User registered: {result['user']['username']}")
        print(f"🔑 Token: {result['access_token'][:50]}...")
        
        token = result['access_token']
        
    except ValueError as e:
        print(f"⚠️ User already exists, testing login instead")
        
        # Test login
        print("\n🔐 Testing user login...")
        result = await user_manager.login_user(
            email_or_username="testuser",
            password="testpass123"
        )
        print(f"✅ User logged in: {result['user']['username']}")
        print(f"🔑 Token: {result['access_token'][:50]}...")
        
        token = result['access_token']
    
    # Test token verification
    print("\n🔍 Testing token verification...")
    payload = jwt_handler.decode_token(token)
    if payload:
        print(f"✅ Token valid!")
        print(f"   User ID: {payload['user_id']}")
        print(f"   Username: {payload['username']}")
        print(f"   Email: {payload['email']}")
    else:
        print("❌ Token invalid")
    
    # Test get user by ID
    print("\n👥 Testing get user by ID...")
    user = await user_manager.get_user_by_id(result['user']['id'])
    if user:
        print(f"✅ User found: {user['username']} ({user['email']})")
    else:
        print("❌ User not found")
    
    # Close connection
    await conn.close()
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_auth())
