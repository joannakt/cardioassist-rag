# CardioAssist

A production RAG chatbot deployed on the website of Comprehensive Cardiology, a multi-location cardiology clinic in the Houston, TX area. Patients can ask questions about appointments, insurance, services, locations, and clinic providers — and get accurate, grounded responses instantly without calling the office.

**Live at:** [ccheart.clinic](https://ccheart.clinic)

---

## What It Does

CardioAssist answers common patient questions by retrieving relevant context from a curated clinic knowledge base and generating responses via the Claude API. It handles questions about:

- Appointment scheduling and new patient intake
- Insurance plans accepted
- Clinic locations and hours
- Services offered (echocardiogram, stress testing, cardiac PET imaging, etc.)
- Provider information
- Patient portal (Healow) setup
- Hospital affiliations

For anything outside its knowledge base or any medical emergency, it directs patients to call the clinic directly or dial 911.

---

## Architecture

```
Patient question
      ↓
FastAPI backend (main.py)
      ↓
ChromaDB vector store — semantic search over clinic FAQ chunks (ingest.py)
      ↓
Retrieved context injected into system prompt
      ↓
Claude API (claude-sonnet-4-6) generates grounded response
      ↓
Response returned to frontend widget
```

**Stack:**
- **Backend:** FastAPI + Uvicorn
- **Vector store:** ChromaDB (persistent, local)
- **Embeddings:** ChromaDB DefaultEmbeddingFunction
- **LLM:** Anthropic Claude API (claude-sonnet-4-6)
- **Deployment:** Render.com
- **Frontend:** Embedded chat widget on clinic website

---

## Project Structure

```
cardioassist/
├── main.py          # FastAPI app — chat endpoint, system prompt, Claude API call
├── ingest.py        # Ingestion pipeline — loads .txt docs into ChromaDB
├── documents/       # Clinic knowledge base (.txt files, chunked by Q&A pair)
├── chroma_db/       # Persistent ChromaDB vector store (gitignored)
├── requirements.txt
├── Procfile         # Render deployment config
└── .env             # API keys (gitignored)
```

---

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/joannakt/cardioassist.git
cd cardioassist
pip install -r requirements.txt
```

### 2. Set environment variables

Create a `.env` file:
```
ANTHROPIC_API_KEY=your_key_here
```

### 3. Ingest clinic documents

Add `.txt` files to the `documents/` folder, then run:
```bash
python ingest.py
```

Documents are split by double newline into Q&A chunks and embedded into ChromaDB.

### 4. Run the backend

```bash
uvicorn main:app --reload
```

API available at `http://localhost:8000`

---

## API

### `POST /chat`

**Request:**
```json
{
  "messages": [
    { "role": "user", "content": "What insurance do you accept?" }
  ]
}
```

**Response:**
```json
{
  "reply": "We accept most major insurance plans including Medicare, Medicaid, Blue Cross Blue Shield, Aetna, Humana, and United Healthcare. Please call our office at (281) 333-9200 to verify your specific plan before your visit."
}
```

### `GET /`

Health check — returns `{ "status": "CardioAssist backend is running!" }`

---

## Deployment

Deployed on Render.com via the included `Procfile`:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

`ANTHROPIC_API_KEY` is set as an environment variable in the Render dashboard — never hardcoded.

---

## Design Decisions

**Why RAG?** The base Claude API has no knowledge of clinic-specific details like hours, providers, or insurance. Without retrieval, it would hallucinate plausible but incorrect answers. RAG grounds every response in verified clinic information.

**Why ChromaDB?** Lightweight, persistent, and deployable without a separate database service — appropriate for the scale of a small clinic knowledge base.

**Why FastAPI?** Async-native, minimal boilerplate, and straightforward to deploy on Render with a single Procfile line.

---

## Requirements

```
fastapi
uvicorn
anthropic
python-dotenv
chromadb
```
