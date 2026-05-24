# AI Chatbot MVP — On-Premises RAG System

A complete AI-powered chatbot with **Retrieval-Augmented Generation (RAG)**, built for on-premises deployment. Uses your organization's **Ollama** instance for LLM and embeddings — no data leaves your network.

---

## 🏗️ Architecture

```
React Frontend (Vite)
       │
       ▼
Django REST API
       │
 ┌─────┴──────────┐
 │                │
 ▼                ▼
RAG Engine     Auth System
 │
 ├── FAQ Retrieval (keyword match)
 ├── Navigation Retrieval (intent match)
 └── PDF Semantic Search (pgvector)
        │
        ▼
 PostgreSQL + pgvector
        │
        ▼
 Ollama (LLM + Embeddings)
```

---

## 📦 What's Included

### User Features
- 🔵 **Floating AI chatbot widget** — always accessible
- ⚡ **Streaming responses** — see answers appear token by token via SSE
- 🔐 **Login authentication** — JWT-based auth with role support
- 💬 **Chat history** — browse, resume, and delete past conversations
- 📄 **PDF knowledge base** — ask questions about uploaded system design documents
- ❓ **FAQ engine** — instant answers for common questions
- 🧭 **Navigation help** — step-by-step app navigation guidance

### Admin Features
- 📤 **Upload/manage PDFs** — automatic extraction, chunking, and embedding
- ✏️ **Add/edit FAQs** — categorize and manage
- ✏️ **Add/edit navigation guides** — map intents to navigation steps
- 📋 **View chat logs** — monitor all user conversations
- ⚙️ **Configure AI provider** — change model, temperature, embeddings

---

## 📁 Project Structure

```
ai-chatbot-mvp/
├── backend/                     # Django REST API
│   ├── chatbot_project/         # Django settings & URLs
│   │   ├── settings.py          # All configuration (DB, Ollama, JWT)
│   │   ├── urls.py              # Root URL routing
│   │   └── wsgi.py
│   ├── api/                     # Main application
│   │   ├── models.py            # All database models (8 tables)
│   │   ├── serializers.py       # DRF serializers
│   │   ├── views.py             # All API endpoints
│   │   ├── urls.py              # API URL routing
│   │   ├── permissions.py       # Admin-only permission class
│   │   ├── admin.py             # Django admin registration
│   │   ├── rag.py               # RAG engine (PDF, embeddings, retrieval, streaming)
│   │   └── management/commands/
│   │       ├── ingest_pdf.py    # PDF ingestion command
│   │       ├── create_admin.py  # Admin user creation command
│   │       └── seed_knowledge.py # Seed FAQs & navigation
│   ├── seed_data/
│   │   └── System_Design_Zero_to_Hero.pdf  # Your seed PDF
│   ├── seed.sh                  # One-command database seeding
│   ├── requirements.txt
│   ├── Dockerfile
│   └── manage.py
│
├── frontend/                    # React (Vite + Tailwind)
│   ├── src/
│   │   ├── App.jsx              # Routes & layout
│   │   ├── main.jsx             # Entry point
│   │   ├── index.css            # Tailwind + custom styles
│   │   ├── api.js               # Centralized API client (all endpoints)
│   │   ├── AuthContext.jsx       # Auth state management
│   │   ├── ChatWidget.jsx        # Floating chatbot with streaming
│   │   ├── Login.jsx             # Login & registration page
│   │   └── AdminDashboard.jsx    # Full admin panel (5 tabs)
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── Dockerfile
│   └── index.html
│
├── docker-compose.yml           # PostgreSQL + Backend + Frontend
├── .env.example                 # Environment configuration template
├── .gitignore
└── README.md                    # This file
```

---

## 🚀 Quick Start (Recommended)

### Prerequisites

