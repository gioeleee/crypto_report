import sqlite3
import time
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import database
import utilities

BASE_URL = "https://cryptopanic.com"



def setup_chrome_driver():
    """Crea e restituisce un'istanza di Chrome WebDriver configurata."""
    chrome_options = Options()
    #chrome_options.add_argument("--headless=new")  # Attivalo se serve in produzione
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    #chrome_options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")

    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)



def scroll_news_page(driver, scroll_container, max_pause=2):
    """Esegue lo scroll e clicca 'Load more' fino a quando non ci sono più nuovi articoli."""
    articles_seen = 0
    scroll_attempts = 0

    while True:
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_container)
        time.sleep(max_pause)

        try:
            load_more_button = driver.find_element(By.XPATH, "//button[contains(@class, 'btn-outline-primary')]")
            if load_more_button.is_displayed():
                print("🔽 Bottone 'Load more' trovato. Clicco...")
                driver.execute_script("arguments[0].click();", load_more_button)
                time.sleep(max_pause)
        except:
            pass

        soup = BeautifulSoup(driver.page_source, "html.parser")
        news_divs = soup.find_all("div", class_="news-row news-row-link")
        current_count = len(news_divs)

        print(f"🌀 Scroll {scroll_attempts+1}: {current_count} articoli trovati finora")

        if current_count == articles_seen:
            print("🛑 Scroll terminato: nessun nuovo contenuto caricato.")
            break

        articles_seen = current_count
        scroll_attempts += 1


def estrai_articoli_da_soup(soup):
    """Estrae lista di tuple (url, data, titolo) da un oggetto BeautifulSoup."""
    articoli = []

    for div in soup.find_all("div", class_="news-row news-row-link"):
        a_tag = div.find("a", href=True)
        time_tag = div.find("time", datetime=True)
        title_span = div.find("span", class_="title-text")
        title = None

        if title_span:
            inner_span = title_span.find("span")
            if inner_span:
                title = inner_span.get_text(strip=True)

        if not a_tag:
            continue

        relative_url = a_tag["href"]
        full_url = BASE_URL + relative_url
        published_at_raw = time_tag["datetime"] if time_tag else None
        published_at = utilities.convert_to_sql_datetime(published_at_raw) if published_at_raw else None

        articoli.append((full_url, published_at, title))

    return articoli


def ordina_articoli_per_data(articoli):
    """Ordina la lista di articoli per data crescente (dal più vecchio)."""
    return sorted(
        [a for a in articoli if a[1] is not None],
        key=lambda x: x[1]
    )


def seleziona_feed_italiano(driver):
    try:
        # 1. Passa sopra l'elemento "Region" per mostrare il menu
        region_menu = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".region-switch"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", region_menu)
        webdriver.ActionChains(driver).move_to_element(region_menu).perform()
        time.sleep(1.5)

        # 2. Trova e deseleziona "English" se è attivo
        english_li = driver.find_elements(By.XPATH, "//li[contains(text(), 'English') and contains(@class, 'active')]")
        if english_li:
            print("🌐 Deseleziono English...")
            driver.execute_script("arguments[0].click();", english_li[0])
            time.sleep(1)

        # 3. Assicura che "Italiano" sia attivo
        italiano_li = driver.find_elements(By.XPATH, "//li[contains(text(), 'Italiano') and not(contains(@class, 'active'))]")
        if italiano_li:
            print("🇮🇹 Attivo Italiano...")
            driver.execute_script("arguments[0].click();", italiano_li[0])
            time.sleep(1)

        print("✅ Feed impostato su solo Italiano.")
    except Exception as e:
        print(f"❌ Errore nel filtrare solo italiano: {e}")







def fetchArticoliCryptopanic():
    driver = setup_chrome_driver()
    driver.get(f"{BASE_URL}/news")

    # 👇 Disattiva filtro inglese se attivo
    seleziona_feed_italiano(driver)

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, "news-row"))
    )
    print("✅ Pagina caricata, articoli visibili.")

    scroll_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "news-container"))
    )

    scroll_news_page(driver, scroll_container)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    articoli = estrai_articoli_da_soup(soup)
    articoli_ordinati = ordina_articoli_per_data(articoli)

    database.salvaArticoliCryptopanic(articoli_ordinati)
