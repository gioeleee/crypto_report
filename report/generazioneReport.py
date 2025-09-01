"""
Estrae le news rilevanti dell'ultima settimana dal DB SQLite 'crypto_news.db'
e genera un PDF con:
- Titolo: "Report mercato cryptovalute [YYYY/MM/DD] - [YYYY/MM/DD]"
- Sezione: "TOP 3 NEWS DELLA SETTIMANA" (Titolo, riassunto_lungo, Data e Sentiment)
- Sezioni per categoria con Top 3 (Titolo, riassunto_breve, Data e Sentiment)

Requisiti:
    pip install reportlab
"""

import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import List, Dict

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

DB_PATH = "crypto_news.db"
OUT_DIR = "reports"  # cartella di output

# Categorie richieste (usa questi label per il match case-insensitive)
CATEGORIES = [
    "News di Mercato, Analisi e Prezzi",
    "Regolamentazione e Normative",
    "Adozione e Mainstreaming",
    "Sicurezza, Hackeraggi e Truffe",
    "Innovazione e Nuovi Progetti",
]

def get_date_range_last_week(tz: str = "Europe/Rome") -> tuple[str, str, str, str]:
    """
    Ritorna (start_date_sql, end_date_sql, start_title, end_title).
    Intervallo: ultimi 7 giorni compreso oggi, nel fuso indicato.
    """
    today_local = datetime.now(ZoneInfo(tz)).date()
    start_date = today_local - timedelta(days=6)
    start_date_sql = start_date.strftime("%Y-%m-%d")
    end_date_sql = today_local.strftime("%Y-%m-%d")
    start_title = start_date.strftime("%Y/%m/%d")
    end_title = today_local.strftime("%Y/%m/%d")
    return start_date_sql, end_date_sql, start_title, end_title

