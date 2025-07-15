import sqlite3
import requests
import re
import database

# Inserisci l’URL aggiornato dell’API
API_URL = "https://2923a93170d3.ngrok-free.app/generate_summaries/"

def pulisci_testo_incompleto(text):
    """
    Rimuove l'ultima frase se incompleta, per evitare output troncati.
    """
    sentences = re.split(r'([.!?]\s+)', text)
    if len(sentences) > 2:
        return "".join(sentences[:-2]).strip() + "."
    return text.strip()

def chiama_api_riassunti(article_text):
    """
    Esegue la chiamata API al modello LLama3.2 per ottenere i riassunti.
    """
    payload = {"article_text": article_text}
    response = requests.post(API_URL, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()

def riassunto_articoli():
    """
    Estrae articoli da riassumere, esegue fino a 3 tentativi di chiamata API
    e salva i risultati o 'NESSUN CONTENUTO' in caso di errore.
    """
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
                result = chiama_api_riassunti(full_article_html)

                if isinstance(result, list) and len(result) == 2:
                    short_summary = pulisci_testo_incompleto(result[0])
                    long_summary = pulisci_testo_incompleto(result[1])

                    # Se i riassunti non sono rilevanti, salva 'NESSUN CONTENUTO'
                    if short_summary.startswith("L'articolo non contiene contenuti rilevanti.") or \
                       long_summary.startswith("L'articolo non contiene contenuti rilevanti."):
                        short_summary = long_summary = "NESSUN CONTENUTO"

                    database.salva_riassunto_articolo(id_articolo, short_summary, long_summary)
                    print(f"✅ Riassunti salvati per articolo ID {id_articolo}")
                    success = True
                    break  # Esce dal ciclo tentativi
                else:
                    print(f"⚠️ Formato risposta non valido per ID {id_articolo}: {result}")

            except requests.exceptions.RequestException as e:
                print(f"❌ Errore API per ID {id_articolo}: {str(e)}")
            except Exception as e:
                print(f"❌ Errore interno per ID {id_articolo}: {str(e)}")

        # Se tutti i tentativi falliscono
        if not success:
            print(f"⛔ Fallimento persistente per articolo ID {id_articolo}, salvo 'NESSUN CONTENUTO'")
            database.salva_riassunto_articolo(id_articolo, "NESSUN CONTENUTO", "NESSUN CONTENUTO")

    print("\n🏁 Riassunto completato per tutti gli articoli.")

