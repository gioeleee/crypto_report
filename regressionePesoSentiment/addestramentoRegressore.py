import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sentence_transformers import SentenceTransformer
import numpy as np
import joblib

# === 1. Caricamento dataset ===
df = pd.read_csv("regressionePesoSentiment/datasetAddestramento.csv", sep=";")  # Adatta il separatore se diverso
df = df.dropna(subset=["titolo", "riassunto_lungo", "peso", "sentiment"])

# === 2. Caricamento modello di embedding ===
model = SentenceTransformer("all-MiniLM-L6-v2")  # Leggero e veloce

# === 3. Calcolo embedding pesati ===
print("Calcolo degli embedding...")

def get_weighted_embedding(title, summary, alpha=0.7):
    title_emb = model.encode(title)
    summary_emb = model.encode(summary)
    return alpha * title_emb + (1 - alpha) * summary_emb

X = np.array([
    get_weighted_embedding(row["titolo"], row["riassunto_lungo"])
    for _, row in df.iterrows()
])

y_peso = df["peso"].values
y_sentiment = df["sentiment"].values

# === 4. Train-test split ===
X_train, X_test, y_peso_train, y_peso_test, y_sent_train, y_sent_test = train_test_split(
    X, y_peso, y_sentiment, test_size=0.2, random_state=42
)

# === 5. Addestramento modelli ===
print("Addestramento modello per 'peso'...")
peso_model = Ridge(alpha=1.0)
peso_model.fit(X_train, y_peso_train)

print("Addestramento modello per 'sentiment'...")
sentiment_model = Ridge(alpha=1.0)
sentiment_model.fit(X_train, y_sent_train)

# === 6. Valutazione ===
def evaluate(model, X_test, y_test, name):
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"\n{name} - MSE: {mse:.4f}, R²: {r2:.4f}")

evaluate(peso_model, X_test, y_peso_test, "Peso")
evaluate(sentiment_model, X_test, y_sent_test, "Sentiment")

# === 7. Salvataggio modelli ===
joblib.dump(peso_model, "peso_model.pkl")
joblib.dump(sentiment_model, "sentiment_model.pkl")
print("\nModelli salvati in: peso_model.pkl e sentiment_model.pkl")