def fetch_news(start_date_sql: str, end_date_sql: str) -> List[Dict]:
    """
    Query parametrizzata sull'intervallo date di meta_articoli.data.
    Filtri sui contenuti testuali in articoli.* (non NULL e non 'NESSUN CONTENUTO').
    """
    query = """
        SELECT
            a.id,
            a.titolo,
            a.articolo_completo_html,
            a.riassunto_breve,
            a.riassunto_lungo,
            a.categoria AS categoria_articolo,
            a.peso,
            a.sentiment,
            ma.data        AS data_articolo,
            ma.url_cryptopanic,
            ma.url_articolo,
            ma.categoria   AS categoria_meta
        FROM articoli AS a
        JOIN meta_articoli AS ma ON a.id = ma.id
        WHERE DATE(ma.data) BETWEEN ? AND ?
          AND a.articolo_completo_html IS NOT NULL AND a.articolo_completo_html != 'NESSUN CONTENUTO'
          AND a.riassunto_breve        IS NOT NULL AND a.riassunto_breve        != 'NESSUN CONTENUTO'
          AND a.riassunto_lungo        IS NOT NULL AND a.riassunto_lungo        != 'NESSUN CONTENUTO'
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(query, (start_date_sql, end_date_sql))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def _fmt_date(date_value) -> str:
    """Prova a formattare la data in YYYY/MM/DD, altrimenti restituisce la stringa originale."""
    try:
        d = datetime.fromisoformat(str(date_value))
        return d.strftime("%Y/%m/%d")
    except Exception:
        return str(date_value)

def _norm(s: str | None) -> str:
    """Normalizza stringhe per confronto case-insensitive e trimming."""
    return (s or "").strip()

def _resolve_category(row: Dict) -> str:
    """
    Determina la categoria dell'articolo:
    - preferisci 'categoria_articolo' se presente, altrimenti 'categoria_meta'
    - ritorna la stringa così com'è per preservare i label noti
    """
    cat = row.get("categoria_articolo") or row.get("categoria_meta") or ""
    return cat.strip()

def build_pdf(news: List[Dict], start_title: str, end_title: str, out_dir: str = OUT_DIR) -> Path:
    """
    Genera il PDF con:
    - Titolo
    - TOP 3 della settimana (peso desc) con riassunto_lungo
    - Sezioni per categoria (Top 3, esclusi i già presenti in TOP 3) con riassunto_breve
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    filename = f"report_mercato_cryptovalute_{start_title.replace('/','-')}_{end_title.replace('/','-')}.pdf"
    out_path = Path(out_dir) / filename

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Report mercato cryptovalute {start_title} - {end_title}",
        author="Report Bot",
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleCenter", parent=styles["Title"], alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="SectionHeader", parent=styles["Heading2"], spaceBefore=14, spaceAfter=8))
    styles.add(ParagraphStyle(name="BodyJustify", parent=styles["BodyText"], alignment=TA_JUSTIFY, leading=14))
    styles.add(ParagraphStyle(name="Meta", parent=styles["BodyText"], spaceBefore=2, spaceAfter=10))

    story = []

    # Titolo
    story.append(Paragraph(f"Report mercato cryptovalute {start_title} - {end_title}", styles["TitleCenter"]))
    story.append(Spacer(1, 12))

    # ===== Sezione TOP 3 NEWS DELLA SETTIMANA =====
    story.append(Paragraph("TOP 3 NEWS DELLA SETTIMANA", styles["SectionHeader"]))
    excluded_ids: set[int] = set()
    if news:
        top3 = sorted(news, key=lambda r: (r.get("peso") is None, r.get("peso")), reverse=True)[:3]
        for i, row in enumerate(top3, start=1):
            excluded_ids.add(row["id"])
            titolo = row.get("titolo") or "(Senza titolo)"
            riassunto_lungo = row.get("riassunto_lungo") or ""
            data_str = _fmt_date(row.get("data_articolo"))
            sentiment = row.get("sentiment")

            story.append(Paragraph(f"{i}. {titolo}", styles["Heading3"]))
            story.append(Paragraph(riassunto_lungo, styles["BodyJustify"]))
            story.append(Paragraph(
                f"<b>Data:</b> {data_str} &nbsp;&nbsp; "
                f"<b>Sentiment:</b> {sentiment if sentiment is not None else 'N/D'}",
                styles["Meta"]
            ))
    else:
        story.append(Paragraph("Nessuna news rilevante trovata nell'intervallo.", styles["BodyJustify"]))

    # ===== Sezioni per categoria (Top 3 per peso, esclusi i già mostrati) =====
    # Prepara un indice per categoria (case-insensitive match contro i label dati)
    if news:
        # normalizza mapping categoria->lista news
        news_by_cat: dict[str, list[Dict]] = {cat: [] for cat in CATEGORIES}

        for row in news:
            if row["id"] in excluded_ids:
                continue  # escludi le notizie già in TOP 3 generale
            cat_value = _resolve_category(row)
            # match case-insensitive sui label forniti
            matched = None
            for target in CATEGORIES:
                if _norm(cat_value).lower() == _norm(target).lower():
                    matched = target
                    break
            if matched:
                news_by_cat[matched].append(row)

        # per ogni categoria, ordina per peso e stampa top 3
        for cat in CATEGORIES:
            cat_items = news_by_cat.get(cat, [])
            # se non c'è nulla, salta la sezione
            if not cat_items:
                continue

            story.append(Spacer(1, 8))
            story.append(Paragraph(cat, styles["SectionHeader"]))

            top3_cat = sorted(cat_items, key=lambda r: (r.get("peso") is None, r.get("peso")), reverse=True)[:3]
            for i, row in enumerate(top3_cat, start=1):
                titolo = row.get("titolo") or "(Senza titolo)"
                riassunto_breve = row.get("riassunto_breve") or ""
                data_str = _fmt_date(row.get("data_articolo"))
                sentiment = row.get("sentiment")

                story.append(Paragraph(f"{i}. {titolo}", styles["Heading3"]))
                story.append(Paragraph(riassunto_breve, styles["BodyJustify"]))
                story.append(Paragraph(
                    f"<b>Data:</b> {data_str} &nbsp;&nbsp; "
                    f"<b>Sentiment:</b> {sentiment if sentiment is not None else 'N/D'}",
                    styles["Meta"]
                ))

    doc.build(story)
    return out_path

def main():
    start_date_sql, end_date_sql, start_title, end_title = get_date_range_last_week("Europe/Rome")
    news = fetch_news(start_date_sql, end_date_sql)
    pdf_path = build_pdf(news, start_title, end_title)
    print(f"PDF creato: {pdf_path}")

if __name__ == "__main__":
    main()
