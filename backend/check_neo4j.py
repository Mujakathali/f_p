#!/usr/bin/env python3
"""
Check Neo4j database content and connections
"""
import asyncio
import sys
import os
from dotenv import load_dotenv
h
# Load environment variables
load_dotenv()

sys.path.append('.')
from db.neo4j_connector import Neo4jConnector

async def check_neo4j():
    print("🔍 Checking Neo4j database...")
    
    neo4j_db = Neo4jConnector()
    
    try:
        # Test connection
        await neo4j_db.initialize()
        print("✅ Neo4j connection successful")
        
        # Count nodes
        query = "MATCH (n) RETURN count(n) as total_nodes"
        result = await neo4j_db.execute_query(query)
        total_nodes = result[0]["total_nodes"] if result else 0
        print(f"📊 Total nodes in Neo4j: {total_nodes}")
        
        # Count memory nodes specifically
        query = "MATCH (m:Memory) RETURN count(m) as memory_count"
        result = await neo4j_db.execute_query(query)
        memory_count = result[0]["memory_count"] if result else 0
        print(f"📝 Memory nodes: {memory_count}")
        
        # Count person nodes
        query = "MATCH (p:Person) RETURN count(p) as person_count"
        result = await neo4j_db.execute_query(query)
        person_count = result[0]["person_count"] if result else 0
        print(f"👥 Person nodes: {person_count}")
        
        # Count location nodes
        query = "MATCH (l:Location) RETURN count(l) as location_count"
        result = await neo4j_db.execute_query(query)
        location_count = result[0]["location_count"] if result else 0
        print(f"📍 Location nodes: {location_count}")
        
        # Count relationships
        query = "MATCH ()-[r]->() RETURN count(r) as total_relationships"
        result = await neo4j_db.execute_query(query)
        total_relationships = result[0]["total_relationships"] if result else 0
        print(f"🔗 Total relationships: {total_relationships}")
        
        if total_nodes > 0:
            print("\n📋 Sample nodes:")
            # Get sample memory nodes
            query = "MATCH (m:Memory) RETURN m.memory_id, m.content, m.timestamp LIMIT 5"
            result = await neo4j_db.execute_query(query)
            for record in result:
                print(f"  Memory {record['m.memory_id']}: {record['m.content'][:50]}...")
            
            # Get sample person nodes
            query = "MATCH (p:Person) RETURN p.name LIMIT 5"
            result = await neo4j_db.execute_query(query)
            for record in result:
                print(f"  Person: {record['p.name']}")
        else:
            print("❌ No data found in Neo4j database!")
            print("💡 This means memories are not being stored in the graph database")
        
        await neo4j_db.close()
        
    except Exception as e:
        print(f"❌ Neo4j error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_neo4j())
