import torch
import joblib
import numpy as np
from transformers import AutoModel  # usa il tokenizer salvato su pickle
from sklearn.linear_model import Ridge  # solo per typing; i modelli li carichi da pickle
import database

# === CONFIG ===
MODEL_NAME = "Musixmatch/umberto-commoncrawl-cased-v1"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MAX_LENGTH = 512

# === 1. Carica tokenizer e modelli addestrati ===
tokenizer = joblib.load("regressionePesoSentiment/tokenizer.pkl")
model_peso = joblib.load("regressionePesoSentiment/model_peso.pkl")
model_sentiment = joblib.load("regressionePesoSentiment/model_sentiment.pkl")

# Carica una volta il modello HF (NON dentro la funzione, per evitare costi ripetuti)
_transformer = AutoModel.from_pretrained(MODEL_NAME).to(DEVICE)
_transformer.eval()

# === 2. Funzione per estrarre embedding (mean pooling) ===
def estrai_embedding(text: str) -> np.ndarray:
    """
    Ritorna un vettore numpy (1, hidden_size) con mean pooling sui token validi.
    Gestisce anche testi vuoti/placeholder senza andare in errore.
    """
    # fallback per testi "vuoti"
    if not isinstance(text, str):
        text = ""
    txt = text.strip()
    try:
        inputs = tokenizer(
            txt,
            truncation=True,
            padding="max_length",
            max_length=MAX_LENGTH,
            return_tensors="pt"
        )
    except Exception:
        # se il tokenizer picklato dovesse fallire su input strani
        inputs = tokenizer(
            "",
            truncation=True,
            padding="max_length",
            max_length=MAX_LENGTH,
            return_tensors="pt"
        )

    input_ids = inputs["input_ids"].to(DEVICE)
    attention_mask = inputs["attention_mask"].to(DEVICE)

    with torch.no_grad():
        output = _transformer(input_ids=input_ids, attention_mask=attention_mask)
        last_hidden = output.last_hidden_state  # (1, seq_len, hidden)

        mask = attention_mask.unsqueeze(-1).expand(last_hidden.size()).float()
        sum_hidden = torch.sum(last_hidden * mask, dim=1)    # (1, hidden)
        sum_mask = torch.clamp(mask.sum(1), min=1e-9)        # (1, hidden) -> (1, 1) broadcast
        mean_embedding = sum_hidden / sum_mask               # (1, hidden)

    return mean_embedding.cpu().numpy()


# === 3. Predizione singola (peso, sentiment) ===
def predici_peso_sentiment(titolo: str, riassunto_lungo: str):
    testo_completo = (titolo or "").strip() + " " + (riassunto_lungo or "").strip()
    embedding = estrai_embedding(testo_completo)
    peso_pred = float(model_peso.predict(embedding)[0])
    sentiment_pred = float(model_sentiment.predict(embedding)[0])
    return round(peso_pred, 3), round(sentiment_pred, 3)


# === 4. Processo batch su DB: solo articoli con categoria IS NOT NULL e senza peso/sentiment ===
def genera_peso_sentiment_per_articoli():
    rows = database.get_articoli_senza_peso_sentiment_con_categoria()
    if not rows:
        print("✅ Nessun articolo da aggiornare (peso/sentiment).")
        return

    aggiornati = 0
    errori = 0

    for (art_id, titolo, riassunto) in rows:
        try:
            peso, sentiment = predici_peso_sentiment(titolo, riassunto)
            database.aggiorna_peso_sentiment_articolo(art_id, peso, sentiment)
            aggiornati += 1
        except Exception as e:
            # non stampiamo stacktrace verbosi: registriamo solo il conteggio
            errori += 1

    print(f"📈 Aggiornamento completato | aggiornati: {aggiornati} | errori: {errori}")
