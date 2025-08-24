import database
import fetchArticoli
import riassunti.riassuntoArticoli as riassuntoArticoli
import classificazione.classificazioneNB
import regressionePesoSentiment.regressorePesoSentiment2 as PesoSentiment

#NON AVVIARE - funzione per creare il database se non esiste - da eseguire una sola volta
#database.creazioneDatabase()

#Recuperiamo nuovi articoli: Titolo, data e url_cryptopanic
fetchArticoli.fetch_articoli_cryptopanic()

#Recuperiamo url originale degli articoli e il contenuto dell' articolo
fetchArticoli.fetch_url_e_html_articoli()

### Aggiungere quy query per impostare riassunto_breve e riassunto_lungo a NESSUN CONTENUTO se articolo_html contiene NESSU CONTENUTO

#Generiamo e salvaiamo il riassutno lungo e corto per gli articoli
riassuntoArticoli.riassunto_articoli()

#Classifichiamo in Categoria gli articoli senza categoria (nuovi)
classificazione.classificazioneNB.classificaNewArticle()

# Generiamo Peso e Sentiment per gli articoli 
PesoSentiment.genera_peso_sentiment_per_articoli()

#database.reset_riassunti_articolo()
