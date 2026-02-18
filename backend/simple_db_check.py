import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

# Database connection
conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    database=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD')
)

cur = conn.cursor()

# Check if memories table exists
cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'memories');")
table_exists = cur.fetchone()[0]
print(f"Memories table exists: {table_exists}")

if table_exists:
    # Count memories
    cur.execute("SELECT COUNT(*) FROM memories;")
    count = cur.fetchone()[0]
    print(f"Total memories: {count}")
    
    if count > 0:
        # Show recent memories
        cur.execute("SELECT id, processed_text, memory_type FROM memories ORDER BY id DESC LIMIT 5;")
        rows = cur.fetchall()
        print("\nRecent memories:")
        for row in rows:
            print(f"ID: {row[0]}, Text: {row[1][:50]}..., Type: {row[2]}")
        
        # Test search
        cur.execute("SELECT id, processed_text FROM memories WHERE processed_text ILIKE %s LIMIT 3;", ('%happy%',))
        search_rows = cur.fetchall()
        print(f"\nSearch for 'happy' found {len(search_rows)} results:")
        for row in search_rows:
            print(f"ID: {row[0]}, Text: {row[1][:50]}...")
    else:
        print("No memories found in database!")
else:
    print("Memories table does not exist!")

cur.close()
conn.close()
