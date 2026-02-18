#!/usr/bin/env python3
"""
Simple test to verify basic setup without downloading models
"""
import asyncio
import sys

async def test_basic_setup():
    """Test basic components without heavy model loading"""
    print("🧪 Testing Basic MemoryGraph AI Setup...")
    
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
        
        # Test embedding processor initialization (without model loading)
        print("2️⃣ Testing embedding processor structure...")
        from utils.embeddings import EmbeddingProcessor
        embedding_processor = EmbeddingProcessor()
        print(f"✅ Embedding processor created with models: {embedding_processor.primary_model} → {embedding_processor.fallback_model}")
        
        # Test CLIP processor structure
        print("3️⃣ Testing CLIP processor structure...")
        from utils.clip_processor import CLIPImageProcessor
        clip_processor = CLIPImageProcessor()
        print(f"✅ CLIP processor created with storage dir: {clip_processor.image_storage_dir}")
        
        # Test NLP processors structure
        print("4️⃣ Testing NLP processors structure...")
        from models.nlp_processor import NLPProcessor
        from models.bert_ner_processor import BERTNERProcessor
        
        nlp_processor = NLPProcessor()
        bert_ner = BERTNERProcessor()
        print(f"✅ NLP processors created")
        
        # Test API routes import
        print("5️⃣ Testing API routes...")
        from routes.memory_routes import memory_router
        print("✅ Memory routes imported successfully")
        
        # Test app structure
        print("6️⃣ Testing app structure...")
        from app import app
        print("✅ FastAPI app imported successfully")
        
        print("\n🎉 Basic setup test passed!")
        print("\n📊 Configuration Summary:")
        print(f"   • Text Embeddings: {embedding_processor.primary_model} (768d) → {embedding_processor.fallback_model} (384d)")
        print(f"   • Image Embeddings: CLIP ViT-B/32 (512d)")
        print(f"   • Sentiment: DistilBERT → VADER fallback")
        print(f"   • NER: {bert_ner.primary_model_name} → {bert_ner.fallback_model_name}")
        print(f"   • Image Storage: {clip_processor.image_storage_dir}")
        
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
    success = asyncio.run(test_basic_setup())
    sys.exit(0 if success else 1)
