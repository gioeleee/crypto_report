import torch
import joblib
import numpy as np
from transformers import AutoModel
from sklearn.linear_model import Ridge
from tqdm import tqdm

# === CONFIG ===
MODEL_NAME = "Musixmatch/umberto-commoncrawl-cased-v1"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MAX_LENGTH = 512

# === 1. Carica tokenizer e modelli addestrati ===
tokenizer = joblib.load("regressionePesoSentiment/tokenizer.pkl")
model_peso = joblib.load("regressionePesoSentiment/model_peso.pkl")
model_sentiment = joblib.load("regressionePesoSentiment/model_sentiment.pkl")

# === 2. Funzione per estrarre embedding (mean pooling) ===
def estrai_embedding(text):
    model = AutoModel.from_pretrained(MODEL_NAME).to(DEVICE)
    model.eval()

    inputs = tokenizer(
        text,
        truncation=True,
        padding="max_length",
        max_length=MAX_LENGTH,
        return_tensors="pt"
    )

    input_ids = inputs["input_ids"].to(DEVICE)
    attention_mask = inputs["attention_mask"].to(DEVICE)

    with torch.no_grad():
        output = model(input_ids=input_ids, attention_mask=attention_mask)
        last_hidden = output.last_hidden_state

        mask = attention_mask.unsqueeze(-1).expand(last_hidden.size()).float()
        sum_hidden = torch.sum(last_hidden * mask, dim=1)
        sum_mask = torch.clamp(mask.sum(1), min=1e-9)
        mean_embedding = sum_hidden / sum_mask

    return mean_embedding.cpu().numpy()

# === 3. Funzione per predire peso e sentiment ===
def predici_peso_sentiment(titolo, riassunto_lungo):
    testo_completo = titolo.strip() + " " + riassunto_lungo.strip()
    embedding = estrai_embedding(testo_completo)

    peso_pred = model_peso.predict(embedding)[0]
    sentiment_pred = model_sentiment.predict(embedding)[0]

    return round(peso_pred, 3), round(sentiment_pred, 3)

# === 4. ESEMPIO USO ===
if __name__ == "__main__":
    titolo = "Snoop Dogg e Telegram Vendono 1 Milione di NFT in 30 Minuti"
    riassunto = (
        "Snoop Dogg e Telegram hanno collaborato per vendere 1 milione di NFT in 30 minuti, generando 12 milioni di dollari. La collezione, chiamata 'Telegram Gifts', è stata distribuita sulla blockchain TON e comprende 996.000 oggetti digitali, tra cui immagini iconiche legate allo stile di Snoop Dogg. L’iniziativa ha suscitato un grande interesse, dimostrando che gli NFT possono ancora attirare attenzione nel mercato in calo. La collaborazione ha evidenziato l’importanza di un marketing innovativo per rinnovare l’interesse per gli asset digitali. Il successo di questa iniziativa potrebbe influenzare il futuro dell’uso degli NFT nel settore Web3. Snoop Dogg ha anche rilasciato un nuovo brano intitolato 'Gifts', accompagnato da un videoclip che ha rafforzato l’entusiasmo per la collezione."
    )

    peso, sentiment = predici_peso_sentiment(titolo, riassunto)

    print("\n📈 Predizioni:")
    print(f"Peso predetto: {peso}")
    print(f"Sentiment predetto: {sentiment}")

