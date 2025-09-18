# -*- coding: utf-8 -*-
# Tokenizzazione → WordEmb → PosEmb → Somma → HiddenStates → Attention → MeanPooling → Cosine → PCA(3D) plot

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# 1) Caricamento tokenizer e modello
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
model.eval()  # no dropout

# 2) Frasi
sentences = [
    "La difficoltà del mining di Bitcoin raggiunge un nuovo record.",
    "La difficoltà della rete di Bitcoin è salita sopra i 136 trilioni, creando condizioni più difficili per i miner.",
    "Sponsored: Scopri la nuova piattaforma di trading con bonus di benvenuto",
]

SPECIAL_TOKENS = set([tokenizer.cls_token_id, tokenizer.sep_token_id,
                      tokenizer.bos_token_id, tokenizer.eos_token_id,
                      tokenizer.pad_token_id])
SPECIAL_TOKENS = {tid for tid in SPECIAL_TOKENS if tid is not None}

def mean_pooling(token_embeddings: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    mask = mask.unsqueeze(-1).type_as(token_embeddings)      # (B,S,1)
    summed = (token_embeddings * mask).sum(dim=1)            # (B,H)
    counts = mask.sum(dim=1).clamp(min=1e-9)                 # (B,1)
    return summed / counts

def l2_normalize(x: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(x, axis=1, keepdims=True) + 1e-12
    return x / norm

def build_non_special_mask(input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    ids = input_ids[0].tolist()
    keep = [0 if tid in SPECIAL_TOKENS else 1 for tid in ids]
    keep = torch.tensor([keep], dtype=attention_mask.dtype, device=attention_mask.device)
    return keep * attention_mask

def safe_token_index(tokens, text_piece):
    for i, tok in enumerate(tokens):
        if text_piece in tok:
            return i
    return 1

# Raccolta embedding frase (L2-normalized)
all_sentence_vecs = []

for idx, text in enumerate(sentences, start=1):
    print("\n" + "="*90)
    print(f"Frase {idx}: {text}")

    # a) Tokenizzazione
    enc = tokenizer(text, return_tensors="pt", padding=False, truncation=True)
    input_ids = enc["input_ids"]
    attention_mask = enc["attention_mask"]
    tokens = tokenizer.convert_ids_to_tokens(input_ids[0])

    print("\n[1) Tokenizzazione]")
    print("Tokens:", tokens)
    print("input_ids:", input_ids.tolist())
    print("attention_mask:", attention_mask.tolist())

    # b) Word & Positional Embeddings (lookup + posizione)
    with torch.no_grad():
        word_embeds = model.embeddings.word_embeddings(input_ids)   # (1,S,H)
        seq_len = input_ids.size(1)
        position_ids = torch.arange(0, seq_len, dtype=torch.long, device=input_ids.device).unsqueeze(0)
        pos_embeds = model.embeddings.position_embeddings(position_ids)   # (1,S,H)
        if hasattr(model.embeddings, "token_type_embeddings"):
            token_type_ids = torch.zeros_like(input_ids)
            tok_type_embeds = model.embeddings.token_type_embeddings(token_type_ids)
        else:
            tok_type_embeds = torch.zeros_like(word_embeds)
        X0 = word_embeds + pos_embeds + tok_type_embeds  # (1,S,H)

    print("\n[2) Lookup & Positional Embeddings]")
    print("WordEmb shape:", tuple(word_embeds.shape), " PosEmb shape:", tuple(pos_embeds.shape))
    max_show = min(6, seq_len)
    for i in range(max_show):
        wv = word_embeds[0, i, :8].cpu().numpy()
        pv = pos_embeds[0, i, :8].cpu().numpy()
        xv = X0[0, i, :8].cpu().numpy()
        print(f"  t[{i:02d}] '{tokens[i]}'")
        print(f"    word_emb[:8] = {np.round(wv, 4)}")
        print(f"    pos_emb [:8] = {np.round(pv, 4)}")
        print(f"    sum X  [:8]  = {np.round(xv, 4)}")

    # c) Forward con hidden states & attention
    with torch.no_grad():
        out = model(input_ids=input_ids,
                    attention_mask=attention_mask,
                    output_hidden_states=True,
                    output_attentions=True,
                    return_dict=True)

    hs = out.hidden_states
    num_layers = len(hs) - 1
    last_hidden = out.last_hidden_state

    print("\n[3) Hidden States]")
    print(f"Totale layer encoder: {num_layers}")
    print("Embeddings output (prima del layer 1):", tuple(hs[0].shape))
    print("Layer intermedio (es. 6):", tuple(hs[min(6, num_layers)].shape))
    print("Ultimo layer (last_hidden_state):", tuple(last_hidden.shape))

    # d) Self-attention (ultimo layer, head 0) – opzionale per ispezione
    atts = out.attentions
    num_heads = atts[-1].shape[1] if len(atts) > 0 else 0
    if num_heads > 0:
        layer_idx = num_layers - 1
        head_idx = 0
        att_matrix = atts[layer_idx][0, head_idx]  # (S,S)
        focus_token_idx = safe_token_index(tokens, "▁raggiunge")
        weights = att_matrix[focus_token_idx].cpu().numpy()
        print("\n[4) Self-Attention (ultimo layer, head 0)]")
        print(f"Token focus: index {focus_token_idx} -> '{tokens[focus_token_idx]}'")
        show_k = min(20, len(tokens))
        for j in range(show_k):
            print(f"  att[{focus_token_idx}->{j}] '{tokens[j]}': {weights[j]:.3f}")
    else:
        print("\n[4) Self-Attention] (non disponibile per questo modello)")

    # e) Mean pooling
    print("\n[5) Mean Pooling]")
    pooled_all = mean_pooling(last_hidden, attention_mask)  # include special
    print(" - Inclusi special tokens   | vector[:8]:", np.round(pooled_all[0, :8].cpu().numpy(), 4))
    non_special_mask = build_non_special_mask(input_ids, attention_mask)
    pooled_no_special = mean_pooling(last_hidden, non_special_mask)
    print(" - Esclusi special tokens   | vector[:8]:", np.round(pooled_no_special[0, :8].cpu().numpy(), 4))

    # f) L2-normalizzazione
    sent_vec_np = pooled_no_special.cpu().numpy()
    sent_vec_np = l2_normalize(sent_vec_np)  # (1,H)
    print("[6) L2-normalized] vector[:8]:", np.round(sent_vec_np[0, :8], 4))

    all_sentence_vecs.append(sent_vec_np)

# 6) Similarità del coseno fra le frasi
emb = np.vstack(all_sentence_vecs)  # (N, H)
sim = cosine_similarity(emb, emb)

print("\n" + "="*90)
print("[Similarità coseno tra frasi]")
for i in range(len(sentences)):
    for j in range(len(sentences)):
        print(f"sim(frase {i+1}, frase {j+1}) = {sim[i,j]:.3f}")

# 7) Proiezione in 3D e grafico
# f) PCA 3D plot
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import ScalarFormatter

# emb = np.vstack(all_sentence_vecs)   # già calcolato sopra (N, 384)
pca = PCA(n_components=3, random_state=0)
coords3d = pca.fit_transform(emb)  # (N, 3)

fig = plt.figure(figsize=(7.5, 8.5))
ax = fig.add_subplot(111, projection="3d")

# Punti + etichette
colors = ["#F59E0B", "#3B82F6", "#10B981"]  # F1, F2, F3
for i, (x, y, z) in enumerate(coords3d):
    ax.scatter(x, y, z, s=90, marker="x", color=colors[i])
    ax.text(x, y, z, f"F{i+1}", fontsize=11, weight="bold")

ax.set_title("Spazio degli embedding (PCA 3D)\nPunti vicini ⇒ alta similarità semantica", pad=16)
ax.set_xlabel("Dim 1")
ax.set_ylabel("Dim 2")
ax.set_zlabel("Dim 3")
ax.grid(True)

# --- Rendere il cubo davvero isotropico (stessi limiti per i tre assi) ---
x, y, z = coords3d[:, 0], coords3d[:, 1], coords3d[:, 2]
x_mid, y_mid, z_mid = np.mean(x), np.mean(y), np.mean(z)
x_rng, y_rng, z_rng = (x.max()-x.min()), (y.max()-y.min()), (z.max()-z.min())
max_rng = max(x_rng, y_rng, z_rng)
half = max_rng / 2.0

ax.set_xlim(x_mid - half, x_mid + half)
ax.set_ylim(y_mid - half, y_mid + half)
ax.set_zlim(z_mid - half, z_mid + half)

# Mantieni anche il box isotropico (per sicurezza)
ax.set_box_aspect([1, 1, 1])

# --- Niente notazione scientifica sugli assi 3D ---
sf = ScalarFormatter(useMathText=False, useOffset=False)
sf.set_powerlimits((-3, 3))
for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
    axis.set_major_formatter(sf)

# --- Margini per evitare tagli a destra/sopra ---
plt.tight_layout()
plt.subplots_adjust(left=0.05, right=0.98, top=0.90, bottom=0.05)

plt.savefig("embeddings_3d_isotropic.png", dpi=200)
plt.show()
print("Figura salvata come: embeddings_3d_isotropic.png")
