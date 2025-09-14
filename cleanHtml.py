import spacy
from sklearn.metrics.pairwise import cosine_similarity
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from langdetect import detect


# Carichiamo il modello NLP per l'italiano
nlp = spacy.load("it_core_news_md")

# Carichiamo il modello SBERT
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

def text_similarity_sbert(text1, text2):
    """ Calcola la similarità coseno usando Sentence-BERT """
    vec1 = model.encode(text1).reshape(1, -1)
    vec2 = model.encode(text2).reshape(1, -1)
    return cosine_similarity(vec1, vec2)[0][0]

def detect_main_language(text):
    """ Rileva la lingua principale del testo """
    try:
        return detect(text)
    except:
        return "unknown"


#funzione per pulire l'html recuperando solo l'articolo
def clean_html_content(html_content, similarity_threshold=0.35, h2_similarity_threshold=0.35):
    """
    Pulisce il codice HTML lavorando solo sul contenuto dentro <body>, rimuovendo contenuti prima di <h1>,
    filtrando i paragrafi incoerenti con il precedente, confrontando <h2> + successivo tag con il titolo <h1>,
    ed eliminando il contenuto se è scritto in una lingua diversa dall'italiano.

    Args:
        html_content (str): Il codice HTML della pagina.
        similarity_threshold (float): Soglia per il confronto tra paragrafi.
        h2_similarity_threshold (float): Soglia più bassa per confrontare <h2> + successivo tag con <h1>.

    Returns:
        str: Testo pulito mantenendo solo i paragrafi coerenti, oppure stringa vuota se il risultato è troppo breve, troppo lungo o scritto in un'altra lingua.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Consideriamo solo il contenuto dentro il <body>
    body = soup.body
    if not body:
        return ""  # Se non c'è un <body>, ritorniamo stringa vuota
    
    # Troviamo il primo <h1> e usiamolo come riferimento principale
    elements = body.find_all(["h1", "h2", "p"])
    h1_index = next((i for i, el in enumerate(elements) if el.name == "h1"), None)

    if h1_index is None:
        return ""  # Se non c'è un <h1>, ritorniamo stringa vuota

    # Estrarre il titolo <h1>
    title = elements[h1_index].get_text(separator=" ", strip=True)

    # Manteniamo solo i tag dopo il primo <h1>
    elements = elements[h1_index:]

    filtered_text = [title]  # Lista per raccogliere solo il testo senza tag
    previous_text = None  # Per confronto tra paragrafi normali
    last_header = None  # Per gestire il confronto <h2> + successivo tag

    for i, element in enumerate(elements[1:]):  # Escludiamo il primo elemento (<h1>)
        text = element.get_text(separator=" ", strip=True)

        # Rimuoviamo elementi vuoti o troppo brevi
        if not text or len(text) < 5:
            continue

        # Se è un <h2>, lo salviamo temporaneamente per confrontarlo con il successivo
        if element.name == "h2":
            last_header = text
            continue

        # Se avevamo un <h2>, confrontiamo con <h1>
        if last_header:
            combined_text = last_header + " " + text
            similarity = text_similarity_sbert(title, combined_text)

            if similarity >= h2_similarity_threshold:
                filtered_text.append(last_header)
                filtered_text.append(text)
                previous_text = text
            last_header = None
            continue

        # Per tutti gli altri elementi, confrontiamo con il paragrafo precedente
        if previous_text:
            similarity = text_similarity_sbert(previous_text, text)
            if similarity >= similarity_threshold:
                filtered_text.append(text)
                previous_text = text
        else:
            filtered_text.append(text)
            previous_text = text

    # Se il numero di elementi è troppo basso, scartiamo il contenuto
    if len(filtered_text) < 3:
        return ""

    # Controlliamo la lingua del testo risultante
    full_text = " ".join(filtered_text)
    
    # Scartiamo il testo se supera i 16.000 caratteri
    if len(full_text) > 16000:
        return ""
    
    detected_lang = detect_main_language(full_text)

    if detected_lang != "it":
        return ""

    return "\n".join(filtered_text)


