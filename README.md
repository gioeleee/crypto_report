# Progetto tesi

 TO DO:
 
- Regressione per la generazione di peso e sentiment (regressione) dando in input titolo, riassunto_lungo.
    Criteri adottati per la generazione da parte di chatgpt del dataset di addestramento:
        Restituirò:
            peso: un valore float tra 0.0 e 1.0 che rappresenta l'importanza dell'articolo
            sentiment: un valore float tra 0 e 1.0 che rappresenta il tono del contenuto
        Criteri (che applicherò):
            Peso:   
                Valore alto (0.8–1.0) per articoli su Bitcoin,Nuovi massimi storici di Bitcoin, Ethereum, ETF, trend globali, regolamentazioni importanti, hack o comunque in generale notizie che hanno un peso o che risultanto essere il trend del momento
                Medio (0.4–0.7) per aggiornamenti su altcoin noti, partnership o tecnologie rilevanti
                Basso (0.0–0.3) per gossip, meme coin, notizie ripetitive o marginali
            Sentiment:
                Negativo: 0.0 → 0.3 (problemi, crolli, hack, FUD)
                Neutro: ≈ 0.4/0.6 (analisi oggettive, previsioni incerte)
                Positivo: 0.7 → 1.0 (bullish, approvazioni, rally, adozione)

- Fare la creazione del report settimanale o in generale del report specificando il periodo
    Top good and bad news
    Top news per categoria
    Generazione del fear and greed index
    (plus) Riassunto di tutte le news e fear and greed index

- Migliorare il codice / errori e gestione degli errori



DONE:
- Estrazione tramite scraping delle News
- Addestramento di LLama3.2 per la generazione di riassunti
- Addestramento di NB per la classificare le news (Classificazione)
- Mettere estrazione del link originale ed estrazione del contenuto della pagina in un unica funzione
- Aggiungere richiesta per chiedere il link dell' API perchè lo avviamo dopo altrimenti su colab se non vengono fatti i calcoli si interrompe l'esecuzione.
Quindi si genera il link e lo si inserisce nella riga di comando come stringa.

NOT DONE:
- Aggiungere il fatto di cliccare sulla check per verificare se non si è un robot quando vengono ritrovati gli url originali degli articoli.





