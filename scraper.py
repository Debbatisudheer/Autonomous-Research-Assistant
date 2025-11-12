# scraper.py

import requests
from bs4 import BeautifulSoup
import time

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# ---------------------------------------------------------
# 1️⃣ PRIMARY: Selenium Search (works on your local PC)
# ---------------------------------------------------------
def selenium_duckduckgo_search(query):
    try:
        print("🟦 Trying Selenium search...")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get("https://lite.duckduckgo.com/lite/")

        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

        time.sleep(2)

        html = driver.page_source
        driver.quit()

        soup = BeautifulSoup(html, "html.parser")
        results = []

        for a in soup.select("a.result-link"):
            url = a["href"]
            title = a.text.strip()

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
# 2️⃣ FALLBACK: Cloud-Safe HTML Request (works on Streamlit)
# ---------------------------------------------------------
def fallback_duckduckgo_search(query):
    print("🌐 Falling back to cloud-safe DDG search...")

    try:
        url = "https://duckduckgo.com/html/"
        data = {"q": query}

        r = requests.post(url, data=data, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        results = []
        for a in soup.select(".result__a"):
            title = a.get_text(strip=True)
            href = a.get("href")
            if href.startswith("http"):
                results.append({"title": title, "url": href})

        print(f"🌐 Fallback found {len(results)} results.")
        return results

    except Exception as e:
        print("❌ Fallback search failed:", e)
        return []


# ---------------------------------------------------------
# 3️⃣ MASTER SEARCH FUNCTION (Auto-switch)
# ---------------------------------------------------------
def duckduckgo_search(query):
    # Try Selenium first
    selenium_results = selenium_duckduckgo_search(query)

    if selenium_results and len(selenium_results) > 0:
        return selenium_results

    # If Selenium fails → Fallback
    return fallback_duckduckgo_search(query)
