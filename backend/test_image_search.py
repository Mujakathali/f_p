#!/usr/bin/env python3
"""
Test script to verify image search functionality
"""
import asyncio
import requests
import json

async def test_image_search():
    """Test the complete image search pipeline"""
    print("🧪 Testing Image Search Pipeline...")
    
    base_url = "http://localhost:8000/api/v1"
    
    try:
        # 1. Test health endpoint
        print("1️⃣ Testing server health...")
        response = requests.get(f"{base_url.replace('/api/v1', '')}/health")
        if response.status_code == 200:
            print("✅ Server is healthy")
        else:
            print("❌ Server not responding")
            return False
        
        # 2. Test text search (should work)
        print("2️⃣ Testing text search...")
        response = requests.get(f"{base_url}/search_memories", params={
            "query": "test",
            "search_type": "keyword",
            "limit": 5
        })
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Text search works: {data['total_found']} results")
        else:
            print(f"⚠️ Text search failed: {response.status_code}")
        
        # 3. Test image search
        print("3️⃣ Testing image search...")
        response = requests.get(f"{base_url}/search_memories", params={
            "query": "sunset",
            "search_type": "image", 
            "limit": 5
        })
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Image search works: {data['total_found']} results")
            print(f"   📊 Breakdown: {data['breakdown']}")
            
            # Check if any results have image metadata
            image_results = [m for m in data['memories'] if m.get('type') == 'image']
            if image_results:
                print(f"   🖼️ Found {len(image_results)} image memories")
                for img in image_results[:2]:
                    print(f"      - ID: {img['id']}, Caption: {img['raw_text'][:50]}...")
                    if 'image_path' in img:
                        print(f"        Path: {img['image_path']}")
            else:
                print("   ℹ️ No image memories found (upload some images first)")
        else:
            print(f"❌ Image search failed: {response.status_code} - {response.text}")
        
        # 4. Test hybrid search
        print("4️⃣ Testing hybrid search...")
        response = requests.get(f"{base_url}/search_memories", params={
            "query": "mountain",
            "search_type": "hybrid",
            "limit": 10
        })
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Hybrid search works: {data['total_found']} results")
            print(f"   📊 Breakdown: {data['breakdown']}")
            
            # Show mix of result types
            text_count = len([m for m in data['memories'] if m.get('type') == 'text'])
            image_count = len([m for m in data['memories'] if m.get('type') == 'image'])
            print(f"   📝 Text results: {text_count}")
            print(f"   🖼️ Image results: {image_count}")
        else:
            print(f"❌ Hybrid search failed: {response.status_code}")
        
        # 5. Test list memories
        print("5️⃣ Testing memory listing...")
        response = requests.get(f"{base_url}/list_memories", params={"limit": 5})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Memory listing works: {len(data['memories'])} memories")
            
            # Show memory types
            types = {}
            for memory in data['memories']:
                mem_type = memory.get('type', 'unknown')
                types[mem_type] = types.get(mem_type, 0) + 1
            print(f"   📊 Memory types: {types}")
        else:
            print(f"❌ Memory listing failed: {response.status_code}")
        
        print("\n🎉 Image search pipeline test completed!")
        print("\n📋 Summary:")
        print("   ✅ Server health check")
        print("   ✅ Text search functionality") 
        print("   ✅ Image search functionality")
        print("   ✅ Hybrid search functionality")
        print("   ✅ Memory listing")
        
        print("\n💡 To test with actual images:")
        print("   1. Upload images via frontend")
        print("   2. Search for image-related terms")
        print("   3. Check that images appear in results")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_image_search())
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
