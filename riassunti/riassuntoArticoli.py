import sqlite3
import requests
import re
import database

API_URL = None  # valorizzato al primo utilizzo

def _normalizza_endpoint(user_input: str) -> str:
    user_input = user_input.strip()
    # Se l'utente incolla già l'endpoint completo, lo manteniamo
    if user_input.endswith("/generate_summaries/"):
        return user_input
    # Altrimenti trattiamo l'input come base URL
    return user_input.rstrip("/") + "/generate_summaries/"

def _endpoint_raggiungibile(endpoint_url: str) -> bool:
    """
    Un endpoint è considerato raggiungibile se la connessione avviene
    e lo status non è 404. (405, 400, 401/403, 200, 204, ecc. vanno bene)
    """
    try:
        # 1) Tentativo leggero: OPTIONS
        r = requests.options(endpoint_url, timeout=5)
        if r.status_code != 404:
            return True
        # 2) Se proprio 404, proviamo un POST di test (qualche server non espone OPTIONS)
        r = requests.post(endpoint_url, json={"article_text": ""}, timeout=5)
        return r.status_code != 404
    except requests.RequestException:
        return False

def _get_api_url():
    """Chiede/valida l'endpoint finché non è raggiungibile, solo alla prima chiamata."""
    global API_URL
    if API_URL is None:
        while True:
            raw = input("Inserisci la BASE URL dell'API (es: https://97134b7c0388.ngrok-free.app): ")
            endpoint = _normalizza_endpoint(raw)
            if _endpoint_raggiungibile(endpoint):
                print("✅ API raggiungibili")
                API_URL = endpoint
                break
            else:
                print("⛔ API non raggiungibili. Controlla l'URL (o il tunnel) e riprova.\n")
    return API_URL

# Rimuove l'ultima frase se incompleta
def pulisci_testo_incompleto(text):
    sentences = re.split(r'([.!?]\s+)', text)
    if len(sentences) > 2:
        return "".join(sentences[:-2]).strip() + "."
    return text.strip()

# Chiamata API per i riassunti
def chiama_api_riassunti(article_text, api_url):
    payload = {"article_text": article_text}
    response = requests.post(api_url, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()

def riassunto_articoli():
    api_url = _get_api_url()  # lazy + validazione effettiva dell'endpoint

    articles = database.ottieni_articoli_da_riassumere()
    if not articles:
        print("✅ Nessun articolo da riassumere.")
        return

    for id_articolo, full_article_html in articles:
        print(f"\n📝 Riassunto per articolo ID {id_articolo}...")

        success = False
        for attempt in range(3):
            try:
                print(f"🔁 Tentativo {attempt+1}/3...")
                result = chiama_api_riassunti(full_article_html, api_url)

                if isinstance(result, list) and len(result) == 2:
                    short_summary = pulisci_testo_incompleto(result[0])
                    long_summary  = pulisci_testo_incompleto(result[1])

                    if short_summary.startswith("L'articolo non contiene contenuti rilevanti.") or \
                       long_summary.startswith("L'articolo non contiene contenuti rilevanti."):
                        short_summary = long_summary = "NESSUN CONTENUTO"

                    database.salva_riassunto_articolo(id_articolo, short_summary, long_summary)
                    print(f"✅ Riassunti salvati per articolo ID {id_articolo}")
                    success = True
                    break
                else:
                    print(f"⚠️ Formato risposta non valido per ID {id_articolo}: {result}")

            except requests.exceptions.RequestException as e:
                print(f"❌ Errore API per ID {id_articolo}: {str(e)}")
            except Exception as e:
                print(f"❌ Errore interno per ID {id_articolo}: {str(e)}")

        if not success:
            print(f"⛔ Fallimento persistente per articolo ID {id_articolo}, salvo 'NESSUN CONTENUTO'")
            database.salva_riassunto_articolo(id_articolo, "NESSUN CONTENUTO", "NESSUN CONTENUTO")

    print("\n🏁 Riassunto completato per tutti gli articoli.")
