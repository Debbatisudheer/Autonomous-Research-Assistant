# scraper_safe.py  (rename to scraper.py)

import time
import requests
from bs4 import BeautifulSoup

# ONLY Selenium imports if user has it installed
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except Exception:
    print("⚠️ Selenium not available — falling back to requests-only mode.")
    SELENIUM_AVAILABLE = False

from summarizer import summarize   # Safe summarizer (local fallback included)


# ============================================================
# SAFE DUCKDUCKGO SEARCH
# ============================================================
def duckduckgo_search(query):
    """
    Searches DuckDuckGo Lite using Selenium.
    If Selenium not available → fallback to simple requests.
    """

    # If Selenium works → use full search
    if SELENIUM_AVAILABLE:
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
            driver.get("https://lite.duckduckgo.com/lite/")

            search_box = driver.find_element(By.NAME, "q")
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)

            time.sleep(2)
            html = driver.page_source
            driver.quit()

            soup = BeautifulSoup(html, "html.parser")
            return extract_results(soup)

        except Exception as e:
            print(f"⚠️ Selenium search failed: {e}")
            print("➡️ Falling back to requests-only search.")

    # ---------- FALLBACK MODE ----------
    params = {"q": query}
    url = "https://duckduckgo.com/html/"
    r = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"})

    soup = BeautifulSoup(r.text, "html.parser")
    return extract_results(soup)


# ============================================================
# PARSE SEARCH RESULTS
# ============================================================
def extract_results(soup):
    results = []

    for a in soup.select("a[href]"):
        title = a.get_text().strip()
        url = a["href"]

        # Remove junk
        if not url.startswith("http"):
            continue
        if "duckduckgo-help" in url:
            continue
        if "ads-by-microsoft" in url:
            continue
        if title.lower() in ["more info", "ad", "sponsored"]:
            continue

        results.append({"title": title, "url": url})

    return results


# ============================================================
# FETCH PAGE TEXT (Clean + Safe)
# ============================================================
def fetch_page_text(url):
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")

        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]

        if not paragraphs:
            return ""

        return "\n".join(paragraphs[:20])

    except Exception as e:
        print(f"⚠️ Error fetching page: {e}")
        return ""


# ============================================================
# STANDALONE TEST
# ============================================================
if __name__ == "__main__":
    query = "AI careers 2025"
    print("🔍 Searching DuckDuckGo for:", query)

    results = duckduckgo_search(query)
    print(results)

    # Pick first valid article
    real_article = None

    for item in results:
        title = item["title"].lower()
        url = item["url"].lower()

        if "duckduckgo-help-pages" in url:
            continue
        if "ads-by-microsoft" in url:
            continue
        if title == "more info":
            continue

        real_article = item
        break

    if real_article:
        print("\n--- Extracting REAL article text ---\n")
        page_text = fetch_page_text(real_article["url"])

        print("\n--- LOCAL/GPT SUMMARY (Safe Mode) ---\n")
        print(summarize(page_text))
    else:
        print("No valid articles found!")
