from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import anthropic
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# CORS so your website can talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Claude client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
embedding_fn = embedding_functions.DefaultEmbeddingFunction()

collection = chroma_client.get_or_create_collection(
    name="clinic_faqs",
    embedding_function=embedding_fn
)

# Request model
class ChatRequest(BaseModel):
    messages: List[dict]

def get_relevant_context(query: str) -> str:
    results = collection.query(
        query_texts=[query],
        n_results=3
    )
    if results and results["documents"]:
        return "\n\n".join(results["documents"][0])
    return ""

@app.post("/chat")
async def chat(request: ChatRequest):
    # Get the latest user message
    user_message = request.messages[-1]["content"]
    
    # Retrieve relevant context from ChromaDB
    context = get_relevant_context(user_message)
    
    # System prompt with RAG context
    system_prompt = f"""You are CardioAssist, a friendly and professional virtual assistant for Comprehensive Cardiology, a cardiology clinic in the Houston, TX area.

You help patients with questions about appointments, insurance, services, and general cardiology information.

Use the following clinic information to answer questions:
{context}

Important rules:
- Always be warm, helpful, and professional
- For medical emergencies, always direct patients to call 911
- Never provide specific medical diagnoses or treatment advice
- If you don't know something, direct patients to call (281) 333-9200
- Keep responses concise and easy to read
- Never use markdown formatting like **bold**, ## headers, or bullet points with dashes. Use plain conversational text only.
- You are not a substitute for professional medical advice"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=system_prompt,
        messages=request.messages
    )
    
    return {"reply": response.content[0].text}

@app.get("/")
async def root():
    return {"status": "CardioAssist backend is running!"}