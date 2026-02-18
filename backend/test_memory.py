"""
Test script to isolate the memory creation issue
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.postgresql_connector import PostgreSQLConnector
from db.neo4j_connector import Neo4jConnector
from models.nlp_processor import NLPProcessor
from utils.embeddings import EmbeddingProcessor

async def test_memory_creation():
    """Test the complete memory creation pipeline"""
    
    # Test text
    test_text = "Hi today I get award from my hod it was my happiest moment"
    
    print("🔍 Starting memory creation test...")
    
    try:
        # Initialize components
        print("1. Initializing components...")
        postgres_db = PostgreSQLConnector()
        neo4j_db = Neo4jConnector()
        nlp_processor = NLPProcessor()
        embedding_processor = EmbeddingProcessor()
        
        # Connect to databases
        print("2. Connecting to databases...")
        await postgres_db.connect()
        print("   ✅ PostgreSQL connected")
        
        await neo4j_db.connect()
        print("   ✅ Neo4j connected")
        
        # Load NLP models
        print("3. Loading NLP models...")
        await nlp_processor.load_models()
        print("   ✅ NLP models loaded")
        
        # Process text
        print("4. Processing text with NLP...")
        nlp_result = await nlp_processor.process_text(test_text)
        print(f"   ✅ NLP result: {nlp_result}")
        
        # Store in PostgreSQL
        print("5. Storing in PostgreSQL...")
        memory_id = await postgres_db.insert_memory(
            raw_text=test_text,
            processed_text=nlp_result["cleaned_text"],
            memory_type="text",
            metadata={}
        )
        print(f"   ✅ Memory stored with ID: {memory_id}")
        
        # Store entities
        if nlp_result["entities"]:
            print("6. Storing entities...")
            await postgres_db.insert_entities(memory_id, nlp_result["entities"])
            print(f"   ✅ Stored {len(nlp_result['entities'])} entities")
        
        # Store sentiment
        if nlp_result["sentiment"]:
            print("7. Storing sentiment...")
            await postgres_db.insert_sentiment(
                memory_id,
                nlp_result["sentiment"]["score"],
                nlp_result["sentiment"]["label"],
                nlp_result["sentiment"]["confidence"]
            )
            print(f"   ✅ Stored sentiment: {nlp_result['sentiment']}")
        
        # Create vector embedding
        print("8. Creating vector embedding...")
        embedding_id = await embedding_processor.store_memory_embedding(
            memory_id, nlp_result["cleaned_text"], {}
        )
        print(f"   ✅ Embedding stored with ID: {embedding_id}")
        
        # Store in Neo4j
        print("9. Storing in Neo4j...")
        await neo4j_db.create_memory_node(
            memory_id,
            nlp_result["cleaned_text"],
            "text",
            "2025-01-15T12:00:00Z",
            nlp_result["sentiment"]["emotion"] if nlp_result["sentiment"] else None
        )
        print("   ✅ Memory node created in Neo4j")
        
        # Create entity relationships
        people = nlp_processor.extract_people_names(nlp_result["entities"])
        for person in people:
            await neo4j_db.create_person_node(person, memory_id)
            print(f"   ✅ Person node created: {person}")
        
        locations = nlp_processor.extract_locations(nlp_result["entities"])
        for location in locations:
            await neo4j_db.create_location_node(location, memory_id)
            print(f"   ✅ Location node created: {location}")
        
        # Create emotion relationship
        if nlp_result["sentiment"]:
            await neo4j_db.create_emotion_relationship(
                memory_id,
                nlp_result["sentiment"]["emotion"],
                nlp_result["sentiment"]["score"]
            )
            print(f"   ✅ Emotion relationship created: {nlp_result['sentiment']['emotion']}")
        
        print("\n🎉 Memory creation test completed successfully!")
        print(f"Memory ID: {memory_id}")
        print(f"Embedding ID: {embedding_id}")
        print(f"Entities: {len(nlp_result['entities'])}")
        print(f"Sentiment: {nlp_result['sentiment']['emotion'] if nlp_result['sentiment'] else 'None'}")
        
    except Exception as e:
        print(f"\n❌ Error during memory creation test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up connections
        try:
            await postgres_db.disconnect()
            await neo4j_db.disconnect()
            print("\n🔌 Database connections closed")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_memory_creation())
