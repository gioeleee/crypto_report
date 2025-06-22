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
