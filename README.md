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





- Ok adesso nel database per ogni articolo c'è il titolo, data, riassunto breve, riassunto lungo, categoria, peso, sentiment.
Sulla base di queste informazioni mi devi creare un file pdf intitolato Report settimanale mercato cryptovalute [data inzio] - [data fine] e deve contenere le seguenti sezioni:
    1) Notizie più rilevanti:
        - Contiene le top 5 notizie con peso maggiore siano esse di sentiment positivo o negativo e per queste notizie contiene titolo,data, riassunto lungo
    2) Le top tre notizie con peso maggiore per ogni categoria (News di Mercato, Analisi e Prezzi - Innovazione e Nuovi Progetti - Sicurezzza, hackeraggi e Truffe - Adozione e Mainstreaming - Regolamentazione e Normative). Per queste notizie però comparirà solo titolo e riassunto breve.

    Infine nel fondo della pagina deve comparire il fear & greed ndex calcolato sulla base di peso e sentiment assegnato ad ogni notizia.


Devo generare la documentazione per la mia tesi di laurea, tieni conto che devo scrivere circa 80/100 pagine.
La mia tesi si intitola "Analisi automatizzata del mercato crypto attraverso tecniche di intelligenza artificiale." e quello che fa tramite script python è:
1) Raccolta delle notizie tramite web scarpaing (fonte: cryptopanic)
2) Addestramento di LLM (LLama3.2) e utilizzato per generazione di riassunti lunghi e brevi delle notizie
3) Classificazione delle news prima anando a dividere le news con un classificatore non supervisionato, dopo che il classificatore non supervisionato ha generato le ipotetiche categorie le ho etichettate e infine addestrato un classificatore superivisonato (NB) per generare le categorie delle nuove news.
4) Generato sentiment e peso andando ad addestrare un regressore
5) Generato il report settimanale + fear & greed index.

Allego un esempio di tesi fatta da un mio collega per darti un idea di come deve essere strutturata e allego anche i mio codice python attuale in modo tale che puoi capire bene come funziona.



MODIFICHE DA FARE:
DB:
    - Modificare campo articolo_completo_html in articolo_completo
    - Rimuovere campo categoria in meta_articoli e lasciarlo solo in articoli