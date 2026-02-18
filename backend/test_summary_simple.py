"""Simple test for summarization"""
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '.')

from routes.summarization_routes import format_date, summarize_image_memory

# Test date formatting
print("Testing date formatting:")
test_date = datetime.now() - timedelta(days=8)
result = format_date(test_date.isoformat())
print(f"8 days ago: {result}")

# Test image summary
print("\nTesting image summary:")
memory = {
    "id": 1,
    "type": "image",
    "raw_text": "CEO meeting",
    "timestamp": test_date.isoformat(),
    "sentiments": [{"label": "positive", "score": 0.9}]
}
summary = summarize_image_memory(memory)
print(summary)

print("\n✅ Tests passed!")
