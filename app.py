# app.py (UPDATED WITH API SAFETY MODE)

import os
import streamlit as st
from datetime import datetime
from conversation_agent import ConversationAgent
from agent import ResearchAgent, save_txt_md_pdf
from pdf_ingest import ingest_pdf, extract_pdf_text
from rag_memory import init_and_connect, query_memory
from ask_memory import answer_from_memory
from openai import OpenAI

# -------------------------------------------------------
# API SAFETY MODE
# -------------------------------------------------------
OPENAI_ENABLED = bool(os.environ.get("OPENAI_API_KEY"))
PINECONE_ENABLED = bool(os.environ.get("PINECONE_API_KEY"))

# If OpenAI or Pinecone unavailable → GPT and Memory disabled
if not OPENAI_ENABLED:
    GPT_DISABLED_MSG = "❌ GPT disabled by admin (Sudheer)."
else:
    GPT_DISABLED_MSG = None

if not PINECONE_ENABLED:
    MEMORY_DISABLED_MSG = "❌ Memory disabled by admin (Sudheer)."
else:
    MEMORY_DISABLED_MSG = None

# Client only created if key exists
client = OpenAI() if OPENAI_ENABLED else None

# -------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------
st.set_page_config(page_title="Autonomous Research Assistant", layout="wide")

st.title("🧠 Autonomous Research Assistant — Chat + PDF + Research")
st.markdown("Built: Chat + Pinecone memory + PDF ingestion + web research")

# -------------------------------------------------------
# INIT MEMORY (ONLY IF ENABLED)
# -------------------------------------------------------
with st.spinner("Initializing memory..."):
    if not PINECONE_ENABLED:
        st.warning(MEMORY_DISABLED_MSG)
    else:
        try:
            init_and_connect()
            st.success("Memory initialized (Pinecone connected).")
        except Exception as e:
            st.error(f"Pinecone init error: {e}")

# -------------------------------------------------------
# SESSION STATE
# -------------------------------------------------------
if "agent" not in st.session_state:
    st.session_state.agent = ConversationAgent()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -------------------------------------------------------
# LAYOUT
# -------------------------------------------------------
left, right = st.columns([3, 1])

# ================================
# LEFT: CHAT PANEL
# ================================
with left:
    st.subheader("Chat")

    # Display chat history
    for (u, a) in st.session_state.chat_history:
        st.markdown(f"**You:** {u}")
        st.markdown(f"**Assistant:** {a}")
        st.write("---")

    # Input box
    user_input = st.text_input("Ask a question or type a research topic", key="user_input")

    cols = st.columns([1, 1, 1])
    send_btn = cols[0].button("Send", key="send")
    research_btn = cols[1].button("Run Research", key="run_research")
    clear_btn = cols[2].button("Clear Chat", key="clear_chat")

    # CLEAR CHAT
    if clear_btn:
        st.session_state.chat_history = []
        st.rerun()

    # SEND CHAT MESSAGE
    if send_btn and user_input:

        if not OPENAI_ENABLED:
            st.error(GPT_DISABLED_MSG)
        else:
            with st.spinner("🧠 Thinking..."):
                try:
                    answer = st.session_state.agent.ask(user_input)
                    st.session_state.chat_history.append((user_input, answer))
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # RUN AUTONOMOUS RESEARCH
    if research_btn and user_input:

        if not OPENAI_ENABLED:
            st.error(GPT_DISABLED_MSG)
        else:
            with st.spinner("🔎 Running autonomous research..."):
                try:
                    researcher = ResearchAgent(query=user_input, max_articles=2)
                    report = researcher.run()

                    saved = save_txt_md_pdf(
                        report,
                        out_base=f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    )

                    st.success("Research completed and saved.")
                    st.write(report)

                    # Download buttons
                    st.download_button("Download TXT", data=open(saved["txt"], "rb").read(),
                                       file_name=os.path.basename(saved["txt"]))
                    st.download_button("Download MD", data=open(saved["md"], "rb").read(),
                                       file_name=os.path.basename(saved["md"]))
                    with open(saved["pdf"], "rb") as f:
                        st.download_button("Download PDF", data=f.read(),
                                           file_name=os.path.basename(saved["pdf"]))

                except Exception as e:
                    st.error(f"Research failed: {e}")

