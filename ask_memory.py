# ask_memory.py (SAFE MODE, GPT OFFLINE PROTECTED)

import os
from openai import OpenAI
from rag_memory import query_memory

# Detect if APIs are enabled
OPENAI_ENABLED = bool(os.environ.get("OPENAI_API_KEY"))
PINECONE_ENABLED = bool(os.environ.get("PINECONE_API_KEY"))


def answer_from_memory(question: str, top_k=5):
    """
    Answer a question only using Pinecone memory + GPT.
    If GPT or Pinecone are disabled → return safe fallback.
    """

    # ------------------------------------------
    # 1️⃣ Memory disabled → cannot search Pinecone
    # ------------------------------------------
    if not PINECONE_ENABLED:
        print("❌ Memory disabled by admin (Sudheer). No Pinecone key.")
        return None

    print("🔎 Searching Pinecone memory...")
    matches = query_memory(question, top_k=top_k)

    if not matches:
        print("⚠️ No memory found.")
        return None

    print(f"📚 Found {len(matches)} relevant memory chunks.")

    # Build memory context
    memory_text = "\n".join([
        f"- {m['metadata'].get('summary', '')}"
        for m in matches
        if m["metadata"].get("summary")
    ])

    # ------------------------------------------
    # 2️⃣ GPT disabled → cannot generate answer
    # ------------------------------------------
    if not OPENAI_ENABLED:
        print("❌ GPT disabled by admin (Sudheer).")
        return "❌ GPT disabled by admin (Sudheer). Cannot generate answer."

    # Build prompt
    prompt = f"""
Use ONLY the memory below to answer the question.

### MEMORY:
{memory_text}

### QUESTION:
{question}

Provide a short and clear answer.
"""

    print("🤖 Generating GPT answer...")
    client = OpenAI()

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0.2,
            max_tokens=200,
            messages=[
                {"role": "system", "content": "You answer strictly using memory."},
                {"role": "user", "content": prompt}
            ]
        )

        # Correct new SDK format
        return response.choices[0].message.content

    except Exception as e:
        print(f"❌ GPT Error: {e}")
        return "❌ GPT error while answering."
