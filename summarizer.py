# summarizer.py (SAFE MODE)
import os
import re
import heapq
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ============================================================
# LOCAL SUMMARIZER (Free fallback)
# ============================================================
def local_summarize(text, sentence_count=5):
    print("🟢 Using LOCAL summarizer (Free Mode)")

    if not text or len(text) < 200:
        return text

    clean_text = text.replace("\n", " ")
    sentences = re.split(r'(?<=[.!?]) +', clean_text)

    words = re.findall(r'\w+', text.lower())
    freq = {}
    for word in words:
        freq[word] = freq.get(word, 0) + 1

    scores = {}
    for sent in sentences:
        for word in sent.lower().split():
            if word in freq:
                scores[sent] = scores.get(sent, 0) + freq[word]

    summary_sentences = heapq.nlargest(sentence_count, scores, key=scores.get)
    summary = " ".join(summary_sentences)

    return summary


# ============================================================
# GPT SUMMARIZER (Only used if API enabled)
# ============================================================
def gpt_summarize(text):
    # If no API key → skip
    if not OPENAI_API_KEY:
        print("⚠️ GPT summarizer disabled by admin (Sudheer).")
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)

        print("🔵 Trying GPT summarizer (max 120 tokens)...")

        prompt = f"""
        Summarize the following text into 5–7 short bullet points.
        Keep summary short, clean, and under 120 tokens.

        TEXT:
        {text}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120
        )

        print("🔵 GPT summary successful!")
        return response.choices[0].message.content

    except Exception as e:
        print(f"⚠️ GPT summarizer error: {e}")
        return None


# ============================================================
# MASTER SUMMARIZER
# ============================================================
def summarize(text):
    # If GPT disabled → use local
    if not OPENAI_API_KEY:
        print("⚠️ GPT disabled — using local summarizer.")
        return local_summarize(text)

    # Try GPT summarizer
    gpt_output = gpt_summarize(text)

    if gpt_output:
        return gpt_output

    # Fallback to local summarizer
    print("🔁 Falling back to LOCAL summarizer.")
    return local_summarize(text)
