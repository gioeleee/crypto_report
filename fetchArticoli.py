import sqlite3
import time
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

DB_PATH = "crypto_news.db"  # Cambia se usi un path diverso
BASE_URL = "https://cryptopanic.com"

def fetchUrlArticoliCryptopanic():
    chrome_options = Options()
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(f"{BASE_URL}/news")
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    news_divs = soup.find_all("div", class_="news-row news-row-link")

    print(f"🔍 Trovati {len(news_divs)} articoli.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    nuovi = 0
    for div in news_divs:
        a_tag = div.find("a", href=True)
        if not a_tag:
            continue

        relative_url = a_tag["href"]
        full_url = BASE_URL + relative_url
        print(full_url)

        #try:
        #    cursor.execute("""
        #        INSERT OR IGNORE INTO meta_articoli (cryptopanic_url)
        #        VALUES (?)
        #    """, (full_url,))
        #    if cursor.rowcount > 0:
        #        nuovi += 1
        #except Exception as e:
        #    print(f"Errore nel salvataggio URL {full_url}: {e}")

    conn.commit()
    conn.close()

    print(f"✅ {nuovi} nuovi link salvati nel database.")



