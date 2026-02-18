#!/usr/bin/env python3
"""
Debug script to test the complete memory storage and retrieval pipeline
"""
import asyncio
import sys
import os
sys.path.append('.')

from db.postgresql_connector import PostgreSQLConnector
from utils.embeddings import EmbeddingProcessor

async def debug_storage_pipeline():
    """Test the complete storage and retrieval pipeline"""
    
    print("🔍 Debugging Memory Storage Pipeline")
    print("=" * 50)
    
    try:
        # Initialize components
        postgres = PostgreSQLConnector()
        embeddings = EmbeddingProcessor()
        
        await postgres.initialize()
        await embeddings.initialize()
        
        # 1. Check PostgreSQL data
        print("\n📊 PostgreSQL Status:")
        memories = await postgres.get_memories(limit=10)
        print(f"   Total memories: {len(memories)}")
        
        if memories:
            for i, memory in enumerate(memories[:3]):
                print(f"   Memory {i+1}: ID={memory['id']}, Text='{memory['raw_text'][:50]}...'")
                print(f"              Entities: {len(memory.get('entities', []))}")
                print(f"              Sentiments: {len(memory.get('sentiments', []))}")
        else:
            print("   ❌ No memories found in PostgreSQL!")
        
        # 2. Check ChromaDB data
        print("\n🧠 ChromaDB Status:")
        collection = embeddings.collection
        if collection:
            count = collection.count()
            print(f"   Total embeddings: {count}")
            
            if count > 0:
                # Get sample data
                sample = collection.peek(limit=3)
                print(f"   Sample embedding IDs: {sample['ids'][:3]}")
                
                # Test search functionality
                print("\n🔍 Testing Semantic Search:")
                test_query = "happy moments"
                results = await embeddings.search_similar_memories(test_query, limit=5, threshold=0.1)
                print(f"   Query: '{test_query}'")
                print(f"   Results found: {len(results)}")
                
                for i, result in enumerate(results[:3]):
                    print(f"   Result {i+1}: Memory ID={result['memory_id']}, Similarity={result['similarity']}")
            else:
                print("   ❌ No embeddings found in ChromaDB!")
        else:
            print("   ❌ ChromaDB collection not initialized!")
        
        # 3. Test keyword search
        print("\n📝 Testing Keyword Search:")
        if memories:
            keyword_results = await postgres.search_memories("happy", limit=5)
            print(f"   Keyword search for 'happy': {len(keyword_results)} results")
            
            advanced_results = await postgres.advanced_search_memories("happy moments", limit=5)
            print(f"   Advanced search for 'happy moments': {len(advanced_results)} results")
        
        # 4. Test embedding creation
        print("\n🔧 Testing Embedding Creation:")
        test_text = "This is a test memory about happiness"
        embedding = await embeddings.create_embedding(test_text)
        print(f"   Test text: '{test_text}'")
        print(f"   Embedding created: {len(embedding) if embedding else 0} dimensions")
        
        await postgres.close()
        
        print("\n" + "=" * 50)
        print("✅ Debug complete!")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_storage_pipeline())
