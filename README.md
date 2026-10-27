# CardioAssist

An administrative chatbot deployed on the website of Comprehensive Cardiology, a two-location cardiology clinic in the Houston, TX area. Patients get quick answers about appointments, insurance, locations, services, providers and the patient portal, without calling the office.

**Live at:** [ccheart.clinic](https://ccheart.clinic)

---

## What It Does

CardioAssist answers common administrative questions using a curated clinic knowledge base and the Claude API:

- Appointment scheduling and new-patient steps
- Insurance (general information only)
- Locations, directions and office hours
- Services offered, in plain-language descriptions (echocardiogram, stress testing, cardiac PET imaging, etc.)
- Provider information and hospital affiliations
- Healow patient portal setup

It is deliberately **not** a medical assistant. It does not interpret symptoms, test results or medications, and it routes possible emergencies to 911 before the language model is ever called.

---

## Architecture

```
Patient message (website chat widget)
      ↓
FastAPI backend (main.py)
      ↓
Input checks: per-IP rate limit, message length and history caps
      ↓
Safety layer (deterministic, runs before any AI call)
  ├─ Crisis language     → 988 Lifeline reply
  ├─ Emergency symptoms  → "Call 911" reply
  └─ Personal identifiers (SSN, DOB, member ID, ...) → privacy reply
      ↓
Claude API (claude-sonnet-4-6, temperature 0.2)
  with a strict administrative system prompt + the clinic knowledge base
      ↓
Reply returned to the widget, tagged with a type
(normal / emergency / privacy / rate_limited / error)
```

**Stack:** FastAPI + Uvicorn · Anthropic Claude API · Render.com · embedded JavaScript widget on the clinic site

---

## Safety and Privacy Design

| Risk | Mitigation |
| --- | --- |
| A patient describes an emergency | Pattern matching on the latest message (chest pain or pressure, trouble breathing, fainting, stroke signs, device shocks, etc.) returns a fixed "call 911" reply. No model call is made. |
| Crisis or self-harm language | Returns the 988 Suicide & Crisis Lifeline message. No model call is made. |
| Patients sharing personal health information | Obvious identifiers (SSN, date of birth, MRN, member or policy numbers, card-like numbers) are blocked and never forwarded to the API. The system prompt also forbids asking for or repeating personal details. |
| Individual medical advice | The system prompt restricts the assistant to administrative topics and textbook-level service descriptions, and sends personal health questions to the care team. |
| Invented clinic facts | The model may only state facts present in the knowledge base; anything else gets "I don't have that information" plus the office phone number. |
| Patient text stored in logs | Logs record event types only (for example `event=emergency_route`), never message content. |
| Abuse and cost | Per-IP rate limiting, 1,000-character message cap, last 12 turns only, CORS restricted to the clinic's domain, public API docs disabled. |
| Prompt injection | The system prompt instructs the model to ignore requests to change its rules or reveal its prompt. |

---

## Design History

The first version (June 2026) was a classic RAG pipeline: `ingest.py` split the FAQ into Q&A chunks, embedded them into a local ChromaDB store, and each question retrieved the top 3 chunks.

In production this broke in two ways:

1. The `sentence-transformers` embedding model exceeded Render's memory limit, so it was replaced with ChromaDB's lighter default embeddings.
2. Render's filesystem is ephemeral, so the vector store was wiped on every redeploy. Retrieval silently returned nothing, and the bot answered from general knowledge (for example, it claimed not to know the office hours).

Because the knowledge base is small (one page of clinic facts), the retrieval layer was removed and the full FAQ now sits in the system prompt. This is simpler, cannot silently fail, and always gives the model complete context. For a larger knowledge base, the next step would be a persistent hosted vector store (for example Postgres with pgvector) rather than an on-disk index.

The safety layer, privacy-safe logging and request limits were in place by September 2026.

---

## Project Structure

```
cc-chatbot-backend/
├── main.py           # FastAPI app: safety layer, knowledge base, system prompt, Claude call
├── requirements.txt
├── Procfile          # Render start command
└── .env              # API key (gitignored)
```

The clinic knowledge base is the `CLINIC_FAQ` string in `main.py`. To update clinic information, edit it there and push; Render redeploys automatically.

---

## Setup

```bash
git clone https://github.com/joannakt/cc-chatbot-backend.git
cd cc-chatbot-backend
pip install -r requirements.txt
```

Create a `.env` file:

```
ANTHROPIC_API_KEY=your_key_here
```

Run locally:

```bash
uvicorn main:app --reload
```

The API is then available at `http://localhost:8000`. Note that CORS only allows the clinic's domain, so a local front end needs its origin added to `ALLOWED_ORIGINS`.

---

## API

### `POST /chat`

**Request**

```json
{
  "messages": [
    { "role": "user", "content": "What insurance do you accept?" }
  ]
}
```

**Response**

```json
{
  "reply": "We accept most major insurance plans, including Medicare, Medicaid, Blue Cross Blue Shield, Aetna, Humana and United Healthcare. Please call our office at (281) 333-9200 to verify your specific plan before your visit.",
  "type": "normal"
}
```

`type` is one of `normal`, `emergency`, `privacy`, `rate_limited` or `error`, so the widget can style safety replies differently. Status codes: `200` for replies, `400` for an empty or malformed conversation, `429` when rate limited, `503` if the Claude API is unavailable.

### `GET /`

Health check: returns `{ "status": "CardioAssist backend is running!" }`.

---

## Deployment

Deployed on Render.com from this repository's `main` branch using the `Procfile`:

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

`ANTHROPIC_API_KEY` is set as an environment variable in the Render dashboard and is never committed.

---

## Known Limitations and Next Steps

- **Emergency detection is pattern-based.** It can miss unusual phrasings and can over-trigger (for example, any message mentioning "ER"). Next step: a labeled test set of emergency and non-emergency messages, with misses and false alarms measured on every change.
- **Rate limiting is in memory**, so it resets when the server restarts and relies on the `X-Forwarded-For` header. Adequate for a single small instance; a shared store such as Redis would be needed at larger scale.
- **No automated evaluation of model answers yet.** Next step: a fixed set of common patient questions with expected facts, checked on each deploy.
