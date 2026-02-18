# 🔧 Frontend-Backend Connection Fix Guide

## 🚨 Problem: Storing & Searching Not Working

The issue is that the backend now requires authentication for all memory operations, but there might be connection or authentication issues.

## ✅ Step-by-Step Fix

### Step 1: Run the Database Migration (CRITICAL!)

**The backend won't start without this:**

```bash
cd d:\final_year_project\backend
python migrate_now.py
```

**OR use pgAdmin:**
```sql
ALTER TABLE memories ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
CREATE INDEX idx_memories_user_id ON memories(user_id);
UPDATE memories SET user_id = (SELECT id FROM users ORDER BY id LIMIT 1) WHERE user_id IS NULL;
```

### Step 2: Start Backend Server

```bash
cd d:\final_year_project\backend
python app.py
```

**You should see:**
```
✅ PostgreSQL connected successfully
✅ Neo4j connected successfully
✅ Authentication system initialized
✅ Backend services initialized successfully
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**If you see errors:**
- ❌ `column "user_id" does not exist` → Run Step 1 migration
- ❌ `Connection refused` → Check PostgreSQL is running
- ❌ `Authentication failed` → Check `.env` credentials

### Step 3: Start Frontend Server

```bash
cd d:\final_year_project\second_brain
npm start
```

**Should open:** `http://localhost:3000`

### Step 4: Test the Flow

1. **Register a New User:**
   - Go to `http://localhost:3000/signup`
   - Create account: username, email, password
   - Should redirect to login

2. **Login:**
   - Go to `http://localhost:3000/login`
   - Enter credentials
   - Should see welcome toast
   - Should redirect to `/chat`

3. **Test Storing Memory:**
   - Type: "I met John at the coffee shop today"
   - Press Send
   - Should see: "✅ Memory stored successfully!"

4. **Test Searching:**
   - Type: "What do I know about John?"
   - Should see related memories

## 🔍 Debugging Steps

### Check 1: Is Backend Running?

Open browser: `http://localhost:8000/docs`

Should see FastAPI Swagger documentation.

### Check 2: Is Authentication Working?

**Open Browser Console (F12) → Console tab**

After login, check:
```javascript
localStorage.getItem('access_token')
```

Should return a JWT token (long string).

**If null:**
- Login failed
- Check backend logs for errors
- Verify user exists in database

### Check 3: Are API Calls Working?

**In Browser Console:**
```javascript
// Test health check
fetch('http://localhost:8000/api/v1/health')
  .then(r => r.json())
  .then(console.log)
```

Should return: `{"status": "healthy"}`

**Test authenticated endpoint:**
```javascript
const token = localStorage.getItem('access_token');
fetch('http://localhost:8000/api/v1/add_memory', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    text: "Test memory",
    metadata: {}
  })
})
.then(r => r.json())
.then(console.log)
.catch(console.error)
```

**Expected:** Memory object with ID
**If 401:** Token is invalid or expired
**If 422:** Request format is wrong
**If 500:** Backend error (check backend logs)

### Check 4: Network Requests

**In Browser (F12) → Network tab:**

1. Type a message in chat
2. Look for request to `add_memory`
3. Click on it
4. Check:
   - **Status:** Should be 200
   - **Headers:** Should have `Authorization: Bearer ...`
   - **Response:** Should have memory data

**Common Issues:**

- **Status 401:** Not authenticated
  - Solution: Logout and login again
  
- **Status 422:** Invalid request format
  - Solution: Check backend expects `{text, metadata}`
  
- **Status 500:** Backend error
  - Solution: Check backend terminal for error logs
  
- **CORS Error:** 
  - Solution: Check backend CORS settings in `app.py`

## 🔧 Common Fixes

### Fix 1: Token Not Being Sent

**Check `src/services/api.js`:**
```javascript
getAuthToken() {
  return localStorage.getItem('access_token');
}

getAuthHeaders() {
  const token = this.getAuthToken();
  if (token) {
    return {
      'Authorization': `Bearer ${token}`
    };
  }
  return {};
}
```

### Fix 2: CORS Issues

