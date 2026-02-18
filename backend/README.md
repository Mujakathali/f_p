# MemoryGraph AI Backend

AI-Powered Life Story Compiler Backend built with FastAPI, PostgreSQL, Neo4j, and advanced NLP processing.

## Features

### 🔹 Phase 1: Memory Input Interface
- **Text Memory Storage**: Direct text input with NLP processing
- **Voice Memory Processing**: OpenAI Whisper transcription with confidence scoring
- **Image Memory Extraction**: Tesseract OCR with image preprocessing
- **PostgreSQL Storage**: Structured data with metadata and relationships
- **Vector Embeddings**: ChromaDB integration for semantic search

### 🔹 Phase 2: NLP Processing & Entity Extraction
- **Named Entity Recognition**: spaCy + Hugging Face BERT models
- **Sentiment Analysis**: DistilBERT fine-tuned for emotion detection
- **Entity Storage**: People, places, dates, organizations
- **Text Normalization**: Cleaning, standardization, keyword extraction

### 🔹 Phase 3: Semantic Graph Construction
- **Neo4j Graph Database**: Nodes for Person, Event, Time, Location, Emotion
- **Relationship Mapping**: Complex entity relationships and memory connections
- **Similarity Detection**: Vector-based memory clustering
- **Graph Visualization**: API endpoints for frontend graph rendering

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Neo4j 4.4+
- Tesseract OCR

### Setup

1. **Clone and navigate to backend directory**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

4. **Database Setup**

**PostgreSQL:**
```sql
CREATE DATABASE memorygraph_ai;
CREATE USER memorygraph_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE memorygraph_ai TO memorygraph_user;
```

**Neo4j:**
- Install Neo4j Desktop or Server
- Create a new database
- Set authentication credentials

5. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your database credentials and API keys
```

6. **Install Tesseract OCR**

**Windows:**
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Add to PATH or update `pytesseract.pytesseract.tesseract_cmd` in `utils/image_processor.py`

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr

# macOS
brew install tesseract
```

## Running the Server

```bash
python app.py
```

Server will start at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

## API Endpoints

### Memory Management
- `POST /api/v1/add_memory` - Add text memory
- `POST /api/v1/add_voice_memory` - Upload and transcribe audio
- `POST /api/v1/add_image_memory` - Upload and extract text from image
- `GET /api/v1/list_memories` - List all memories with pagination
- `GET /api/v1/memory/{id}` - Get specific memory
- `GET /api/v1/search_memories` - Text and semantic search
- `GET /api/v1/similar_memories/{id}` - Find similar memories
- `DELETE /api/v1/memory/{id}` - Delete memory
- `GET /api/v1/stats` - Memory statistics

### Graph Operations
- `GET /api/v1/get_graph` - Get graph structure for visualization
- `GET /api/v1/query_graph` - Query by person, location, emotion
- `GET /api/v1/similar_memories_graph/{id}` - Graph-based similarity
- `GET /api/v1/graph_stats` - Graph database statistics
- `GET /api/v1/entities/{type}` - Get entities by type
- `POST /api/v1/create_relationship` - Create memory relationships
- `GET /api/v1/memory_connections/{id}` - Get memory connections
- `GET /api/v1/timeline_graph` - Time-filtered graph data
- `GET /api/v1/entity_network/{type}` - Entity relationship networks

## Project Structure

```
backend/
├── app.py                 # Main FastAPI application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── README.md             # This file
├── db/
│   ├── postgresql_connector.py    # PostgreSQL operations
│   └── neo4j_connector.py        # Neo4j graph operations
├── models/
│   └── nlp_processor.py          # NLP processing pipeline
├── utils/
│   ├── audio_processor.py        # Whisper audio transcription
│   ├── image_processor.py        # Tesseract OCR processing
│   └── embeddings.py            # ChromaDB vector operations
└── routes/
    ├── memory_routes.py          # Memory CRUD operations
    └── graph_routes.py           # Graph query operations
```

## Models Used

### NLP Models
- **spaCy**: `en_core_web_sm` for general NLP tasks
- **NER**: `dslim/bert-base-NER` for named entity recognition
- **Sentiment**: `distilbert-base-uncased-finetuned-sst-2-english`
- **Embeddings**: `all-MiniLM-L6-v2` for semantic similarity

### Audio/Image Models
- **Whisper**: `base` model for speech-to-text
- **Tesseract**: OCR engine for text extraction

## Database Schema

### PostgreSQL Tables
- `memories`: Core memory storage with metadata
- `entities`: Extracted named entities
- `sentiments`: Sentiment analysis results
- `memory_relationships`: Memory similarity relationships

### Neo4j Graph Schema
- **Nodes**: Memory, Person, Location, Event, Emotion
- **Relationships**: MENTIONS, HAPPENED_AT, HAS_EMOTION, SIMILAR_TO

## Configuration

### Environment Variables
- Database credentials (PostgreSQL, Neo4j)
- API keys (OpenAI, Hugging Face)
- Model settings (Whisper size, embedding model)
- File upload limits and directories

### Performance Tuning
- Connection pooling for databases
- Thread pools for CPU-intensive tasks
- Async processing for I/O operations
- Caching for frequently accessed data

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black .
flake8 .
```

### Adding New Features
1. Create new route in appropriate router
2. Add database operations if needed
3. Update models and processors
4. Add tests and documentation

## Troubleshooting

### Common Issues
1. **Database Connection**: Check credentials in `.env`
2. **Model Loading**: Ensure sufficient RAM for ML models
3. **Tesseract**: Verify installation and PATH configuration
4. **Audio Processing**: Check audio file formats and size limits

### Performance Optimization
- Use smaller Whisper models for faster transcription
- Implement caching for embeddings
- Batch process multiple files
- Use GPU acceleration if available

## License

MIT License - see LICENSE file for details
