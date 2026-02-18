"""
One-off database fixer for MemoryGraph AI.

What it does (idempotent and safe to rerun):
1) Ensures users table exists with correct columns (password_hash, full_name, last_login, is_active, profile_data).
2) Renames old column hashed_password -> password_hash if present.
3) Adds any missing columns on users.
4) Ensures required indexes on users.
5) Ensures memories/entities/sentiments/memory_relationships tables exist (same schema as app).

Run:
    python fix_db_schema.py
"""
import asyncio
import os
from dotenv import load_dotenv

import asyncpg


load_dotenv()


DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "memorygraph_ai"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "password"),
}


async def ensure_users_table(conn: asyncpg.Connection):
    # Create table if missing
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            profile_data JSONB DEFAULT '{}'
        );
        """
    )

    # Rename legacy column if present
    hashed_col = await conn.fetchval(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'hashed_password'
        """
    )
    password_hash_col = await conn.fetchval(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'password_hash'
        """
    )
    if hashed_col and not password_hash_col:
        await conn.execute('ALTER TABLE users RENAME COLUMN "hashed_password" TO "password_hash";')

    # Ensure required columns exist
    async def add_column_if_missing(name: str, ddl: str):
        exists = await conn.fetchval(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = $1
            """,
            name,
        )
        if not exists:
            await conn.execute(f"ALTER TABLE users ADD COLUMN {ddl};")

    await add_column_if_missing("full_name", "full_name VARCHAR(255)")
    await add_column_if_missing("last_login", "last_login TIMESTAMP")
    await add_column_if_missing("is_active", "is_active BOOLEAN DEFAULT TRUE")
    await add_column_if_missing("profile_data", "profile_data JSONB DEFAULT '{}'")
    await add_column_if_missing("password_hash", "password_hash TEXT NOT NULL DEFAULT ''")

    # Ensure indexes
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")


async def ensure_memories_tables(conn: asyncpg.Connection):
    await conn.execute(
        """
        -- Memories table
        CREATE TABLE IF NOT EXISTS memories (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            raw_text TEXT NOT NULL,
            processed_text TEXT,
            type VARCHAR(20) NOT NULL CHECK (type IN ('text', 'voice', 'image')),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}',
            embedding_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id);
        CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
        CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp);
        CREATE INDEX IF NOT EXISTS idx_entities_memory_id ON entities(memory_id);
        CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
        CREATE INDEX IF NOT EXISTS idx_sentiments_memory_id ON sentiments(memory_id);
        CREATE INDEX IF NOT EXISTS idx_memory_relationships_memory_ids ON memory_relationships(memory_id_1, memory_id_2);
        """
    )


async def main():
    print("🔄 Connecting to PostgreSQL to fix schema...")
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        await ensure_users_table(conn)
        await ensure_memories_tables(conn)
        print("✅ Database schema verified/fixed.")
    finally:
        await conn.close()
        print("🔌 Connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
