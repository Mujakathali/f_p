#!/usr/bin/env python3
"""
BERT NER Processor with dslim/bert-base-NER and RoBERTa multilingual fallback
"""
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import torch
import os
from typing import List, Dict, Any, Optional
import asyncio

class BERTNERProcessor:
    def __init__(self):
        self.primary_model_name = "dslim/bert-base-NER"
        self.fallback_model_name = "xlm-roberta-large-finetuned-conll03-english"
        self.tokenizer = None
        self.model = None
        self.ner_pipeline = None
        self.current_model = None
        self.is_loaded = False

    async def load_models(self):
        """Load BERT NER model with RoBERTa fallback"""
        try:
            # Get Hugging Face token
            hf_token = os.getenv('HUGGINGFACE_API_KEY') or os.getenv('HUGGINGFACE_TOKEN')
            
            # Try primary model first
            try:
                print(f"🔄 Loading primary NER model: {self.primary_model_name}")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.primary_model_name,
                    use_auth_token=hf_token
                )
                self.model = AutoModelForTokenClassification.from_pretrained(
                    self.primary_model_name,
                    use_auth_token=hf_token
                )
                self.ner_pipeline = pipeline(
                    "ner",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    aggregation_strategy="simple"
                )
                self.current_model = self.primary_model_name
                print(f"✅ Primary NER model loaded: {self.primary_model_name}")
                
            except Exception as e:
                print(f"⚠️ Primary model failed: {e}, trying fallback...")
                
                # Try fallback model
                try:
                    print(f"🔄 Loading fallback NER model: {self.fallback_model_name}")
                    self.tokenizer = AutoTokenizer.from_pretrained(
                        self.fallback_model_name,
                        use_auth_token=hf_token
                    )
                    self.model = AutoModelForTokenClassification.from_pretrained(
                        self.fallback_model_name,
                        use_auth_token=hf_token
                    )
                    self.ner_pipeline = pipeline(
                        "ner",
                        model=self.model,
                        tokenizer=self.tokenizer,
                        aggregation_strategy="simple"
                    )
                    self.current_model = self.fallback_model_name
                    print(f"✅ Fallback NER model loaded: {self.fallback_model_name}")
                    
                except Exception as fallback_error:
                    print(f"❌ Both NER models failed: {fallback_error}")
                    raise fallback_error
            
            self.is_loaded = True
            print("✅ BERT NER processor initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to load BERT NER models: {e}")
            raise

    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities using BERT NER"""
        if not self.is_loaded:
            await self.load_models()
        
        try:
            # Run NER pipeline
            entities = self.ner_pipeline(text)
            
            # Format entities
            formatted_entities = []
            for entity in entities:
                formatted_entities.append({
                    "text": entity["word"],
                    "label": entity["entity_group"],
                    "start": entity["start"],
                    "end": entity["end"],
                    "confidence": entity["score"],
                    "source": f"bert_{self.current_model.split('/')[-1]}"
                })
            
            return formatted_entities
            
        except Exception as e:
            print(f"⚠️ BERT NER extraction failed: {e}")
            return []

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "current_model": self.current_model,
            "is_loaded": self.is_loaded,
            "primary_model": self.primary_model_name,
            "fallback_model": self.fallback_model_name
        }