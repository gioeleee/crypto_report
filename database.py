import sqlite3

DB_PATH = "crypto_news.db"


# Creazione database
def creazioneDatabase():
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Creazione della tabella per i metadati degli articoli
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meta_articoli (
        id INTEGER PRIMARY KEY AUTOINCREMENT,       
        url_cryptopanic VARCHAR(512) UNIQUE,
        url_articolo VARCHAR(512),
        data DATETIME,
        categoria VARCHAR(100)
    );
    """)

    # Creazione della tabella per le descrizioni complete (contenuto estratto via web scraping o AI)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS articoli (
        id INTEGER PRIMARY KEY,
        titolo VARCHAR(512),
        articolo_completo_html TEXT,  
        riassunto_breve TEXT,
        riassunto_lungo TEXT,
        categoria VARCHAR(250),
        peso FLOAT,
        sentiment FLOAT,
        FOREIGN KEY (id) REFERENCES articoli_meta(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()
    print(f"✅ Database creato correttamente (se non esiste già) !")


### Gestisce l'inserimento di uno più articoli dei campi : titolo, data, url_cryptopanic
def salvaArticoliCryptopanic(articoli):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    nuovi = 0

    for url, data, titolo in articoli:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO meta_articoli (url_cryptopanic, data)
                VALUES (?, ?)
            """, (url, data))
            id = cursor.lastrowid

            if cursor.rowcount > 0:
                cursor.execute("""
                    INSERT INTO articoli (id, titolo)
                    VALUES (?, ?)
                """, (id, titolo))
                nuovi += 1
        except Exception as e:
            print(f"❌ Errore salvataggio: {e}")

    conn.commit()
    conn.close()
    print(f"✅ {nuovi} articoli nuovi salvati nel database.")


def get_articoli_senza_url_originale():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, url_cryptopanic
        FROM meta_articoli
        WHERE url_articolo IS NULL
    """)
    risultati = cursor.fetchall()
    conn.close()
    return risultati

def aggiorna_url_originale(id_articolo, url_articolo):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE meta_articoli
        SET url_articolo = ?
        WHERE id = ?
    """, (url_articolo, id_articolo))
    conn.commit()
    conn.close()



def get_articoli_da_processare_html():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, url_articolo
        FROM meta_articoli
        WHERE url_articolo IS NOT NULL OR url_articolo!="NESSUN CONTENUTO"
    """)
    risultati = cursor.fetchall()
    conn.close()
    return risultati

def salva_html_articolo(id_articolo, html_pulito):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE articoli
        SET articolo_completo_html = ?
        WHERE id = ?
    """, (html_pulito, id_articolo))

    conn.commit()
    conn.close()


# Restituisce una lista di articoli (id, contenuto html) che non sono ancora stati riassunti.
def ottieni_articoli_da_riassumere():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, articolo_completo_html
        FROM articoli
        WHERE articolo_completo_html IS NOT NULL AND articolo_completo_html !="NESSUN CONTENUTO"
          AND (riassunto_breve IS NULL OR riassunto_lungo IS NULL)
    """)

    articoli = cursor.fetchall()
    conn.close()
    return articoli

# Restituisce una lista di articoli (id, contenuto html) che non sono ancora stati riassunti.
def salva_riassunto_articolo(id_articolo, riassunto_breve, riassunto_lungo):
    """
    Salva i riassunti breve e lungo per un articolo dato il suo ID.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE articoli
        SET riassunto_breve = ?, riassunto_lungo = ?
        WHERE id = ?
    """, (riassunto_breve, riassunto_lungo, id_articolo))

    conn.commit()
    conn.close()


def reset_riassunti_articolo():
    """
    Imposta a NULL i valori di riassunto_breve e riassunto_lungo
    per l'articolo corrispondente a id_articolo.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE articoli
            SET riassunto_breve = NULL,
                riassunto_lungo = NULL
        """)
        conn.commit()
    finally:
        conn.close()



# === Classificazione: funzioni DB ===
def get_articoli_senza_categoria():
    """
    Ritorna lista di tuple (id, riassunto_lungo) per articoli
    con riassunto_lungo non NULL e categoria NULL.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, riassunto_lungo
        FROM articoli
        WHERE riassunto_lungo IS NOT NULL
          AND categoria IS NULL
    """)
    dati = cursor.fetchall()
    conn.close()
    return dati


def aggiorna_categoria_articolo(id_articolo: int, categoria: str):
    """
    Aggiorna la categoria di un singolo articolo.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE articoli
        SET categoria = ?
        WHERE id = ?
    """, (categoria, id_articolo))
    conn.commit()
    conn.close()


def aggiorna_categorie_articoli(updates):
    """
    Aggiornamento in batch. 'updates' è una lista di tuple (categoria, id).
    Utile se vuoi fare un solo round-trip al DB.
    """
    if not updates:
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executemany("""
        UPDATE articoli
        SET categoria = ?
        WHERE id = ?
    """, updates)
    conn.commit()
    conn.close()



# === Peso & Sentiment: funzioni DB ===

def get_articoli_senza_peso_sentiment_con_categoria():
    """
    Ritorna [(id, titolo, riassunto_lungo)] per articoli con categoria NON NULL
    e peso/sentiment NULL (uno dei due o entrambi).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, COALESCE(titolo, ''), COALESCE(riassunto_lungo, '')
        FROM articoli
        WHERE categoria IS NOT NULL
          AND (peso IS NULL OR sentiment IS NULL)
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def aggiorna_peso_sentiment_articolo(id_articolo: int, peso: float, sentiment: float):
    """
    Aggiorna entrambi i campi per l'articolo indicato.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE articoli
        SET peso = ?, sentiment = ?
        WHERE id = ?
    """, (peso, sentiment, id_articolo))
    conn.commit()
    conn.close()
