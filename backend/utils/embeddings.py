"""
Vector embeddings processor using ChromaDB and Sentence Transformers
"""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
import uuid

class EmbeddingProcessor:
    def __init__(self):
        self.chroma_client = None
        self.collection = None
        self.embedding_model = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._init_lock = asyncio.Lock()
        # Primary: BGE-base, Fallback: MiniLM
        self.primary_model = "BAAI/bge-base-en-v1.5"
        self.fallback_model = "all-MiniLM-L6-v2"
        self.model_name = self.primary_model
        self.current_model = None
        self.text_collection_name = "text_embeddings"
        self.image_collection_name = "image_embeddings"
        self.collection = None  # Text embeddings collection
        self.image_collection = None  # Image embeddings collection

    async def initialize(self):
        """Initialize ChromaDB and embedding model"""
        async with self._init_lock:
            if self.embedding_model is not None and self.collection is not None:
                return

            try:
                # Initialize ChromaDB
                self.chroma_client = chromadb.PersistentClient(
                    path="./chroma_db",
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )

                # Get or create text embeddings collection (768d for BGE-base)
                try:
                    self.collection = self.chroma_client.get_collection(
                        name=self.text_collection_name
                    )
                    print(f"✅ Text embeddings collection found: {self.text_collection_name}")
                except:
                    self.collection = self.chroma_client.create_collection(
                        name=self.text_collection_name,
                        metadata={"description": "Text embeddings for semantic search (BGE-base 768d)", "dimensions": 768}
                    )
                    print(f"✅ Text embeddings collection created: {self.text_collection_name}")

                # Get or create image embeddings collection (512d for CLIP)
                try:
                    self.image_collection = self.chroma_client.get_collection(
                        name=self.image_collection_name
                    )
                    print(f"✅ Image embeddings collection found: {self.image_collection_name}")
                except:
                    self.image_collection = self.chroma_client.create_collection(
                        name=self.image_collection_name,
                        metadata={"description": "Image embeddings for semantic search (CLIP 512d)", "dimensions": 512}
                    )
                    print(f"✅ Image embeddings collection created: {self.image_collection_name}")

                # Load embedding model with fallback
                loop = asyncio.get_event_loop()

                # Get Hugging Face token if available
                hf_token = os.getenv('HUGGINGFACE_API_KEY') or os.getenv('HUGGINGFACE_TOKEN')

                def _load_model(model_name: str):
                    # Force CPU. Keep args compatible across sentence-transformers versions.
                    # (Some older versions do not support model_kwargs.)
                    try:
                        return SentenceTransformer(
                            model_name,
                            device="cpu",
                            use_auth_token=hf_token,
                        )
                    except TypeError:
                        # Fallback for older signatures
                        return SentenceTransformer(
                            model_name,
                            use_auth_token=hf_token,
                        )

                try:
                    print(f"🔄 Loading primary embedding model: {self.primary_model}")
                    self.embedding_model = await loop.run_in_executor(
                        self.executor,
                        lambda: _load_model(self.primary_model)
                    )
                    print(f"✅ Primary embedding model loaded: {self.primary_model}")
                    self.model_name = self.primary_model
                    self.current_model = self.primary_model
                except Exception as e:
                    print(f"⚠️ Primary model failed: {e}, falling back to {self.fallback_model}")
                    self.embedding_model = await loop.run_in_executor(
                        self.executor,
                        lambda: _load_model(self.fallback_model)
                    )
                    print(f"✅ Fallback embedding model loaded: {self.fallback_model}")
                    self.model_name = self.fallback_model
                    self.current_model = self.fallback_model

                print(f"✅ Embedding processor initialized successfully with model: {self.current_model}")

            except Exception as e:
                print(f"❌ Failed to initialize embedding processor: {e}")
                raise

    async def create_embedding(self, text: str) -> List[float]:
        """Create embedding for text"""
        if not self.embedding_model:
            await self.initialize()
        
        try:
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                self.executor,
                self.embedding_model.encode,
                text
            )
            return embedding.tolist()
        except Exception as e:
            print(f"❌ Embedding creation failed: {e}")
            return []

    async def store_memory_embedding(self, memory_id: int, text: str, 
                                   metadata: Dict = None) -> str:
        """Store memory embedding in ChromaDB"""
        if not self.collection:
            await self.initialize()
        
        try:
            # Create embedding
            embedding = await self.create_embedding(text)
            if not embedding:
                return None
            
            # Generate unique ID for ChromaDB
            embedding_id = f"memory_{memory_id}_{uuid.uuid4().hex[:8]}"
            
            # Prepare metadata
            doc_metadata = {
                "memory_id": memory_id,
                "text_length": len(text),
                "timestamp": metadata.get("timestamp", ""),
                **(metadata or {})
            }
            
            # Store in ChromaDB
            self.collection.add(
                embeddings=[embedding],
                documents=[text],
                metadatas=[doc_metadata],
                ids=[embedding_id]
            )
            
            return embedding_id
            
        except Exception as e:
            print(f"❌ Failed to store embedding: {e}")
            return None

    async def search_similar_memories(self, query: str, limit: int = 10, 
                                     threshold: float = 0.3) -> List[Dict]:
        """Search for similar memories using semantic similarity with enhanced filtering"""
        if not self.collection:
            await self.initialize()
        
        try:
            print(f"🔍 Semantic search for: '{query}' (threshold: {threshold}, limit: {limit})")
            
            # Create query embedding
            query_embedding = await self.create_embedding(query)
            if not query_embedding:
                print("❌ Failed to create query embedding")
                return []
            
            # Search in ChromaDB with higher limit to allow for filtering
            search_limit = min(limit * 3, 100)  # Get more results for better filtering
            
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self.executor,
                lambda: self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=search_limit,
                    include=['metadatas', 'distances', 'documents']
                )
            )
            
            # Process and rank results
            similar_memories = []
            if results['ids'] and results['ids'][0]:
                for i, (embedding_id, distance, metadata, document) in enumerate(zip(
                    results['ids'][0], 
                    results['distances'][0], 
                    results['metadatas'][0],
                    results['documents'][0] if results['documents'] else [None] * len(results['ids'][0])
                )):
                    # Convert distance to similarity (ChromaDB uses cosine distance)
                    similarity = 1 - distance
                    
                    if similarity >= threshold:
                        # Extract memory_id from metadata or embedding_id
                        memory_id = metadata.get("memory_id")
                        if not memory_id and embedding_id:
                            # Try to extract from embedding_id format: "memory_123_uuid"
                            try:
                                memory_id = int(embedding_id.split('_')[1])
                            except (IndexError, ValueError):
                                continue
                        
                        similar_memories.append({
                            "memory_id": memory_id,
                            "embedding_id": embedding_id,
                            "similarity": round(similarity, 4),
                            "distance": round(distance, 4),
                            "document_preview": document[:100] + "..." if document and len(document) > 100 else document,
                            "metadata": metadata
                        })
            
            # Sort by similarity and limit results
            similar_memories.sort(key=lambda x: x["similarity"], reverse=True)
            final_results = similar_memories[:limit]
            
            print(f"✅ Found {len(final_results)} similar memories above threshold {threshold}")
            return final_results
            
        except Exception as e:
            print(f"❌ Semantic search failed: {e}")
            return []

    async def hybrid_search_memories(self, query: str, limit: int = 20, 
                                   semantic_weight: float = 0.6, 
                                   keyword_weight: float = 0.4) -> List[Dict]:
        """Perform hybrid search combining semantic and keyword matching"""
        try:
            print(f"🔄 Hybrid search: '{query}' (semantic: {semantic_weight}, keyword: {keyword_weight})")
            
            # Get semantic results
            semantic_results = await self.search_similar_memories(
                query, limit=limit, threshold=0.2
            )
            
            # Create combined scoring
            hybrid_results = []
            for result in semantic_results:
                # Calculate hybrid score
                semantic_score = result["similarity"]
                
                # Simple keyword matching score for the document preview
                document = result.get("document_preview", "")
                keyword_score = self._calculate_keyword_match_score(document, query)
                
                hybrid_score = (semantic_score * semantic_weight) + (keyword_score * keyword_weight)
                
                hybrid_results.append({
                    **result,
                    "keyword_score": round(keyword_score, 4),
                    "hybrid_score": round(hybrid_score, 4)
                })
            
            # Sort by hybrid score
            hybrid_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
            
            print(f"✅ Hybrid search completed: {len(hybrid_results)} results")
            return hybrid_results[:limit]
            
        except Exception as e:
            print(f"❌ Hybrid search failed: {e}")
            return []

    def _calculate_keyword_match_score(self, text: str, query: str) -> float:
        """Calculate keyword matching score for a text"""
        if not text or not query:
            return 0.0
        
        text_lower = text.lower()
        query_terms = query.lower().split()
        
        score = 0.0
        for term in query_terms:
            if term in text_lower:
                # Exact match
                score += 1.0
                # Frequency bonus
                score += text_lower.count(term) * 0.1
        
        # Normalize by number of query terms
        return min(score / len(query_terms), 1.0) if query_terms else 0.0

    async def find_related_memories(self, memory_id: int, 
                                  limit: int = 5) -> List[Dict]:
        """Find memories related to a specific memory"""
        try:
            # Get the memory's embedding
            memory_data = self.collection.get(
                where={"memory_id": memory_id},
                include=["documents", "embeddings"]
            )
            
            if not memory_data["documents"]:
                return []
            
            # Use the memory's text to find similar ones
            memory_text = memory_data["documents"][0]
            similar = await self.search_similar_memories(
                memory_text, 
                limit=limit + 1  # +1 to exclude self
            )
            
            # Filter out the original memory
            related = [m for m in similar if m["memory_id"] != memory_id]
            return related[:limit]
            
        except Exception as e:
            print(f"❌ Related memories search failed: {e}")
            return []

    async def update_memory_embedding(self, memory_id: int, new_text: str) -> bool:
        """Update embedding for existing memory"""
        try:
            # Delete old embeddings for this memory
            await self.delete_memory_embedding(memory_id)
            
            # Create new embedding
            embedding_id = await self.store_memory_embedding(memory_id, new_text)
            return embedding_id is not None
            
        except Exception as e:
            print(f"❌ Failed to update embedding: {e}")
            return False

    async def delete_memory_embedding(self, memory_id: int) -> bool:
        """Delete embedding for memory"""
        if not self.collection:
            return False
        
        try:
            # Get IDs to delete
            results = self.collection.get(
                where={"memory_id": memory_id},
                include=["documents"]
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Failed to delete embedding: {e}")
            return False

    async def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about stored embeddings"""
        if not self.collection:
            await self.initialize()
        
        try:
            count = self.collection.count()
            
            # Get sample of metadata to analyze
            sample = self.collection.peek(limit=100)
            
            stats = {
                "total_embeddings": count,
                "model_name": self.model_name,
                "current_model": self.current_model,
                "primary_model": self.primary_model,
                "fallback_model": self.fallback_model,
                "collection_name": self.collection_name
            }
            
            if sample["metadatas"]:
                # Analyze metadata
                memory_ids = [m.get("memory_id") for m in sample["metadatas"]]
                unique_memories = len(set(memory_ids))
                
                text_lengths = [m.get("text_length", 0) for m in sample["metadatas"]]
                avg_text_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0
                
                stats.update({
                    "unique_memories": unique_memories,
                    "avg_text_length": avg_text_length,
                    "sample_size": len(sample["metadatas"])
                })
            
            return stats
            
        except Exception as e:
            print(f"❌ Failed to get embedding stats: {e}")
            return {"error": str(e)}

    async def batch_create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts efficiently"""
        if not self.embedding_model:
            await self.initialize()
        
        try:
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                self.executor,
                self.embedding_model.encode,
                texts
            )
            return embeddings.tolist()
            
        except Exception as e:
            print(f"❌ Batch embedding creation failed: {e}")
            return []

    async def cluster_memories(self, memory_ids: List[int] = None, 
                             n_clusters: int = 5) -> Dict[str, Any]:
        """Cluster memories based on semantic similarity"""
        try:
            from sklearn.cluster import KMeans
            
            # Get embeddings
            if memory_ids:
                # Get specific memories
                results = self.collection.get(
                    where={"memory_id": {"$in": memory_ids}},
                    include=["embeddings", "metadatas", "documents"]
                )
            else:
                # Get all memories
                results = self.collection.get(
                    include=["embeddings", "metadatas", "documents"]
                )
            
            if not results["embeddings"]:
                return {"clusters": [], "error": "No embeddings found"}
            
            # Perform clustering
            embeddings = np.array(results["embeddings"])
            kmeans = KMeans(n_clusters=min(n_clusters, len(embeddings)), random_state=42)
            cluster_labels = kmeans.fit_predict(embeddings)
            
            # Organize results by cluster
            clusters = {}
            for i, (label, metadata, doc) in enumerate(zip(
                cluster_labels, 
                results["metadatas"], 
                results["documents"]
            )):
                if label not in clusters:
                    clusters[label] = []
                
                clusters[label].append({
                    "memory_id": metadata["memory_id"],
                    "text": doc[:200] + "..." if len(doc) > 200 else doc,
                    "metadata": metadata
                })
            
            return {
                "clusters": [{"id": k, "memories": v} for k, v in clusters.items()],
                "n_clusters": len(clusters),
                "total_memories": len(results["embeddings"])
            }
            
        except Exception as e:
            print(f"❌ Memory clustering failed: {e}")
            return {"clusters": [], "error": str(e)}

    def cleanup(self):
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
