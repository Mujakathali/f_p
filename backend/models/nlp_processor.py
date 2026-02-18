"""
NLP Processing module using spaCy (lightweight) with graceful fallbacks
"""
import spacy
from typing import List, Dict, Any, Optional
import re
from datetime import datetime
import asyncio

class NLPProcessor:
    def __init__(self):
        self.nlp = None
        self.sentiment_pipeline = None
        self.ner_pipeline = None
        self.is_models_loaded = False

    async def load_models(self):
        """Load all NLP models"""
        try:
            # Load spaCy model for general NLP tasks
            self.nlp = spacy.load("en_core_web_sm")
            
            # Use spaCy for sentiment analysis (no external dependencies)
            # We'll implement basic sentiment using spaCy's built-in capabilities
            self.sentiment_pipeline = None  # Will use spaCy-based sentiment
            
            # Use spaCy for NER (already loaded above)
            self.ner_pipeline = None  # Will use spaCy NER
            
            self.is_models_loaded = True
            print("✅ NLP models loaded successfully")
            
        except Exception as e:
            print(f"❌ Failed to load NLP models: {e}")
            # Fallback to a lightweight blank English pipeline so the app still works
            try:
                self.nlp = spacy.blank("en")
                # Add a simple sentencizer to avoid errors in downstream usage
                if "sentencizer" not in self.nlp.pipe_names:
                    self.nlp.add_pipe("sentencizer")
                self.sentiment_pipeline = None
                self.ner_pipeline = None
                self.is_models_loaded = True
                print("⚠️ Using spaCy.blank('en') fallback (minimal NLP enabled)")
            except Exception as fallback_error:
                print(f"❌ Failed to load any NLP models, even fallback: {fallback_error}")
                raise

    def is_loaded(self) -> bool:
        """Check if models are loaded"""
        return self.is_models_loaded

    async def process_text(self, text: str) -> Dict[str, Any]:
        """Process text and extract all NLP features"""
        if not self.is_models_loaded:
            await self.load_models()
        
        # Clean and normalize text
        cleaned_text = self.clean_text(text)
        
        # Extract entities
        entities = await self.extract_entities(cleaned_text)
        
        # Analyze sentiment
        sentiment = await self.analyze_sentiment(cleaned_text)
        
        # Extract dates and times
        dates = self.extract_dates(cleaned_text)
        
        # Extract keywords
        keywords = self.extract_keywords(cleaned_text)
        
        return {
            "cleaned_text": cleaned_text,
            "entities": entities,
            "sentiment": sentiment,
            "dates": dates,
            "keywords": keywords,
            "word_count": len(cleaned_text.split()),
            "char_count": len(cleaned_text)
        }

    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Fix common OCR errors
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\'\"]', ' ', text)
        
        # Normalize quotes
        text = re.sub(r'["""]', '"', text)
        text = re.sub(r"[''']", "'", text)
        
        return text

    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities using spaCy with enhanced detection"""
        entities = []
        
        try:
            # spaCy NER with enhanced patterns
            doc = self.nlp(text)
            
            # Standard spaCy entities
            for ent in doc.ents:
                entities.append({
                    "text": ent.text.strip(),
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "confidence": 0.85,
                    "source": "spacy"
                })
            
            # Enhanced pattern matching for better entity detection
            # Look for capitalized words that might be names
            for token in doc:
                if (token.is_title and 
                    not token.is_stop and 
                    not token.is_punct and 
                    len(token.text) > 2 and
                    token.pos_ in ["PROPN", "NOUN"]):
                    
                    # Check if it's not already captured
                    already_captured = any(
                        ent["start"] <= token.idx < ent["end"] 
                        for ent in entities
                    )
                    
                    if not already_captured:
                        # Try to determine entity type based on context
                        entity_type = self._classify_entity_type(token, doc)
                        if entity_type:
                            entities.append({
                                "text": token.text,
                                "label": entity_type,
                                "start": token.idx,
                                "end": token.idx + len(token.text),
                                "confidence": 0.7,
                                "source": "pattern_enhanced"
                            })
            
        except Exception as e:
            print(f"⚠️ Entity extraction error: {e}")
        
        # Remove duplicates and merge overlapping entities
        entities = self.merge_entities(entities)
        
        return entities

    def _classify_entity_type(self, token, doc) -> str:
        """Classify entity type based on context and patterns"""
        text_lower = token.text.lower()
        
        # Common location indicators
        location_indicators = ["city", "town", "street", "avenue", "road", "park", "beach", "mountain"]
        # Common person name patterns
        person_indicators = ["mr", "mrs", "dr", "prof", "sir", "miss"]
        # Common organization patterns
        org_indicators = ["inc", "corp", "ltd", "llc", "company", "university", "school"]
        
        # Check surrounding context
        context_window = 3
        start_idx = max(0, token.i - context_window)
        end_idx = min(len(doc), token.i + context_window + 1)
        context_tokens = [t.text.lower() for t in doc[start_idx:end_idx]]
        
        # Location detection
        if any(indicator in context_tokens for indicator in location_indicators):
            return "GPE"
        
        # Person detection
        if any(indicator in context_tokens for indicator in person_indicators):
            return "PERSON"
            
        # Organization detection
        if any(indicator in context_tokens for indicator in org_indicators):
            return "ORG"
        
        # Default classification based on capitalization patterns
        if token.is_title and len(token.text) > 3:
            return "PERSON"  # Most likely a person name
            
        return None

    def merge_entities(self, entities: List[Dict]) -> List[Dict]:
        """Merge overlapping entities and remove duplicates"""
        if not entities:
            return []
        
        # Sort by start position
        entities.sort(key=lambda x: x["start"])
        
        merged = []
        for entity in entities:
            if not merged:
                merged.append(entity)
                continue
            
            last = merged[-1]
            
            # Check for overlap
            if entity["start"] <= last["end"] and entity["end"] >= last["start"]:
                # Merge entities - keep the one with higher confidence
                if entity["confidence"] > last["confidence"]:
                    merged[-1] = entity
            else:
                merged.append(entity)
        
        return merged

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using Hugging Face model"""
        try:
            if self.sentiment_pipeline:
                result = self.sentiment_pipeline(text)[0]
                
                # Convert to standardized format
                label = result["label"].lower()
                score = result["score"]
                
                # Map to emotion categories
                emotion_mapping = {
                    "positive": "joy",
                    "negative": "sadness",
                    "neutral": "neutral"
                }
                
                return {
                    "label": label,
                    "score": score,
                    "emotion": emotion_mapping.get(label, "neutral"),
                    "confidence": score
                }
            else:
                # Fallback to basic sentiment
                return self.basic_sentiment_analysis(text)
                
        except Exception as e:
            print(f"⚠️ Sentiment analysis error: {e}")
            return self.basic_sentiment_analysis(text)

    def basic_sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """Enhanced sentiment analysis using spaCy and word lists"""
        if self.nlp:
            doc = self.nlp(text)
            
            # Use spaCy's built-in sentiment indicators
            positive_words = ["happy", "joy", "love", "amazing", "wonderful", "great", "excellent", "fantastic", 
                            "awesome", "brilliant", "perfect", "beautiful", "success", "win", "achievement", 
                            "proud", "excited", "thrilled", "delighted", "pleased", "satisfied", "award"]
            negative_words = ["sad", "angry", "hate", "terrible", "awful", "bad", "horrible", "disappointed",
                            "frustrated", "upset", "worried", "anxious", "stressed", "failed", "loss", 
                            "problem", "issue", "difficult", "hard", "struggle", "pain", "hurt"]
            
            text_lower = text.lower()
            pos_count = sum(1 for word in positive_words if word in text_lower)
            neg_count = sum(1 for word in negative_words if word in text_lower)
            
            # Enhanced scoring based on word frequency and context
            total_words = len([token for token in doc if token.is_alpha])
            pos_ratio = pos_count / max(total_words, 1)
            neg_ratio = neg_count / max(total_words, 1)
            
            if pos_count > neg_count:
                score = min(0.9, 0.6 + pos_ratio * 2)
                return {"label": "positive", "score": score, "emotion": "joy", "confidence": score}
            elif neg_count > pos_count:
                score = min(0.9, 0.6 + neg_ratio * 2)
                return {"label": "negative", "score": score, "emotion": "sadness", "confidence": score}
            else:
                return {"label": "neutral", "score": 0.6, "emotion": "neutral", "confidence": 0.5}
        else:
            # Fallback without spaCy
            positive_words = ["happy", "joy", "love", "amazing", "wonderful", "great", "excellent", "fantastic", "award"]
            negative_words = ["sad", "angry", "hate", "terrible", "awful", "bad", "horrible", "disappointed"]
            
            text_lower = text.lower()
            pos_count = sum(1 for word in positive_words if word in text_lower)
            neg_count = sum(1 for word in negative_words if word in text_lower)
            
            if pos_count > neg_count:
                return {"label": "positive", "score": 0.7, "emotion": "joy", "confidence": 0.6}
            elif neg_count > pos_count:
                return {"label": "negative", "score": 0.7, "emotion": "sadness", "confidence": 0.6}
            else:
                return {"label": "neutral", "score": 0.6, "emotion": "neutral", "confidence": 0.5}

    def extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """Extract dates and temporal expressions"""
        dates = []
        
        try:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ["DATE", "TIME"]:
                    dates.append({
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char
                    })
            
            # Additional regex patterns for dates
            date_patterns = [
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or MM-DD-YYYY
                r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD or YYYY-MM-DD
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
                r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b'     # DD Month YYYY
            ]
            
            for pattern in date_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    dates.append({
                        "text": match.group(),
                        "label": "DATE",
                        "start": match.start(),
                        "end": match.end()
                    })
            
        except Exception as e:
            print(f"⚠️ Date extraction error: {e}")
        
        return dates

    def extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        try:
            doc = self.nlp(text)
            
            # Extract nouns, proper nouns, and adjectives
            keywords = []
            for token in doc:
                if (token.pos_ in ["NOUN", "PROPN", "ADJ"] and 
                    not token.is_stop and 
                    not token.is_punct and 
                    len(token.text) > 2):
                    keywords.append(token.lemma_.lower())
            
            # Remove duplicates while preserving order
            seen = set()
            unique_keywords = []
            for keyword in keywords:
                if keyword not in seen:
                    seen.add(keyword)
                    unique_keywords.append(keyword)
            
            return unique_keywords[:20]  # Return top 20 keywords
            
        except Exception as e:
            print(f"⚠️ Keyword extraction error: {e}")
            return []

    def extract_people_names(self, entities: List[Dict]) -> List[str]:
        """Extract person names from entities"""
        people = []
        for entity in entities:
            if entity["label"] in ["PERSON", "PER"]:
                people.append(entity["text"])
        return list(set(people))  # Remove duplicates

    def extract_locations(self, entities: List[Dict]) -> List[str]:
        """Extract location names from entities"""
        locations = []
        for entity in entities:
            if entity["label"] in ["GPE", "LOC", "LOCATION"]:
                locations.append(entity["text"])
        return list(set(locations))  # Remove duplicates

    def extract_organizations(self, entities: List[Dict]) -> List[str]:
        """Extract organization names from entities"""
        organizations = []
        for entity in entities:
            if entity["label"] in ["ORG", "ORGANIZATION"]:
                organizations.append(entity["text"])
        return list(set(organizations))  # Remove duplicates  what are the things done here?