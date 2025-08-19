import sqlite3
import pandas as pd

# Connessione al database SQLite
conn = sqlite3.connect('crypto_news.db')
cursor = conn.cursor()

# Caricamento del CSV
df = pd.read_csv('regressionePesoSentiment/dataset_id_peso_sentiment.csv', delimiter=';')

# Aggiornamento delle righe
for _, row in df.iterrows():
    cursor.execute("""
        UPDATE articoli
        SET peso = ?, sentiment = ?
        WHERE id = ?;
    """, (row['peso'], row['sentiment'], int(row['id'])))

# Salva e chiude
conn.commit()
conn.close()
