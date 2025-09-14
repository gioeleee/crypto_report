# -*- coding: utf-8 -*-
# Script dimostrativo: calcola e STAMPA step-by-step gli embedding frase
# con tokenizzazione, token embeddings, mean pooling e similarità coseno.

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# 1) Caricamento tokenizer e modello (backbone di SBERT)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)  # encoder BERT-like

# 2) Frasi di interesse
sentences = [
    "La difficoltà del mining di Bitcoin raggiunge un nuovo record.",
    "La difficoltà della rete di Bitcoin è salita sopra i 136 trilioni, creando condizioni più difficili per i miner.",
    "Sponsored: Scopri la nuova piattaforma di trading con bonus di benvenuto",
]

def mean_pooling(token_embeddings: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    """
    Mean pooling esplicito: media dei token validi (mask=1).
    token_embeddings: (batch_size, seq_len, hidden_size)
    attention_mask:   (batch_size, seq_len)
    return:           (batch_size, hidden_size)
    """
    mask = attention_mask.unsqueeze(-1).type_as(token_embeddings)  # (B,S,1)
    summed = (token_embeddings * mask).sum(dim=1)                  # (B,H)
    counts = mask.sum(dim=1).clamp(min=1e-9)                       # (B,1)
    return summed / counts

def l2_normalize(x: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(x, axis=1, keepdims=True) + 1e-12
    return x / norm

# 3) Pipeline per ogni frase
all_sentence_vecs = []

for idx, text in enumerate(sentences, start=1):
    print("\n" + "="*80)
    print(f"Frase {idx}: {text}")

    # a) Tokenizzazione
    enc = tokenizer(text, return_tensors="pt", padding=False, truncation=True)
    input_ids = enc["input_ids"]          # (1, seq_len)
    attention_mask = enc["attention_mask"]# (1, seq_len)
    tokens = tokenizer.convert_ids_to_tokens(input_ids[0])

    print("\n[Tokenizzazione]")
    print("Token:", tokens)
    print("input_ids:", input_ids.tolist())
    print("attention_mask:", attention_mask.tolist())

    # b) Forward pass -> token embeddings (last_hidden_state)
    with torch.no_grad():
        out = model(**enc)
    token_embeddings = out.last_hidden_state  # (1, seq_len, hidden_size)
    hidden_size = token_embeddings.shape[-1]

    print("\n[Token Embeddings] shape:", tuple(token_embeddings.shape))
    # Mostra solo i primi 6 token e prime 8 dimensioni per compattezza
    max_show_tokens = min(6, token_embeddings.shape[1])
    for i in range(max_show_tokens):
        vec = token_embeddings[0, i, :8].cpu().numpy()  # prime 8 dims
        print(f"  t[{i:02d}] '{tokens[i]}': {np.round(vec, 4)} ...")

    # c) Mean pooling esplicito
    sent_vec = mean_pooling(token_embeddings, attention_mask)  # (1, hidden_size)
    print("\n[Mean Pooling] (media pesata dalla mask)")
    print("Vector (prime 8 dims):", np.round(sent_vec[0, :8].cpu().numpy(), 4))

    # d) L2-normalizzazione (utile per cosine)
    sent_vec_np = sent_vec.cpu().numpy()
    sent_vec_np = l2_normalize(sent_vec_np)  # (1, H)
    print("[L2-normalized] (prime 8 dims):", np.round(sent_vec_np[0, :8], 4))

    all_sentence_vecs.append(sent_vec_np)

# 4) Similarità del coseno tra tutte le coppie di frasi
emb = np.vstack(all_sentence_vecs)  # (3, hidden_size)
sim = cosine_similarity(emb, emb)

print("\n" + "="*80)
print("[Similarità coseno tra frasi]")
for i in range(len(sentences)):
    for j in range(len(sentences)):
        print(f"sim(frase {i+1}, frase {j+1}) = {sim[i,j]:.3f}")
