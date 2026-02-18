"""
Test Gemini AI Summarization
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, '.')

from utils.gemini_summarizer import gemini_summarizer

# Test data
test_memory = {
    "id": 1,
    "type": "image",
    "raw_text": "Meeting with CEO for internship signing ceremony at the company headquarters",
    "timestamp": (datetime.now() - timedelta(days=8)).isoformat(),
    "sentiments": [{"label": "positive", "score": 0.92, "confidence": 0.92}],
    "entities": [
        {"entity": "CEO", "type": "PERSON", "confidence": 0.95},
        {"entity": "company headquarters", "type": "LOC", "confidence": 0.88}
    ],
    "image_url": "/api/v1/images/ceo_meeting.jpg"
}

def test_gemini():
    print("🧪 Testing Gemini AI Summarization\n")
    print("=" * 70)
    
    # Initialize
    print("\n1️⃣ Initializing Gemini...")
    if gemini_summarizer.initialize():
        print("   ✅ Gemini initialized successfully!")
    else:
        print("   ❌ Failed to initialize Gemini")
        return
    
    # Test single memory summarization
    print("\n2️⃣ Testing single memory summarization...")
    print("-" * 70)
    print(f"Input: {test_memory['raw_text']}")
    print(f"Type: {test_memory['type']}")
    print(f"Time: 8 days ago")
    print(f"Sentiment: positive (0.92)")
    print("\n🤖 Gemini's Summary:")
    print("-" * 70)
    
    summary = gemini_summarizer.summarize_memory(test_memory)
    print(summary)
    
    # Test search results summarization
    print("\n\n3️⃣ Testing search results summarization...")
    print("-" * 70)
    
    test_memories = [
        test_memory,
        {
            "id": 2,
            "type": "text",
            "raw_text": "Had a productive meeting with John at Starbucks discussing the new AI project. He's really excited about the possibilities!",
            "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
            "sentiments": [{"label": "positive", "score": 0.85, "confidence": 0.85}],
            "entities": [
                {"entity": "John", "type": "PERSON", "confidence": 0.98},
                {"entity": "Starbucks", "type": "LOC", "confidence": 0.92}
            ]
        }
    ]
    
    result = gemini_summarizer.summarize_search_results("meeting", test_memories)
    
    print(f"\n📖 Search Summary:")
    print("-" * 70)
    print(result['summary'])
    
    print(f"\n📝 Individual Memory Summaries:")
    print("-" * 70)
    for i, mem_summary in enumerate(result['memory_summaries'], 1):
        print(f"\n{i}. {mem_summary['summary']}")
        if mem_summary.get('image_url'):
            print(f"   🖼️ Image: {mem_summary['image_url']}")
    
    print("\n" + "=" * 70)
    print("✅ All tests completed!\n")
    
    print("💡 Gemini AI is now generating natural, conversational summaries!")
    print("   - More creative and varied than rule-based templates")
    print("   - Understands context and emotions better")
    print("   - Produces human-like narratives\n")

if __name__ == "__main__":
    test_gemini()
