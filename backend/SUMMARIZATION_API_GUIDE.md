# Summarization API Guide

## Overview
The Summarization API transforms raw search results into human-friendly, conversational narratives. It's the core feature that makes your MemoryGraph AI feel natural and personal!

## Endpoints

### 1. `/api/v1/summarize_search` (POST)
Generate a narrative summary from search results.

**Request Body:**
```json
{
  "query": "ceo sign",
  "memories": [
    {
      "id": 45,
      "type": "image",
      "raw_text": "Meeting with CEO for internship signing",
      "timestamp": "2024-11-01T10:30:00",
      "sentiments": [{"label": "positive", "score": 0.9}],
      "entities": [{"entity": "CEO", "type": "PERSON"}],
      "image_url": "/api/v1/images/image_123.jpg"
    }
  ],
  "total_found": 1
}
```

**Response:**
```json
{
  "summary": "I found 1 memory matching 'ceo sign' (1 image):",
  "memory_summaries": [
    {
      "memory_id": 45,
      "type": "image",
      "summary": "You captured this image 8 days ago: \"Meeting with CEO for internship signing\". It seems to be a very happy moment.",
      "timestamp": "2024-11-01T10:30:00",
      "image_url": "/api/v1/images/image_123.jpg"
    }
  ],
  "total_found": 1,
  "query": "ceo sign"
}
```

### 2. `/api/v1/summarize_memory` (POST)
Generate a narrative summary for a single memory.

**Request Body:**
```json
{
  "id": 45,
  "type": "text",
  "raw_text": "Had an amazing meeting with John at the coffee shop. We discussed the new project and he seemed really excited about it!",
  "timestamp": "2024-11-05T14:30:00",
  "sentiments": [{"label": "positive", "score": 0.85}],
  "entities": [
    {"entity": "John", "type": "PERSON"},
    {"entity": "coffee shop", "type": "LOC"}
  ]
}
```

**Response:**
```json
{
  "memory_id": 45,
  "type": "text",
  "summary": "You recorded this 4 days ago with a positive tone (mentioning John, at coffee shop).\n\n\"Had an amazing meeting with John at the coffee shop. We discussed the new project and he seemed...\"",
  "timestamp": "2024-11-05T14:30:00",
  "image_url": null
}
```

## Features

### 🕐 Smart Time Formatting
- "today"
- "yesterday"
- "3 days ago"
- "2 weeks ago"
- "5 months ago"
- "1 year ago"

### 😊 Emotion Detection
Converts sentiment scores to natural language:
- **Positive (>0.8)**: "very happy"
- **Positive**: "positive"
- **Negative (>0.8)**: "quite emotional"
- **Negative**: "reflective"
- **Neutral**: "neutral"

### 🏷️ Entity Context
Automatically includes relevant entities:
- **People**: "mentioning John, Sarah"
- **Places**: "at coffee shop"
- **Organizations**: "related to Google"

### 📝 Memory Type Handling
Different narratives for different types:

**Text Memory:**
```
You recorded this 5 days ago with a positive tone (mentioning John, at coffee shop).

"Had an amazing meeting with John at the coffee shop..."
```

**Image Memory:**
```
You captured this image 2 weeks ago: "My graduation ceremony". It seems to be a very happy moment.
```

**Voice Memory:**
```
You recorded a voice note yesterday in a positive mood:

"Just finished the presentation and it went really well..."
```

## Integration Examples

### Frontend Integration (React)

```javascript
// After getting search results
const searchResults = await ApiService.searchMemories(query);

// Get summarized narrative
const summarized = await fetch('http://localhost:8000/api/v1/summarize_search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(searchResults)
});

const narrative = await summarized.json();

// Display to user
console.log(narrative.summary);
// "I found 3 memories matching 'birthday party' (2 images, 1 text memory):"

narrative.memory_summaries.forEach(mem => {
  console.log(mem.summary);
  // "You captured this image 3 months ago: 'Birthday celebration with friends'. It seems to be a very happy moment."
});
```

### Python Integration

```python
import requests

# Get search results
search_response = requests.get(
    "http://localhost:8000/api/v1/search_memories",
    params={"query": "vacation", "limit": 10}
)
search_data = search_response.json()

# Summarize results
summary_response = requests.post(
    "http://localhost:8000/api/v1/summarize_search",
    json=search_data
)
narrative = summary_response.json()

print(narrative['summary'])
for memory in narrative['memory_summaries']:
    print(f"\n{memory['summary']}")
```

## Use Cases

### 1. Search Results Display
Transform technical search results into conversational narratives for better UX.

### 2. Memory Timeline
Generate story-like descriptions for memory timelines.

### 3. Daily Recap
Create daily/weekly summaries: "This week you captured 5 memories..."

### 4. Memory Sharing
Generate shareable narratives: "On this day 1 year ago, you..."

### 5. Voice Assistant Integration
Perfect for voice-based memory recall: "Tell me about my meeting with John"

## Benefits

✅ **Natural Language** - Feels like talking to a friend  
✅ **Context-Aware** - Includes time, emotion, and entities  
✅ **Type-Specific** - Different narratives for text/image/voice  
✅ **Scalable** - Handles single or multiple memories  
✅ **Frontend-Ready** - JSON responses easy to display  

## Testing

```bash
# Start backend
cd d:\final_year_project\backend
python -m backend.start_server

# Test summarization endpoint
curl -X POST http://localhost:8000/api/v1/summarize_search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test",
    "memories": [{
      "id": 1,
      "type": "text",
      "raw_text": "Test memory",
      "timestamp": "2024-11-09T10:00:00",
      "sentiments": [{"label": "positive", "score": 0.8}],
      "entities": []
    }],
    "total_found": 1
  }'
```

## Next Steps

1. **Restart backend** to load the new API
2. **Update frontend** to call summarization after search
3. **Display narratives** instead of raw JSON
4. **Test with real memories** to see natural language output

Your MemoryGraph AI now speaks like a human! 🎉
