import database
import fetchArticoli

#funzione per creare il database se non esiste - da eseguire una sola volta
database.creazioneDatabase()

#Recuperiamo Titolo, data e url_cryptopanic
fetchArticoli.fetchArticoliCryptopanic2()