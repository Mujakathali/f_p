"""
Memory-related API routes
"""
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import tempfile
import os
import json
import asyncio

from auth.dependencies import get_current_user
from db.postgresql_connector import PostgreSQLConnector
from db.neo4j_connector import Neo4jConnector
from models.nlp_processor import NLPProcessor
from models.bert_ner_processor import BERTNERProcessor
from utils.embeddings import EmbeddingProcessor
from utils.audio_processor import AudioProcessor
from utils.clip_processor import CLIPImageProcessor
from utils.groq_client import groq_client
import traceback

# Router instance
memory_router = APIRouter()

# Global instances (shared across requests)
postgres_db = PostgreSQLConnector()
neo4j_db = Neo4jConnector()
nlp_processor = NLPProcessor()
bert_ner_processor = BERTNERProcessor()
audio_processor = AudioProcessor()
clip_processor = CLIPImageProcessor()
embedding_processor = EmbeddingProcessor()

# Global initialization flag
_initialized = False

# Initialize all processors once
async def initialize_all_processors():
    """Initialize all processors once"""
    global _initialized
    if not _initialized:
        print("🔄 Initializing processors in memory routes...")
        await postgres_db.connect()
        await neo4j_db.connect()
        await nlp_processor.load_models()
        await bert_ner_processor.load_models()
        await clip_processor.load_models()
        await embedding_processor.initialize()
        _initialized = True
        print("✅ All processors initialized in memory routes")

# Dependency injection - return already initialized instances
async def get_postgres_db():
    if not _initialized:
        await initialize_all_processors()
    return postgres_db

async def get_neo4j_db():
    if not _initialized:
        await initialize_all_processors()
    return neo4j_db

async def get_nlp_processor():
    if not _initialized:
        await initialize_all_processors()
    return nlp_processor

async def get_bert_ner_processor():
    if not _initialized:
        await initialize_all_processors()
    return bert_ner_processor

async def get_clip_processor():
    if not _initialized:
        await initialize_all_processors()
    return clip_processor

async def get_embedding_processor():
    if not _initialized:
        await initialize_all_processors()
    return embedding_processor

async def get_audio_processor():
    return audio_processor

async def get_image_processor():
    return image_processor

# Pydantic models
class TextMemoryRequest(BaseModel):
    text: str
    metadata: Optional[Dict] = {}

class MemoryResponse(BaseModel):
    id: int
    raw_text: str
    processed_text: str
    type: str
    timestamp: datetime
    entities: List[Dict] = []
    sentiment: Optional[Dict] = None
    embedding_id: Optional[str] = None

class AskRequest(BaseModel):
    question: str
    limit: int = Field(default=8, ge=1, le=30)
    search_type: str = Field(default="hybrid")
    memory_type: Optional[str] = Field(default=None)
    memory_types: Optional[List[str]] = Field(default=None)

class AskResponse(BaseModel):
    question: str
    answer: str
    memory_ids: List[int] = []

