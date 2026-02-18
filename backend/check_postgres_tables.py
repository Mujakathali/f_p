#!/usr/bin/env python3
"""
Check PostgreSQL database structure and content
"""
import asyncio
from db.postgresql_connector import PostgreSQLConnector

async def check_postgres_structure():
    """Check PostgreSQL tables and data"""
    print("🔍 Checking PostgreSQL Database Structure...")
    
    postgres_db = PostgreSQLConnector()
    
    try:
        await postgres_db.connect()
        
        # 1. List all tables
        print("\n📋 **Available Tables:**")
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """
        
        async with postgres_db.pool.acquire() as conn:
            tables = await conn.fetch(tables_query)
            for i, table in enumerate(tables, 1):
                print(f"   {i}. {table['table_name']}")
        
        # 2. Check memories table structure
        print("\n🗂️ **Memories Table Structure:**")
        structure_query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'memories'
        ORDER BY ordinal_position;
        """
        
        async with postgres_db.pool.acquire() as conn:
            columns = await conn.fetch(structure_query)
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"   • {col['column_name']}: {col['data_type']} {nullable}{default}")
        
        # 3. Check recent memories data
        print("\n📊 **Recent Memories Data:**")
        data_query = """
        SELECT id, memory_type, raw_text, embedding_id, 
               CASE WHEN metadata IS NOT NULL THEN 'Has metadata' ELSE 'No metadata' END as metadata_status,
               created_at
        FROM memories 
        ORDER BY created_at DESC 
        LIMIT 10;
        """
        
        async with postgres_db.pool.acquire() as conn:
            memories = await conn.fetch(data_query)
            print(f"   Found {len(memories)} recent memories:")
            for memory in memories:
                embed_status = "✅" if memory['embedding_id'] else "❌ NULL"
                print(f"   • ID: {memory['id']}, Type: {memory['memory_type']}, "
                      f"Embedding: {embed_status}, Text: {memory['raw_text'][:50]}...")
        
        # 4. Check embedding_id statistics
        print("\n📈 **Embedding ID Statistics:**")
        stats_query = """
        SELECT 
            memory_type,
            COUNT(*) as total_count,
            COUNT(embedding_id) as with_embedding,
            COUNT(*) - COUNT(embedding_id) as null_embedding
        FROM memories 
        GROUP BY memory_type;
        """
        
        async with postgres_db.pool.acquire() as conn:
            stats = await conn.fetch(stats_query)
            for stat in stats:
                print(f"   • {stat['memory_type']}: {stat['total_count']} total, "
                      f"{stat['with_embedding']} with embedding, "
                      f"{stat['null_embedding']} with NULL embedding")
        
        # 5. Check if there are other embedding-related tables
        print("\n🔗 **Other Tables (entities, sentiments, etc.):**")
        other_tables = ['entities', 'sentiments', 'keywords', 'embeddings']
        
        for table_name in other_tables:
            check_query = f"""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_name = '{table_name}' AND table_schema = 'public';
            """
            
            async with postgres_db.pool.acquire() as conn:
                result = await conn.fetchval(check_query)
                if result > 0:
                    count_query = f"SELECT COUNT(*) FROM {table_name};"
                    count = await conn.fetchval(count_query)
                    print(f"   • {table_name}: {count} records")
                else:
                    print(f"   • {table_name}: Table does not exist")
        
        print("\n✅ Database check completed!")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await postgres_db.disconnect()

if __name__ == "__main__":
    asyncio.run(check_postgres_structure())
