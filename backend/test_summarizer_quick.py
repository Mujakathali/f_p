"""
Quick test for summarization (works with or without Gemini)
"""
import sys
sys.path.insert(0, '.')

from datetime import datetime, timedelta
from utils.gemini_summarizer import gemini_summarizer

# Test data
test_memories = [
    {
        "id": 1,
        "type": "image",
        "raw_text": "Meeting with CEO for internship signing",
        "timestamp": (datetime.now() - timedelta(days=8)).isoformat(),
        "sentiments": [{"label": "positive", "score": 0.92}],
        "entities": [{"entity": "CEO", "type": "PERSON"}],
        "image_url": "/api/v1/images/ceo.jpg"
    },
    {
        "id": 2,
        "type": "text",
        "raw_text": "Had coffee with John at Starbucks to discuss the new AI project",
        "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
        "sentiments": [{"label": "positive", "score": 0.85}],
        "entities": [
            {"entity": "John", "type": "PERSON"},
            {"entity": "Starbucks", "type": "LOC"}
        ]
    }
]

print("🧪 Testing Summarization System\n")
print("=" * 70)

# Test initialization
print("\n1️⃣ Initializing summarizer...")
if gemini_summarizer.initialize():
    print("   ✅ Using Gemini AI")
else:
    print("   ⚠️ Using fallback (rule-based) summaries")

# Test search summary
print("\n2️⃣ Testing search summarization...")
print("-" * 70)

result = gemini_summarizer.summarize_search_results("meeting", test_memories)

print(f"\n📖 Summary:")
print(result['summary'])

print(f"\n📝 Individual Summaries:")
for i, mem in enumerate(result['memory_summaries'], 1):
    print(f"\n{i}. {mem['summary']}")
    if mem.get('image_url'):
        print(f"   🖼️ {mem['image_url']}")

print("\n" + "=" * 70)
print("✅ Test completed!")
print("\nℹ️ If Gemini is not working, the system automatically uses")
print("   high-quality rule-based summaries as fallback.\n")
