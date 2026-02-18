# JWT Authentication System

Complete JWT-based authentication system for user registration, login, and protected routes.

## 📁 Structure

```
auth/
├── __init__.py              # Module initialization
├── jwt_handler.py           # JWT token creation and validation
├── user_manager.py          # User registration, login, and management
├── dependencies.py          # FastAPI dependencies for protected routes
├── auth_routes.py           # Authentication API endpoints
└── README.md               # This file
```

## 🔐 Features

- ✅ User registration with email and username
- ✅ Secure password hashing with bcrypt
- ✅ JWT token generation and validation
- ✅ Protected routes with Bearer token authentication
- ✅ User profile management
- ✅ Token verification endpoint
- ✅ PostgreSQL database integration

## 🗄️ Database Schema

### Users Table

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    profile_data JSONB DEFAULT '{}'
);
```

## 🚀 API Endpoints

### 1. Register User

**POST** `/auth/register`

Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe",
    "full_name": "John Doe",
    "created_at": "2024-01-01T00:00:00"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### 2. Login

**POST** `/auth/login`

Login with email/username and password.

**Request:**
```json
{
  "email_or_username": "johndoe",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe",
    "full_name": "John Doe"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### 3. Get Current User Profile

**GET** `/auth/me`

Get current authenticated user's profile (protected route).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "created_at": "2024-01-01T00:00:00",
  "last_login": "2024-01-02T10:30:00"
}
```

### 4. Verify Token

**POST** `/auth/verify`

Verify if JWT token is valid (protected route).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "valid": true,
  "user_id": 1,
  "username": "johndoe",
  "email": "user@example.com"
}
```

## 🔧 Usage in Your Routes

### Protect a Route (Require Authentication)

```python
from fastapi import APIRouter, Depends
from auth.dependencies import get_current_user
from typing import Dict

router = APIRouter()

@router.get("/protected-endpoint")
async def protected_route(current_user: Dict = Depends(get_current_user)):
    """
    This route requires authentication
    User must send: Authorization: Bearer <token>
    """
    return {
        "message": f"Hello {current_user['username']}!",
        "user_id": current_user["user_id"]
    }
```

### Optional Authentication

```python
from auth.dependencies import get_optional_user
from typing import Optional, Dict

@router.get("/optional-auth")
async def optional_route(current_user: Optional[Dict] = Depends(get_optional_user)):
    """
    This route works with or without authentication
    """
    if current_user:
        return {"message": f"Hello {current_user['username']}!"}
    return {"message": "Hello guest!"}
```

## 🔑 Environment Variables

Add these to your `.env` file:

```env
# JWT Authentication Settings
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-12345
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days
```

## 📦 Required Dependencies

```txt
PyJWT==2.8.0
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
```

Install with:
```bash
pip install PyJWT passlib[bcrypt] python-jose[cryptography]
```

## 🧪 Testing with cURL

### Register
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpass123",
    "full_name": "Test User"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email_or_username": "testuser",
    "password": "testpass123"
  }'
```

### Get Profile (Protected)
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 🔐 Security Features

1. **Password Hashing**: Uses bcrypt for secure password storage
2. **JWT Tokens**: Stateless authentication with expiration
3. **Token Validation**: Automatic token verification on protected routes
4. **SQL Injection Protection**: Uses parameterized queries
5. **Unique Constraints**: Email and username must be unique
6. **Active Status**: Users can be deactivated without deletion

## 🎯 Frontend Integration Example

### React/JavaScript

```javascript
// Register
const register = async (email, username, password, fullName) => {
  const response = await fetch('http://localhost:8000/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, username, password, full_name: fullName })
  });
  const data = await response.json();
  
  // Store token
  localStorage.setItem('access_token', data.access_token);
  return data;
};

// Login
const login = async (emailOrUsername, password) => {
  const response = await fetch('http://localhost:8000/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      email_or_username: emailOrUsername, 
      password 
    })
  });
  const data = await response.json();
  
  // Store token
  localStorage.setItem('access_token', data.access_token);
  return data;
};

// Make authenticated request
const getProfile = async () => {
  const token = localStorage.getItem('access_token');
  const response = await fetch('http://localhost:8000/auth/me', {
    headers: { 
      'Authorization': `Bearer ${token}` 
    }
  });
  return await response.json();
};

// Logout
const logout = () => {
  localStorage.removeItem('access_token');
};
```

## 🛡️ Best Practices

1. **Change JWT Secret**: Update `JWT_SECRET_KEY` in production
2. **Use HTTPS**: Always use HTTPS in production
3. **Token Storage**: Store tokens securely (httpOnly cookies or secure storage)
4. **Token Expiration**: Implement refresh tokens for long sessions
5. **Rate Limiting**: Add rate limiting to prevent brute force attacks
6. **Input Validation**: Validate all user inputs
7. **Error Messages**: Don't reveal if email/username exists on login failure

## 🔄 Token Lifecycle

```
1. User registers/logs in
   ↓
2. Server generates JWT token (valid for 7 days)
   ↓
3. Client stores token (localStorage/cookies)
   ↓
4. Client sends token in Authorization header
   ↓
5. Server validates token on each request
   ↓
6. Token expires after 7 days
   ↓
7. User must login again
```

## 🚨 Error Handling

### Common Errors

- **400 Bad Request**: Invalid input (email format, password too short)
- **401 Unauthorized**: Invalid credentials or expired token
- **404 Not Found**: User not found
- **409 Conflict**: Email/username already exists
- **500 Internal Server Error**: Server error

## 📝 Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Update .env**: Set your JWT secret key
3. **Start server**: `python -m backend.start_server`
4. **Test endpoints**: Use cURL or Postman
5. **Integrate frontend**: Add login/register forms

## 🎉 You're All Set!

Your authentication system is ready to use. All memory routes can now be protected by adding `Depends(get_current_user)` to require authentication.
