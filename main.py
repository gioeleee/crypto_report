import database
import fetchArticoli

#funzione per creare il database se non esiste - da eseguire una sola volta
database.creazioneDatabase()

#Recuperiamo nuovi articoli: Titolo, data e url_cryptopanic
#fetchArticoli.fetchArticoliCryptopanic()

#Recuperiamo url originale degli articoli
#fetchArticoli.fetchUrlArticoli()

#Recuperiamo il contenuto dell'articolo
fetchArticoli.fetch_and_process_html_articoli()
