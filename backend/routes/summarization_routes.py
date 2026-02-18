"""
Summarization API Routes - Generate human-friendly narratives from search results
Uses Gemini AI for natural language generation
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.gemini_summarizer import gemini_summarizer

summarization_router = APIRouter()

def format_date(timestamp) -> str:
    """Format timestamp to human-readable date"""
    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        now = datetime.now()
        diff = now - dt.replace(tzinfo=None)
        
        # Relative time formatting
        if diff.days == 0:
            return "today"
        elif diff.days == 1:
            return "yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        elif diff.days < 365:
            months = diff.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = diff.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
    except:
        return "some time ago"

def get_emotion_text(sentiment) -> str:
    """Convert sentiment to emotion text"""
    if not sentiment:
        return "neutral"
    
    if isinstance(sentiment, list) and len(sentiment) > 0:
        sentiment = sentiment[0]
    
    label = sentiment.get('label', 'neutral').lower()
    score = sentiment.get('score', 0.5)
    
    if label in ['positive', 'joy', 'happy']:
        if score > 0.8:
            return "very happy"
        return "positive"
    elif label in ['negative', 'sad', 'angry']:
        if score > 0.8:
            return "quite emotional"
        return "reflective"
    else:
        return "neutral"

def summarize_text_memory(memory: Dict) -> str:
    """Generate summary for text memory"""
    text = memory.get('raw_text', '')
    timestamp = memory.get('timestamp')
    sentiment = memory.get('sentiments')
    entities = memory.get('entities', [])
    
    # Build summary
    time_text = format_date(timestamp)
    emotion_text = get_emotion_text(sentiment)
    
    # Extract key entities
    people = []
    places = []
    orgs = []
    
    if isinstance(entities, list):
        for entity in entities:
            entity_type = entity.get('type', '').upper()
            entity_text = entity.get('entity', '')
            
            if entity_type == 'PERSON' and entity_text:
                people.append(entity_text)
            elif entity_type in ['GPE', 'LOC'] and entity_text:
                places.append(entity_text)
            elif entity_type == 'ORG' and entity_text:
                orgs.append(entity_text)
    
    # Build narrative
    summary_parts = []
    
    # Time context
    summary_parts.append(f"You recorded this {time_text}")
    
    # Emotion context
    if emotion_text != "neutral":
        summary_parts.append(f"with a {emotion_text} tone")
    
    # Entity context
    context_parts = []
    if people:
        context_parts.append(f"mentioning {', '.join(people[:2])}")
    if places:
        context_parts.append(f"at {places[0]}")
    if orgs:
        context_parts.append(f"related to {orgs[0]}")
    
    if context_parts:
        summary_parts.append(f"({', '.join(context_parts)})")
    
    # Add snippet of the text
    text_snippet = text[:100] + "..." if len(text) > 100 else text
    
    summary = f"{'. '.join(summary_parts)}.\n\n\"{text_snippet}\""
    
    return summary

def summarize_image_memory(memory: Dict) -> str:
    """Generate summary for image memory"""
    caption = memory.get('raw_text', 'an image')
    timestamp = memory.get('timestamp')
    sentiment = memory.get('sentiments')
    
    time_text = format_date(timestamp)
    emotion_text = get_emotion_text(sentiment)
    
    # Build narrative for image
    summary = f"You captured this image {time_text}"
    
    if caption and caption.lower() != 'image':
        summary += f": \"{caption}\""
    
    if emotion_text != "neutral":
        summary += f". It seems to be a {emotion_text} moment"
    
    summary += "."
    
    return summary

def summarize_voice_memory(memory: Dict) -> str:
    """Generate summary for voice memory"""
    text = memory.get('raw_text', '')
    timestamp = memory.get('timestamp')
    sentiment = memory.get('sentiments')
    
    time_text = format_date(timestamp)
    emotion_text = get_emotion_text(sentiment)
    
    summary = f"You recorded a voice note {time_text}"
    
    if emotion_text != "neutral":
        summary += f" in a {emotion_text} mood"
    
    if text:
        text_snippet = text[:100] + "..." if len(text) > 100 else text
        summary += f":\n\n\"{text_snippet}\""
    
    return summary

@summarization_router.post("/summarize_search")
async def summarize_search_results(request: Dict[str, Any]):
    """
    Generate a human-friendly summary of search results using Gemini AI
    
    Request body:
    {
        "query": "search query",
        "memories": [list of memory objects],
        "total_found": number
    }
    """
    try:
        query = request.get('query', '')
        memories = request.get('memories', [])
        total_found = request.get('total_found', len(memories))
        
        if not memories:
            return {
                "summary": f"I couldn't find any memories matching '{query}'. Try a different search term or add more memories!",
                "memory_summaries": [],
                "total_found": 0,
                "query": query
            }
        
        # Use Gemini AI to generate summaries
        print(f"🤖 Using Gemini AI to summarize {len(memories)} memories for query: '{query}'")
        result = gemini_summarizer.summarize_search_results(query, memories)
        
        return result
        
    except Exception as e:
        print(f"❌ Summarization error: {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

@summarization_router.post("/summarize_memory")
async def summarize_single_memory(memory: Dict[str, Any]):
    """
    Generate a human-friendly summary of a single memory using Gemini AI
    """
    try:
        print(f"🤖 Using Gemini AI to summarize memory {memory.get('id')}")
        summary = gemini_summarizer.summarize_memory(memory)
        
        return {
            "memory_id": memory.get('id'),
            "type": memory.get('type', 'text'),
            "summary": summary,
            "timestamp": memory.get('timestamp'),
            "image_url": memory.get('image_url')
        }
        
    except Exception as e:
        print(f"❌ Memory summarization error: {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")
