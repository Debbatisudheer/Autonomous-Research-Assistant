# pdf_ingest.py  (SAFE DEPLOYMENT MODE — No Pinecone / No GPT required)

import uuid
import time
import os
from pdf_to_text import pdf_to_text

# -------------------------------
# STATUS FLAGS
# -------------------------------
PINECONE_ENABLED = False   # Admin Disabled by Sudheer
GPT_ENABLED = False        # Admin Disabled by Sudheer


# -------------------------------
# Extract raw PDF text (for skill extraction)
# -------------------------------
def extract_pdf_text(pdf_path: str) -> str:
    """
    Extract raw text from PDF.
    Always works because it does NOT require GPT or Pinecone.
    """
    try:
        text = pdf_to_text(pdf_path)
        print("📄 PDF text extracted successfully.")
        return text
    except Exception as e:
        print(f"❌ PDF text extraction failed: {e}")
        return ""


# -------------------------------
# Chunk PDF text (still allowed)
# -------------------------------
def split_text_into_chunks(text, chunk_size=800):
    """
    Keep this working, even if Pinecone is disabled.
    """
    words = text.split()
    chunks = []
    current = []

    for word in words:
        current.append(word)
        if len(current) >= chunk_size:
            chunks.append(" ".join(current))
            current = []

    if current:
        chunks.append(" ".join(current))

    return chunks


# --------------------------------------------------------
# SAFE MODE: Ingest PDF (NO Pinecone)
# --------------------------------------------------------
def ingest_pdf(pdf_path: str, source_name="PDF"):
    """
    In normal mode → PDF is chunked, embedded, uploaded to Pinecone.
    In SAFE MODE → function does nothing except notify user.
    """

    print(f"📄 Attempting to ingest PDF: {pdf_path}...")

    if not PINECONE_ENABLED:
        print("🚫 Pinecone disabled by Admin (Sudheer).")
        print("ℹ️ PDF text extraction still works, but memory ingestion is OFF.")
        print("✔️ Returning safely without error.")
        return

    # If Pinecone ON — run normal ingestion (you can restore later)
    from rag_memory import init_and_connect, embed_text
    from pinecone_init import INDEX_NAME

    text = extract_pdf_text(pdf_path)
    if not text.strip():
        print("❌ PDF appears empty or unreadable.")
        return

    print("✂️ Splitting PDF into chunks...")
    chunks = split_text_into_chunks(text)
    print(f"📦 Total chunks: {len(chunks)}")

    pc = init_and_connect()
    index = pc.Index(INDEX_NAME)

    for i, chunk in enumerate(chunks):
        print(f"🧩 Embedding chunk {i+1}/{len(chunks)}...")
        vector = embed_text(chunk)

        metadata = {
            "title": f"{source_name} - chunk {i+1}",
            "summary": chunk,
            "source": source_name,
            "timestamp": int(time.time())
        }

        index.upsert([{
            "id": str(uuid.uuid4()),
            "values": vector,
            "metadata": metadata
        }])

    print("✅ PDF ingestion complete! Memory added to Pinecone.")
