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
import cleanHtml
import uuid

BASE_URL = "https://cryptopanic.com"


# Crea e restituisce un'istanza di Chrome WebDriver configurata.
def setup_chrome_driver():
    
    # Inizializzia istanza opzioni di Chrome WebDriver
    chrome_options = Options()

    # Disattiva l'accelerazione hardware (opzionale, per maggiore compatibilità)
    chrome_options.add_argument("--disable-gpu")
    # Previene errori di sandboxing su alcune piattaforme Linux
    chrome_options.add_argument("--no-sandbox")
    # Imposta uno user-agent realistico per evitare blocchi da parte dei siti web
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

    #Usa una cartella temporanea diversa per ogni esecuzione
    chrome_options.add_argument(f"--user-data-dir=/tmp/chrome-user-data-{uuid.uuid4()}")

    # (Facoltativo) Usa una cartella temporanea come profilo utente per sessioni isolate
    #chrome_options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")
    # Attiva modalità headless se necessario (non mostra il browser a schermo)
    #chrome_options.add_argument("--headless=new") 

    # Restituisce istanza ChromeDriver con le opzioni configurate
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


# Esegue lo scroll e clicca 'Load more' fino a quando non ci sono più nuovi articoli.
def scroll_news_page(driver, scroll_container, max_pause=2):

    articles_seen = 0 # Conta il numero di articoli rilevati all'inizio
    scroll_attempts = 0 # Conta quanti scroll sono stati eseguiti

    while True:
        # Scrolla in fondo al contenitore che mostra le notizie
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_container)
        time.sleep(max_pause)

        # Tenta di cliccare il bottone "Load more" se è visibile
        try:
            load_more_button = driver.find_element(By.XPATH, "//button[contains(@class, 'btn-outline-primary')]")
            if load_more_button.is_displayed():
                print("🔽 Bottone 'Load more' trovato. Clicco...")
                driver.execute_script("arguments[0].click();", load_more_button)
                time.sleep(max_pause)
        except:
            # Se il bottone non esiste o non è cliccabile, ignora e continua
            pass

        # Analizza il DOM aggiornato per contare gli articoli
        soup = BeautifulSoup(driver.page_source, "html.parser")
        news_divs = soup.find_all("div", class_="news-row news-row-link")
        current_count = len(news_divs)

        print(f"🌀 Scroll {scroll_attempts+1}: {current_count} articoli trovati finora")

        # Interrompe se non sono stati aggiunti nuovi articoli rispetto all’iterazione precedente
        if current_count == articles_seen:
            print("🛑 Scroll terminato: nessun nuovo contenuto caricato.")
            break

        # Aggiorna il numero di articoli rilevati e passa allo scroll successivo
        articles_seen = current_count
        scroll_attempts += 1


# Estrae lista di tuple (url, data, titolo) da un oggetto BeautifulSoup.
def estrai_articoli_da_soup(soup):

    articoli = [] # Lista finale che conterrà tutte le tuple (url, data, titolo)

    # Cicla su tutti i blocchi di notizie standard (esclude quelle sponsorizzate)
    for div in soup.find_all("div", class_="news-row news-row-link"):
        # Cerca il link interno all'articolo (sul sito di CryptoPanic)
        a_tag = div.find("a", href=True)
        # Cerca il tag <time> con attributo datetime (per la data dell'articolo)
        time_tag = div.find("time", datetime=True)
        # Estrae il titolo dell'articolo dal blocco <span class="title-text"><span>Testo</span></span>
        title_span = div.find("span", class_="title-text")
        title = None

        if title_span:
            inner_span = title_span.find("span") # Il vero titolo è nel figlio interno
            if inner_span:
                title = inner_span.get_text(strip=True) # Rimuove spazi extra e newline

        if not a_tag:
            continue # Se non c'è un link, ignora questo blocco

        # Costruisce l'URL completo assoluto partendo dal path relativo
        relative_url = a_tag["href"]
        full_url = BASE_URL + relative_url

        # Converte la stringa datetime in oggetto datetime Python (formato SQL compatibile)
        published_at_raw = time_tag["datetime"] if time_tag else None
        published_at = utilities.convert_to_sql_datetime(published_at_raw) if published_at_raw else None

        # Aggiunge il risultato come tupla alla lista
        articoli.append((full_url, published_at, title))
    
    # Restituisce tutti gli articoli trovati
    return articoli


