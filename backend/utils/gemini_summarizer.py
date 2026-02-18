"""
Gemini AI-powered summarization for memories
"""
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai not installed. Run: pip install google-generativeai")

import os
from typing import Dict, List, Any
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GeminiSummarizer:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model = None
        self.is_initialized = False
        self.gemini_available = GEMINI_AVAILABLE
        
    def initialize(self):
        """Initialize Gemini API"""
        try:
            if not self.gemini_available:
                print("⚠️ Gemini package not available, using fallback summaries")
                return False
                
            if not self.api_key:
                print("⚠️ GEMINI_API_KEY not found in environment, using fallback summaries")
                print(f"   Current API key value: {self.api_key}")
                return False
                
            genai.configure(api_key=self.api_key)
            # Use gemini-2.5-flash (latest model)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            self.is_initialized = True
            print("✅ Gemini AI initialized successfully (gemini-2.0-flash-exp)")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Gemini: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def format_date(self, timestamp) -> str:
        """Format timestamp to human-readable date"""
        try:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = timestamp
            
            now = datetime.now()
            diff = now - dt.replace(tzinfo=None)
            
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
    
    def summarize_memory(self, memory: Dict) -> str:
        """Generate AI-powered summary for a single memory"""
        if not self.is_initialized:
            if not self.initialize():
                return self._fallback_summary(memory)
        
        try:
            mem_type = memory.get('type', 'text')
            raw_text = memory.get('raw_text', '')
            timestamp = memory.get('timestamp')
            sentiments = memory.get('sentiments', [])
            entities = memory.get('entities', [])
            
            # Format time
            time_text = self.format_date(timestamp)
            
            # Extract entity info
            people = [e.get('entity', '') for e in entities if e.get('type', '').upper() == 'PERSON']
            places = [e.get('entity', '') for e in entities if e.get('type', '').upper() in ['GPE', 'LOC']]
            orgs = [e.get('entity', '') for e in entities if e.get('type', '').upper() == 'ORG']
            
            # Get sentiment
            sentiment_label = sentiments[0].get('label', 'neutral') if sentiments else 'neutral'
            sentiment_score = sentiments[0].get('score', 0.5) if sentiments else 0.5
            
            # Build prompt for detailed 2-3 sentence summary
            prompt = f"""Create a detailed, comprehensive summary of this memory in 2-3 full sentences (40-50 words).

Memory Type: {mem_type}
Time: {time_text}
Content: "{raw_text}"
Emotion: {sentiment_label} (confidence: {sentiment_score:.2f})
People: {', '.join(people) if people else 'none'}
Places: {', '.join(places) if places else 'none'}
Organizations: {', '.join(orgs) if orgs else 'none'}

Requirements:
- Write 2-3 complete sentences (40-50 words total)
- Professional but conversational tone
- First sentence: What happened, when, and where
- Second sentence: Key details, people involved, and specific actions or outcomes
- Third sentence (if needed): Why it matters, emotional context, or future implications
- Always start with "You"
- Include specific details from the content
- For text memories: Include relevant quotes or key phrases
- For image memories: Describe what's visible and its significance
- Make it feel personal and meaningful

Example for text memory:
"You had an in-depth discussion with the engineering team last Tuesday afternoon about the new API architecture and scalability challenges. The conversation covered microservices design patterns, database optimization strategies, and deployment pipelines, with John and Sarah providing valuable insights on handling high-traffic scenarios. This technical deep-dive helped clarify the roadmap for the next quarter's infrastructure improvements."

Example for image memory:
"You captured this memorable photo during your college graduation ceremony on campus last month, showing you with your classmates celebrating the completion of your degree. The image features you in your graduation gown standing with your best friends near the main auditorium, all smiling and holding diplomas after four years of hard work. This moment marked a significant milestone in your academic journey and the beginning of your professional career."

Now create a detailed 2-3 sentence summary:"""

            # Generate summary
            response = self.model.generate_content(prompt)
            summary = response.text.strip()
            
            print(f"✨ Gemini generated summary for memory {memory.get('id')}")
            return summary
            
        except Exception as e:
            print(f"⚠️ Gemini summarization failed: {e}, using fallback")
            return self._fallback_summary(memory)
    
    def summarize_search_results(self, query: str, memories: List[Dict]) -> Dict[str, Any]:
        """Generate AI-powered summary for search results"""
        if not self.is_initialized:
            if not self.initialize():
                return self._fallback_search_summary(query, memories)
        
        try:
            # Count memory types
            memory_types = {}
            for memory in memories:
                mem_type = memory.get('type', 'text')
                memory_types[mem_type] = memory_types.get(mem_type, 0) + 1
            
            # Build type description
            type_parts = []
            if memory_types.get('image'):
                type_parts.append(f"{memory_types['image']} image{'s' if memory_types['image'] > 1 else ''}")
            if memory_types.get('text'):
                type_parts.append(f"{memory_types['text']} text memor{'ies' if memory_types['text'] > 1 else 'y'}")
            if memory_types.get('voice'):
                type_parts.append(f"{memory_types['voice']} voice note{'s' if memory_types['voice'] > 1 else ''}")
            
            type_text = ', '.join(type_parts) if type_parts else 'memories'
            
            # Create intro prompt
            intro_prompt = f"""Create a professional, concise introduction for search results.

Query: "{query}"
Found: {len(memories)} memories ({type_text})

Create a professional 1-sentence introduction that summarizes what was found.

Examples:
- "Found 3 relevant memories related to your birthday celebration, including 2 images and 1 text entry."
- "Retrieved 5 memories documenting your coffee meetings from recent months."

Now create an introduction:"""

            intro_response = self.model.generate_content(intro_prompt)
            intro = intro_response.text.strip()
            
            # Generate individual summaries
            memory_summaries = []
            for memory in memories:
                try:
                    summary = self.summarize_memory(memory)
                    memory_summaries.append({
                        "memory_id": memory.get('id'),
                        "type": memory.get('type'),
                        "summary": summary,
                        "timestamp": memory.get('timestamp'),
                        "image_url": memory.get('image_url')
                    })
                except Exception as mem_error:
                    print(f"⚠️ Error summarizing memory {memory.get('id')}: {mem_error}")
                    # Use fallback for this specific memory
                    summary = self._fallback_summary(memory)
                    memory_summaries.append({
                        "memory_id": memory.get('id'),
                        "type": memory.get('type'),
                        "summary": summary,
                        "timestamp": memory.get('timestamp'),
                        "image_url": memory.get('image_url')
                    })
            
            print(f"✨ Gemini generated search summary for {len(memories)} memories")
            
            return {
                "summary": intro,
                "memory_summaries": memory_summaries,
                "total_found": len(memories),
                "query": query
            }
            
        except Exception as e:
            print(f"⚠️ Gemini search summarization failed: {e}, using fallback")
            return self._fallback_search_summary(query, memories)
    
    def _fallback_summary(self, memory: Dict) -> str:
        """Fallback to rule-based summary if Gemini fails"""
        try:
            # Ensure memory is a dict
            if not isinstance(memory, dict):
                print(f"⚠️ Memory is not a dict: {type(memory)}")
                return "Unable to summarize this memory."
            
            mem_type = memory.get('type', 'text')
            raw_text = memory.get('raw_text', '')
            timestamp = memory.get('timestamp')
            
            # Handle sentiments (can be list or JSON string)
            sentiments = memory.get('sentiments', [])
            if isinstance(sentiments, str):
                import json
                try:
                    sentiments = json.loads(sentiments)
                except:
                    sentiments = []
            if not isinstance(sentiments, list):
                sentiments = []
            
            # Handle entities (can be list or JSON string)
            entities = memory.get('entities', [])
            if isinstance(entities, str):
                import json
                try:
                    entities = json.loads(entities)
                except:
                    entities = []
            if not isinstance(entities, list):
                entities = []
            
            time_text = self.format_date(timestamp)
            
            # Get emotion
            emotion = "neutral"
            if sentiments and len(sentiments) > 0:
                sentiment = sentiments[0]
                if isinstance(sentiment, dict):
                    label = sentiment.get('label', 'neutral').lower()
                    score = sentiment.get('score', 0.5)
                    if label in ['positive', 'joy', 'happy']:
                        emotion = "very happy" if score > 0.8 else "positive"
                    elif label in ['negative', 'sad', 'angry']:
                        emotion = "reflective" if score > 0.8 else "thoughtful"
            
            # Get key entities
            people = []
            places = []
            if entities:
                for e in entities:
                    if isinstance(e, dict):
                        entity_type = e.get('type', '').upper()
                        if entity_type == 'PERSON' and len(people) < 2:
                            people.append(e.get('entity', ''))
                        elif entity_type in ['GPE', 'LOC'] and len(places) < 1:
                            places.append(e.get('entity', ''))
            
            # Build detailed 2-3 sentence summary
            if mem_type == 'image':
                # Sentence 1: What and when
                summary = f"You captured an image {time_text}"
                if raw_text:
                    summary += f" showing {raw_text[:100]}"
                summary += "."
                
                # Sentence 2: Context with people and places
                context_parts = []
                if people:
                    context_parts.append(f"featuring {', '.join(people)}")
                if places:
                    context_parts.append(f"at {places[0]}")
                
                if context_parts:
                    summary += f" The image captures {', '.join(context_parts)}"
                    if emotion != "neutral":
                        summary += f", reflecting a {emotion} moment"
                    summary += "."
                
                # Sentence 3: Significance
                if emotion != "neutral" and not context_parts:
                    summary += f" This was a {emotion} moment worth remembering."
                    
            elif mem_type == 'voice':
                # Sentence 1: What and when
                summary = f"You recorded a voice note {time_text}"
                if emotion != "neutral":
                    summary += f" while feeling {emotion}"
                summary += "."
                
                # Sentence 2-3: Content details
                if raw_text:
                    text_snippet = raw_text[:150] + "..." if len(raw_text) > 150 else raw_text
                    summary += f" The recording discusses: {text_snippet}"
                    if people:
                        summary += f" You mentioned {', '.join(people)} during the recording."
                    
            else:
                # Sentence 1: What, when, and context
                summary = f"You documented this {time_text}"
                context = []
                if people:
                    context.append(f"involving {', '.join(people)}")
                if places:
                    context.append(f"at {places[0]}")
                if context:
                    summary += f" {', '.join(context)}"
                summary += "."
                
                # Sentence 2: Main content
                if raw_text:
                    text_snippet = raw_text[:150] + "..." if len(raw_text) > 150 else raw_text
                    summary += f" The entry states: {text_snippet}"
                
                # Sentence 3: Emotional context
                if emotion != "neutral":
                    summary += f" This reflection carries a {emotion} tone, capturing your feelings at that moment."
            
            return summary
            
        except Exception as e:
            print(f"❌ Fallback summary error: {e}")
            import traceback
            traceback.print_exc()
            # Return a basic summary with available info
            try:
                time_str = self.format_date(memory.get('timestamp')) if isinstance(memory, dict) else 'unknown time'
                text = memory.get('raw_text', '') if isinstance(memory, dict) else ''
                if text:
                    text_snippet = text[:100] + "..." if len(text) > 100 else text
                    return f"You recorded this {time_str}. {text_snippet}"
                return f"Memory from {time_str}."
            except:
                return "Unable to generate summary for this memory."
    
    def _fallback_search_summary(self, query: str, memories: List[Dict]) -> Dict[str, Any]:
        """Fallback search summary if Gemini fails"""
        memory_summaries = []
        for memory in memories:
            summary = self._fallback_summary(memory)
            memory_summaries.append({
                "memory_id": memory.get('id'),
                "type": memory.get('type'),
                "summary": summary,
                "timestamp": memory.get('timestamp'),
                "image_url": memory.get('image_url')
            })
        
        # Count types
        memory_types = {}
        for memory in memories:
            mem_type = memory.get('type', 'text')
            memory_types[mem_type] = memory_types.get(mem_type, 0) + 1
        
        # Build professional intro
        if len(memories) == 1:
            intro = f"Retrieved 1 memory related to '{query}'."
        else:
            type_text = []
            if memory_types.get('image'):
                type_text.append(f"{memory_types['image']} image{'s' if memory_types['image'] > 1 else ''}")
            if memory_types.get('text'):
                type_text.append(f"{memory_types['text']} text entr{'ies' if memory_types['text'] > 1 else 'y'}")
            if memory_types.get('voice'):
                type_text.append(f"{memory_types['voice']} voice recording{'s' if memory_types['voice'] > 1 else ''}")
            
            intro = f"Found {len(memories)} relevant memories related to '{query}'"
            if type_text:
                intro += f", including {', '.join(type_text)}"
            intro += "."
        
        return {
            "summary": intro,
            "memory_summaries": memory_summaries,
            "total_found": len(memories),
            "query": query
        }

# Global instance
gemini_summarizer = GeminiSummarizer()
