import chromadb
from chromadb.utils import embedding_functions
import os

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Use sentence transformers for embeddings
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Create or get collection
collection = chroma_client.get_or_create_collection(
    name="clinic_faqs",
    embedding_function=embedding_fn
)

def load_documents():
    docs_path = "./documents"
    documents = []
    ids = []
    
    for i, filename in enumerate(os.listdir(docs_path)):
        if filename.endswith(".txt"):
            with open(os.path.join(docs_path, filename), "r") as f:
                content = f.read()
                # Split by double newline to get individual Q&A pairs
                chunks = [c.strip() for c in content.split("\n\n") if c.strip()]
                for j, chunk in enumerate(chunks):
                    documents.append(chunk)
                    ids.append(f"{filename}_{i}_{j}")
    
    return documents, ids

def ingest():
    print("Loading documents...")
    documents, ids = load_documents()
    
    print(f"Found {len(documents)} chunks to ingest...")
    
    collection.add(
        documents=documents,
        ids=ids
    )
    
    print("Documents ingested successfully!")

if __name__ == "__main__":
    ingest()