# cleanup_pdf_memory.py

from pinecone import Pinecone
import os

INDEX_NAME = os.getenv("INDEX_NAME", "research-memory")

def delete_pdf_chunks():
    api_key = os.getenv("PINECONE_API_KEY")
    region = os.getenv("PINECONE_REGION", "us-east-1")

    pc = Pinecone(api_key=api_key)
    index = pc.Index(INDEX_NAME)

    print("🔍 Fetching PDF-related vectors...")

    # Query all PDF metadata entries
    results = index.query(
        vector=[0.0] * 1536,
        filter={"source": {"$eq": "PDF"}},
        top_k=500
    )

    if not results.matches:
        print("✅ No PDF chunks found in memory.")
        return

    ids = [m.id for m in results.matches]

    print(f"🗑 Deleting {len(ids)} PDF chunks...")

    index.delete(ids)

    print("✅ PDF chunks deleted successfully!")

if __name__ == "__main__":
    delete_pdf_chunks()
