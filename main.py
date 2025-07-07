import database
import fetchArticoli
import riassuntoArticoli
import classificazione.classificazioneNB

#funzione per creare il database se non esiste - da eseguire una sola volta
#database.creazioneDatabase()

#Recuperiamo nuovi articoli: Titolo, data e url_cryptopanic
fetchArticoli.fetch_articoli_cryptopanic()

#Recuperiamo url originale degli articoli
fetchArticoli.fetch_url_articoli()

#Recuperiamo il contenuto dell'articolo dall' url originale
fetchArticoli.fetch_contenuto_html_articoli()

### Aggiungere quy query per impostare riassunto_breve e riassunto_lungo a NESSUN CONTENUTO se articolo_html contiene NESSU CONTENUTO

#Generiamo e salvaiamo il riassutno lungo e corto per gli articoli
riassuntoArticoli.riassunto_articoli()

#Classifichiamo in Categoria gli articoli senza categoria (nuovi)
classificazione.classificazioneNB.classificaNewArticle()

#database.reset_riassunti_articolo()
