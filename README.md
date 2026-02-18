# Final Year Project — MemoryGraph AI

MemoryGraph AI is an AI-powered “second brain” that lets you store and retrieve memories (text + images) with a modern React UI and a FastAPI backend backed by PostgreSQL + Neo4j.

## Repo Structure

- `backend/` — FastAPI backend, DB connectors, NLP/AI utilities
- `second_brain/` — React frontend (Create React App)

## Prerequisites (New Laptop)

Install these first:

- Git
- Python 3.10+ (3.8+ should work, but 3.10+ recommended)
- Node.js 18+ (LTS recommended)
- Docker Desktop (recommended for PostgreSQL + Neo4j)

If you don’t want Docker, you can install PostgreSQL + Neo4j locally, but Docker is the simplest.

## 1) Download / Clone the Project

```bash
git clone <YOUR_GITHUB_REPO_URL>
cd final_year_project
```

## 2) Start Databases (PostgreSQL + Neo4j)

### Option A (Recommended): Docker Compose

A Docker Compose file is provided at `backend/docker-compose.yml`.

```bash
cd backend
docker compose up -d
```

This starts:

- PostgreSQL on `localhost:5432`
- Neo4j on:
  - Browser UI: `http://localhost:7474`
  - Bolt: `bolt://localhost:7687`

### Option B (Manual Install)

If you install PostgreSQL/Neo4j manually, ensure:

- PostgreSQL running on `localhost:5432`
- Neo4j running on `localhost:7687` (bolt)

## 3) Backend Setup (FastAPI)

### Create a virtual environment

From the repo root:

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
# source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## 4) Backend Environment Variables (`backend/.env`)

### Create `.env` from the template

```bash
cd backend
copy .env.example .env
```

Then open `backend/.env` and fill it.

### Example `backend/.env` (DO NOT paste real keys into GitHub)

```env
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=memorygraph_ai
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password

# API Keys (Optional)
OPENAI_API_KEY=your_openai_api_key_here
HUGGINGFACE_API_KEY=your_huggingface_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Application Settings
DEBUG=True
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# File Upload Settings
MAX_FILE_SIZE=10485760
UPLOAD_DIR=./uploads
TEMP_DIR=./temp

# Model Settings
WHISPER_MODEL_SIZE=base
EMBEDDING_MODEL=all-MiniLM-L6-v2
SPACY_MODEL=en_core_web_sm

# JWT Authentication Settings
JWT_SECRET_KEY=change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

### Security notes

- Never commit `.env` files.
- If any API key was ever exposed publicly, revoke/rotate it immediately in the provider dashboard.

## 5) Run the Backend

From `backend/`:

```bash
python app.py
```

Backend runs at:

- `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

## 6) Frontend Setup (React)

In a separate terminal:

```bash
cd second_brain
npm install
npm start
```

Frontend runs at:

- `http://localhost:3000`

## 7) Verify Everything Works

1. Make sure Docker containers are running (Postgres + Neo4j)
2. Start backend at `http://localhost:8000`
3. Start frontend at `http://localhost:3000`
4. Try storing a text memory and check Timeline.

## Common Issues

### GitHub push is failing / repo is huge

- Ensure `node_modules/` is not tracked.
- Ensure `backend/.env` is not tracked.
- Use the root `.gitignore`.

### Neo4j credentials mismatch

If using Docker Compose, check the values in `backend/docker-compose.yml` and set the same values in `backend/.env`.

### CORS errors

Ensure `CORS_ORIGINS` in `backend/.env` includes the frontend URL:

```env
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```
