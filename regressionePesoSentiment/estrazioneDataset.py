import sqlite3
import pandas as pd

# Connessione al database SQLite
db_path = 'crypto_news.db'  # Cambia il nome se necessario
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Query SQL
query = """
SELECT id, titolo, riassunto_breve, peso, sentiment
FROM articoli
WHERE titolo IS NOT NULL
  AND (riassunto_breve IS NOT NULL AND riassunto_breve != 'NESSUN CONTENUTO')
  AND peso IS NOT NULL
  AND sentiment IS NOT NULL AND id < 1600;
"""

# Esecuzione della query e caricamento in un DataFrame
df = pd.read_sql_query(query, conn)

# Mostra le prime righe (facoltativo)
print(df.head())

# Salva il dataset in CSV (facoltativo)
df.to_csv('regressionePesoSentiment/datasetAddestramento2.csv', index=False, sep='|')

# Chiusura della connessione
conn.close()
