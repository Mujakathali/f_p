"""
Script to update existing Neo4j Memory nodes with user_id from PostgreSQL
Run this once to migrate existing data
"""
import asyncio
import asyncpg
from neo4j import AsyncGraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

# Database configurations
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "memorygraph_ai"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "iammuja008")
}

NEO4J_CONFIG = {
    "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    "user": os.getenv("NEO4J_USER", "neo4j"),
    "password": os.getenv("NEO4J_PASSWORD", "iammuja008")
}

async def update_neo4j_user_ids():
    """Update Neo4j Memory nodes with user_id from PostgreSQL"""
    
    # Connect to PostgreSQL
    print("📊 Connecting to PostgreSQL...")
    pg_conn = await asyncpg.connect(**POSTGRES_CONFIG)
    
    # Connect to Neo4j
    print("🔗 Connecting to Neo4j...")
    neo4j_driver = AsyncGraphDatabase.driver(
        NEO4J_CONFIG["uri"],
        auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"])
    )
    
    try:
        # Get all memories from PostgreSQL with their user_ids
        print("📝 Fetching memories from PostgreSQL...")
        memories = await pg_conn.fetch(
            "SELECT id, user_id FROM memories WHERE user_id IS NOT NULL"
        )
        print(f"✅ Found {len(memories)} memories in PostgreSQL")
        
        # Update Neo4j nodes
        print("🔄 Updating Neo4j Memory nodes...")
        updated_count = 0
        not_found_count = 0
        
        async with neo4j_driver.session() as session:
            for memory in memories:
                memory_id = memory["id"]
                user_id = memory["user_id"]
                
                # Update the Memory node in Neo4j
                result = await session.run(
                    """
                    MATCH (m:Memory {id: $memory_id})
                    SET m.user_id = $user_id
                    RETURN m
                    """,
                    memory_id=memory_id,
                    user_id=user_id
                )
                
                record = await result.single()
                if record:
                    updated_count += 1
                    if updated_count % 10 == 0:
                        print(f"   Updated {updated_count}/{len(memories)} memories...")
                else:
                    not_found_count += 1
        
        print(f"\n✅ Migration complete!")
        print(f"   ✓ Updated: {updated_count} Memory nodes")
        print(f"   ⚠ Not found in Neo4j: {not_found_count} memories")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        raise
    finally:
        # Close connections
        await pg_conn.close()
        await neo4j_driver.close()
        print("🔌 Connections closed")

if __name__ == "__main__":
    print("=" * 60)
    print("Neo4j Memory Node User ID Migration")
    print("=" * 60)
    print()
    
    asyncio.run(update_neo4j_user_ids())
    
    print()
    print("=" * 60)
    print("Migration completed successfully!")
    print("=" * 60)
