import requests

URL = "https://cryptopanic.com/news/25035331/Gli-ETF-su-Ethereum-subiscono-il-secondo-piu-grande-ritiro-giornaliero-dal-lancio"
OUTPUT_FILE = "pagina_desktop.html"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
}

def main():
    try:
        resp = requests.get(URL, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[ERRORE] {e}")
        return

    # Salva i byte grezzi così com’è la pagina (nessuna conversione di encoding)
    with open(OUTPUT_FILE, "wb") as f:
        f.write(resp.content)

    print(f"[OK] HTML salvato in {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