@memory_router.post("/add_memory", response_model=MemoryResponse)
async def add_text_memory(
    request: TextMemoryRequest,
    current_user: Dict = Depends(get_current_user),
    postgres_db: PostgreSQLConnector = Depends(get_postgres_db),
    neo4j_db: Neo4jConnector = Depends(get_neo4j_db),
    nlp_processor: NLPProcessor = Depends(get_nlp_processor),
    bert_ner_processor: BERTNERProcessor = Depends(get_bert_ner_processor),
    embedding_processor: EmbeddingProcessor = Depends(get_embedding_processor)
):
    """Add a text memory (requires authentication)"""
    try:
        user_id = current_user["user_id"]
        print(f"🔍 Processing memory for user {user_id}: {request.text}")  # Debug log
        
        # Process text with NLP (sentiment, keywords, dates)
        nlp_result = await nlp_processor.process_text(request.text)
        
        # Extract entities using BERT NER
        bert_entities = await bert_ner_processor.extract_entities(request.text)
        
        # Combine entities (use BERT NER instead of spaCy)
        nlp_result["entities"] = bert_entities
        
        print(f"📊 NLP Results: sentiment={nlp_result['sentiment']['label']}, entities={len(bert_entities)}, keywords={len(nlp_result['keywords'])}")
        
        # Store plaintext in PostgreSQL with user_id (pre-AES behavior)
        memory_id = await postgres_db.insert_memory(
            raw_text=request.text,
            processed_text=nlp_result["cleaned_text"],
            memory_type="text",
            metadata=request.metadata,
            user_id=user_id
        )
        
        # Store entities
        if nlp_result["entities"]:
            await postgres_db.insert_entities(memory_id, nlp_result["entities"])
        
        # Store sentiment
        if nlp_result["sentiment"]:
            await postgres_db.insert_sentiment(
                memory_id,
                nlp_result["sentiment"]["score"],
                nlp_result["sentiment"]["label"],
                nlp_result["sentiment"]["confidence"]
            )
        
        # Create vector embedding
        embedding_id = await embedding_processor.store_memory_embedding(
            memory_id, nlp_result["cleaned_text"], request.metadata
        )
        
        # Update embedding ID in PostgreSQL
        if embedding_id:
            await postgres_db.connection_pool.execute(
                "UPDATE memories SET embedding_id = $1 WHERE id = $2",
                embedding_id, memory_id
            )
        
        # Store in Neo4j graph
        try:
            print(f"🔗 Creating Neo4j memory node for ID: {memory_id}")
            await neo4j_db.create_memory_node(
                memory_id,
                nlp_result["cleaned_text"],
                "text",
                datetime.now().isoformat(),
                nlp_result["sentiment"]["emotion"] if nlp_result["sentiment"] else None,
                user_id
            )
            print(f"✅ Neo4j memory node created")
            
            # Create entity relationships
            people = nlp_processor.extract_people_names(nlp_result["entities"])
            locations = nlp_processor.extract_locations(nlp_result["entities"])
            organizations = nlp_processor.extract_organizations(nlp_result["entities"])
            
            print(f"🔍 ENTITY EXTRACTION RESULTS:")
            print(f"   👥 People: {people if people else 'None found'}")
            print(f"   📍 Locations: {locations if locations else 'None found'}")
            print(f"   🏢 Organizations: {organizations if organizations else 'None found'}")
            print(f"   🎭 Sentiment: {nlp_result['sentiment']['emotion']} ({nlp_result['sentiment']['score']:.2f})")
            print(f"   🔑 Keywords: {nlp_result.get('keywords', [])[:5]}")
            
            for person in people:
                await neo4j_db.create_person_node(person, memory_id)
                print(f"   ✅ Created person node: {person}")
            
            for location in locations:
                await neo4j_db.create_location_node(location, memory_id)
                print(f"   ✅ Created location node: {location}")
            
            for org in organizations:
                await neo4j_db.create_organization_node(org, memory_id)
                print(f"   ✅ Created organization node: {org}")
            
            # Create emotion relationship
            if nlp_result["sentiment"]:
                await neo4j_db.create_emotion_relationship(
                    memory_id,
                    nlp_result["sentiment"]["emotion"],
                    nlp_result["sentiment"]["score"]
                )
                print(f"   💝 Created emotion relationship: {nlp_result['sentiment']['emotion']}")
        except Exception as neo4j_error:
            print(f"⚠️ Neo4j storage error: {neo4j_error}")
            # Continue without failing the entire request
        
        # Convert numpy types to Python native types for JSON serialization
        def convert_numpy_types(obj):
            if hasattr(obj, 'item'):  # numpy scalar
                return obj.item()
            elif isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(v) for v in obj]
            return obj
        
        # Return response
        print(f"✅ Memory stored successfully with ID: {memory_id}")  # Debug log
        return MemoryResponse(
            id=memory_id,
            raw_text=request.text,
            processed_text=nlp_result["cleaned_text"],
            type="text",
            timestamp=datetime.now(),
            entities=convert_numpy_types(nlp_result["entities"]),
            sentiment=convert_numpy_types(nlp_result["sentiment"]),
            embedding_id=embedding_id
        )
        
    except Exception as e:
        print(f"❌ Error adding memory: {e}")
        import traceback
        traceback.print_exc()  # Print full stack trace
        raise HTTPException(status_code=500, detail=f"Failed to add memory: {str(e)}")

