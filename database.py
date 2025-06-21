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
        url_cryptopanic VARCHAR(512),
        url_articolo VARCHAR(512),
        data DATE,
        categoria VARCHAR(100)
    );
    """)

    # Creazione della tabella per le descrizioni complete (contenuto estratto via web scraping o AI)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS articoli (
        id_articolo INTEGER PRIMARY KEY,
        titolo VARCHAR(512),
        articolo_completo_html TEXT,  
        riassunto_breve TEXT,
        riassunto_lungo TEXT,
        FOREIGN KEY (id_articolo) REFERENCES articoli_meta(id) ON DELETE CASCADE
    );
    """)