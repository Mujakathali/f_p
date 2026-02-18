"""
Migration script to add user_id column to memories table
Run this after setting up authentication
"""
import asyncio
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

async def migrate():
    """Add user_id column to memories table"""
    
    # Connect to database
    conn = await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        database=os.getenv("POSTGRES_DB", "memorygraph_ai"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    
    print("✅ Connected to database")
    
    try:
        # Check if column already exists
        check_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='memories' AND column_name='user_id';
        """
        
        existing = await conn.fetchval(check_query)
        
        if existing:
            print("⚠️ user_id column already exists in memories table")
        else:
            # Add user_id column
            print("\n📋 Adding user_id column to memories table...")
            await conn.execute("""
                ALTER TABLE memories 
                ADD COLUMN user_id INTEGER REFERENCES users(id);
            """)
            print("✅ user_id column added")
            
            # Add index for performance
            print("\n📊 Creating index on user_id...")
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_user_id 
                ON memories(user_id);
            """)
            print("✅ Index created")
            
            # Optional: Set a default user for existing memories
            print("\n👤 Checking for existing memories...")
            memory_count = await conn.fetchval("SELECT COUNT(*) FROM memories WHERE user_id IS NULL")
            
            if memory_count > 0:
                print(f"⚠️ Found {memory_count} memories without user_id")
                print("   You may want to assign them to a default user")
                
                # Get first user
                first_user = await conn.fetchrow("SELECT id, username FROM users LIMIT 1")
                
                if first_user:
                    print(f"\n   Assign to user '{first_user['username']}' (ID: {first_user['id']})? (y/n)")
                    # In production, you'd want to handle this differently
                    # For now, we'll just report
                else:
                    print("   No users found. Create a user first, then assign memories manually.")
            else:
                print("✅ No existing memories to migrate")
        
        print("\n✅ Migration complete!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())
