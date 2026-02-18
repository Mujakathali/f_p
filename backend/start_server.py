#!/usr/bin/env python3
"""
Simple server starter script to debug backend issues
"""
import uvicorn
import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    print("🚀 Starting MemoryGraph Backend Server...")
    print("📍 Current directory:", os.getcwd())
    print("🐍 Python path:", sys.path[0])
    
    # Import the app
    from app import app
    print("✅ App imported successfully")
    
    # Start the server
    print("🌐 Starting server on http://localhost:8000")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info",
        reload=True
    )
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📦 Available modules:")
    import pkgutil
    for importer, modname, ispkg in pkgutil.iter_modules():
        if 'fastapi' in modname or 'uvicorn' in modname:
            print(f"  - {modname}")
            
except Exception as e:
    print(f"❌ Server startup failed: {e}")
    import traceback
    traceback.print_exc()
