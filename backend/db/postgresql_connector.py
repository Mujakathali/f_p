"""
PostgreSQL database connector and schema management
"""
import asyncpg
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import base64
import hashlib
from dotenv import load_dotenv
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

load_dotenv()

class PostgreSQLConnector:
    def __init__(self):
        self.connection_pool = None
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB', 'memorygraph_ai'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'password')
        }

    async def connect(self):
        """Create connection pool"""
        try:
            self.connection_pool = await asyncpg.create_pool(
                **self.db_config,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            await self.create_tables()
            print("✅ PostgreSQL connected successfully")
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            raise

    async def disconnect(self):
        """Close connection pool"""
        if self.connection_pool:
            await self.connection_pool.close()

    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.connection_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except:
            return False

    async def create_tables(self):
        """Create database tables if they don't exist"""
        create_tables_sql = """
        -- Users table (must be created first)
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            profile_data JSONB DEFAULT '{}'
        );
        
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

        -- Memories table
        CREATE TABLE IF NOT EXISTS memories (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            raw_text TEXT NOT NULL,
            cipher_text TEXT,
            processed_text TEXT,
            type VARCHAR(20) NOT NULL CHECK (type IN ('text', 'voice', 'image')),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}',
            embedding_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP
        );

        -- Entities table
        CREATE TABLE IF NOT EXISTS entities (
            id SERIAL PRIMARY KEY,
            memory_id INTEGER REFERENCES memories(id) ON DELETE CASCADE,
            entity TEXT NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            confidence FLOAT DEFAULT 0.0,
            start_pos INTEGER,
            end_pos INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Sentiments table
        CREATE TABLE IF NOT EXISTS sentiments (
            id SERIAL PRIMARY KEY,
            memory_id INTEGER REFERENCES memories(id) ON DELETE CASCADE,
            sentiment_score FLOAT NOT NULL,
            sentiment_label VARCHAR(20) NOT NULL,
            confidence FLOAT DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Memory relationships table
        CREATE TABLE IF NOT EXISTS memory_relationships (
            id SERIAL PRIMARY KEY,
            memory_id_1 INTEGER REFERENCES memories(id) ON DELETE CASCADE,
            memory_id_2 INTEGER REFERENCES memories(id) ON DELETE CASCADE,
            relationship_type VARCHAR(50) NOT NULL,
            similarity_score FLOAT DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(memory_id_1, memory_id_2, relationship_type)
        );

        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id);
        CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
        CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp);
        CREATE INDEX IF NOT EXISTS idx_entities_memory_id ON entities(memory_id);
        CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
        CREATE INDEX IF NOT EXISTS idx_sentiments_memory_id ON sentiments(memory_id);
        CREATE INDEX IF NOT EXISTS idx_memory_relationships_memory_ids ON memory_relationships(memory_id_1, memory_id_2);

        -- Activity logs
        CREATE TABLE IF NOT EXISTS activity_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            action VARCHAR(100) NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id);

        -- Shared memories (invite-based)
        CREATE TABLE IF NOT EXISTS shared_memories (
            id SERIAL PRIMARY KEY,
            owner_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            memory_id INTEGER REFERENCES memories(id) ON DELETE CASCADE,
            shared_with_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            invite_token VARCHAR(255),
            can_edit BOOLEAN DEFAULT FALSE,
            revoked BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(invite_token)
        );
        CREATE INDEX IF NOT EXISTS idx_shared_memories_owner ON shared_memories(owner_user_id);
        CREATE INDEX IF NOT EXISTS idx_shared_memories_shared_with ON shared_memories(shared_with_user_id);

        -- Revoked tokens
        CREATE TABLE IF NOT EXISTS revoked_tokens (
            jti VARCHAR(255) PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        async with self.connection_pool.acquire() as conn:
            await conn.execute(create_tables_sql)
            # Ensure deleted_at exists (in case table pre-existed without it)
            await conn.execute("ALTER TABLE memories ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;")
            # Store-only ciphertext column (plain text is still stored in raw_text)
            await conn.execute("ALTER TABLE memories ADD COLUMN IF NOT EXISTS cipher_text TEXT;")
            # Ensure supporting tables exist even if create_tables_sql was previously trimmed
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                action VARCHAR(100) NOT NULL,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id);
            CREATE TABLE IF NOT EXISTS shared_memories (
                id SERIAL PRIMARY KEY,
                owner_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                memory_id INTEGER REFERENCES memories(id) ON DELETE CASCADE,
                shared_with_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                invite_token VARCHAR(255),
                can_edit BOOLEAN DEFAULT FALSE,
                revoked BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(invite_token)
            );
            CREATE INDEX IF NOT EXISTS idx_shared_memories_owner ON shared_memories(owner_user_id);
            CREATE INDEX IF NOT EXISTS idx_shared_memories_shared_with ON shared_memories(shared_with_user_id);
            CREATE TABLE IF NOT EXISTS revoked_tokens (
                jti VARCHAR(255) PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

    def _encrypt_to_cipher_text(self, plaintext: str) -> str:
        """Encrypt plaintext using AES-GCM and return base64(nonce+ciphertext).

        This is intentionally 'store-only': ciphertext is not used anywhere else.
        """
        key_material = os.getenv("CIPHER_KEY") or os.getenv("JWT_SECRET_KEY") or "memorygraph-default-key"
        key = hashlib.sha256(key_material.encode("utf-8")).digest()  # 32 bytes
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.urlsafe_b64encode(nonce + ct).decode("utf-8")

    async def insert_memory(self, raw_text: str, processed_text: str, memory_type: str, 
                           metadata: Dict = None, embedding_id: str = None, user_id: int = None) -> int:
        """Insert a new memory and return its ID"""
        cipher_text = self._encrypt_to_cipher_text(raw_text)
        query = """
        INSERT INTO memories (user_id, raw_text, cipher_text, processed_text, type, metadata, embedding_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
        """
        async with self.connection_pool.acquire() as conn:
            memory_id = await conn.fetchval(
                query, user_id, raw_text, cipher_text, processed_text, memory_type, 
                json.dumps(metadata or {}), embedding_id
            )
        return memory_id

    async def insert_entities(self, memory_id: int, entities: List[Dict]):
        """Insert extracted entities for a memory"""
        if not entities:
            return
        
        query = """
        INSERT INTO entities (memory_id, entity, entity_type, confidence, start_pos, end_pos)
        VALUES ($1, $2, $3, $4, $5, $6)
        """
        async with self.connection_pool.acquire() as conn:
            await conn.executemany(query, [
                (memory_id, entity['text'], entity['label'], 
                 entity.get('confidence', 0.0), entity.get('start', 0), entity.get('end', 0))
                for entity in entities
            ])

    async def insert_sentiment(self, memory_id: int, sentiment_score: float, 
                              sentiment_label: str, confidence: float = 0.0):
        """Insert sentiment analysis for a memory"""
        query = """
        INSERT INTO sentiments (memory_id, sentiment_score, sentiment_label, confidence)
        VALUES ($1, $2, $3, $4)
        """
        async with self.connection_pool.acquire() as conn:
            await conn.execute(query, memory_id, sentiment_score, sentiment_label, confidence)

    async def get_memories(
        self,
        limit: int = 100,
        offset: int = 0,
        memory_type: str = None,
        user_id: int = None,
        include_deleted: bool = False,
    ) -> List[Dict]:
        """Retrieve memories with optional filtering"""
        base_query = """
        SELECT m.*, 
               COALESCE(json_agg(DISTINCT jsonb_build_object(
                   'entity', e.entity, 
                   'type', e.entity_type, 
                   'confidence', e.confidence
               )) FILTER (WHERE e.id IS NOT NULL), '[]') as entities,
               COALESCE(json_agg(DISTINCT jsonb_build_object(
                   'score', s.sentiment_score,
                   'label', s.sentiment_label,
                   'confidence', s.confidence
               )) FILTER (WHERE s.id IS NOT NULL), '[]') as sentiments
        FROM memories m
        LEFT JOIN entities e ON m.id = e.memory_id
        LEFT JOIN sentiments s ON m.id = s.memory_id
        """
        
        where_clauses = []
        params = []
        param_count = 1
        
        # Add user_id filter if provided
        if user_id is not None:
            where_clauses.append(f"m.user_id = ${param_count}")
            params.append(user_id)
            param_count += 1
        
        # Add memory_type filter if provided
        if memory_type:
            where_clauses.append(f"m.type = ${param_count}")
            params.append(memory_type)
            param_count += 1
        
        # Exclude soft-deleted by default
        if not include_deleted:
            where_clauses.append("m.deleted_at IS NULL")
        
        # Add WHERE clause if there are any filters
        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)
        
        # Add limit and offset
        base_query += f"""
        GROUP BY m.id
        ORDER BY m.timestamp DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        
        # Add limit and offset to params
        params.extend([limit, offset])
        
        async with self.connection_pool.acquire() as conn:
            rows = await conn.fetch(base_query, *params)
            return [dict(row) for row in rows]

    async def get_memory_by_id(self, memory_id: int, include_deleted: bool = False) -> Optional[Dict]:
        """Get a specific memory by ID"""
        deleted_filter = "" if include_deleted else "AND m.deleted_at IS NULL"
        query = f"""
        SELECT m.*, 
               COALESCE(json_agg(DISTINCT jsonb_build_object(
                   'entity', e.entity, 
                   'type', e.entity_type, 
                   'confidence', e.confidence
               )) FILTER (WHERE e.id IS NOT NULL), '[]') as entities,
               COALESCE(json_agg(DISTINCT jsonb_build_object(
                   'score', s.sentiment_score,
                   'label', s.sentiment_label,
                   'confidence', s.confidence
               )) FILTER (WHERE s.id IS NOT NULL), '[]') as sentiments
        FROM memories m
        LEFT JOIN entities e ON m.id = e.memory_id
        LEFT JOIN sentiments s ON m.id = s.memory_id
        WHERE m.id = $1 {deleted_filter}
        GROUP BY m.id
        """
        
        async with self.connection_pool.acquire() as conn:
            row = await conn.fetchrow(query, memory_id)
            return dict(row) if row else None

    async def soft_delete_memory(self, memory_id: int, user_id: int) -> bool:
        """Soft-delete a memory"""
        query = """
        UPDATE memories
        SET deleted_at = CURRENT_TIMESTAMP
        WHERE id = $1 AND user_id = $2 AND deleted_at IS NULL
        """
        async with self.connection_pool.acquire() as conn:
            result = await conn.execute(query, memory_id, user_id)
            return result and result.upper().startswith("UPDATE")

    async def restore_memory(self, memory_id: int, user_id: int) -> bool:
        """Restore a soft-deleted memory"""
        query = """
        UPDATE memories
        SET deleted_at = NULL
        WHERE id = $1 AND user_id = $2 AND deleted_at IS NOT NULL
        """
        async with self.connection_pool.acquire() as conn:
            result = await conn.execute(query, memory_id, user_id)
            return result and result.upper().startswith("UPDATE")

    async def log_activity(self, user_id: int, action: str, metadata: Dict = None):
        """Log user activity"""
        query = """
        INSERT INTO activity_logs (user_id, action, metadata)
        VALUES ($1, $2, $3)
        """
        async with self.connection_pool.acquire() as conn:
            await conn.execute(query, user_id, action, json.dumps(metadata or {}))

    async def revoke_token(self, jti: str, user_id: int):
        """Store revoked token"""
        query = """
        INSERT INTO revoked_tokens (jti, user_id, revoked_at)
        VALUES ($1, $2, CURRENT_TIMESTAMP)
        ON CONFLICT (jti) DO NOTHING
        """
        async with self.connection_pool.acquire() as conn:
            await conn.execute(query, jti, user_id)

    async def is_token_revoked(self, jti: str) -> bool:
        """Check if token jti is revoked"""
        query = "SELECT 1 FROM revoked_tokens WHERE jti = $1"
        async with self.connection_pool.acquire() as conn:
            row = await conn.fetchrow(query, jti)
            return row is not None

    async def export_memories(self, user_id: int) -> List[Dict]:
        """Export all non-deleted memories (with entities/sentiments) for a user"""
        query = """
        SELECT m.*, 
               COALESCE(json_agg(DISTINCT jsonb_build_object(
                   'entity', e.entity, 
                   'type', e.entity_type, 
                   'confidence', e.confidence
               )) FILTER (WHERE e.id IS NOT NULL), '[]') as entities,
               COALESCE(json_agg(DISTINCT jsonb_build_object(
                   'score', s.sentiment_score,
                   'label', s.sentiment_label,
                   'confidence', s.confidence
               )) FILTER (WHERE s.id IS NOT NULL), '[]') as sentiments
        FROM memories m
        LEFT JOIN entities e ON m.id = e.memory_id
        LEFT JOIN sentiments s ON m.id = s.memory_id
        WHERE m.user_id = $1 AND m.deleted_at IS NULL
        GROUP BY m.id
        ORDER BY m.timestamp DESC
        """
        async with self.connection_pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return [dict(row) for row in rows]

    async def import_memories(self, user_id: int, memories: List[Dict]) -> int:
        """Import memories for a user (basic insert with nested entities/sentiments)"""
        count = 0
        async with self.connection_pool.acquire() as conn:
            async with conn.transaction():
                for m in memories:
                    raw = m.get("raw_text") or ""
                    processed = m.get("processed_text") or raw
                    mtype = m.get("type") or "text"
                    ts = m.get("timestamp") or datetime.utcnow()
                    metadata = m.get("metadata") or {}
                    mem_id = await conn.fetchval(
                        """
                        INSERT INTO memories (user_id, raw_text, processed_text, type, timestamp, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        RETURNING id
                        """,
                        user_id, raw, processed, mtype, ts, json.dumps(metadata)
                    )
                    for e in m.get("entities") or []:
                        await conn.execute(
                            """
                            INSERT INTO entities (memory_id, entity, entity_type, confidence, start_pos, end_pos)
                            VALUES ($1, $2, $3, $4, $5, $6)
                            """,
                            mem_id,
                            e.get("entity") or e.get("text"),
                            e.get("type") or e.get("entity_type"),
                            e.get("confidence", 0.0),
                            e.get("start", 0),
                            e.get("end", 0),
                        )
                    for s in m.get("sentiments") or []:
                        await conn.execute(
                            """
                            INSERT INTO sentiments (memory_id, sentiment_score, sentiment_label, confidence)
                            VALUES ($1, $2, $3, $4)
                            """,
                            mem_id,
                            s.get("score") or s.get("sentiment_score") or 0.0,
                            s.get("label") or s.get("sentiment_label") or "neutral",
                            s.get("confidence", 0.0),
                        )
                    count += 1
        return count

    async def create_share_invite(self, owner_user_id: int, memory_id: int, shared_with_user_id: int, invite_token: str, can_edit: bool):
        query = """
        INSERT INTO shared_memories (owner_user_id, memory_id, shared_with_user_id, invite_token, can_edit, revoked)
        VALUES ($1, $2, $3, $4, $5, FALSE)
        ON CONFLICT (invite_token) DO NOTHING
        """
        async with self.connection_pool.acquire() as conn:
            await conn.execute(query, owner_user_id, memory_id, shared_with_user_id, invite_token, can_edit)

    async def accept_share_invite(self, invite_token: str, user_id: int) -> Optional[Dict]:
        query = """
        UPDATE shared_memories
        SET shared_with_user_id = $1, revoked = FALSE
        WHERE invite_token = $2 AND revoked = FALSE
        RETURNING *
        """
        async with self.connection_pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, invite_token)
            return dict(row) if row else None

    async def revoke_share_invite(self, invite_token: str, owner_user_id: int) -> bool:
        query = """
        UPDATE shared_memories
        SET revoked = TRUE
        WHERE invite_token = $1 AND owner_user_id = $2
        """
        async with self.connection_pool.acquire() as conn:
            result = await conn.execute(query, invite_token, owner_user_id)
            return result and result.upper().startswith("UPDATE")

    async def list_shared_for_user(self, user_id: int) -> List[Dict]:
        query = """
        SELECT sm.*, m.raw_text, m.type, m.timestamp
        FROM shared_memories sm
        JOIN memories m ON sm.memory_id = m.id
        WHERE (sm.owner_user_id = $1 OR sm.shared_with_user_id = $1)
          AND sm.revoked = FALSE
          AND m.deleted_at IS NULL
        """
        async with self.connection_pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return [dict(row) for row in rows]

    async def search_memories(self, query: str, limit: int = 50) -> List[Dict]:
        """Basic search memories by text content"""
        search_query = """
        SELECT m.*, 
               COALESCE(json_agg(DISTINCT jsonb_build_object(
                   'entity', e.entity, 
                   'type', e.entity_type, 
                   'confidence', e.confidence
               )) FILTER (WHERE e.id IS NOT NULL), '[]') as entities,
               COALESCE(json_agg(DISTINCT jsonb_build_object(
                   'score', s.sentiment_score,
                   'label', s.sentiment_label,
                   'confidence', s.confidence
               )) FILTER (WHERE s.id IS NOT NULL), '[]') as sentiments
        FROM memories m
        LEFT JOIN entities e ON m.id = e.memory_id
        LEFT JOIN sentiments s ON m.id = s.memory_id
        WHERE m.processed_text ILIKE $1 OR m.raw_text ILIKE $1
        GROUP BY m.id
        ORDER BY m.timestamp DESC
        LIMIT $2
        """
        
        search_term = f"%{query}%"
        async with self.connection_pool.acquire() as conn:
            rows = await conn.fetch(search_query, search_term, limit)
            return [dict(row) for row in rows]

    async def advanced_search_memories(self, query: str, limit: int = 50, user_id: int = None) -> List[Dict]:
        """Advanced keyword search with full-text search and ranking (optionally filtered by user_id)"""
        
        # Split query into individual terms for better matching
        query_terms = query.lower().split()
        
        # Build dynamic WHERE clause - separate user_id filter from search terms
        params = []
        param_count = 1
        user_filter = ""
        search_conditions = []
        
        # Add user_id filter if provided (must use AND, not OR)
        if user_id is not None:
            user_filter = f"m.user_id = ${param_count}"
            params.append(user_id)
            param_count += 1
        
        # Add search term conditions (these use OR among themselves)
        for term in query_terms:
            term_pattern = f"%{term}%"
            search_conditions.append(f"""
                (m.processed_text ILIKE ${param_count} OR 
                 m.raw_text ILIKE ${param_count} OR
                 e.entity ILIKE ${param_count})
            """)
            params.append(term_pattern)
            param_count += 1
        
        # Build WHERE clause: user_id AND (search terms)
        where_clause = ""
        if user_filter and search_conditions:
            where_clause = f"WHERE {user_filter} AND ({' OR '.join(search_conditions)})"
        elif user_filter:
            where_clause = f"WHERE {user_filter}"
        elif search_conditions:
            where_clause = f"WHERE ({' OR '.join(search_conditions)})"
        
        # Add limit parameter
        params.append(limit)
        limit_param = f"${param_count}"
        
        # Build the base query
        search_query = f"""
        SELECT m.id, m.raw_text, m.processed_text, m.type, m.timestamp, m.metadata, m.embedding_id, m.created_at, m.updated_at, m.user_id,
               COALESCE(
                   (SELECT json_agg(jsonb_build_object(
                       'entity', e2.entity, 
                       'type', e2.entity_type, 
                       'confidence', e2.confidence
                   ))
                   FROM entities e2
                   WHERE e2.memory_id = m.id), '[]'::json
               ) as entities,
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
        LEFT JOIN entities e ON m.id = e.memory_id
        LEFT JOIN sentiments s ON m.id = s.memory_id
        {where_clause}
        GROUP BY m.id, m.raw_text, m.processed_text, m.type, m.timestamp, m.metadata, m.embedding_id, m.created_at, m.updated_at, m.user_id
        ORDER BY m.timestamp DESC
        LIMIT {limit_param}
        """
        
        async with self.connection_pool.acquire() as conn:
            rows = await conn.fetch(search_query, *params)
            return [dict(row) for row in rows]

    async def get_entities_by_type(self, entity_type: str) -> List[Dict]:
        """Get all entities of a specific type"""
        query = """
        SELECT DISTINCT e.entity, e.entity_type, COUNT(*) as frequency
        FROM entities e
        WHERE e.entity_type = $1
        GROUP BY e.entity, e.entity_type
        ORDER BY frequency DESC
        """
        
        async with self.connection_pool.acquire() as conn:
            rows = await conn.fetch(query, entity_type)
            return [dict(row) for row in rows]
