import database
import fetchArticoli
import riassunti.riassuntoArticoli as riassuntoArticoli
import classificazione.classificazioneNB

#NON AVVIARE - funzione per creare il database se non esiste - da eseguire una sola volta
#database.creazioneDatabase()

#Recuperiamo nuovi articoli: Titolo, data e url_cryptopanic
#fetchArticoli.fetch_articoli_cryptopanic()

    ###NON AVVIARE - Procedura precedente con recupero url e recupero contentuto separati
#Recuperiamo url originale degli articoli
###fetchArticoli.fetch_url_articoli()
#Recuperiamo il contenuto dell'articolo dall' url originale
###fetchArticoli.fetch_contenuto_html_articoli()

#Recuperiamo url originale degli articoli e il contenuto dell' articolo
#fetchArticoli.fetch_url_e_html_articoli()


### Aggiungere quy query per impostare riassunto_breve e riassunto_lungo a NESSUN CONTENUTO se articolo_html contiene NESSU CONTENUTO

#Generiamo e salvaiamo il riassutno lungo e corto per gli articoli
riassuntoArticoli.riassunto_articoli()

#Classifichiamo in Categoria gli articoli senza categoria (nuovi)
classificazione.classificazioneNB.classificaNewArticle()

#database.reset_riassunti_articolo()