# Verifica che sia attivo solo il filtro per notizie in italiano
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
    
    # Aspetta tre secondi in modo tale che saranno caricati solo gli articoli in italiano
    time.sleep(3)

### FUNZIONE PRINCIPALE: estrae gli articoli da cryptopanic: titolo, url_cryptopanic e data
def fetch_articoli_cryptopanic():

    # Inizializza chrome driver
    driver = setup_chrome_driver()

    # Apre la pagina principale delle notizie di CryptoPanic
    driver.get(f"{BASE_URL}/news")

    # Disattiva filtro inglese se attivo
    seleziona_feed_italiano(driver)

    # Aspetta che gli articoli siano caricati completamente nel DOM
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, "news-row"))
    )
    print("✅ Pagina caricata, articoli visibili.")

    # Identifica il contenitore scrollabile contenente la lista articoli
    scroll_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "news-container"))
    )

    # Scrolla fino in fondo alla pagina per caricare tutti gli articoli
    scroll_news_page(driver, scroll_container)

    # Analizza l'HTML della pagina interamente scrollata con BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Chiude il browser per liberare risorse
    driver.quit()

    # Estrae tutti i dati utili (titolo, url_cryptopanic, data) dai singoli articoli presenti nella pagina
    articoli = estrai_articoli_da_soup(soup)

    # Ordina gli articoli dal più vecchio al più recente per un inserimento cronologico
    articoli_ordinati = utilities.ordina_articoli_per_data(articoli)

    # Salva tutti gli articoli ordinati all'interno del database locale
    database.salvaArticoliCryptopanic(articoli_ordinati)


# Estrae il l'url originale degli articoli da cryptopanic
def scraping_url_articoli(driver, cryptopanic_url):
    try:
        driver.get(cryptopanic_url)

        # Aspetta che il titolo sia cliccabile
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "h1.post-title span.text"))
        )

        article_title = driver.find_element(By.CSS_SELECTOR, "h1.post-title span.text")
        print(f"Titolo cliccabile trovato: {article_title.text}")

        # Clicca con scroll
        driver.execute_script("arguments[0].scrollIntoView(true);", article_title)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", article_title)
        time.sleep(2)

        # Salva la finestra attuale
        original_window = driver.current_window_handle

        # Se si apre una nuova scheda, passaci
        WebDriverWait(driver, 5).until(lambda d: len(d.window_handles) > 1)
        new_tabs = [tab for tab in driver.window_handles if tab != original_window]
        if new_tabs:
            driver.switch_to.window(new_tabs[0])
            time.sleep(5)
            article_url = driver.current_url
            driver.close()  # ❌ chiude la scheda appena aperta
            driver.switch_to.window(original_window)  # 🔁 torna alla scheda principale
            return article_url

        return None  # Nessuna nuova scheda aperta

    except Exception as e:
        print(f"❌ Errore durante l'estrazione URL: {e}")
        return None


### FUNZIONE PRINCIPALE: estrarre gli url originali degli articoli
def fetch_url_articoli():
    articoli = database.get_articoli_senza_url_originale()

    if not articoli:
        print("✅ Nessun articolo da aggiornare.")
        return

    print(f"🔍 Trovati {len(articoli)} articoli da elaborare.")

    # 🔄 Istanzia una sola volta il ChromeDriver
    driver = setup_chrome_driver()

    for id_articolo, url_cryptopanic in articoli:
        print(f"\n🔄 Elaborazione articolo ID {id_articolo}...")

        url_articolo = scraping_url_articoli(driver, url_cryptopanic)

        if url_articolo:
            print(f"✅ URL originale trovato: {url_articolo}")
            database.aggiorna_url_originale(id_articolo, url_articolo)
        else:
            print(f"⚠️ Nessun URL trovato per {url_cryptopanic}")
            database.aggiorna_url_originale(id_articolo, "NESSUN CONTENUTO")

        time.sleep(1.5)  # Rate limiting

    # 🔚 Chiudi il driver solo alla fine
    driver.quit()


