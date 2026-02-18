"""
Test script to verify search fixes
"""
import asyncio
import sys
sys.path.insert(0, '.')

from db.postgresql_connector import PostgreSQLConnector

async def test_search():
    print("🔍 Testing PostgreSQL search fix...")
    
    postgres_db = PostgreSQLConnector()
    await postgres_db.connect()
    
    try:
        # Test advanced search
        results = await postgres_db.advanced_search_memories("muja formal dress", limit=10)
        print(f"✅ Search completed! Found {len(results)} results")
        
        for result in results:
            print(f"\n📝 Memory ID: {result['id']}")
            print(f"   Type: {result['type']}")
            print(f"   Text: {result['raw_text'][:50]}...")
            print(f"   Entities: {len(result.get('entities', []))} entities")
            print(f"   Sentiments: {len(result.get('sentiments', []))} sentiments")
            
    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await postgres_db.disconnect()

if __name__ == "__main__":
    asyncio.run(test_search())