1. **Docker & Docker Compose** — [Install Docker](https://docs.docker.com/get-docker/)
2. **Ollama** — [Install Ollama](https://ollama.com/) on your machine or server
3. **Pull required models in Ollama:**
   ```bash
   ollama pull llama3.2          # LLM for chat
   ollama pull nomic-embed-text  # Embedding model
   ```

### Step 1: Clone & Configure

```bash
cd ai-chatbot-mvp

# Copy environment file and update if needed
cp .env.example .env
```

**Important:** If Ollama is running on the same machine, the default `.env` will work. If Ollama is on a different server, update `OLLAMA_BASE_URL` in `.env`.

### Step 2: Start with Docker Compose

```bash
docker compose up --build
```

This starts:
- **PostgreSQL** with pgvector on port 5432
- **Django backend** on port 8000
- **React frontend** on port 3000

### Step 3: Seed the Database

Open a new terminal and run:

```bash
# Run migrations and seed data
docker compose exec backend bash seed.sh
```

This creates:
- **Admin account:** `admin` / `admin123`
- **Test user account:** `user` / `user123`
- **Sample FAQs** (5 entries)
- **Sample navigation guides** (5 entries)
- **Ingests the System Design PDF** (chunked & embedded)

### Step 4: Access the App

- 🌐 **Chat interface:** http://localhost:3000
- 🔧 **Admin dashboard:** http://localhost:3000/admin
- 📡 **API root:** http://localhost:8000/api/

---

## 💻 Running Without Docker (Local Development)

If you prefer running directly on your machine:

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL 16** with **pgvector extension**
- **Ollama** with `llama3.2` and `nomic-embed-text` models

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate    # Linux/Mac
# venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Update .env with local PostgreSQL settings
# POSTGRES_HOST=localhost
# OLLAMA_BASE_URL=http://localhost:11434

# Run migrations
python manage.py migrate

# Seed the database
bash seed.sh

# Start the server
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Enable pgvector in PostgreSQL

Before running migrations, make sure the pgvector extension is enabled:

```sql
-- Connect to your PostgreSQL database and run:
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## 🔧 Configuration

All configuration is in the `.env` file. Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Your Ollama instance URL |
| `OLLAMA_LLM_MODEL` | `llama3.2` | Chat model name |
| `OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model name |
| `OLLAMA_TEMPERATURE` | `0.7` | Response creativity (0.0–1.0) |
| `OLLAMA_MAX_TOKENS` | `2048` | Max response length |
| `CHUNK_SIZE` | `1000` | Characters per PDF chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `VECTOR_SEARCH_TOP_K` | `5` | Number of chunks to retrieve |

### AI Configuration via Admin Panel

You can also change AI settings from the **Admin Dashboard → AI Config** tab without restarting the server. Changes take effect immediately for new queries.

---

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register new user |
| POST | `/api/auth/token/` | Get JWT tokens (login) |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| GET | `/api/auth/me/` | Get current user profile |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/chat/sessions/` | List user's chat sessions |
| POST | `/api/chat/sessions/` | Create new session |
| GET | `/api/chat/sessions/{id}/` | Get session details |
| DELETE | `/api/chat/sessions/{id}/` | Delete session |
| GET | `/api/chat/sessions/{id}/messages/` | List session messages |
| POST | `/api/chat/query/` | Send message (SSE streaming response) |

### Admin — Knowledge Base
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/documents/` | List all PDFs |
| POST | `/api/admin/documents/` | Upload new PDF |
| GET | `/api/admin/documents/{id}/` | Get PDF details |
| DELETE | `/api/admin/documents/{id}/` | Delete PDF and chunks |

### Admin — FAQs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/faqs/` | List all FAQs |
| POST | `/api/admin/faqs/` | Create FAQ |
| PATCH | `/api/admin/faqs/{id}/` | Update FAQ |
| DELETE | `/api/admin/faqs/{id}/` | Delete FAQ |

### Admin — Navigation
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/navigation/` | List all guides |
| POST | `/api/admin/navigation/` | Create guide |
| PATCH | `/api/admin/navigation/{id}/` | Update guide |
| DELETE | `/api/admin/navigation/{id}/` | Delete guide |

### Admin — Other
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/chat-logs/` | View all chat logs |
| GET | `/api/admin/ai-config/` | Get AI configuration |
| PUT | `/api/admin/ai-config/` | Update AI configuration |

---

## 🧠 How the RAG Engine Works

When a user asks a question, the system follows this pipeline:

```
User Question
      │
      ▼
1. FAQ Match? ──── YES ──→ Return direct FAQ answer
      │ NO
      ▼
2. Navigation Match? ── YES ──→ Return navigation steps
      │ NO
      ▼
3. Semantic Vector Search (pgvector)
      │
      ▼
4. Top-K chunks retrieved
      │
      ▼
5. Build context prompt with retrieved chunks
      │
      ▼
6. Ollama LLM generates response (streamed via SSE)
```

### Embedding Choice

We use **Ollama's nomic-embed-text** model because:
- Runs entirely on-premises (no external API calls)
- 768-dimensional vectors — good balance of quality and performance
- Fast inference via Ollama's optimized runtime
- No additional Python dependencies (no sentence-transformers needed)
- Works with the same Ollama instance you already have

### Vector Search

We use **PostgreSQL + pgvector** with a **HNSW index** for approximate nearest-neighbor search using **cosine distance**. This provides:
- Sub-millisecond search on millions of vectors
- No separate vector database to manage
- SQL-based filtering and joining with document metadata
- Battle-tested PostgreSQL reliability

---

## 🔒 Security

- **All AI processing is on-premises** — no data leaves your network
- **API keys and model secrets** are never exposed to the frontend
- **JWT authentication** with short-lived access tokens
- **Role-based access** — admin endpoints require admin role
- **Ollama API key is optional** — not needed for local Ollama instances

---

## 🛠️ Troubleshooting

### Ollama Connection Issues
```
Error: Failed to embed query / Connection refused
```
**Fix:** Make sure Ollama is running and accessible:
```bash
# Test Ollama connection
curl http://localhost:11434/api/tags

# If using Docker, use host.docker.internal instead of localhost
# In .env: OLLAMA_BASE_URL=http://host.docker.internal:11434
```

### pgvector Extension Missing
```
Error: type "vector" does not exist
```
**Fix:** Connect to PostgreSQL and run:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### PDF Processing Fails
```
Error: PDF appears to be empty or image-only
```
**Fix:** The PDF may be scanned/image-based. You need OCR pre-processing before ingestion. For text-based PDFs, this should work fine.

### Port Already in Use
```
Error: Port 8000 is already in use
```
**Fix:** Change the port in `.env`:
```
DJANGO_PORT=8001
FRONTEND_PORT=3001
```

---

## 📋 Management Commands

```bash
# Ingest a new PDF
python manage.py ingest_pdf /path/to/document.pdf --title "My Document"

# Create an admin user
python manage.py create_admin --username admin --password secret --email admin@company.com

# Seed sample FAQs and navigation guides
python manage.py seed_knowledge

# Start Django shell
python manage.py shell
```

---

## 🔄 Adding More PDFs

1. Log in as **admin** at http://localhost:3000/admin
2. Go to **Knowledge Base** tab
3. Click **Upload PDF**
4. The system will automatically extract text, chunk it, generate embeddings, and store it in the vector database
5. New documents are immediately available for search queries

---

## 📈 Scaling & Future Enhancements

This MVP is designed to scale. Future additions:
- **Celery + Redis** for async PDF processing
- **Multi-PDF collections** with per-document access control
- **Re-ranking** with a cross-encoder for better retrieval
- **Voice input** via Web Speech API
- **Citation highlighting** showing source PDF pages
- **Analytics dashboard** tracking query patterns
- **Multi-language support**
- **Fine-tuned models** on your domain data

---

## 📝 License

Internal use only — built for your organization's on-premises deployment.