@memory_router.post("/add_voice_memory")
async def add_voice_memory(
    audio_file: UploadFile = File(...),
    metadata: str = Form("{}"),
    current_user: Dict = Depends(get_current_user),
    postgres_db: PostgreSQLConnector = Depends(get_postgres_db),
    neo4j_db: Neo4jConnector = Depends(get_neo4j_db),
    nlp_processor: NLPProcessor = Depends(get_nlp_processor),
    bert_ner_processor: BERTNERProcessor = Depends(get_bert_ner_processor),
    audio_processor: AudioProcessor = Depends(get_audio_processor),
    embedding_processor: EmbeddingProcessor = Depends(get_embedding_processor)
):
    """Add a voice memory by transcribing audio (requires authentication)"""
    try:
        import json
        metadata_dict = json.loads(metadata) if metadata else {}
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Validate audio file
            validation = await audio_processor.validate_audio_file(temp_file_path)
            if not validation["valid"]:
                raise HTTPException(status_code=400, detail=validation["error"])
            
            # Transcribe audio
            transcription = await audio_processor.transcribe_audio(temp_file_path)
            
            if not transcription["text"]:
                raise HTTPException(status_code=400, detail="No speech detected in audio")
            
            # Process transcribed text with NLP (sentiment, keywords, dates)
            nlp_result = await nlp_processor.process_text(transcription["text"])
            
            # Extract entities using BERT NER
            bert_entities = await bert_ner_processor.extract_entities(transcription["text"])
            nlp_result["entities"] = bert_entities
            
            print(f"📊 Audio NLP Results: sentiment={nlp_result['sentiment']['label']}, entities={len(bert_entities)}")
            
            # Add audio metadata
            audio_metadata = {
                **metadata_dict,
                "audio_duration": transcription["duration"],
                "transcription_confidence": transcription["confidence"],
                "detected_language": transcription["language"]
            }
            
            # Store in PostgreSQL with user_id
            user_id = current_user["user_id"]
            memory_id = await postgres_db.insert_memory(
                raw_text=transcription["text"],
                processed_text=nlp_result["cleaned_text"],
                memory_type="voice",
                metadata=audio_metadata,
                user_id=user_id
            )
            
            # Store entities and sentiment
            if nlp_result["entities"]:
                await postgres_db.insert_entities(memory_id, nlp_result["entities"])
            
            if nlp_result["sentiment"]:
                await postgres_db.insert_sentiment(
                    memory_id,
                    nlp_result["sentiment"]["score"],
                    nlp_result["sentiment"]["label"],
                    nlp_result["sentiment"]["confidence"]
                )
            
            # Create vector embedding
            embedding_id = await embedding_processor.store_memory_embedding(
                memory_id, nlp_result["cleaned_text"], audio_metadata
            )
            
            # Store in Neo4j
            await neo4j_db.create_memory_node(
                memory_id,
                nlp_result["cleaned_text"],
                "voice",
                datetime.now().isoformat(),
                nlp_result["sentiment"]["emotion"] if nlp_result["sentiment"] else None,
                user_id
            )
            
            # Create entity relationships
            people = nlp_processor.extract_people_names(nlp_result["entities"])
            for person in people:
                await neo4j_db.create_person_node(person, memory_id)
            
            locations = nlp_processor.extract_locations(nlp_result["entities"])
            for location in locations:
                await neo4j_db.create_location_node(location, memory_id)
            
            return {
                "id": memory_id,
                "raw_text": transcription["text"],
                "processed_text": nlp_result["cleaned_text"],
                "type": "voice",
                "timestamp": datetime.now(),
                "transcription": transcription,
                "entities": nlp_result["entities"],
                "sentiment": nlp_result["sentiment"],
                "embedding_id": embedding_id
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process voice memory: {str(e)}")

@memory_router.post("/add_image_memory")
async def add_image_memory(
    image_file: UploadFile = File(...),
    caption: str = Form(""),
    metadata: str = Form("{}"),
    current_user: Dict = Depends(get_current_user),
    postgres_db: PostgreSQLConnector = Depends(get_postgres_db),
    neo4j_db: Neo4jConnector = Depends(get_neo4j_db),
    nlp_processor: NLPProcessor = Depends(get_nlp_processor),
    bert_ner_processor: BERTNERProcessor = Depends(get_bert_ner_processor),
    clip_processor: CLIPImageProcessor = Depends(get_clip_processor),
    embedding_processor: EmbeddingProcessor = Depends(get_embedding_processor)
):
    """Add an image memory using CLIP encoding and optional caption (requires authentication)"""
    try:
        import json
        metadata_dict = json.loads(metadata) if metadata else {}
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            content = await image_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Validate image file using CLIP processor
            validation = await clip_processor.validate_image_file(temp_file_path)
            if not validation["valid"]:
                raise HTTPException(status_code=400, detail=validation["error"])
            
            print(f"🖼️ Processing image: {image_file.filename}")
            
            # Store image locally
            storage_info = await clip_processor.store_image_locally(temp_file_path, metadata_dict)
            if "error" in storage_info:
                raise HTTPException(status_code=500, detail=f"Failed to store image: {storage_info['error']}")
            
            # Generate caption if not provided
            if not caption.strip():
                caption_result = await clip_processor.generate_caption(temp_file_path)
                caption = caption_result.get("caption", "Image uploaded")
                print(f"🤖 Generated caption: {caption}")
            else:
                print(f"📝 User provided caption: {caption}")
            
            # Process caption with NLP (sentiment, keywords, entities)
            nlp_result = await nlp_processor.process_text(caption)
            
            # Extract entities using BERT NER from caption
            bert_entities = await bert_ner_processor.extract_entities(caption)
            nlp_result["entities"] = bert_entities
            
            print(f"📊 Image Caption NLP Results: sentiment={nlp_result['sentiment']['label']}, entities={len(bert_entities)}")
            
            # Encode image using CLIP
            image_embedding = await clip_processor.encode_image(temp_file_path)
            if not image_embedding:
                raise HTTPException(status_code=500, detail="Failed to encode image")
            
            # Combine metadata
            combined_metadata = {
                **metadata_dict,
                "image_path": storage_info["stored_path"],
                "filename": storage_info["filename"],
                "image_width": storage_info["width"],
                "image_height": storage_info["height"],
                "image_format": storage_info["format"],
                "file_size": storage_info["file_size"],
                "caption_source": "user" if caption != nlp_result.get("cleaned_text", "") else "generated"
            }
            
            # Generate image embedding ID first (before storing in PostgreSQL)
            image_embedding_id = f"image_{int(datetime.now().timestamp())}_{storage_info['filename']}"
            
            # Store in PostgreSQL with user_id (store caption as text, image path in metadata, and image embedding ID)
            user_id = current_user["user_id"]
            memory_id = await postgres_db.insert_memory(
                raw_text=caption,
                processed_text=nlp_result["cleaned_text"],
                memory_type="image",
                metadata=combined_metadata,
                embedding_id=image_embedding_id,  # Store the image embedding ID
                user_id=user_id
            )
            
            # Store entities and sentiment
            if nlp_result["entities"]:
                await postgres_db.insert_entities(memory_id, nlp_result["entities"])
            
            if nlp_result["sentiment"]:
                await postgres_db.insert_sentiment(
                    memory_id,
                    nlp_result["sentiment"]["score"],
                    nlp_result["sentiment"]["label"],
                    nlp_result["sentiment"]["confidence"]
                )
            
            # Create text embedding for caption
            text_embedding_id = await embedding_processor.store_memory_embedding(
                memory_id, nlp_result["cleaned_text"], combined_metadata
            )
            
            # Store CLIP image embedding in separate ChromaDB collection (use the same ID as PostgreSQL)
            try:
                if hasattr(embedding_processor, 'image_collection') and embedding_processor.image_collection:
                    embedding_processor.image_collection.add(
                        embeddings=[image_embedding],
                        documents=[f"Image: {caption}"],
                        metadatas=[{
                            "memory_id": memory_id,
                            "type": "image",
                            "image_path": storage_info["stored_path"],
                            "filename": storage_info["filename"],
                            "caption": caption,
                            **combined_metadata
                        }],
                        ids=[image_embedding_id]
                    )
                    print(f"💾 CLIP image embedding stored: {image_embedding_id}")
                else:
                    print("⚠️ Image collection not initialized")
            except Exception as e:
                print(f"⚠️ Failed to store image embedding: {e}")
            
            # Store in Neo4j
            await neo4j_db.create_memory_node(
                memory_id,
                nlp_result["cleaned_text"],
                "image",
                datetime.now().isoformat(),
                nlp_result["sentiment"]["emotion"] if nlp_result["sentiment"] else None,
                user_id
            )
            
            # Create entity relationships (with error handling for image endpoint)
            try:
                people = nlp_processor.extract_people_names(nlp_result["entities"]) if hasattr(nlp_processor, 'extract_people_names') else []
                for person in people:
                    await neo4j_db.create_person_node(person, memory_id)
                
                locations = nlp_processor.extract_locations(nlp_result["entities"]) if hasattr(nlp_processor, 'extract_locations') else []
                for location in locations:
                    await neo4j_db.create_location_node(location, memory_id)
                    
                print(f"✅ Image memory processed successfully: {memory_id}")
            except Exception as entity_error:
                print(f"⚠️ Entity relationship creation failed: {entity_error}")
                # Continue without failing the whole request
            
            # Convert numpy types to Python native types for JSON serialization
            def convert_numpy_types(obj):
                if hasattr(obj, 'item'):  # numpy scalar
                    return obj.item()
                elif isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(v) for v in obj]
                return obj
            
            response_data = {
                "id": memory_id,
                "raw_text": caption,
                "processed_text": nlp_result["cleaned_text"],
                "type": "image",
                "timestamp": datetime.now().isoformat(),
                "image_info": convert_numpy_types(storage_info),
                "entities": convert_numpy_types(nlp_result["entities"]),
                "sentiment": convert_numpy_types(nlp_result["sentiment"]),
                "text_embedding_id": text_embedding_id,
                "image_embedding_id": image_embedding_id,
                "status": "success"
            }
            
            return response_data
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image memory: {str(e)}")

