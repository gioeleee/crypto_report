import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from nltk.corpus import stopwords
import joblib
import scipy.sparse as sp
import nltk

# Scarica le stopwords italiane (solo la prima volta)
# nltk.download('stopwords')
italian_stopwords = stopwords.words('italian')

# === 1. Carica il dataset
df = pd.read_csv('regressionePesoSentiment/datasetAddestramento2.csv', delimiter='|')

# === 2. Filtra righe valide
df = df.dropna(subset=["titolo", "riassunto_breve", "peso", "sentiment"])

# === 3. TF-IDF separati per titolo e riassunto_lungo
vectorizer_titolo = TfidfVectorizer(stop_words=italian_stopwords, max_features=2000)
vectorizer_riassunto = TfidfVectorizer(stop_words=italian_stopwords, max_features=6000)

X_titolo = vectorizer_titolo.fit_transform(df["titolo"])
X_riassunto = vectorizer_riassunto.fit_transform(df["riassunto_breve"])

# === 4. Applica peso maggiore al titolo
title_weight = 1.25
X_titolo_pesato = X_titolo * title_weight

# === 5. Combina i due vettori
X = sp.hstack([X_titolo_pesato, X_riassunto])

# === 6. Target
y_peso = df["peso"]
y_sentiment = df["sentiment"]

# === 7. Train-test split
X_train, X_test, y_peso_train, y_peso_test, y_sentiment_train, y_sentiment_test = train_test_split(
    X, y_peso, y_sentiment, test_size=0.2, random_state=42
)

# === 8. Modelli
model_peso = RandomForestRegressor(random_state=42)
model_sentiment = RandomForestRegressor(random_state=42)

model_peso.fit(X_train, y_peso_train)
model_sentiment.fit(X_train, y_sentiment_train)

# === 9. Valutazione
y_peso_pred = model_peso.predict(X_test)
y_sentiment_pred = model_sentiment.predict(X_test)

print(f"Peso - MSE: {mean_squared_error(y_peso_test, y_peso_pred):.4f}, R²: {r2_score(y_peso_test, y_peso_pred):.4f}")
print(f"Sentiment - MSE: {mean_squared_error(y_sentiment_test, y_sentiment_pred):.4f}, R²: {r2_score(y_sentiment_test, y_sentiment_pred):.4f}")

# === 10. Salvataggio modelli e vectorizer
joblib.dump(model_peso, "modello_peso.pkl")
joblib.dump(model_sentiment, "modello_sentiment.pkl")
joblib.dump(vectorizer_titolo, "vectorizer_titolo.pkl")
joblib.dump(vectorizer_riassunto, "vectorizer_riassunto.pkl")

print("✅ Modelli e vectorizer salvati.")



# === 11. Mostra un confronto tra input e output predetti
X_test_indices = y_peso_test.index  # per mappare le predizioni agli articoli originali
df_test = df.loc[X_test_indices].copy()

df_test["peso_predetto"] = y_peso_pred
df_test["sentiment_predetto"] = y_sentiment_pred

# Mostra le prime 10 righe per esempio
print("\n🎯 Confronto tra valori reali e predetti:")
print(df_test[["peso", "peso_predetto", "sentiment", "sentiment_predetto"]].head(50))

