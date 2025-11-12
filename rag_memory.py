# rag_memory.py (SAFE MODE UPDATE — NO API CRASHES)

import os
import uuid
import time
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
from pinecone_init import init_pinecone, ensure_index, INDEX_NAME

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

EMBED_MODEL = "text-embedding-3-small"

# Safe flags
OPENAI_ENABLED = bool(OPENAI_API_KEY)
PINECONE_ENABLED = bool(PINECONE_API_KEY)

pc = None
index = None


# ----------------------------------------------
# SAFE INIT: Prevent crashes when Pinecone is OFF
# ----------------------------------------------
def init_and_connect(index_name=INDEX_NAME):
    """
    Initialize Pinecone + connect to index.
    If Pinecone is disabled → returns None.
    """

    global pc, index

    if not PINECONE_ENABLED:
        print("❌ Memory disabled by admin (Sudheer). Pinecone API key missing.")
        return None

    print("🔧 Initializing Pinecone memory...")

    try:
        pc = init_pinecone()  # safe
    except Exception as e:
        print(f"❌ Pinecone initialization failed: {e}")
        return None

    # Cannot generate embedding if GPT is disabled
    if not OPENAI_ENABLED:
        print("❌ GPT disabled by admin (Sudheer). Cannot compute embedding dimensions.")
        return None

    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        emb = client.embeddings.create(
            model=EMBED_MODEL,
            input="dimension test"
        )
    except Exception as e:
        print(f"❌ GPT embedding error: {e}")
        return None

    dimension = len(emb.data[0].embedding)

    try:
        ensure_index(index_name, dimension)
        index = pc.Index(index_name)
        print(f"✅ Connected to Pinecone index: {index_name}")
        return index
    except Exception as e:
        print(f"❌ Failed to connect to index: {e}")
        return None


# ----------------------------------------------
# SAFE EMBEDDING FUNCTION
# ----------------------------------------------
def embed_text(text: str):
    """Generate embeddings safely."""

    if not OPENAI_ENABLED:
        print("❌ GPT disabled by admin (Sudheer). Cannot generate embeddings.")
        return None

    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        emb = client.embeddings.create(
            model=EMBED_MODEL,
            input=text
        )
        return emb.data[0].embedding
    except Exception as e:
        print(f"❌ Embedding error: {e}")
        return None


# ----------------------------------------------
# UPSERT (store memory) with safety
# ----------------------------------------------
def upsert_summary(title: str, url: str, summary: str, source="web"):
    global index

    if not PINECONE_ENABLED:
        print("❌ Cannot store memory. Pinecone disabled by admin (Sudheer).")
        return

    if not OPENAI_ENABLED:
        print("❌ Cannot embed summary. GPT disabled by admin (Sudheer).")
        return

    if index is None:
        print("❌ No active Pinecone index.")
        return

    vector = embed_text(summary or title)
    if vector is None:
        return

    meta = {
        "title": title,
        "url": url,
        "summary": summary,
        "source": source,
        "timestamp": int(time.time())
    }

    vid = str(uuid.uuid4())

    try:
        index.upsert(vectors=[{
            "id": vid,
            "values": vector,
            "metadata": meta
        }])
        print(f"🧠 Stored in Pinecone: {title}")
    except Exception as e:
        print(f"❌ Upsert failed: {e}")


# ----------------------------------------------
# QUERY MEMORY (RAG) with Safety
# ----------------------------------------------
def query_memory(question: str, top_k: int = 5):
    global index

    if not PINECONE_ENABLED:
        print("❌ Memory disabled by admin (Sudheer). Cannot query memory.")
        return []

    if not OPENAI_ENABLED:
        print("❌ Cannot generate query embeddings. GPT disabled by admin (Sudheer).")
        return []

    if index is None:
        print("❌ No active Pinecone index.")
        return []

    vector = embed_text(question)
    if vector is None:
        return []

    try:
        result = index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True
        )
    except Exception as e:
        print(f"❌ Memory query error: {e}")
        return []

    matches = []
    try:
        for m in result["matches"]:
            matches.append({
                "id": m["id"],
                "score": m["score"],
                "metadata": m["metadata"]
            })
    except:
        return []

    return matches
