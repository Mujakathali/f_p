#!/usr/bin/env python3
"""
Test script to verify the complete setup works
"""
import asyncio
import os
import sys

async def test_setup():
    """Test all components"""
    print("🧪 Testing MemoryGraph AI Setup...")
    
    try:
        # Test database connections
        print("1️⃣ Testing database connections...")
        from db.postgresql_connector import PostgreSQLConnector
        from db.neo4j_connector import Neo4jConnector
        
        postgres_db = PostgreSQLConnector()
        neo4j_db = Neo4jConnector()
        
        await postgres_db.connect()
        await neo4j_db.connect()
        print("✅ Database connections successful")
        
        # Test NLP processor
        print("2️⃣ Testing NLP processor...")
        from models.nlp_processor import NLPProcessor
        nlp_processor = NLPProcessor()
        await nlp_processor.load_models()
        print("✅ NLP processor loaded")
        
        # Test BERT NER
        print("3️⃣ Testing BERT NER processor...")
        from models.bert_ner_processor import BERTNERProcessor
        bert_ner = BERTNERProcessor()
        await bert_ner.load_models()
        print("✅ BERT NER processor loaded")
        
        # Test embeddings
        print("4️⃣ Testing embedding processor...")
        from utils.embeddings import EmbeddingProcessor
        embedding_processor = EmbeddingProcessor()
        await embedding_processor.initialize()
        print(f"✅ Embedding processor loaded with model: {embedding_processor.current_model}")
        
        # Test CLIP processor
        print("5️⃣ Testing CLIP processor...")
        from utils.clip_processor import CLIPImageProcessor
        clip_processor = CLIPImageProcessor()
        await clip_processor.load_models()
        print("✅ CLIP processor loaded")
        
        # Test a simple text processing pipeline
        print("6️⃣ Testing complete text processing pipeline...")
        test_text = "I went to Coimbatore with my mom for graduation day at SKCT which made us cry in happy tears"
        
        # Process with NLP
        nlp_result = await nlp_processor.process_text(test_text)
        print(f"   • Sentiment: {nlp_result['sentiment']['label']} ({nlp_result['sentiment']['confidence']:.2f})")
        print(f"   • Keywords: {nlp_result['keywords'][:5]}")
        
        # Extract entities with BERT NER
        entities = await bert_ner.extract_entities(test_text)
        print(f"   • Entities found: {len(entities)}")
        for entity in entities[:3]:
            print(f"     - {entity['text']} ({entity['label']})")
        
        # Create embedding
        embedding = await embedding_processor.create_embedding(test_text)
        print(f"   • Embedding dimensions: {len(embedding)}")
        
        print("\n🎉 All tests passed! The system is ready to use.")
        print("\n📊 Final Model Stack:")
        print(f"   • Sentiment: DistilBERT → VADER fallback")
        print(f"   • Embeddings: {embedding_processor.current_model}")
        print(f"   • NER: {bert_ner.current_model}")
        print(f"   • Images: CLIP ViT-B/32 + BLIP captioning")
        
        # Cleanup
        await postgres_db.disconnect()
        await neo4j_db.disconnect()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_setup())
    sys.exit(0 if success else 1)
