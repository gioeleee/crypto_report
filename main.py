import database
import fetchArticoli

#funzione per creare il database se non esiste - da eseguire una sola volta
#database.creazioneDatabase()

#Recuperiamo nuovi articoli: Titolo, data e url_cryptopanic
#fetchArticoli.fetch_articoli_cryptopanic()

#Recuperiamo url originale degli articoli
#fetchArticoli.fetch_url_articoli()

#Recuperiamo il contenuto dell'articolo dall' url originale
fetchArticoli.fetch_contenuto_html_articoli()
