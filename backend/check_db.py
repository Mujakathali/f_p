import asyncio
import sys
import os
sys.path.append('.')

from db.postgresql_connector import PostgreSQLConnector
from utils.embeddings import EmbeddingProcessor

async def check_database():
    print("🔍 Checking PostgreSQL database...")
    
    # Check PostgreSQL
    db = PostgreSQLConnector()
    await db.initialize()
    
    # Count total memories
    count = await db.connection_pool.fetchval("SELECT COUNT(*) FROM memories")
    print(f"📊 Total memories in PostgreSQL: {count}")
    
    if count > 0:
        # Get recent memories
        rows = await db.connection_pool.fetch("""
            SELECT id, processed_text, memory_type, timestamp 
            FROM memories 
            ORDER BY id DESC 
            LIMIT 10
        """)
        
        print(f"\n📝 Recent memories:")
        for row in rows:
            print(f"  ID: {row[0]}")
            print(f"  Text: {row[1][:100]}...")
            print(f"  Type: {row[2]}")
            print(f"  Time: {row[3]}")
            print("  ---")
        
        # Test text search
        print(f"\n🔍 Testing text search for 'happy'...")
        search_results = await db.search_memories("happy", 5)
        print(f"📝 Text search found {len(search_results)} results")
        for result in search_results:
            print(f"  - {result['processed_text'][:100]}...")
    
    await db.connection_pool.close()
    
    # Check ChromaDB embeddings
    print(f"\n🧠 Checking ChromaDB embeddings...")
    embedding_processor = EmbeddingProcessor()
    await embedding_processor.initialize()
    
    stats = await embedding_processor.get_embedding_stats()
    print(f"📊 Embedding stats: {stats}")
    
    if stats.get('total_embeddings', 0) > 0:
        # Test semantic search
        print(f"\n🔍 Testing semantic search for 'happy moments'...")
        semantic_results = await embedding_processor.search_similar_memories("happy moments", 5)
        print(f"🧠 Semantic search found {len(semantic_results)} results")
        for result in semantic_results:
            print(f"  - Similarity: {result['similarity']:.3f}")
            print(f"  - Text: {result['text'][:100]}...")
            print(f"  - Memory ID: {result['memory_id']}")
    
    embedding_processor.cleanup()

if __name__ == "__main__":
    asyncio.run(check_database())
