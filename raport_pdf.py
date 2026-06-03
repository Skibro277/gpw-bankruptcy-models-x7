"""
Generator raportu PDF z analizy ryzyka upadlosci.
Uzywa wylacznie standardowych fontow Helvetica (bez zewnetrznych .ttf)
dla pelnej kompatybilnosci ze Streamlit Cloud i kazdym lokalnym systemem.
"""
from io import BytesIO
from datetime import datetime
from typing import Dict, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)

FONT = "Helvetica"
FONT_B = "Helvetica-Bold"

# Kolory korporacyjne (zgodne z app.py)
GRANATOWY = colors.HexColor("#0F2A47")
ZLOTO = colors.HexColor("#C9A227")
JASNY = colors.HexColor("#F4F6FA")
BIALY = colors.white
SZARY = colors.HexColor("#475569")
ZAGROZONY = colors.HexColor("#dc2626")
SZARA_STREFA = colors.HexColor("#f59e0b")
BEZPIECZNY = colors.HexColor("#16a34a")


def _ascii(text: str) -> str:
    """Zamienia polskie znaki diakrytyczne na odpowiedniki ASCII."""
    mapa = str.maketrans({
        '\u0105': 'a', '\u0107': 'c', '\u0119': 'e', '\u0142': 'l',
        '\u0144': 'n', '\u00f3': 'o', '\u015b': 's', '\u017a': 'z',
        '\u017c': 'z', '\u0104': 'A', '\u0106': 'C', '\u0118': 'E',
        '\u0141': 'L', '\u0143': 'N', '\u00d3': 'O', '\u015a': 'S',
        '\u0179': 'Z', '\u017b': 'Z',
    })
    return text.translate(mapa) if isinstance(text, str) else text


def _style():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=styles["Title"], fontName=FONT_B,
            fontSize=18, textColor=GRANATOWY, spaceAfter=4, leading=22,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=styles["Normal"], fontName=FONT,
            fontSize=10, textColor=SZARY, spaceAfter=12,
        ),
        "h2": ParagraphStyle(
            "h2", parent=styles["Heading2"], fontName=FONT_B,
            fontSize=13, textColor=GRANATOWY, spaceBefore=14, spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "h3", parent=styles["Heading3"], fontName=FONT_B,
            fontSize=11, textColor=GRANATOWY, spaceBefore=10, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body", parent=styles["Normal"], fontName=FONT,
            fontSize=9.5, textColor=colors.HexColor("#1F2937"),
            spaceAfter=6, leading=13,
        ),
        "small": ParagraphStyle(
            "small", parent=styles["Normal"], fontName=FONT,
            fontSize=8, textColor=SZARY, spaceAfter=4, leading=10,
        ),
        "footer": ParagraphStyle(
            "footer", parent=styles["Normal"], fontName=FONT,
            fontSize=7.5, textColor=SZARY, alignment=1,
        ),
    }


def _kolor_strefy(interpretacja: str):
    if "Zagro" in interpretacja:
        return ZAGROZONY
    if "szar" in interpretacja.lower() or "Slaba" in interpretacja or "S\u0142aba" in interpretacja:
        return SZARA_STREFA
    if interpretacja in ("Brak danych do obliczenia", "\u2014"):
        return SZARY
    return BEZPIECZNY


def _naglowek_stopka(canvas, doc, autor: str):
    canvas.saveState()
    canvas.setFont(FONT, 7.5)
    canvas.setFillColor(SZARY)
    canvas.setStrokeColor(ZLOTO)
    canvas.setLineWidth(0.8)
    canvas.line(20 * mm, 18 * mm, A4[0] - 20 * mm, 18 * mm)
    canvas.drawString(
        20 * mm, 12 * mm,
        _ascii(f"{autor}  |  Kalkulator Zagrozenia Upadloscia  |  Projekt portfolio"),
    )
    canvas.drawRightString(
        A4[0] - 20 * mm, 12 * mm,
        f"Strona {doc.page}",
    )
    canvas.drawString(
        20 * mm, 7 * mm,
        "Raport ma charakter edukacyjno-portfolio'wy. Nie stanowi rekomendacji "
        "inwestycyjnej w rozumieniu MAR / Rozp. 2017/565.",
    )
    canvas.restoreState()


