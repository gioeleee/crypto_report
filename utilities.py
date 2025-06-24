from datetime import datetime

def convert_to_sql_datetime(datetime_str):
    try:
        # Esempio: "Sat Jun 21 2025 15:44:38 GMT+0200"
        dt_clean = datetime_str.split(" GMT")[0]  # Rimuove il fuso orario e commenti
        dt_obj = datetime.strptime(dt_clean, "%a %b %d %Y %H:%M:%S")
        return dt_obj.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"❌ Errore nella conversione della data: {datetime_str} → {e}")
        return None

# Ordina la lista di articoli per data crescente (dal più vecchio).
def ordina_articoli_per_data(articoli):
    """Ordina la lista di articoli per data crescente (dal più vecchio)."""
    return sorted(
        [a for a in articoli if a[1] is not None],  # Filtra gli articoli che hanno `data` valida (non None)
        key=lambda x: x[1]                          # Ordina per la data (secondo elemento della tupla [1])
    )
