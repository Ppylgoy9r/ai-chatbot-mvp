# 🚀 AI Chatbot MVP — Run & Deployment Manual

Welcome to the run manual for the **AI Chatbot MVP (On-Premises RAG System)**. This document contains complete instructions on what has been built, how to run and verify the system, and a **dedicated guide for deployment on a restricted corporate TCS laptop (macOS)**.

---

## 📝 1. Summary of Completed Work

The AI Chatbot MVP is a state-of-the-art, fully on-premises **Retrieval-Augmented Generation (RAG)** search assistant. Here is what has been built and configured:

1. **RAG Search & Retrieval Pipeline** (`backend/api/rag.py`):
   - **Step 1 (FAQ Match)**: Performs direct keyword matches on pre-seeded FAQs for high-speed, accurate answers.
   - **Step 2 (Navigation Match)**: Evaluates user intent to retrieve step-by-step application navigation guides.
   - **Step 3 (Semantic Document Search)**: Connects to PostgreSQL using `pgvector` to run cosine distance vector similarity searches on uploaded PDFs.
   - **Step 4 (AI Completion)**: Gathers the most relevant context and sends it to a local Ollama LLM (`qwen2.5`) to stream replies back via Server-Sent Events (SSE).

2. **Premium Admin Dashboard** (`frontend/src/AdminDashboard.jsx`):
   - **Knowledge Base Tab**: Visualizes uploaded documents and tracks total chunk sizes.
   - **FAQs Tab**: Allows real-time viewing, updating, creating, and deleting FAQ entries.
   - **Navigation Tab**: Enables managing routing instructions based on user intent.
   - **Chat Logs Tab**: Shows historical conversation logs, query sessions, message counts, and timestamps.
   - **AI Config Tab**: Directly configures the Ollama API host, LLM model, and embedding configurations on-the-fly.

3. **Secure Authentication & Routing**:
   - Implemented JWT token exchange using `django-simplejwt`.
   - Developed role-based middleware to restrict API configurations, FAQ management, and document uploads to the **Admin** role.
   - Rerouted page navigations with protected frontend route guards (`App.jsx`).

4. **Fixed Connectivity & Configuration Issues**:
   - Corrected backend CORS policies and Vite reverse proxy configurations (`vite.config.js`) to seamlessly proxy frontend `/api` requests to `127.0.0.1:8000` without triggering CORS blockers.

---

## 🏃‍♂️ 2. Quick-Start (Personal Laptop / Docker Allowed)

If you are running on a machine that has Docker Desktop and open network access:

### Prerequisites
- Install **Docker & Docker Compose**
- Install **Ollama** locally, and pull the required models:
  ```bash
  ollama pull qwen2.5:latest
  ollama pull nomic-embed-text:latest
  ```

### Steps
1. Navigate to the project root:
   ```bash
   cd ai-chatbot-mvp
   ```
2. Copy the environment variables configuration:
   ```bash
   cp .env.example .env
   ```
3. Start the containers:
   ```bash
   docker compose up --build
   ```
4. In a separate terminal, seed the database and ingest the sample PDF:
   ```bash
   docker compose exec backend bash seed.sh
   ```
5. Access the application:
   - **User Chat App**: `http://localhost:3000`
   - **Admin Dashboard**: `http://localhost:3000/admin` (Credentials: `admin` / `admin123`)

---

## 🏢 3. TCS Laptop (macOS) Setup & Running Guide

TCS corporate laptops are highly secure, locked down, and restricted. You will face four main roadblocks:
1. **No Docker Desktop** (Requires root admin permissions which are blocked).
2. **No Root Admin Database Installations** (Cannot install PostgreSQL via installers).
3. **Zscaler/Proxy SSL Blocks** (Causes `pip install` and `npm install` SSL handshake errors).
4. **Ollama Network Blocks** (Firewall blocks `ollama pull` downloads).

Here is the step-by-step guide to run the app **completely locally, without Docker and without Admin Rights**.

---

### Step A: Bypassing Zscaler & Proxy Blocks for Dependencies

To install python packages and node modules behind the corporate proxy, configure your terminals as follows:

#### For Node.js / NPM:
If `npm install` errors out with an SSL issue, run:
```bash
# Disable SSL strictness temporarily for installing dependencies
npm config set strict-ssl false

# Alternatively, set your TCS HTTP proxy (replace proxy-host:port with TCS specific ones if needed)
# npm config set proxy http://your-tcs-proxy:8080
# npm config set https-proxy http://your-tcs-proxy:8080
```