def generuj_raport(
    tytul: str,
    podtytul: str,
    autor: str,
    dane: Dict[str, float],
    wyniki: Dict[str, dict],
    pola_etykiety: list,
    kontekst: Optional[Dict] = None,
) -> bytes:
    s = _style()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=24 * mm,
    )
    story = []

    story.append(Paragraph(_ascii(tytul), s["title"]))
    story.append(Paragraph(_ascii(podtytul), s["subtitle"]))

    if kontekst:
        kontekst_rows = [[_ascii(str(k)), _ascii(str(v))] for k, v in kontekst.items()]
        t = Table(kontekst_rows, colWidths=[55 * mm, 105 * mm])
        t.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, -1), FONT, 9),
            ("TEXTCOLOR", (0, 0), (0, -1), GRANATOWY),
            ("FONT", (0, 0), (0, -1), FONT_B, 9),
            ("BACKGROUND", (0, 0), (-1, -1), JASNY),
            ("BOX", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))

    story.append(Paragraph("Wyniki modeli dyskryminacyjnych", s["h2"]))

    rows = [["Model", "Z-score", "Klasyfikacja"]]
    kolory_wierszy = [None]
    for nazwa, info in wyniki.items():
        z = info["wynik"]
        z_str = "\u2014" if z is None else f"{z:.4f}"
        rows.append([_ascii(nazwa), z_str, _ascii(info["interpretacja"])])
        kolory_wierszy.append(_kolor_strefy(info["interpretacja"]))

    t = Table(rows, colWidths=[55 * mm, 30 * mm, 75 * mm])
    style_cmds = [
        ("FONT", (0, 0), (-1, 0), FONT_B, 9),
        ("BACKGROUND", (0, 0), (-1, 0), GRANATOWY),
        ("TEXTCOLOR", (0, 0), (-1, 0), BIALY),
        ("FONT", (0, 1), (-1, -1), FONT, 9),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    for i, kolor in enumerate(kolory_wierszy):
        if kolor and i > 0:
            style_cmds.append(("TEXTCOLOR", (2, i), (2, i), kolor))
            style_cmds.append(("FONT", (2, i), (2, i), FONT_B, 9))
    t.setStyle(TableStyle(style_cmds))
    story.append(t)

    licz_zagr = sum(
        1 for v in wyniki.values()
        if v["wynik"] is not None and "Zagro" in v["interpretacja"]
    )
    licz_obl = sum(1 for v in wyniki.values() if v["wynik"] is not None)
    konsensus = "ZAGROZENIE" if licz_zagr > licz_obl / 2 else "BRAK ZAGROZENIA"
    kolor_kons = ZAGROZONY if "ZAGROZENIE" == konsensus else BEZPIECZNY

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f"<font name='{FONT_B}'>Konsensus modeli: "
        f"<font color='{kolor_kons.hexval()}'>{konsensus}</font></font> "
        f"({licz_zagr} z {licz_obl} modeli sygnalizuje zagrozenie)",
        s["body"],
    ))

    story.append(Paragraph("Dane wejsciowe (w tysiacach PLN)", s["h2"]))
    rows = [["Pozycja", "Wartosc"]]
    for klucz, etyk in pola_etykiety:
        v = dane.get(klucz, 0)
        rows.append([_ascii(etyk), f"{v:,.2f}".replace(",", " ")])
    t = Table(rows, colWidths=[100 * mm, 60 * mm])
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), FONT_B, 9),
        ("BACKGROUND", (0, 0), (-1, 0), GRANATOWY),
        ("TEXTCOLOR", (0, 0), (-1, 0), BIALY),
        ("FONT", (0, 1), (-1, -1), FONT, 8.5),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BIALY, JASNY]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)

    story.append(Paragraph("Wskazniki szczegolowe per model", s["h2"]))
    for nazwa, info in wyniki.items():
        story.append(Paragraph(_ascii(nazwa), s["h3"]))
        wsk = info.get("wskazniki") or {}
        if not wsk:
            story.append(Paragraph("Brak wskaznikow do wyswietlenia.", s["small"]))
            continue
        rows = [["Wskaznik", "Wartosc"]]
        for k, v in wsk.items():
            rows.append([_ascii(str(k)), "\u2014" if v is None else f"{v:.4f}"])
        t = Table(rows, colWidths=[40 * mm, 40 * mm])
        t.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, 0), FONT_B, 8.5),
            ("BACKGROUND", (0, 0), (-1, 0), JASNY),
            ("TEXTCOLOR", (0, 0), (-1, 0), GRANATOWY),
            ("FONT", (0, 1), (-1, -1), FONT, 8.5),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),
            ("BOX", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Paragraph(_ascii(info.get("opis", "")), s["small"]))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>Zastrzezenie:</b> Raport zostal wygenerowany automatycznie przez "
        "aplikacje 'Kalkulator Zagrozenia Upadloscia' w ramach projektu "
        "portfolio. Wartosci wskaznikow i klasyfikacji opieraja sie wylacznie "
        "na danych wprowadzonych do formularza i nie uwzgledniaja jakosciowych "
        "czynnikow ryzyka (jakosc audytora, struktura wynagrodzenia zarzadu, "
        "ryzyko sektorowe, czynniki makroekonomiczne). Raport nie stanowi "
        "rekomendacji inwestycyjnej w rozumieniu rozporzadzenia MAR (UE 596/2014) "
        "ani Rozporzadzenia Delegowanego Komisji (UE) 2017/565. Kazda decyzja "
        "inwestycyjna lub kredytowa wymaga uzupelniajacych analiz.",
        s["small"],
    ))

    def _stopka(canvas, doc):
        _naglowek_stopka(canvas, doc, autor)

    doc.build(story, onFirstPage=_stopka, onLaterPages=_stopka)
    return buf.getvalue()
