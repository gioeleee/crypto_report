import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import database

def classificaNewArticle():
    # Estrai ID e riassunto lungo da articoli senza categoria (via modulo database)
    dati = database.get_articoli_senza_categoria()

    # Se non ci sono articoli, esci pulitamente per evitare l'errore 0 sample
    if not dati:
        print("✅ Nessun articolo da classificare.")
        return

    # Crea DataFrame
    df = pd.DataFrame(dati, columns=['id', 'riassunto_lungo'])

    # Carica modello e vettorizzatore
    with open('classificazione/modello_naive_bayes.pkl', 'rb') as model_file:
        model = pickle.load(model_file)

    with open('classificazione/vectorizer_tfidf.pkl', 'rb') as vectorizer_file:
        vectorizer = pickle.load(vectorizer_file)

    # Trasforma in TF-IDF
    X_tfidf = vectorizer.transform(df['riassunto_lungo'].astype(str))

    # Predizione
    df['categoria'] = model.predict(X_tfidf)

    # Aggiorna il database
    # — Opzione A: come il tuo codice originale, per riga —
    for _, row in df.iterrows():
        database.aggiorna_categoria_articolo(row['id'], row['categoria'])

    # — Opzione B (più efficiente): in batch —
    # updates = list(zip(df['categoria'].tolist(), df['id'].tolist()))
    # database.aggiorna_categorie_articoli(updates)

    print("✅ Categorizzazione completata e salvata nel database.")


