import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    mean_squared_error,
    r2_score,
    mean_absolute_error,
    mean_absolute_percentage_error,
    explained_variance_score,
)
import joblib
from tqdm import tqdm
import os

# === CONFIGURAZIONI ===
MODEL_NAME = "Musixmatch/umberto-commoncrawl-cased-v1"
BATCH_SIZE = 16
MAX_LENGTH = 512
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# === FUNZIONI ===
class BertDataset(Dataset):
    def __init__(self, texts, tokenizer, max_length):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        encoding = self.tokenizer(
            self.texts[idx],
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        return {key: val.squeeze(0) for key, val in encoding.items()}


def extract_embeddings(texts, tokenizer, model_name, batch_size, max_length):
    model = AutoModel.from_pretrained(model_name).to(DEVICE)
    model.eval()

    dataset = BertDataset(texts, tokenizer, max_length)
    dataloader = DataLoader(dataset, batch_size=batch_size)

    all_embeddings = []
    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Estrazione embeddings"):
            input_ids = batch['input_ids'].to(DEVICE)
            attention_mask = batch['attention_mask'].to(DEVICE)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            last_hidden = outputs.last_hidden_state

            mask = attention_mask.unsqueeze(-1).expand(last_hidden.size()).float()
            sum_hidden = torch.sum(last_hidden * mask, 1)
            sum_mask = torch.clamp(mask.sum(1), min=1e-9)
            mean_embeddings = sum_hidden / sum_mask

            all_embeddings.append(mean_embeddings.cpu().numpy())

    return np.vstack(all_embeddings)


def evaluate_model(y_true, y_pred, name=""):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = mean_absolute_percentage_error(y_true, y_pred)
    evs = explained_variance_score(y_true, y_pred)

    print(f"\n📊 Metriche per {name}:")
    print(f"MAE: {mae:.4f}, RMSE: {rmse:.4f}, MAPE: {mape:.2%}, EVS: {evs:.4f}")


# === MAIN ===
def main():
    # Caricamento e preprocessing dataset
    df = pd.read_csv("regressionePesoSentiment/datasetAddestramento.csv", delimiter='|')
    df = df.dropna(subset=["titolo", "riassunto_lungo", "peso", "sentiment"])
    df["testo"] = df["titolo"] + " " + df["riassunto_lungo"]

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    # Train/test split
    X_train_texts, X_test_texts, y_peso_train, y_peso_test, y_sentiment_train, y_sentiment_test = train_test_split(
        df["testo"].tolist(), df["peso"], df["sentiment"], test_size=0.2, random_state=42
    )

    # Estrazione embeddings
    X_train_embeddings = extract_embeddings(X_train_texts, tokenizer, MODEL_NAME, BATCH_SIZE, MAX_LENGTH)
    X_test_embeddings = extract_embeddings(X_test_texts, tokenizer, MODEL_NAME, BATCH_SIZE, MAX_LENGTH)

    # Salvataggio embeddings opzionale
    np.save("regressionePesoSentiment/X_train_embeddings.npy", X_train_embeddings)
    np.save("regressionePesoSentiment/X_test_embeddings.npy", X_test_embeddings)

    # Alpha ottimale via RidgeCV
    alphas = [0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0]
    model_peso = RidgeCV(alphas=alphas, scoring='neg_mean_squared_error', cv=5)
    model_sentiment = RidgeCV(alphas=alphas, scoring='neg_mean_squared_error', cv=5)

    model_peso.fit(X_train_embeddings, y_peso_train)
    model_sentiment.fit(X_train_embeddings, y_sentiment_train)

    print(f"\n✅ Alpha selezionato per P**eso**: {model_peso.alpha_}")
    print(f"✅ Alpha selezionato per S**entiment**: {model_sentiment.alpha_}")

    # Confronto per alpha
    mse_per_alpha = {
        alpha: -cross_val_score(RidgeCV(alphas=[alpha]), X_train_embeddings, y_peso_train, cv=5, scoring='neg_mean_squared_error').mean()
        for alpha in alphas
    }

    print("\n📊 Top 3 alpha per P**eso**:")
    for alpha, mse in sorted(mse_per_alpha.items(), key=lambda x: x[1])[:3]:
        print(f"  alpha = {alpha:<5} → MSE = {mse:.4f}")

    # Valutazione
    y_peso_pred = model_peso.predict(X_test_embeddings)
    y_sentiment_pred = model_sentiment.predict(X_test_embeddings)

    print(f"\n🎯 Performance finale:")
    print(f"Peso     - MSE: {mean_squared_error(y_peso_test, y_peso_pred):.4f}, R²: {r2_score(y_peso_test, y_peso_pred):.4f}")
    print(f"Sentiment - MSE: {mean_squared_error(y_sentiment_test, y_sentiment_pred):.4f}, R²: {r2_score(y_sentiment_test, y_sentiment_pred):.4f}")

    evaluate_model(y_peso_test, y_peso_pred, name="Peso")
    evaluate_model(y_sentiment_test, y_sentiment_pred, name="Sentiment")

    # Confronto predizioni
    print("\n🧪 Confronto valori reali vs predetti (prime 20 righe):")
    for i in range(min(20, len(y_peso_test))):
        print(f"[{i+1:2}] Peso    → Reale: {y_peso_test.iloc[i]:.3f} | Predetto: {y_peso_pred[i]:.3f}")
        print(f"     Sentiment → Reale: {y_sentiment_test.iloc[i]:.3f} | Predetto: {y_sentiment_pred[i]:.3f}")

    # === Salvataggio ===
    os.makedirs("regressionePesoSentiment", exist_ok=True)
    joblib.dump(model_peso, "regressionePesoSentiment/model_peso.pkl")
    joblib.dump(model_sentiment, "regressionePesoSentiment/model_sentiment.pkl")
    joblib.dump(tokenizer, "regressionePesoSentiment/tokenizer.pkl")
    print("\n💾 Modelli e tokenizer salvati con successo.")


if __name__ == "__main__":
    main()

