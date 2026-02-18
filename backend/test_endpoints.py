"""
Quick test script to verify all endpoints are accessible
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoints():
    print("="*70)
    print("TESTING BACKEND ENDPOINTS")
    print("="*70)
    
    # Test 1: Root endpoint
    print("\n1️⃣ Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        print("   ✅ Root endpoint working")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return
    
    # Test 2: Health check
    print("\n2️⃣ Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Services: {json.dumps(data.get('services', {}), indent=6)}")
            print("   ✅ Health check working")
        else:
            print(f"   ❌ Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 3: Register endpoint
    print("\n3️⃣ Testing register endpoint...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "username": "testuser123",
                "email": "test123@example.com",
                "password": "testpass123",
                "full_name": "Test User"
            }
        )
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 201]:
            print("   ✅ Register endpoint working")
        elif response.status_code == 400:
            print("   ⚠️  User might already exist (this is OK)")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 4: Login endpoint
    print("\n4️⃣ Testing login endpoint...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "username": "testuser123",
                "password": "testpass123"
            }
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"   Token: {token[:30]}..." if token else "   No token received")
            print("   ✅ Login endpoint working")
            
            # Test 5: Authenticated endpoint
            if token:
                print("\n5️⃣ Testing authenticated memory creation...")
                try:
                    response = requests.post(
                        f"{BASE_URL}/api/v1/add_memory",
                        headers={"Authorization": f"Bearer {token}"},
                        json={
                            "text": "Test memory from endpoint test",
                            "metadata": {"source": "test"}
                        }
                    )
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        print("   ✅ Memory creation working")
                    else:
                        print(f"   Response: {response.text}")
                except Exception as e:
                    print(f"   ❌ Failed: {e}")
                
                # Test 6: Search endpoint
                print("\n6️⃣ Testing memory search...")
                try:
                    response = requests.get(
                        f"{BASE_URL}/api/v1/search_memories",
                        headers={"Authorization": f"Bearer {token}"},
                        params={"query": "test", "limit": 5}
                    )
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        count = len(data.get("memories", []))
                        print(f"   Found {count} memories")
                        print("   ✅ Search working")
                    else:
                        print(f"   Response: {response.text}")
                except Exception as e:
                    print(f"   ❌ Failed: {e}")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    print("\n" + "="*70)
    print("ENDPOINT TESTING COMPLETE")
    print("="*70)
    print("\nIf all tests passed, your backend is working correctly!")
    print("If tests failed, check:")
    print("  1. Backend is running on port 8000")
    print("  2. Database migration has been run")
    print("  3. PostgreSQL is running")
    print("  4. Check backend terminal for errors")

if __name__ == "__main__":
    test_endpoints()
