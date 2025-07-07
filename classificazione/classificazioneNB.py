import sqlite3
import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

def classificaNewArticle():
    # Connessione al database
    conn = sqlite3.connect('crypto_news.db')
    cursor = conn.cursor()

    # Estrai ID e riassunto lungo da articoli senza categoria
    query = """
        SELECT id, riassunto_lungo
        FROM articoli
        WHERE riassunto_lungo IS NOT NULL AND categoria IS NULL;
    """
    cursor.execute(query)
    dati = cursor.fetchall()

    # Crea DataFrame
    df = pd.DataFrame(dati, columns=['id', 'riassunto_lungo'])

    # Carica modello e vettorizzatore
    with open('Classificazione/modello_naive_bayes.pkl', 'rb') as model_file:
        model = pickle.load(model_file)

    with open('Classificazione/vectorizer_tfidf.pkl', 'rb') as vectorizer_file:
        vectorizer = pickle.load(vectorizer_file)

    # Trasforma in TF-IDF
    X_tfidf = vectorizer.transform(df['riassunto_lungo'])

    # Predizione
    df['categoria'] = model.predict(X_tfidf)

    # Aggiorna il database
    for _, row in df.iterrows():
        cursor.execute("""
            UPDATE articoli
            SET categoria = ?
            WHERE id = ?;
        """, (row['categoria'], row['id']))

    conn.commit()
    conn.close()
    print("✅ Categorizzazione completata e salvata nel database.")
