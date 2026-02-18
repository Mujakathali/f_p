# 🔧 Database Migration Instructions

## Problem
Your backend is failing because the `user_id` column doesn't exist in the `memories` table yet.

## Solution - Run the Migration

### Option 1: Using Python Script (Recommended)

1. **Open a NEW Command Prompt or PowerShell window**

2. **Navigate to the backend directory:**
   ```bash
   cd d:\final_year_project\backend
   ```

3. **Run the migration script:**
   ```bash
   python migrate_now.py
   ```

4. **You should see output like:**
   ```
   ======================================================================
   DATABASE MIGRATION - Adding user_id to memories table
   ======================================================================
   
   Connecting to database: memorygraph_ai at localhost:5432
   ✅ Connected to PostgreSQL successfully
   
   🔍 Checking if user_id column exists...
   📝 user_id column does not exist, adding it now...
   ✅ Successfully added user_id column to memories table
   
   🔍 Creating index on user_id...
   ✅ Index created successfully
   
   🎉 MIGRATION COMPLETED SUCCESSFULLY!
   ```

### Option 2: Using pgAdmin (GUI Method)

1. **Open pgAdmin**

2. **Connect to your PostgreSQL server**

3. **Navigate to:**
   - Servers → PostgreSQL → Databases → memorygraph_ai → Schemas → public → Tables → memories

4. **Right-click on `memories` table → Query Tool**

5. **Copy and paste this SQL:**
   ```sql
   -- Add user_id column
   ALTER TABLE memories 
   ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;

   -- Create index
   CREATE INDEX idx_memories_user_id ON memories(user_id);

   -- Assign existing memories to first user
   UPDATE memories 
   SET user_id = (SELECT id FROM users ORDER BY id LIMIT 1)
   WHERE user_id IS NULL;

   -- Verify
   SELECT COUNT(*) as total, COUNT(user_id) as with_user_id FROM memories;
   ```

6. **Click Execute (F5)**

### Option 3: Using psql Command Line

1. **Open Command Prompt**

2. **Connect to PostgreSQL:**
   ```bash
   psql -U postgres -d memorygraph_ai
   ```
   (Password: `iammuja008`)

3. **Run these commands:**
   ```sql
   ALTER TABLE memories ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
   CREATE INDEX idx_memories_user_id ON memories(user_id);
   UPDATE memories SET user_id = (SELECT id FROM users ORDER BY id LIMIT 1) WHERE user_id IS NULL;
   \q
   ```

## After Migration

1. **Restart your backend server:**
   ```bash
   python app.py
   ```

2. **You should see:**
   ```
   ✅ PostgreSQL connected successfully
   ✅ Authentication system initialized
   ✅ Backend services initialized successfully
   ```

## Verify Migration Success

Run this SQL query to check:
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'memories' AND column_name = 'user_id';
```

Should return:
```
 column_name | data_type 
-------------+-----------
 user_id     | integer
```

## Troubleshooting

### If you get "users table doesn't exist":
The users table should have been created by the auth system. Check if it exists:
```sql
SELECT * FROM users;
```

If it doesn't exist, restart the backend once to create it, then run the migration.

### If migration still fails:
1. Make sure PostgreSQL is running
2. Check your `.env` file has correct credentials:
   - POSTGRES_HOST=localhost
   - POSTGRES_PORT=5432
   - POSTGRES_DB=memorygraph_ai
   - POSTGRES_USER=postgres
   - POSTGRES_PASSWORD=iammuja008

3. Test connection:
   ```bash
   psql -U postgres -d memorygraph_ai -c "SELECT version();"
   ```

## What This Migration Does

1. ✅ Adds `user_id` column to `memories` table
2. ✅ Creates foreign key relationship to `users` table
3. ✅ Creates index for fast queries
4. ✅ Assigns existing memories to first user (backward compatibility)

## Files Created

- `migrate_now.py` - Main migration script
- `fix_database.sql` - SQL commands for manual execution
- `run_migration.py` - Alternative migration runner

## Need Help?

If the migration still doesn't work:
1. Check if PostgreSQL service is running
2. Verify database credentials in `.env`
3. Try the pgAdmin GUI method (Option 2)
4. Check PostgreSQL logs for errors
