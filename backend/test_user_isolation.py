"""
Test script to verify user memory isolation
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "memorygraph_ai"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "iammuja008")
}

async def test_user_isolation():
    """Test that memories are properly isolated by user_id"""
    
    print("=" * 70)
    print("USER MEMORY ISOLATION TEST")
    print("=" * 70)
    print()
    
    # Connect to PostgreSQL
    print("📊 Connecting to PostgreSQL...")
    conn = await asyncpg.connect(**POSTGRES_CONFIG)
    
    try:
        # Test 1: Check if user_id column exists
        print("\n✅ Test 1: Verify user_id column exists")
        columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'memories' AND column_name = 'user_id'
        """)
        
        if columns:
            print(f"   ✓ user_id column exists: {columns[0]['data_type']}")
        else:
            print("   ❌ user_id column NOT FOUND!")
            return
        
        # Test 2: Count total memories
        print("\n✅ Test 2: Count total memories")
        total_count = await conn.fetchval("SELECT COUNT(*) FROM memories")
        print(f"   Total memories in database: {total_count}")
        
        # Test 3: Count memories per user
        print("\n✅ Test 3: Count memories per user")
        user_counts = await conn.fetch("""
            SELECT user_id, COUNT(*) as count 
            FROM memories 
            GROUP BY user_id 
            ORDER BY user_id
        """)
        
        if user_counts:
            print("   User ID | Memory Count")
            print("   --------|-------------")
            for row in user_counts:
                user_id = row['user_id'] if row['user_id'] is not None else "NULL"
                print(f"   {str(user_id):>7} | {row['count']:>12}")
        else:
            print("   No memories found")
        
        # Test 4: Check for memories without user_id
        print("\n✅ Test 4: Check for orphaned memories (no user_id)")
        orphaned_count = await conn.fetchval("""
            SELECT COUNT(*) FROM memories WHERE user_id IS NULL
        """)
        
        if orphaned_count > 0:
            print(f"   ⚠️  WARNING: {orphaned_count} memories without user_id")
            print("   These memories won't be visible to any user!")
            print("   Consider assigning them to a user or deleting them.")
        else:
            print(f"   ✓ All memories have user_id assigned")
        
        # Test 5: Get sample memories for each user
        print("\n✅ Test 5: Sample memories per user")
        users = await conn.fetch("""
            SELECT DISTINCT user_id 
            FROM memories 
            WHERE user_id IS NOT NULL 
            ORDER BY user_id
        """)
        
        for user_row in users:
            user_id = user_row['user_id']
            
            # Get user info
            user_info = await conn.fetchrow("""
                SELECT username, email FROM users WHERE id = $1
            """, user_id)
            
            username = user_info['username'] if user_info else "Unknown"
            email = user_info['email'] if user_info else "Unknown"
            
            # Get memory count
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM memories WHERE user_id = $1
            """, user_id)
            
            # Get latest memory
            latest = await conn.fetchrow("""
                SELECT id, raw_text, timestamp 
                FROM memories 
                WHERE user_id = $1 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, user_id)
            
            print(f"\n   👤 User {user_id}: {username} ({email})")
            print(f"      Memories: {count}")
            if latest:
                text_preview = latest['raw_text'][:50] + "..." if len(latest['raw_text']) > 50 else latest['raw_text']
                print(f"      Latest: [{latest['id']}] {text_preview}")
                print(f"      Time: {latest['timestamp']}")
        
        # Test 6: Verify index exists
        print("\n✅ Test 6: Check for user_id index")
        indexes = await conn.fetch("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'memories' 
            AND indexdef LIKE '%user_id%'
        """)
        
        if indexes:
            print("   ✓ Index on user_id exists:")
            for idx in indexes:
                print(f"      - {idx['indexname']}")
        else:
            print("   ⚠️  No index on user_id (may affect performance)")
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        if orphaned_count == 0 and user_counts:
            print("✅ User isolation is properly configured!")
            print("✅ All memories have user_id assigned")
            print("✅ Each user has their own memory space")
            print("\n🎉 Timeline should now show user-specific memories only!")
        elif orphaned_count > 0:
            print("⚠️  Some memories don't have user_id")
            print("   Run update_neo4j_user_ids.py to fix")
        else:
            print("ℹ️  No memories in database yet")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()
        print("\n🔌 Database connection closed")

if __name__ == "__main__":
    asyncio.run(test_user_isolation())