**Check `backend/app.py`:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Fix 3: Backend Not Accepting Requests

**Check backend routes are registered:**
```python
# In app.py
app.include_router(memory_router, prefix="/api/v1", tags=["memories"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
```

### Fix 4: Database Connection Issues

**Check `.env` file:**
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=memorygraph_ai
POSTGRES_USER=postgres
POSTGRES_PASSWORD=iammuja008
```

**Test PostgreSQL connection:**
```bash
psql -U postgres -d memorygraph_ai -c "SELECT COUNT(*) FROM users;"
```

## 📋 Checklist

- [ ] Database migration completed (user_id column exists)
- [ ] Backend server running on port 8000
- [ ] Frontend server running on port 3000
- [ ] PostgreSQL service is running
- [ ] Neo4j service is running
- [ ] User can register successfully
- [ ] User can login successfully
- [ ] JWT token is stored in localStorage
- [ ] API calls include Authorization header
- [ ] Backend accepts authenticated requests
- [ ] Memories are being stored
- [ ] Search is returning results

## 🎯 Quick Test Script

**Save as `test_frontend_backend.js` and run in browser console:**

```javascript
async function testSystem() {
  console.log('🧪 Testing Frontend-Backend Connection...\n');
  
  // Test 1: Backend Health
  console.log('1️⃣ Testing backend health...');
  try {
    const health = await fetch('http://localhost:8000/api/v1/health').then(r => r.json());
    console.log('✅ Backend is healthy:', health);
  } catch (e) {
    console.error('❌ Backend health check failed:', e);
    return;
  }
  
  // Test 2: Check Token
  console.log('\n2️⃣ Checking authentication token...');
  const token = localStorage.getItem('access_token');
  if (token) {
    console.log('✅ Token found:', token.substring(0, 20) + '...');
  } else {
    console.error('❌ No token found - please login first');
    return;
  }
  
  // Test 3: Test Authenticated Request
  console.log('\n3️⃣ Testing authenticated memory creation...');
  try {
    const response = await fetch('http://localhost:8000/api/v1/add_memory', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        text: 'Test memory from browser console',
        metadata: { source: 'test' }
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Memory created successfully:', data);
    } else {
      console.error('❌ Memory creation failed:', response.status, await response.text());
    }
  } catch (e) {
    console.error('❌ Request failed:', e);
  }
  
  // Test 4: Test Search
  console.log('\n4️⃣ Testing memory search...');
  try {
    const response = await fetch('http://localhost:8000/api/v1/search_memories?query=test&limit=5', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Search successful:', data);
    } else {
      console.error('❌ Search failed:', response.status);
    }
  } catch (e) {
    console.error('❌ Search request failed:', e);
  }
  
  console.log('\n✅ Testing complete!');
}

testSystem();
```

## 🆘 Still Not Working?

1. **Clear browser cache and localStorage:**
   ```javascript
   localStorage.clear();
   location.reload();
   ```

2. **Restart both servers:**
   - Stop backend (Ctrl+C)
   - Stop frontend (Ctrl+C)
   - Start backend first
   - Then start frontend

3. **Check backend logs** for specific errors

4. **Check browser console** for JavaScript errors

5. **Verify database has users:**
   ```sql
   SELECT * FROM users;
   ```

6. **Verify memories table has user_id column:**
   ```sql
   \d memories
   ```

## 📝 Files Updated

- ✅ `src/services/api.js` - Fixed FormData auth headers
- ✅ `backend/routes/memory_routes.py` - Added authentication
- ✅ `backend/db/postgresql_connector.py` - Added user_id support
- ✅ `backend/migrate_now.py` - Migration script created

## 🎉 Success Indicators

When everything works, you should see:

**Backend Terminal:**
```
🔍 Processing memory for user 1: I met John today
📊 NLP Results: sentiment=POSITIVE, entities=1
✅ Memory stored with ID: 42
```

**Frontend:**
- Messages send successfully
- "✅ Memory stored successfully!" appears
- Search returns relevant results
- No 401 errors in console
- No CORS errors in console
