"""
Estrae le news dell'ultima settimana dal DB 'crypto_news.db' e genera un PDF con:
- Titolo
- TOP 3 NEWS DELLA SETTIMANA (riassunto_lungo)
- Sezioni per categoria (Top 3, riassunto_breve)
- Fear & Greed Index (media ponderata su peso) con gauge disegnata direttamente nel PDF

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
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Wedge, Line, Circle, String

DB_PATH = "crypto_news.db"
OUT_DIR = "reports"  # cartella di output

CATEGORIES = [
    "News di Mercato, Analisi e Prezzi",
    "Regolamentazione e Normative",
    "Adozione e Mainstreaming",
    "Sicurezza, Hackeraggi e Truffe",
    "Innovazione e Nuovi Progetti",
]

# ---------------------- Date ----------------------
def get_date_range_last_week(tz: str = "Europe/Rome") -> tuple[str, str, str, str]:
    today_local = datetime.now(ZoneInfo(tz)).date()
    start_date = today_local - timedelta(days=6)
    start_date_sql = start_date.strftime("%Y-%m-%d")
    end_date_sql = today_local.strftime("%Y-%m-%d")
    start_title = start_date.strftime("%Y/%m/%d")
    end_title = today_local.strftime("%Y/%m/%d")
    return start_date_sql, end_date_sql, start_title, end_title

# ---------------------- DB ----------------------
def fetch_news(start_date_sql: str, end_date_sql: str) -> List[Dict]:
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

# ---------------------- Util ----------------------
def _fmt_date(date_value) -> str:
    try:
        d = datetime.fromisoformat(str(date_value))
        return d.strftime("%Y/%m/%d")
    except Exception:
        return str(date_value)

def _norm(s: str | None) -> str:
    return (s or "").strip()

def _resolve_category(row: Dict) -> str:
    return (row.get("categoria_articolo") or row.get("categoria_meta") or "").strip()

# ---------------------- Fear & Greed ----------------------
def compute_fng_index(news: List[Dict]) -> tuple[int, str]:
    """
    Ritorna (indice 0-100, label).
    indice = 100 * media ponderata di 'sentiment' con pesi 'peso'.
    """
    values, weights = [], []
    for r in news:
        s, w = r.get("sentiment"), r.get("peso")
        if s is None or w is None:
            continue
        try:
            s = float(s); w = float(w)
        except Exception:
            continue
        if w < 0:
            continue
        values.append(s); weights.append(w)

    if not values:
        return 50, "Neutral"

    wsum = sum(weights)
    avg = (sum(values) / len(values)) if wsum <= 0 else sum(v*w for v, w in zip(values, weights)) / wsum
    score = int(round(max(0.0, min(1.0, avg)) * 100))

    if score <= 24:
        label = "Extreme Fear"
    elif score <= 44:
        label = "Fear"
    elif score <= 55:
        label = "Neutral"
    elif score <= 75:
        label = "Greed"
    else:
        label = "Extreme Greed"
    return score, label

def draw_fng_gauge(score: int, label: str, width: int = 420, height: int = 260) -> Drawing:
    """
    Crea e restituisce un Drawing (Flowable) con una gauge semicircolare.
    Nessun uso di renderPM/rlPyCairo: viene inserita direttamente nel PDF.
    """
    d = Drawing(width, height)

    cx, cy = width / 2, height * 0.58
    r_outer = min(width, height) * 0.40
    r_inner = r_outer * 0.72

    # settori (rosso -> arancio -> giallo -> verde chiaro -> verde)
    sectors = [
        (0, 36, colors.red),
        (36, 72, colors.orange),
        (72, 108, colors.yellow),
        (108, 144, colors.yellowgreen),
        (144, 180, colors.green),
    ]
    for start, end, col in sectors:
        d.add(Wedge(cx, cy, r_outer, 180 - end, 180 - start, strokeColor=colors.white, fillColor=col, strokeWidth=0))
        d.add(Wedge(cx, cy, r_inner, 180 - end, 180 - start, strokeColor=colors.white, fillColor=colors.white, strokeWidth=0))

    # Ago
    import math
    angle = 180 - (score / 100.0) * 180.0
    x2 = cx + r_outer * 0.95 * math.cos(math.radians(angle))
    y2 = cy + r_outer * 0.95 * math.sin(math.radians(angle))
    d.add(Line(cx, cy, x2, y2, strokeColor=colors.gray, strokeWidth=4))
    d.add(Circle(cx, cy, r_outer * 0.06, strokeColor=colors.gray, fillColor=colors.whitesmoke, strokeWidth=2))

    # Punteggio
    d.add(String(cx, cy - r_outer * 0.15, str(score), fontName="Helvetica-Bold", fontSize=24, fillColor=colors.black, textAnchor="middle"))

    # Titolo + label
    d.add(String(cx, height * 0.12, "Fear & Greed Index", fontName="Helvetica-Bold", fontSize=16, textAnchor="middle"))
    d.add(String(cx, height * 0.07, label, fontName="Helvetica", fontSize=12, textAnchor="middle"))

    return d

# ---------------------- PDF ----------------------
def build_pdf(news: List[Dict], start_title: str, end_title: str, out_dir: str = OUT_DIR) -> Path:
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
    story.append(Paragraph(f"Report mercato cryptovalute {start_title} - {end_title}", styles["TitleCenter"]))
    story.append(Spacer(1, 12))

    # ===== TOP 3 NEWS DELLA SETTIMANA =====
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

    # ===== Sezioni per categoria =====
    if news:
        news_by_cat: dict[str, list[Dict]] = {cat: [] for cat in CATEGORIES}
        for row in news:
            if row["id"] in excluded_ids:
                continue
            cat_value = _resolve_category(row)
            for target in CATEGORIES:
                if _norm(cat_value).lower() == _norm(target).lower():
                    news_by_cat[target].append(row)
                    break

        for cat in CATEGORIES:
            cat_items = news_by_cat.get(cat, [])
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

    # ===== Fear & Greed Index =====
    score, label = compute_fng_index(news or [])
    story.append(Spacer(1, 16))
    story.append(Paragraph("Fear & Greed Index (news-weighted)", styles["SectionHeader"]))
    story.append(Paragraph(
        "Calcolato come media ponderata del sentiment (0–1) con pesi proporzionali alla rilevanza (peso). "
        "0 = Extreme Fear, 100 = Extreme Greed.",
        styles["BodyJustify"]
    ))

    # Gauge disegnata direttamente (niente PNG, niente renderPM)
    gauge = draw_fng_gauge(score, label, width=int(12*cm), height=int(7.5*cm))
    story.append(Spacer(1, 6))
    story.append(gauge)
    story.append(Paragraph(f"Now: <b>{label}</b> (indice: <b>{score}</b>)", styles["Meta"]))

    doc.build(story)
    return out_path

# ---------------------- Main ----------------------
def main():
    start_date_sql, end_date_sql, start_title, end_title = get_date_range_last_week("Europe/Rome")
    news = fetch_news(start_date_sql, end_date_sql)
    pdf_path = build_pdf(news, start_title, end_title)
    print(f"PDF creato: {pdf_path}")

if __name__ == "__main__":
    main()
