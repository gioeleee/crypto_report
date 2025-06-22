from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import tempfile

def salva_html_cryptopanic():
    url = "https://cryptopanic.com/news/"

    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")
    # chrome_options.add_argument("--headless=new")  # Disattiva per vedere cosa succede

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(url)

    try:
        # Aspetta che compaia la sidebar
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "left-nav"))
        )
        print("✅ Pagina caricata. Estraggo HTML...")

        time.sleep(2)  # Attesa aggiuntiva per completare il rendering dinamico

        with open("cryptopanic.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        print("💾 HTML salvato in 'cryptopanic.html'")

    except Exception as e:
        print(f"⚠️ Errore durante il salvataggio HTML: {e}")

    finally:
        driver.quit()

if __name__ == "__main__":
    salva_html_cryptopanic()
