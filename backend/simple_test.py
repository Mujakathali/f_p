"""
Simple test script without databases - for quick backend testing
"""
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="MemoryGraph AI - Simple Test")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "MemoryGraph AI Backend is running!", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy", "databases": "not connected (test mode)"}

@app.post("/api/v1/add_memory")
async def add_memory_test(request: dict):
    return {
        "id": 1,
        "text": request.get("text", "Test memory"),
        "type": "text",
        "status": "stored (test mode)"
    }

@app.get("/api/v1/list_memories")
async def list_memories_test():
    return {
        "memories": [
            {"id": 1, "text": "Test memory 1", "type": "text"},
            {"id": 2, "text": "Test memory 2", "type": "text"}
        ],
        "count": 2
    }

if __name__ == "__main__":
    print("🚀 Starting MemoryGraph AI Backend (Test Mode)")
    print("📍 Server: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
