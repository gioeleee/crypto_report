import sqlite3

DB_PATH = "crypto_news.db"

#funzione per la creazione del database
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
        FOREIGN KEY (id) REFERENCES articoli_meta(id) ON DELETE CASCADE
    );
    """)

    print(f"✅ Database creato se non esiste!")




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

