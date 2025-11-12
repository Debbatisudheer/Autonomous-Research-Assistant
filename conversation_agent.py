# conversation_agent.py (UPDATED FOR API SAFETY MODE)

import os
from ask_memory import answer_from_memory
from rag_memory import init_and_connect
from agent import ResearchAgent

# API safety check
OPENAI_ENABLED = bool(os.environ.get("OPENAI_API_KEY"))
PINECONE_ENABLED = bool(os.environ.get("PINECONE_API_KEY"))

if not OPENAI_ENABLED:
    GPT_DISABLED_MSG = "❌ GPT disabled by admin (Sudheer)."
else:
    GPT_DISABLED_MSG = None

if not PINECONE_ENABLED:
    MEMORY_DISABLED_MSG = "❌ Memory disabled by admin (Sudheer)."
else:
    MEMORY_DISABLED_MSG = None


class ConversationAgent:

    def __init__(self):
        print("\n🔧 Initializing Conversation Agent...")

        # Initialize Pinecone only if allowed
        if PINECONE_ENABLED:
            try:
                init_and_connect()
                print("✅ Memory connected (Pinecone).")
            except Exception as e:
                print(f"❌ Pinecone initialization failed: {e}")
        else:
            print(MEMORY_DISABLED_MSG)

        self.history = []
        print("✅ Conversation Agent Ready.\n")

    def ask(self, query):
        print(f"\n🧠 User asked: {query}")
        self.history.append(query)

        # -----------------------------------
        # 1️⃣ MEMORY LOOKUP (only if allowed)
        # -----------------------------------
        if not PINECONE_ENABLED:
            print("⚠️ Memory disabled, cannot search Pinecone.")
        else:
            print("🔎 Searching Pinecone memory...")
            try:
                answer = answer_from_memory(query)
                if answer:
                    return answer
            except Exception as e:
                print(f"❌ Memory search error: {e}")

        # ------------------------------------------------
        # 2️⃣ GPT OFF? → Stop here (NO web research allowed)
        # ------------------------------------------------
        if not OPENAI_ENABLED:
            return GPT_DISABLED_MSG

        # ------------------------------------------------
        # 3️⃣ Run Web Research Agent (uses GPT internally)
        # ------------------------------------------------
        print("\n⚠️ Memory insufficient. Running web research...")

        try:
            researcher = ResearchAgent(query, max_articles=2)
            report = researcher.run()
        except Exception as e:
            return f"❌ Research failed: {e}"

        # ------------------------------------------------
        # 4️⃣ Retry memory after adding new research
        # ------------------------------------------------
        if PINECONE_ENABLED:
            print("🔁 Retrying memory after research...")
            try:
                answer = answer_from_memory(query)
                if answer:
                    return answer
            except:
                pass

        # ------------------------------------------------
        # 5️⃣ Fallback return
        # ------------------------------------------------
        return "I could not find enough information, even after research."
