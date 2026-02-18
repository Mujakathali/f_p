"""
User Manager for Authentication
Handles user registration, login, and user data management
"""
import asyncpg
from typing import Optional, Dict
from datetime import datetime
from .jwt_handler import jwt_handler


class UserManager:
    """Manage user authentication and data"""
    
    def __init__(self, connection_pool):
        """
        Initialize UserManager with asyncpg connection pool
        
        Args:
            connection_pool: asyncpg pool
        """
        self.pool = connection_pool
    
    async def create_users_table(self):
        """Create users table if it doesn't exist"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
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
        
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        """
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(create_table_query)
            print("✅ Users table created/verified")
        except Exception as e:
            print(f"❌ Error creating users table: {e}")
            raise
    
    async def register_user(self, email: str, username: str, password: str, 
                           full_name: Optional[str] = None) -> Dict:
        """
        Register a new user
        
        Args:
            email: User email
            username: Username
            password: Plain text password (will be hashed)
            full_name: Optional full name
            
        Returns:
            Dictionary with user data and token
        """
        try:
            # Check if user already exists
            async with self.pool.acquire() as conn:
                existing_user = await conn.fetchrow(
                    "SELECT id FROM users WHERE email = $1 OR username = $2",
                    email, username
                )
            
            if existing_user:
                raise ValueError("User with this email or username already exists")
            
            # Hash password
            password_hash = jwt_handler.hash_password(password)
            
            # Insert new user
            async with self.pool.acquire() as conn:
                user = await conn.fetchrow(
                    """
                    INSERT INTO users (email, username, password_hash, full_name)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id, email, username, full_name, created_at
                    """,
                    email, username, password_hash, full_name
                )
            
            # Create JWT token
            token_data = {
                "user_id": user["id"],
                "email": user["email"],
                "username": user["username"]
            }
            access_token = jwt_handler.create_access_token(token_data)
            
            print(f"✅ User registered: {username} ({email})")
            
            return {
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "username": user["username"],
                    "full_name": user["full_name"],
                    "created_at": user["created_at"].isoformat()
                },
                "access_token": access_token,
                "token_type": "bearer"
            }
            
        except ValueError as e:
            raise e
        except Exception as e:
            print(f"❌ Registration error: {e}")
            raise Exception(f"Registration failed: {str(e)}")
    
    async def login_user(self, email_or_username: str, password: str) -> Dict:
        """
        Login user and return JWT token
        
        Args:
            email_or_username: User email or username
            password: Plain text password
            
        Returns:
            Dictionary with user data and token
        """
        try:
            # Find user by email or username
            async with self.pool.acquire() as conn:
                user = await conn.fetchrow(
                    """
                    SELECT id, email, username, password_hash, full_name, is_active
                    FROM users
                    WHERE email = $1 OR username = $1
                    """,
                    email_or_username
                )
            
            if not user:
                raise ValueError("Invalid credentials")
            
            if not user["is_active"]:
                raise ValueError("Account is disabled")
            
            # Verify password
            if not jwt_handler.verify_password(password, user["password_hash"]):
                raise ValueError("Invalid credentials")
            
            # Update last login
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE users SET last_login = $1 WHERE id = $2",
                    datetime.utcnow(), user["id"]
                )
            
            # Create JWT token
            token_data = {
                "user_id": user["id"],
                "email": user["email"],
                "username": user["username"]
            }
            access_token = jwt_handler.create_access_token(token_data)
            
            print(f"✅ User logged in: {user['username']}")
            
            return {
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "username": user["username"],
                    "full_name": user["full_name"]
                },
                "access_token": access_token,
                "token_type": "bearer"
            }
            
        except ValueError as e:
            raise e
        except Exception as e:
            print(f"❌ Login error: {e}")
            raise Exception(f"Login failed: {str(e)}")
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        try:
            async with self.pool.acquire() as conn:
                user = await conn.fetchrow(
                    """
                    SELECT id, email, username, full_name, created_at, last_login, profile_data
                    FROM users
                    WHERE id = $1 AND is_active = TRUE
                    """,
                    user_id
                )
            
            if not user:
                return None
            
            return {
                "id": user["id"],
                "email": user["email"],
                "username": user["username"],
                "full_name": user["full_name"],
                "created_at": user["created_at"].isoformat() if user["created_at"] else None,
                "last_login": user["last_login"].isoformat() if user["last_login"] else None,
                "profile_data": user["profile_data"]
            }
            
        except Exception as e:
            print(f"❌ Error fetching user: {e}")
            return None
    
    async def verify_token_and_get_user(self, token: str) -> Optional[Dict]:
        """
        Verify JWT token and return user data
        
        Args:
            token: JWT token string
            
        Returns:
            User data dictionary or None if invalid
        """
        payload = jwt_handler.decode_token(token)
        
        if not payload:
            return None
        
        user_id = payload.get("user_id")
        if not user_id:
            return None
        
        return await self.get_user_by_id(user_id)
