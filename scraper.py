# scraper.py

import time
import requests
from bs4 import BeautifulSoup

# Selenium imports (works locally but fails in Streamlit)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# ---------------------------------------------------------
# 1️⃣ PRIMARY: Selenium Search (Local PC)
# ---------------------------------------------------------
def selenium_duckduckgo_search(query):
    try:
        print("🟦 Trying Selenium search...")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get("https://lite.duckduckgo.com/lite/")

        box = driver.find_element(By.NAME, "q")
        box.send_keys(query)
        box.send_keys(Keys.RETURN)
        time.sleep(2)

        html = driver.page_source
        driver.quit()

        soup = BeautifulSoup(html, "html.parser")
        results = []

        for a in soup.select("a.result-link"):
            title = a.get_text(strip=True)
            url = a.get("href")

            if not url.startswith("http"):
                continue
            if title.lower() in ["more info", "ad", "sponsored"]:
                continue

            results.append({"title": title, "url": url})

        print(f"🟦 Selenium found {len(results)} results.")
        return results

    except Exception as e:
        print("⚠️ Selenium search failed:", e)
        return None


# ---------------------------------------------------------
# 2️⃣ FALLBACK: Cloud-safe request search (Streamlit)
# ---------------------------------------------------------
def fallback_duckduckgo_search(query):
    try:
        print("🌐 Using fallback search (HTML)...")

        r = requests.post("https://duckduckgo.com/html/", data={"q": query}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        results = []

        for a in soup.select(".result__a"):
            title = a.get_text(strip=True)
            url = a.get("href")
            if url.startswith("http"):
                results.append({"title": title, "url": url})

        print(f"🌐 Fallback found {len(results)} results.")
        return results

    except Exception as e:
        print("❌ Fallback search failed:", e)
        return []


# ---------------------------------------------------------
# 3️⃣ MASTER SEARCH FUNCTION (Auto Switch)
# ---------------------------------------------------------
def duckduckgo_search(query):
    # Try Selenium first
    res = selenium_duckduckgo_search(query)
    if res and len(res) > 0:
        return res

    # Fallback for Streamlit cloud
    return fallback_duckduckgo_search(query)


# ---------------------------------------------------------
# FETCH PAGE CONTENT (used in agent.py)
# ---------------------------------------------------------
def fetch_page_text(url):
    print(f"🌍 Fetching page: {url}")

    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]

        if not paragraphs:
            return ""

        # Return first ~20 paragraphs (enough for summary)
        return "\n".join(paragraphs[:20])

    except Exception as e:
        print("❌ Error fetching page:", e)
        return ""
