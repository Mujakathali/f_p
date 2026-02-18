# AI-Powered MemoryGraph System

A comprehensive personal memory management system with AI-powered insights, semantic search, and multi-modal input support.

## Features

- **Multi-modal Memory Input**: Text, voice, and image support
- **AI-Powered Processing**: NLP analysis with entity extraction and sentiment analysis
- **Hybrid Search**: Combines keyword matching and semantic similarity
- **Knowledge Graph**: Neo4j-based relationship mapping
- **Voice Transcription**: OpenAI Whisper integration
- **Modern UI**: React-based interface with dark/light themes

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Neo4j Desktop or Server

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Mujakathali/final_year_project.git
   cd final_year_project/backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

3. **Environment Configuration**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your actual credentials:
   ```env
   # Database passwords
   POSTGRES_PASSWORD=your_actual_postgres_password
   NEO4J_PASSWORD=your_actual_neo4j_password
   
   # API Keys (optional but recommended)
   OPENAI_API_KEY=your_openai_api_key
   HUGGINGFACE_API_KEY=your_huggingface_api_key
   ```

4. **Database Setup**
   - Start PostgreSQL service
   - Start Neo4j Desktop/Server
   - Create database: `memorygraph_ai`

5. **Run Backend**
   ```bash
   python app.py
   ```

### Frontend Setup

1. **Navigate to frontend**
   ```bash
   cd ../second_brain
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm start
   ```

## Architecture

- **Backend**: FastAPI with PostgreSQL, Neo4j, ChromaDB
- **Frontend**: React with modern UI components
- **AI Models**: spaCy NLP, Sentence Transformers, OpenAI Whisper
- **Search**: Hybrid system combining keyword and semantic search

## Security Note

Never commit real API keys or passwords to version control. Use the `.env.example` template and set your actual credentials locally.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational purposes as part of a final year project.
"# f_p" 