# Estrae il contenuto html di ogni articolo della pagina dato un URL
def fetch_html_articolo(driver, url):
    """
    Scarica il codice HTML completo della pagina specificata.
    Usa un'istanza esistente di Chrome WebDriver.
    """
    try:
        driver.get(url)

        # Attende che il contenuto principale della pagina venga caricato
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        return driver.page_source

    except Exception as e:
        print(f"❌ Errore durante il download HTML da {url}: {e}")
        return None



### FUNZIONE PRINCIPALE: Estrae e salva l'HTML pulito degli articoli il cui contenuto non è ancora stato processato.
def fetch_contenuto_html_articoli():

    articoli = database.get_articoli_da_processare_html()
    if not articoli:
        print("✅ Tutti gli articoli sono già stati elaborati.")
        return

    # Inizializza una sola istanza di Chrome WebDriver
    driver = setup_chrome_driver()

    for id_articolo, url_articolo in articoli:
        print(f"\n🔍 Elaborazione articolo ID {id_articolo}")

        contenuto_html = fetch_html_articolo(driver, url_articolo)
        if not contenuto_html:
            print("⚠️ HTML non disponibile.")
            database.salva_html_articolo(id_articolo, "NESSUN CONTENUTO")
            continue

        contenuto_html_pulito = cleanHtml.clean_html_content(contenuto_html)
        if not contenuto_html_pulito.strip():
            print("⚠️ HTML pulito vuoto o non valido.")
            database.salva_html_articolo(id_articolo, "NESSUN CONTENUTO")
            continue

        try:
            database.salva_html_articolo(id_articolo, contenuto_html_pulito)
            print(f"✅ Contenuto salvato per articolo ID {id_articolo}")
        except Exception as e:
            print(f"❌ Errore nel salvataggio DB per articolo ID {id_articolo}: {e}")
            database.salva_html_articolo(id_articolo, "NESSUN CONTENUTO")

        time.sleep(1.5)  # Rate limiting

    # Chiude il WebDriver dopo aver processato tutti gli articoli
    driver.quit()
    print("\n🏁 Completato il salvataggio di tutti gli HTML.")


### Funzione per estrarre l'url originale e il contenuto degli articoli
def fetch_url_e_html_articoli():
    articoli = database.get_articoli_senza_url_originale()
    if not articoli:
        print("✅ Nessun articolo da aggiornare.")
        return

    print(f"🔍 Trovati {len(articoli)} articoli da processare (URL + contenuto).")

    driver = setup_chrome_driver()

    for id_articolo, url_cryptopanic in articoli:
        print(f"\n🔄 Articolo ID {id_articolo}")

        # Step 1: Accedi a CryptoPanic e clicca sul titolo
        url_articolo = None
        contenuto_html_pulito = None

        try:
            driver.get(url_cryptopanic)

            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "h1.post-title span.text"))
            )
            article_title = driver.find_element(By.CSS_SELECTOR, "h1.post-title span.text")
            driver.execute_script("arguments[0].scrollIntoView(true);", article_title)
            driver.execute_script("arguments[0].click();", article_title)
            time.sleep(2)

            original_window = driver.current_window_handle
            WebDriverWait(driver, 5).until(lambda d: len(d.window_handles) > 1)
            new_tab = [w for w in driver.window_handles if w != original_window][0]

            driver.switch_to.window(new_tab)
            time.sleep(3)

            url_articolo = driver.current_url
            contenuto_html = driver.page_source

            contenuto_html_pulito = cleanHtml.clean_html_content(contenuto_html)

            driver.close()
            driver.switch_to.window(original_window)

        except Exception as e:
            print(f"❌ Errore durante l'accesso o estrazione: {e}")

        # Step 2: Salvataggio dei dati
        if url_articolo:
            database.aggiorna_url_originale(id_articolo, url_articolo)
        else:
            url_articolo = "NESSUN CONTENUTO"
            database.aggiorna_url_originale(id_articolo, url_articolo)

        if contenuto_html_pulito and contenuto_html_pulito.strip():
            database.salva_html_articolo(id_articolo, contenuto_html_pulito)
            print(f"✅ Contenuto HTML salvato")
        else:
            database.salva_html_articolo(id_articolo, "NESSUN CONTENUTO")
            print("⚠️ Contenuto HTML mancante o vuoto")

        time.sleep(1.5)

    driver.quit()
    print("🏁 Operazione completata per tutti gli articoli.")


