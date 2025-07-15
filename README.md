# Progetto tesi

 TO DO:
 
 - Analisi dell'importanza tematica: identificare concetti o entità (es. criptovalute, eventi, aziende) che ricorrono frequentemente nei contenuti in uno specifico intervallo temporale, per attribuire maggiore rilevanza a determinati temi. Questo è utile per stabile quali saranno le notizie che compariranno nel report settimanale.

- Sviluppo del Fear and Greed Index: progettare un indicatore aggregato basato sui contenuti analizzati, utile a rappresentare il sentiment generale del mercato;

- Generazione di un report settimanale automatizzato: strutturato per categoria tematica, con evidenza degli articoli principali e dei relativi indicatori (incluso l'indice di sentiment).


FATTO:
- Estrazione tramite scraping delle News
- Addestramento di LLama3.2 per la generazione di riassunti
- Addestramento di NB per la classificare le news (Classificazione)

TO DO:
- Mettere estrazione del link originale ed estrazione del contenuto della pagina in un unica funzione
- Aggiungere il fatto di cliccare sulla check per verificare se non si è un robot quando vengono ritrovati gli url originali degli articoli.
- Addestramento di DistilBERT per la generazione di peso e sentiment (regressione) dando in input titolo, riassunto_lungo e categoria (precedentemente creata con NB):
    - criteri adottati per la generazione da parte di chatgpt del dataset di addestramento:
        Restituirò:
            peso: un valore float tra 0.0 e 1.0 che rappresenta l'importanza dell'articolo
            sentiment: un valore float tra 0 e 1.0 che rappresenta il tono del contenuto
        Criteri (che applicherò):
            Peso:   
                Valore alto (0.8–1.0) per articoli su Bitcoin, Ethereum, ETF, trend globali, regolamentazioni importanti
                Medio (0.4–0.7) per aggiornamenti su altcoin noti, partnership o tecnologie rilevanti
                Basso (0.0–0.3) per gossip, meme coin, notizie ripetitive o marginali
            Sentiment:
                Negativo: 0.0 → 0.3 (problemi, crolli, hack, FUD)
                Neutro: ≈ 0.4/0.6 (analisi oggettive, previsioni incerte)
                Positivo: 0.7 → 1.0 (bullish, approvazioni, rally, adozione)



