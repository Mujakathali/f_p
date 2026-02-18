"""
Direct migration script - adds user_id to memories table
"""
import asyncio
import asyncpg
import os
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

async def run_migration():
    """Add user_id column to memories table"""
    
    # Database configuration
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'memorygraph_ai'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'password')
    }
    
    print("\n" + "="*70)
    print("DATABASE MIGRATION - Adding user_id to memories table")
    print("="*70)
    print(f"\nConnecting to database: {db_config['database']} at {db_config['host']}:{db_config['port']}")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(**db_config)
        print("✅ Connected to PostgreSQL successfully")
        
        # Check if column exists
        print("\n🔍 Checking if user_id column exists...")
        check_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='memories' AND column_name='user_id';
        """
        exists = await conn.fetchval(check_query)
        
        if exists:
            print("✅ user_id column already exists in memories table")
        else:
            print("📝 user_id column does not exist, adding it now...")
            
            # Add user_id column
            alter_query = """
            ALTER TABLE memories 
            ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
            """
            await conn.execute(alter_query)
            print("✅ Successfully added user_id column to memories table")
        
        # Create index
        print("\n🔍 Creating index on user_id...")
        index_query = """
        CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id);
        """
        await conn.execute(index_query)
        print("✅ Index created successfully")
        
        # Check if there are any users
        print("\n🔍 Checking for existing users...")
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        print(f"📊 Found {user_count} users in database")
        
        if user_count > 0:
            # Update existing memories
            print("\n🔄 Updating existing memories with user_id...")
            first_user_id = await conn.fetchval("SELECT id FROM users ORDER BY id LIMIT 1")
            print(f"📝 Assigning memories to user ID: {first_user_id}")
            
            update_query = """
            UPDATE memories 
            SET user_id = $1
            WHERE user_id IS NULL;
            """
            result = await conn.execute(update_query, first_user_id)
            print(f"✅ Updated existing memories: {result}")
        else:
            print("⚠️  No users found - memories will need user_id when created")
        
        # Verify changes
        print("\n📊 Verifying changes...")
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_memories,
                COUNT(user_id) as memories_with_user_id
            FROM memories
        """)
        print(f"   Total memories: {stats['total_memories']}")
        print(f"   Memories with user_id: {stats['memories_with_user_id']}")
        
        await conn.close()
        
        print("\n" + "="*70)
        print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("\n✅ You can now restart your backend server")
        print("✅ All memory operations will now be user-specific\n")
        
    except Exception as e:
        print("\n" + "="*70)
        print("❌ MIGRATION FAILED!")
        print("="*70)
        print(f"\nError: {e}")
        print("\nFull error details:")
        import traceback
        traceback.print_exc()
        print("\n" + "="*70)
        raise

if __name__ == "__main__":
    asyncio.run(run_migration())