# ================================
# RIGHT: TOOLS PANEL
# ================================
with right:
    st.subheader("Tools")

    # ----------------------------
    # PDF INGEST + SKILL EXTRACTION
    # ----------------------------
    st.markdown("### 📄 PDF Ingest")

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    pdf_name_input = st.text_input("Optional source name (e.g., Resume)")

    if uploaded_file is not None:
        tmp_path = os.path.join("tmp", uploaded_file.name)
        os.makedirs("tmp", exist_ok=True)

        with open(tmp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Ingest to Pinecone
        if st.button("Ingest PDF into memory"):
            if not PINECONE_ENABLED:
                st.error(MEMORY_DISABLED_MSG)
            else:
                with st.spinner("Ingesting PDF..."):
                    try:
                        ingest_pdf(tmp_path, source_name=(pdf_name_input or uploaded_file.name))
                        st.success("PDF ingested into memory.")
                    except Exception as e:
                        st.error(f"Ingest failed: {e}")

        # Extract skills using GPT
        if st.button("Extract Skills From This PDF"):
            if not OPENAI_ENABLED:
                st.error(GPT_DISABLED_MSG)
            else:
                with st.spinner("Extracting skills using GPT..."):
                    try:
                        text = extract_pdf_text(tmp_path)

                        if not text.strip():
                            st.error("PDF contains no extractable text.")
                        else:
                            prompt = f"""
                            Extract skills under:
                            - Technical Skills
                            - Tools & Frameworks
                            - Soft Skills

                            TEXT:
                            {text}
                            """

                            response = client.chat.completions.create(
                                model="gpt-4.1-mini",
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=400
                            )

                            skills = response.choices[0].message.content
                            st.success("Skills extracted successfully!")
                            st.markdown(skills)

                    except Exception as e:
                        st.error(f"Skill extraction failed: {e}")

    st.markdown("---")

    # MEMORY VIEWER
    st.markdown("### 🧾 Memory Viewer")

    mem_q = st.text_input("Enter memory query", key="mem_q")
    mem_k = st.slider("Top K", 1, 10, 4)

    if st.button("Search Memory"):
        if not PINECONE_ENABLED:
            st.error(MEMORY_DISABLED_MSG)
        else:
            with st.spinner("Querying memory..."):
                try:
                    matches = query_memory(mem_q, top_k=mem_k)
                    if not matches:
                        st.info("No matches found.")
                    else:
                        for m in matches:
                            md = m["metadata"]
                            st.write(f"**{md.get('title','(no title)')}** — score: {m.get('score')}")
                            st.write(md.get("summary")[:450] + "...")
                            st.write(md.get("url", ""))
                            st.write("---")
                except Exception as e:
                    st.error(f"Memory query failed: {e}")

    st.markdown("---")

    # RECONNECT MEMORY
    st.markdown("### ⚙️ Utilities")

    if st.button("Reconnect memory"):
        if not PINECONE_ENABLED:
            st.error(MEMORY_DISABLED_MSG)
        else:
            with st.spinner("Reconnecting memory..."):
                try:
                    init_and_connect()
                    st.success("Memory reconnected.")
                except Exception as e:
                    st.error(f"Reconnect failed: {e}")

    st.markdown("### 🔋 Tips")
    st.write("- GPT features disabled automatically if key missing.")
    st.write("- Pinecone memory disabled if key missing.")
    st.write("- Safe for deployment without any API keys.")

st.markdown("---")
st.caption("Autonomous Research Assistant — Streamlit UI (local).")
