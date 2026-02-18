"""
Test script to verify database connections
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_postgresql():
    """Test PostgreSQL connection"""
    try:
        import asyncpg
        
        conn = await asyncpg.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            database=os.getenv('POSTGRES_DB', 'memorygraph_ai'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'password')
        )
        
        # Test query
        result = await conn.fetchval('SELECT version()')
        print(f"✅ PostgreSQL connected successfully!")
        print(f"   Version: {result[:50]}...")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

async def test_neo4j():
    """Test Neo4j connection"""
    try:
        from neo4j import AsyncGraphDatabase
        
        driver = AsyncGraphDatabase.driver(
            os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            auth=(
                os.getenv('NEO4J_USERNAME', 'neo4j'),
                os.getenv('NEO4J_PASSWORD', 'password')
            )
        )
        
        async with driver.session() as session:
            result = await session.run("RETURN 'Hello Neo4j!' as message")
            record = await result.single()
            print(f"✅ Neo4j connected successfully!")
            print(f"   Message: {record['message']}")
        
        await driver.close()
        return True
        
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        return False

async def main():
    """Run all connection tests"""
    print("🔍 Testing database connections...\n")
    
    # Test PostgreSQL
    print("📊 Testing PostgreSQL...")
    pg_success = await test_postgresql()
    print()
    
    # Test Neo4j
    print("🕸️  Testing Neo4j...")
    neo4j_success = await test_neo4j()
    print()
    
    # Summary
    if pg_success and neo4j_success:
        print("🎉 All database connections successful!")
        print("   You can now run the FastAPI server with: python app.py")
    else:
        print("⚠️  Some database connections failed.")
        print("   Please check your database installations and .env configuration.")

if __name__ == "__main__":
    asyncio.run(main())
