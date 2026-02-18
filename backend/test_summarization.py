"""
Test script for Summarization API
"""
import asyncio
import sys
from datetime import datetime, timedelta

# Test data
sample_memories = [
    {
        "id": 1,
        "type": "image",
        "raw_text": "Meeting with CEO for internship signing ceremony",
        "timestamp": (datetime.now() - timedelta(days=8)).isoformat(),
        "sentiments": [{"label": "positive", "score": 0.9, "confidence": 0.9}],
        "entities": [
            {"entity": "CEO", "type": "PERSON", "confidence": 0.95}
        ],
        "image_url": "/api/v1/images/ceo_meeting.jpg"
    },
    {
        "id": 2,
        "type": "text",
        "raw_text": "Had an amazing coffee meeting with John at Starbucks. We discussed the new AI project and he was really excited about the possibilities. Can't wait to start working on it!",
        "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
        "sentiments": [{"label": "positive", "score": 0.85, "confidence": 0.85}],
        "entities": [
            {"entity": "John", "type": "PERSON", "confidence": 0.98},
            {"entity": "Starbucks", "type": "LOC", "confidence": 0.92},
            {"entity": "AI project", "type": "ORG", "confidence": 0.75}
        ]
    },
    {
        "id": 3,
        "type": "voice",
        "raw_text": "Just finished my presentation at the conference. It went really well and got great feedback from the audience. Feeling proud!",
        "timestamp": (datetime.now() - timedelta(hours=5)).isoformat(),
        "sentiments": [{"label": "positive", "score": 0.92, "confidence": 0.92}],
        "entities": [
            {"entity": "conference", "type": "LOC", "confidence": 0.80}
        ]
    }
]

async def test_summarization():
    """Test the summarization functions"""
    print("🧪 Testing Summarization API\n")
    print("=" * 60)
    
    # Import the summarization module
    sys.path.insert(0, '.')
    from routes.summarization_routes import (
        summarize_text_memory,
        summarize_image_memory,
        summarize_voice_memory,
        format_date
    )
    
    # Test 1: Format date
    print("\n📅 Test 1: Date Formatting")
    print("-" * 60)
    for days_ago in [0, 1, 3, 10, 45, 400]:
        test_date = datetime.now() - timedelta(days=days_ago)
        formatted = format_date(test_date.isoformat())
        print(f"  {days_ago} days ago → '{formatted}'")
    
    # Test 2: Individual memory summaries
    print("\n📝 Test 2: Individual Memory Summaries")
    print("-" * 60)
    
    print("\n🖼️ Image Memory:")
    image_summary = summarize_image_memory(sample_memories[0])
    print(f"  {image_summary}")
    
    print("\n📄 Text Memory:")
    text_summary = summarize_text_memory(sample_memories[1])
    print(f"  {text_summary}")
    
    print("\n🎤 Voice Memory:")
    voice_summary = summarize_voice_memory(sample_memories[2])
    print(f"  {voice_summary}")
    
    # Test 3: Full search summarization
    print("\n\n🔍 Test 3: Full Search Summarization")
    print("-" * 60)
    
    search_request = {
        "query": "meeting project",
        "memories": sample_memories,
        "total_found": len(sample_memories)
    }
    
    # Manually build the summary (simulating the API endpoint)
    query = search_request['query']
    memories = search_request['memories']
    
    # Count types
    memory_types = {}
    for memory in memories:
        mem_type = memory.get('type', 'text')
        memory_types[mem_type] = memory_types.get(mem_type, 0) + 1
    
    # Build intro
    type_text = []
    if memory_types.get('image'):
        type_text.append(f"{memory_types['image']} image{'s' if memory_types['image'] > 1 else ''}")
    if memory_types.get('text'):
        type_text.append(f"{memory_types['text']} text memor{'ies' if memory_types['text'] > 1 else 'y'}")
    if memory_types.get('voice'):
        type_text.append(f"{memory_types['voice']} voice note{'s' if memory_types['voice'] > 1 else ''}")
    
    intro = f"I found {len(memories)} memories matching '{query}'"
    if type_text:
        intro += f" ({', '.join(type_text)})"
    intro += ":"
    
    print(f"\n📖 {intro}\n")
    
    # Print each summary
    for i, memory in enumerate(memories, 1):
        mem_type = memory.get('type', 'text')
        
        if mem_type == 'image':
            summary = summarize_image_memory(memory)
        elif mem_type == 'voice':
            summary = summarize_voice_memory(memory)
        else:
            summary = summarize_text_memory(memory)
        
        print(f"\n{i}. {summary}")
        if memory.get('image_url'):
            print(f"   🖼️ Image: {memory['image_url']}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!\n")
    
    print("💡 To test the actual API endpoint:")
    print("   1. Start the backend: python -m backend.start_server")
    print("   2. Use curl or Postman to POST to /api/v1/summarize_search")
    print("   3. Or integrate into your frontend using the example code\n")

if __name__ == "__main__":
    asyncio.run(test_summarization())
