"""
Quick test to verify image URLs are included in search results
"""
import asyncio
import sys
sys.path.insert(0, '.')

from routes.memory_routes import _hybrid_rank_results

async def test_image_url():
    # Mock image result
    mock_image_result = {
        "id": 1,
        "type": "image",
        "raw_text": "Internship logo",
        "processed_text": "internship logo",
        "metadata": {
            "filename": "test_image.jpg",
            "image_path": "./stored_images/test_image.jpg"
        }
    }
    
    # Test hybrid ranking
    results = await _hybrid_rank_results([], [], [mock_image_result], "internship", 10)
    
    print("Test Results:")
    for result in results:
        print(f"  ID: {result['id']}")
        print(f"  Type: {result['type']}")
        print(f"  Filename: {result.get('filename', 'N/A')}")
        print(f"  Image Path: {result.get('image_path', 'N/A')}")
        print()
    
    print("✅ Image URL fix ready to test!")
    print("🔄 Restart your backend server and search for your internship images")

if __name__ == "__main__":
    asyncio.run(test_image_url())
