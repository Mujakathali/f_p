"""
Migration script to add user_id column to memories table
Run this script to update the database schema for user-specific memories
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def migrate():
    """Add user_id column to memories table and create index"""
    
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'memorygraph_ai'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'password')
    }
    
    conn = await asyncpg.connect(**db_config)
    
    try:
        print("🔄 Starting migration to add user_id to memories table...")
        
        # Check if column already exists
        check_column = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='memories' AND column_name='user_id';
        """
        exists = await conn.fetchval(check_column)
        
        if exists:
            print("✅ user_id column already exists in memories table")
        else:
            # Add user_id column
            alter_table = """
            ALTER TABLE memories 
            ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
            """
            await conn.execute(alter_table)
            print("✅ Added user_id column to memories table")
        
        # Create index for better query performance
        create_index = """
        CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id);
        """
        await conn.execute(create_index)
        print("✅ Created index on user_id column")
        
        # Update existing memories to have a default user_id (optional)
        # This assigns all existing memories to the first user
        update_existing = """
        UPDATE memories 
        SET user_id = (SELECT id FROM users ORDER BY id LIMIT 1)
        WHERE user_id IS NULL;
        """
        updated_count = await conn.execute(update_existing)
        print(f"✅ Updated {updated_count} existing memories with default user_id")
        
        print("\n🎉 Migration completed successfully!")
        print("📝 All memories are now user-specific")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())