@memory_router.get("/list_memories")
async def list_memories(
    limit: int = 100,
    offset: int = 0,
    memory_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    postgres_db: PostgreSQLConnector = Depends(get_postgres_db)
):
    """List stored memories with pagination (filtered by current user)"""
    try:
        user_id = current_user["user_id"]
        memories = await postgres_db.get_memories(limit, offset, memory_type, user_id)
        
        decrypted_memories = memories
        
        # Add image URLs to image memories
        for memory in decrypted_memories:
            if memory.get("type") == "image":
                metadata = memory.get("metadata")
                # Handle metadata as dict or JSON string
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                elif not isinstance(metadata, dict):
                    metadata = {}
                
                filename = metadata.get("filename") if metadata else None
                if filename:
                    memory["image_url"] = f"/api/v1/images/{filename}"
        
        return {"memories": decrypted_memories, "total": len(decrypted_memories), "limit": limit, "offset": offset, "count": len(memories)}
    except Exception as e:
        print(f"❌ list_memories error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memories: {str(e)}")

@memory_router.get("/timeline_summary")
async def timeline_summary(
    timeframe: str = "weekly",  # "weekly" or "monthly"
    limit: int = 500,
    current_user: Dict = Depends(get_current_user),
    postgres_db: PostgreSQLConnector = Depends(get_postgres_db)
):
    """Return a simple weekly/monthly grouped timeline summary for the current user."""
    if timeframe not in ("weekly", "monthly"):
        raise HTTPException(status_code=400, detail="Invalid timeframe. Use 'weekly' or 'monthly'.")
    try:
        user_id = current_user["user_id"]
        async with postgres_db.connection_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT m.id,
                       m.raw_text, m.processed_text, m.type, m.timestamp, m.metadata, m.user_id,
                       COALESCE(
                           (SELECT json_agg(jsonb_build_object(
                               'score', s2.sentiment_score,
                               'label', s2.sentiment_label,
                               'confidence', s2.confidence
                           ))
                           FROM sentiments s2
                           WHERE s2.memory_id = m.id), '[]'::json
                       ) as sentiments
                FROM memories m
                WHERE m.user_id = $1 AND m.deleted_at IS NULL
                ORDER BY m.timestamp DESC
                LIMIT $2
                """,
                user_id, limit
            )

        def parse_ts(ts):
            if isinstance(ts, str):
                try:
                    return datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except Exception:
                    return datetime.utcnow()
            return ts

        def sentiment_score(sentiments):
            if not sentiments:
                return 0.0
            scores = []
            for s in sentiments:
                try:
                    scores.append(float(s.get("score", 0.0)))
                except Exception:
                    continue
            return scores[0] if scores else 0.0

        groups = {}
        for row in rows:
            mem = dict(row)

            ts = parse_ts(mem.get("timestamp"))
            if timeframe == "weekly":
                iso = ts.isocalendar()
                key = f"{iso.year}-W{iso.week:02d}"
                start = ts - timedelta(days=ts.weekday())
                end = start + timedelta(days=6)
            else:
                key = f"{ts.year}-{ts.month:02d}"
                start = datetime(ts.year, ts.month, 1)
                if ts.month == 12:
                    end = datetime(ts.year + 1, 1, 1) - timedelta(days=1)
                else:
                    end = datetime(ts.year, ts.month + 1, 1) - timedelta(days=1)

            mem_entry = {
                "id": mem.get("id"),
                "raw_text": mem.get("raw_text"),
                "processed_text": mem.get("processed_text"),
                "type": mem.get("type"),
                "timestamp": ts.isoformat(),
                "metadata": mem.get("metadata"),
                "sentiments": mem.get("sentiments"),
                "sentiment_score": sentiment_score(mem.get("sentiments")),
            }

            # Attach image_url for image memories
            if mem_entry.get("type") == "image":
                md = mem_entry.get("metadata")
                if isinstance(md, str):
                    try:
                        md = json.loads(md)
                    except Exception:
                        md = {}
                if isinstance(md, dict):
                    filename = md.get("filename")
                    if filename:
                        mem_entry["image_url"] = f"/api/v1/images/{filename}"

            if key not in groups:
                groups[key] = {
                    "period": key,
                    "start": start.date().isoformat(),
                    "end": end.date().isoformat(),
                    "memories": [],
                }
            groups[key]["memories"].append(mem_entry)

        # Build highlights per group
        summary_groups = []
        for key, data in groups.items():
            mems = data["memories"]
            if not mems:
                continue
            # top positive/negative by sentiment_score
            top_positive = max(mems, key=lambda m: m.get("sentiment_score", 0.0))
            top_negative = min(mems, key=lambda m: m.get("sentiment_score", 0.0))
            summary_groups.append({
                "period": data["period"],
                "start": data["start"],
                "end": data["end"],
                "count": len(mems),
                "top_positive": top_positive,
                "top_negative": top_negative,
                "memories": mems,
            })

        # Sort groups descending by start date
        summary_groups.sort(key=lambda g: g["start"], reverse=True)

        return {
            "timeframe": timeframe,
            "total_memories": len(rows),
            "groups": summary_groups
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build timeline summary: {str(e)}")

@memory_router.get("/memory/{memory_id}")
async def get_memory(
    memory_id: int,
    current_user: dict = Depends(get_current_user),
    postgres_db: PostgreSQLConnector = Depends(get_postgres_db)
):
    """Get a specific memory by ID (user can only access their own memories)"""
    try:
        memory = await postgres_db.get_memory_by_id(memory_id)
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Verify the memory belongs to the current user
        if memory.get("user_id") != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied: You can only access your own memories")
        
        # Add image URL if it's an image memory
        if memory.get("type") == "image":
            metadata = memory.get("metadata")
            # Handle metadata as dict or JSON string
            if isinstance(metadata, str):
                import json
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            elif not isinstance(metadata, dict):
                metadata = {}
            
            filename = metadata.get("filename") if metadata else None
            if filename:
                memory["image_url"] = f"/api/v1/images/{filename}"
        
        return memory
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memory: {str(e)}")

@memory_router.get("/search_memories")
async def search_memories(
    query: str,
    limit: int = 50,
    search_type: str = "hybrid",  # "hybrid", "keyword", "semantic", "image"
    memory_type: Optional[str] = None,
    memory_types: Optional[str] = None,
    current_user: Dict = Depends(get_current_user),
    postgres_db: PostgreSQLConnector = Depends(get_postgres_db),
    embedding_processor: EmbeddingProcessor = Depends(get_embedding_processor),
    clip_processor: CLIPImageProcessor = Depends(get_clip_processor)
):
    """Advanced hybrid search combining keyword matching and semantic similarity (requires authentication)"""
    try:
        user_id = current_user["user_id"]
        print(f"🔍 Hybrid search for user {user_id}: '{query}' (type: {search_type}, limit: {limit})")
        
        # Initialize results containers
        keyword_results = []
        semantic_results = []
        image_results = []
        
        # 1. Keyword-based search in PostgreSQL (filtered by user_id)
        if search_type in ["hybrid", "keyword"]:
            try:
                keyword_results = await postgres_db.advanced_search_memories(query, limit, user_id=user_id)
                print(f"📝 Keyword search found {len(keyword_results)} results for user {user_id}")
            except Exception as keyword_error:
                print(f"⚠️ Keyword search error: {keyword_error}")
                keyword_results = []
        
        # 2. Semantic search in ChromaDB
        if search_type in ["hybrid", "semantic"]:
            try:
                semantic_matches = await embedding_processor.search_similar_memories(
                    query, limit * 2, threshold=0.45
                )
                print(f"🧠 Semantic search for: '{query}' (threshold: 0.45, limit: {limit * 2})")
                
                # Get full memory details for semantic matches (filter by user_id)
                for match in semantic_matches:
                    try:
                        memory = await postgres_db.get_memory_by_id(match["memory_id"])
                        # Only include memories belonging to the current user
                        if memory and memory.get("user_id") == user_id and match["similarity"] >= 0.5:  # Minimum score filtering - strict
                            memory["similarity_score"] = match["similarity"]
                            memory["search_type"] = "semantic"
                            semantic_results.append(memory)
                    except Exception as e:
                        print(f"⚠️ Error fetching memory {match['memory_id']}: {e}")
                        continue
                        
            except Exception as semantic_error:
                print(f"⚠️ Semantic search error: {semantic_error}")
                semantic_results = []
        
        # 3. Image search using CLIP
        if search_type in ["hybrid", "image"]:
            try:
                if hasattr(embedding_processor, 'image_collection') and embedding_processor.image_collection:
                    # Encode query text with CLIP text encoder
                    loop = asyncio.get_event_loop()
                    query_embedding = await loop.run_in_executor(
                        clip_processor.executor,
                        clip_processor._encode_text_sync,
                        query
                    )
                    
                    # Search image embeddings collection with lower threshold for better recall
                    image_matches = embedding_processor.image_collection.query(
                        query_embeddings=[query_embedding.tolist()],
                        n_results=limit * 2,  # Get more results for better filtering
                        include=['metadatas', 'distances', 'documents']
                    )
                    
                    print(f"🖼️ Image search found {len(image_matches['ids'][0]) if image_matches['ids'] else 0} matches")
                    print(f"🔍 Image search distances: {image_matches['distances'][0][:5] if image_matches['distances'] else 'None'}")
                    
                    # Process image results
                    if image_matches['ids'] and image_matches['ids'][0]:
                        for i, (embedding_id, distance, metadata, document) in enumerate(zip(
                            image_matches['ids'][0],
                            image_matches['distances'][0],
                            image_matches['metadatas'][0],
                            image_matches['documents'][0] if image_matches['documents'] else [None] * len(image_matches['ids'][0])
                        )):
                            similarity = 1 - distance  # Convert distance to similarity
                            # Higher threshold for better image relevance - very strict
                            if similarity >= 0.35:
                                try:
                                    memory = await postgres_db.get_memory_by_id(metadata["memory_id"])
                                    # Only include memories belonging to the current user
                                    if memory and memory.get("user_id") == user_id:
                                        memory["similarity_score"] = similarity
                                        memory["search_type"] = "image"
                                        memory["image_path"] = metadata.get("image_path")
                                        memory["filename"] = metadata.get("filename")
                                        image_results.append(memory)
                                        print(f"   ✅ Added image memory {metadata['memory_id']} (similarity: {similarity:.3f})")
                                except Exception as e:
                                    print(f"⚠️ Error fetching image memory {metadata['memory_id']}: {e}")
                                    continue
                            else:
                                print(f"   ⏭️ Skipped image {metadata.get('memory_id')} (similarity: {similarity:.3f} < 0.35)")
                else:
                    print("⚠️ Image collection not available")
                    
            except Exception as image_error:
                print(f"⚠️ Image search error: {image_error}")
                image_results = []
        
        # 4. Optional type filtering (UI-driven)
        allowed_types = {"text", "image", "voice"}
        selected_types = None
        if memory_type is not None:
            memory_type = (memory_type or "").strip().lower()
            if memory_type not in allowed_types:
                raise HTTPException(status_code=400, detail="Invalid memory_type")
            selected_types = {memory_type}
        elif memory_types is not None:
            parsed = [t.strip().lower() for t in (memory_types or "").split(",") if t.strip()]
            if not parsed:
                raise HTTPException(status_code=400, detail="Invalid memory_types")
            if any(t not in allowed_types for t in parsed):
                raise HTTPException(status_code=400, detail="Invalid memory_types")
            selected_types = set(parsed)

        if selected_types is not None:
            keyword_results = [m for m in keyword_results if (m or {}).get("type") in selected_types]
            semantic_results = [m for m in semantic_results if (m or {}).get("type") in selected_types]
            image_results = [m for m in image_results if (m or {}).get("type") in selected_types]

        # 5. Hybrid ranking and fusion
        final_results = await _hybrid_rank_results(
            keyword_results, semantic_results, image_results, query, limit
        )
        
        # 6. Add image URLs to results
        for result in final_results:
            if result.get("type") == "image":
                metadata = result.get("metadata")
                # Handle metadata as dict or JSON string
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                elif not isinstance(metadata, dict):
                    metadata = {}
                
                filename = metadata.get("filename") if metadata else None
                if filename:
                    result["image_url"] = f"/api/v1/images/{filename}"
                    print(f"🖼️ Added image URL: {result['image_url']}")
        
        # Log result types
        result_types = {}
        for result in final_results:
            mem_type = result.get("type", "unknown")
            result_types[mem_type] = result_types.get(mem_type, 0) + 1
        
        type_summary = ", ".join([f"{count} {type}" for type, count in result_types.items()])
        print(f"✅ Hybrid search completed. Returning {len(final_results)} results: {type_summary}")
        
        return {
            "query": query,
            "search_type": search_type,
            "memory_type": memory_type,
            "memory_types": memory_types,
            "memories": final_results,
            "total_found": len(final_results),
            "breakdown": {
                "keyword_matches": len(keyword_results),
                "semantic_matches": len(semantic_results),
                "image_matches": len(image_results)
            }
        }
        
    except Exception as e:
        print(f"❌ Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")


@memory_router.post("/ask", response_model=AskResponse)
async def ask_from_memories(
    request: AskRequest,
    current_user: Dict = Depends(get_current_user),
    postgres_db: PostgreSQLConnector = Depends(get_postgres_db),
    embedding_processor: EmbeddingProcessor = Depends(get_embedding_processor),
    clip_processor: CLIPImageProcessor = Depends(get_clip_processor)
):
    user_id = current_user["user_id"]
    question = (request.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="question is required")

    # Reuse the same retrieval primitives as /search_memories
    keyword_results = []
    semantic_results = []
    image_results = []

    allowed_types = {"text", "image", "voice"}
    memory_type = request.memory_type
    memory_types = request.memory_types
    selected_types = None
    if memory_type is not None:
        memory_type = (memory_type or "").strip().lower()
        if memory_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid memory_type")
        selected_types = {memory_type}
    elif memory_types is not None:
        parsed = [(t or "").strip().lower() for t in memory_types if (t or "").strip()]
        if not parsed:
            raise HTTPException(status_code=400, detail="Invalid memory_types")
        if any(t not in allowed_types for t in parsed):
            raise HTTPException(status_code=400, detail="Invalid memory_types")
        selected_types = set(parsed)

    if request.search_type in ["hybrid", "keyword"]:
        try:
            keyword_results = await postgres_db.advanced_search_memories(question, request.limit, user_id=user_id)
            if not keyword_results:
                keyword_results = await postgres_db.search_memories(question, request.limit, user_id=user_id)
        except Exception:
            keyword_results = []

    if request.search_type in ["hybrid", "semantic"]:
        try:
            semantic_matches = await embedding_processor.search_similar_memories(question, request.limit * 3, threshold=0.10)
            for match in semantic_matches:
                mem = await postgres_db.get_memory_by_id(match["memory_id"])
                if mem and mem.get("user_id") == user_id:
                    mem["similarity_score"] = match.get("similarity", 0.0)
                    mem["search_type"] = "semantic"
                    semantic_results.append(mem)
        except Exception:
            semantic_results = []

    if request.search_type in ["hybrid", "image"]:
        try:
            if hasattr(embedding_processor, 'image_collection') and embedding_processor.image_collection:
                loop = asyncio.get_event_loop()
                query_embedding = await loop.run_in_executor(
                    clip_processor.executor,
                    clip_processor._encode_text_sync,
                    question
                )
                image_matches = embedding_processor.image_collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=request.limit * 2,
                    include=['metadatas', 'distances', 'documents']
                )

                if image_matches.get('ids') and image_matches['ids'][0]:
                    for distance, metadata in zip(image_matches['distances'][0], image_matches['metadatas'][0]):
                        similarity = 1 - distance
                        mem = await postgres_db.get_memory_by_id(metadata["memory_id"])
                        if mem and mem.get("user_id") == user_id:
                            mem["similarity_score"] = float(similarity)
                            mem["search_type"] = "image"
                            mem["image_path"] = metadata.get("image_path")
                            mem["filename"] = metadata.get("filename")
                            image_results.append(mem)
        except Exception:
            image_results = []

    if selected_types is not None:
        keyword_results = [m for m in keyword_results if (m or {}).get("type") in selected_types]
        semantic_results = [m for m in semantic_results if (m or {}).get("type") in selected_types]
        image_results = [m for m in image_results if (m or {}).get("type") in selected_types]

    fused = await _hybrid_rank_results(keyword_results, semantic_results, image_results, question, request.limit)
    memory_ids = [m.get("id") for m in fused if m.get("id") is not None]

    # Build concise context for Groq
    context_lines = []
    for m in fused[: request.limit]:
        m_type = m.get("type")
        raw_text = (m.get("raw_text") or "").strip()
        processed_text = (m.get("processed_text") or "").strip()
        text = raw_text or processed_text
        if m_type == "image":
            text = f"Image memory caption: {text}" if text else "Image memory"
        elif m_type == "voice":
            text = f"Voice memory transcript: {text}" if text else "Voice memory"
        context_lines.append(f"- (id={m.get('id')}, type={m_type}) {text}")

    system_prompt = (
        "You are a memory assistant.\n"
        "Answer the user's question using ONLY the retrieved memories.\n"
        "Do not quote or repeat the memories verbatim.\n"
        "First, infer the emotional tone of the retrieved memories (sad vs neutral/happy).\n"
        "If the tone is sad, respond with empathy and brief encouragement.\n"
        "If the tone is neutral or happy, respond politely and directly.\n"
        "If the answer is not present, say 'I don't know.'"
    )
    user_prompt = f"Question: {question}\n\nRetrieved memories:\n" + "\n".join(context_lines)

    try:
        answer = await groq_client.answer(system_prompt=system_prompt, user_prompt=user_prompt)
    except Exception as e:
        print(f"❌ Groq request failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Groq request failed: {str(e)}")

    return AskResponse(question=question, answer=answer, memory_ids=memory_ids)


async def _hybrid_rank_results(keyword_results, semantic_results, image_results, query, limit):
    """Advanced hybrid ranking combining keyword and semantic scores"""

    query_terms = set(query.lower().split())

    def _keyword_sorted(results):
        scored = []
        for memory in results:
            processed_text = memory.get('processed_text', '') or ''
            raw_text = memory.get('raw_text', '') or ''
            text_content = f"{processed_text} {raw_text}"
            keyword_score = _calculate_keyword_score(text_content, query_terms)
            scored.append((keyword_score, memory))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored

    keyword_scored = _keyword_sorted(keyword_results)
    semantic_sorted = sorted(semantic_results, key=lambda m: m.get("similarity_score", 0.0), reverse=True)
    image_sorted = sorted(image_results, key=lambda m: m.get("similarity_score", 0.0), reverse=True)

    rrf_k = 60.0
    fused = {}

    def _add_rrf(memory, rank, source, *, score_field=None, extra_fields=None):
        memory_id = memory["id"]
        if memory_id not in fused:
            fused[memory_id] = {
                **memory,
                "match_types": [],
                "keyword_score": 0.0,
                "semantic_score": 0.0,
                "image_score": 0.0,
                "hybrid_score": 0.0,
            }

        fused[memory_id]["hybrid_score"] += 1.0 / (rrf_k + rank)
        fused[memory_id]["match_types"].append(source)

        if score_field == "keyword_score":
            fused[memory_id]["keyword_score"] = max(
                fused[memory_id].get("keyword_score", 0.0),
                memory.get("keyword_score", 0.0),
            )
        elif score_field == "semantic_score":
            fused[memory_id]["semantic_score"] = max(
                fused[memory_id].get("semantic_score", 0.0),
                memory.get("similarity_score", 0.0),
            )
        elif score_field == "image_score":
            fused[memory_id]["image_score"] = max(
                fused[memory_id].get("image_score", 0.0),
                memory.get("similarity_score", 0.0),
            )

        if extra_fields:
            for k, v in extra_fields.items():
                fused[memory_id][k] = v

    for rank, (kw_score, memory) in enumerate(keyword_scored, start=1):
        memory = {**memory, "keyword_score": kw_score}
        _add_rrf(memory, rank, "keyword", score_field="keyword_score")

    for rank, memory in enumerate(semantic_sorted, start=1):
        _add_rrf(memory, rank, "semantic", score_field="semantic_score")

    for rank, memory in enumerate(image_sorted, start=1):
        _add_rrf(
            memory,
            rank,
            "image",
            score_field="image_score",
            extra_fields={
                "image_path": memory.get("image_path"),
                "filename": memory.get("filename"),
            },
        )

    sorted_results = sorted(fused.values(), key=lambda x: x.get("hybrid_score", 0.0), reverse=True)
    return sorted_results[:limit]


def _calculate_keyword_score(text, query_terms):
    """Calculate keyword relevance score based on term frequency and position"""
    if not text or not query_terms:
        return 0.0
    
    text_lower = text.lower()
    words = text_lower.split()
    
    score = 0.0
    total_words = len(words)
    
    for term in query_terms:
        # Exact matches
        exact_matches = text_lower.count(term)
        score += exact_matches * 2.0
        
        # Partial matches
        partial_matches = sum(1 for word in words if term in word and word != term)
        score += partial_matches * 0.5
        
        # Position bonus (earlier mentions get higher score)
        try:
            first_position = text_lower.index(term)
            position_bonus = max(0, 1.0 - (first_position / len(text_lower)))
            score += position_bonus
        except ValueError:
            pass
    
    # Normalize by text length
    return min(score / max(total_words / 100, 1), 10.0)

@memory_router.get("/similar_memories/{memory_id}")
async def get_similar_memories(
    memory_id: int,
    limit: int = 5,
    embedding_processor: EmbeddingProcessor = Depends(get_embedding_processor)
):
    """Get memories similar to a specific memory"""
    try:
        similar_memories = await embedding_processor.find_related_memories(memory_id, limit)
        return {
            "memory_id": memory_id,
            "similar_memories": similar_memories,
            "count": len(similar_memories)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar memories: {str(e)}")

@memory_router.delete("/memory/{memory_id}")
async def delete_memory(
    memory_id: int,
    postgres_db: PostgreSQLConnector = Depends(get_postgres_db),
    embedding_processor: EmbeddingProcessor = Depends(get_embedding_processor)
):
    """Delete a memory and all related data"""
    try:
        # Check if memory exists
        memory = await postgres_db.get_memory_by_id(memory_id)
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Delete from vector database
        await embedding_processor.delete_memory_embedding(memory_id)
        
        # Delete from PostgreSQL (cascades to entities and sentiments)
        async with postgres_db.connection_pool.acquire() as conn:
            await conn.execute("DELETE FROM memories WHERE id = $1", memory_id)
        
        return {"message": f"Memory {memory_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete memory: {str(e)}")

@memory_router.get("/stats")
async def get_memory_stats(
    postgres_db: PostgreSQLConnector = Depends(get_postgres_db),
    embedding_processor: EmbeddingProcessor = Depends(get_embedding_processor)
):
    """Get memory statistics"""
    try:
        # PostgreSQL stats
        async with postgres_db.connection_pool.acquire() as conn:
            total_memories = await conn.fetchval("SELECT COUNT(*) FROM memories")
            type_counts = await conn.fetch("""
                SELECT type, COUNT(*) as count 
                FROM memories 
                GROUP BY type
            """)
            recent_count = await conn.fetchval("""
                SELECT COUNT(*) FROM memories 
                WHERE timestamp >= NOW() - INTERVAL '7 days'
            """)
        
        # Embedding stats
        embedding_stats = await embedding_processor.get_embedding_stats()
        
        return {
            "total_memories": total_memories,
            "recent_memories_7_days": recent_count,
            "memories_by_type": {row["type"]: row["count"] for row in type_counts},
            "embedding_stats": embedding_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
