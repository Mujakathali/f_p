"""
Main FastAPI application for MemoryGraph AI Backend
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import os
import sys
from pathlib import Path
from datetime import datetime
from starlette.requests import Request

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

# Ensure project root is on sys.path for absolute imports when spawned by uvicorn
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

if load_dotenv is not None:
    load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)

from db.postgresql_connector import PostgreSQLConnector
from db.neo4j_connector import Neo4jConnector
from models.nlp_processor import NLPProcessor
from models.bert_ner_processor import BERTNERProcessor
from utils.audio_processor import AudioProcessor
from utils.image_processor import ImageProcessor
from utils.clip_processor import CLIPImageProcessor
from utils.embeddings import EmbeddingProcessor
from routes.memory_routes import memory_router
from routes.graph_routes import graph_router
from routes.image_serve_routes import image_router
from routes.summarization_routes import summarization_router
from auth.auth_routes import auth_router, initialize_auth

# Initialize FastAPI app
app = FastAPI(
    title="MemoryGraph AI Backend",
    description="AI-Powered Life Story Compiler Backend API",
    version="1.0.0"
)

# CORS middleware for React frontend
cors_origins_env = os.getenv("CORS_ORIGINS")
cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]
if cors_origins_env:
    cors_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    origin = request.headers.get("origin")
    print(f"➡️  {request.method} {request.url.path} origin={origin}")
    response = await call_next(request)
    print(f"⬅️  {request.method} {request.url.path} status={response.status_code}")
    return response

# Initialize database connections
postgres_db = PostgreSQLConnector()
neo4j_db = Neo4jConnector()

# Initialize processors
nlp_processor = NLPProcessor()
bert_ner_processor = BERTNERProcessor()
audio_processor = AudioProcessor()
image_processor = ImageProcessor()
clip_processor = CLIPImageProcessor()
embedding_processor = EmbeddingProcessor()

# Pydantic models
class TextMemoryRequest(BaseModel):
    text: str
    metadata: Optional[dict] = {}

class MemoryResponse(BaseModel):
    id: int
    raw_text: str
    processed_text: str
    type: str
    timestamp: datetime
    entities: List[dict] = []
    sentiment: Optional[dict] = None

@app.on_event("startup")
async def startup_event():
    """Initialize database connections and models on startup"""
    try:
        print("🚀 Starting MemoryGraph AI Backend...")
        
        # Initialize databases
        print("🔄 Connecting to databases...")
        await postgres_db.connect()
        await neo4j_db.connect()
        print("✅ Database connections established")
        
        # Initialize NLP models
        print("🔄 Loading NLP models...")
        await nlp_processor.load_models()
        print("✅ Sentiment analysis models loaded")
        
        # Initialize BERT NER
        print("🔄 Loading BERT NER models...")
        await bert_ner_processor.load_models()
        print("✅ Named Entity Recognition models loaded")
        
        # Initialize embedding processor
        print("🔄 Loading embedding models...")
        await embedding_processor.initialize()
        print("✅ Embedding models loaded")
        
        # Initialize CLIP processor
        print("🔄 Loading CLIP image processing models...")
        await clip_processor.load_models()
        print("✅ CLIP image processing models loaded")
        
        # Initialize authentication system
        print("🔄 Initializing authentication system...")
        user_manager = initialize_auth(postgres_db.connection_pool)
        await user_manager.create_users_table()
        print("✅ Authentication system initialized")
        
        print("🎉 Backend services initialized successfully!")
        print(f"📊 Model Stack Summary:")
        print(f"   • Sentiment: DistilBERT → VADER fallback")
        print(f"   • Embeddings: {embedding_processor.current_model}")
        print(f"   • NER: {bert_ner_processor.current_model}")
        print(f"   • Auth: JWT with bcrypt password hashing")
        
    except Exception as e:
        print(f"❌ Failed to initialize backend services: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown"""
    await postgres_db.disconnect()
    await neo4j_db.disconnect()
    print("🔌 Database connections closed")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "MemoryGraph AI Backend is running",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/api/v1/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "services": {
            "postgresql": await postgres_db.health_check(),
            "neo4j": await neo4j_db.health_check(),
            "nlp_models": nlp_processor.is_loaded(),
            "bert_ner": bert_ner_processor.is_loaded if hasattr(bert_ner_processor, 'is_loaded') else False,
            "embeddings": embedding_processor.current_model if hasattr(embedding_processor, 'current_model') else "unknown"
        }
    }

# Include routers with proper prefixes
app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(memory_router, prefix="/api/v1", tags=["memories"])
app.include_router(graph_router, prefix="/api/v1", tags=["graph"])
app.include_router(image_router, prefix="/api/v1", tags=["images"])
app.include_router(summarization_router, prefix="/api/v1", tags=["summarization"])

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"
    )