#### For Python / PIP:
If `pip install` fails with SSL Certificate Verification errors, bypass it by running:
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r backend/requirements.txt
```

---

### Step B: Database Setup (PostgreSQL with `pgvector`) WITHOUT Admin Rights

Since you cannot run Docker or use official `.pkg` root installers, you should use **Postgres.app**. It is a full-featured, self-contained macOS app that runs entirely within the User Space (no admin password required).

1. **Download Postgres.app**:
   - Go to [Postgresapp.com](https://postgresapp.com/) on a browser.
   - Download the **Postgres.app with PostgreSQL 16** (or the latest version).
   - *Tip: Ensure you download the version labeled "with pgvector", which is included in standard releases!*
2. **Install & Run**:
   - Drag `Postgres.app` into your home user Applications directory (`/Users/ishankumar/Applications` or `/Applications`).
   - Open the app. Click **Start** to run a local database instance on Port `5432`.
3. **Create the Database and Enable `pgvector`**:
   - Open a terminal and run the setup script included in your project folder to create the database:
     ```bash
     python backend/create_db.py
     ```
   - Enable the vector search extension:
     ```bash
     python backend/create_extension.py
     ```
   - *Note: These scripts use `psycopg2` to automatically create the `chatbot` database and initialize the `vector` extension.*

---

### Step C: Manual Ollama Setup & Offline Model Ingestion

If the TCS network blocks the `ollama pull` commands, you can manually load models offline:

1. **Download Ollama for macOS**:
   - Download the zip from [Ollama's website](https://ollama.com/download/mac).
   - Unzip and drag the `Ollama.app` into your `/Applications` or home applications folder. Run it.
2. **Download Model Files Manually (Using standard HTTPS)**:
   - If `ollama pull qwen2.5` blocks, download the GGUF model files from HuggingFace on your browser (since browser traffic is usually permitted through corporate Zscaler proxies).
   - Download **Qwen 2.5 (e.g. `qwen2.5-3b-instruct-q4_K_M.gguf`)** and **nomic-embed-text-v1.5.Q4_K_M.gguf** from Hugging Face.
3. **Import into Ollama**:
   - Create a file named `Modelfile` for Qwen:
     ```dockerfile
     FROM /path/to/downloaded/qwen2.5-3b-instruct-q4_K_M.gguf
     ```
   - In terminal, create the model:
     ```bash
     ollama create qwen2.5:latest -f Modelfile
     ```
   - Repeat for the embedding model:
     ```dockerfile
     FROM /path/to/downloaded/nomic-embed-text-v1.5.Q4_K_M.gguf
     ```
     ```bash
     ollama create nomic-embed-text:latest -f Modelfile
     ```

---

### Step D: Running the Servers (Backend & Frontend)

Once your database is running via Postgres.app and Ollama has the models:

#### 1. Start the Django Backend:
Navigate to the `backend/` directory, activate the virtual environment, apply migrations, seed the database, and launch the server:
```bash
cd backend

# 1. Activate virtual environment
source venv/bin/activate

# 2. Install dependencies (if you haven't)
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

# 3. Apply database migrations
python manage.py migrate

# 4. Seed the admin, FAQs, navigation guides, and PDF documents
bash seed.sh

# 5. Start the local server
python manage.py runserver 127.0.0.1:8000
```

#### 2. Start the Vite Frontend:
In a **new terminal window**, navigate to the `frontend/` directory and run the dev server:
```bash
cd frontend

# 1. Install Node dependencies (if you haven't)
npm install

# 2. Run the development environment
npm run dev
```
*The frontend will run on **http://localhost:3000** and automatically proxy `/api` calls to the Django backend running on Port 8000.*

---

## 🎯 4. Post-Deployment Verification Checklist

Once the application is running on your TCS laptop, verify it with this checklist:

- [ ] **Access Page**: Open `http://localhost:3000`. You should see the chat app home screen with an "AI Assistant" prompt in the middle.
- [ ] **Admin Login**: Click the Chat bubble icon in the bottom right, go to login, or go directly to `http://localhost:3000/admin`. Log in using `admin` / `admin123`.
- [ ] **Vector Search Test**: Ask the chatbot: *"What is event sourcing?"*
  - *Verify*: The response streams in token-by-token and answers using details retrieved from the PDF.
- [ ] **FAQ Check**: Ask the chatbot: *"How do I reset my password?"*
  - *Verify*: It returns the direct answer immediately without needing to search the PDF document.
- [ ] **Database Inspection**: In the Admin Dashboard, under the **Chat Logs** tab, verify that your queries appear in the logs with correct metadata and timestamps.
- [ ] **AI Configuration**: In the Admin Dashboard, navigate to the **AI Config** tab. Confirm it matches the parameters in your backend `.env` file.

---

### 🚨 Troubleshooting Port Conflicts
If your TCS laptop uses Port `3000` or `8000` for corporate software:
1. Update `DJANGO_PORT` and `FRONTEND_PORT` inside `backend/.env`.
2. In `frontend/vite.config.js`, change the `port: 3000` value to your new frontend port, and update `CORS_ALLOWED_ORIGINS` in your `.env` to match.
