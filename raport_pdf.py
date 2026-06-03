"""
Generator raportu PDF z analizy ryzyka upadłości.

Wykorzystuje reportlab + DejaVu Sans (obsługa polskich znaków diakrytycznych).
Zwraca bajty PDF gotowe do przekazania do st.download_button.
"""
from io import BytesIO
from datetime import datetime
from typing import Dict, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)

# --- Rejestracja czcionki z polskimi znakami ---
from pathlib import Path
# --- Rejestracja czcionki z polskimi znakami ---
# Ścieżki relatywne do tego pliku — działają lokalnie, na Replicie
# i na Streamlit Cloud (pliki .ttf są commitowane do repozytorium).
_FONTS_DIR = Path(__file__).parent / "fonts"
_FONT_PATHS = {
    "DejaVu":      _FONTS_DIR / "DejaVuSans.ttf",
    "DejaVu-Bold": _FONTS_DIR / "DejaVuSans-Bold.ttf",
}
_FONTS_REGISTERED = False
def _zarejestruj_czcionki():
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    try:
        for name, path in _FONT_PATHS.items():
            pdfmetrics.registerFont(TTFont(name, str(path)))
        _FONTS_REGISTERED = True
    except Exception:
        # Fallback do Helvetica jeśli pliki .ttf niedostępne
        _FONTS_REGISTERED = False


# Kolory korporacyjne (zgodne z app.py)
GRANATOWY = colors.HexColor("#0F2A47")
ZLOTO = colors.HexColor("#C9A227")
JASNY = colors.HexColor("#F4F6FA")
BIALY = colors.white
SZARY = colors.HexColor("#475569")
ZAGROZONY = colors.HexColor("#dc2626")
SZARA_STREFA = colors.HexColor("#f59e0b")
BEZPIECZNY = colors.HexColor("#16a34a")


def _style():
    """Zwraca słownik styli akapitów."""
    _zarejestruj_czcionki()
    font = "DejaVu" if _FONTS_REGISTERED else "Helvetica"
    font_b = "DejaVu-Bold" if _FONTS_REGISTERED else "Helvetica-Bold"

    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=styles["Title"], fontName=font_b,
            fontSize=18, textColor=GRANATOWY, spaceAfter=4, leading=22,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=styles["Normal"], fontName=font,
            fontSize=10, textColor=SZARY, spaceAfter=12,
        ),
        "h2": ParagraphStyle(
            "h2", parent=styles["Heading2"], fontName=font_b,
            fontSize=13, textColor=GRANATOWY, spaceBefore=14, spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "h3", parent=styles["Heading3"], fontName=font_b,
            fontSize=11, textColor=GRANATOWY, spaceBefore=10, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body", parent=styles["Normal"], fontName=font,
            fontSize=9.5, textColor=colors.HexColor("#1F2937"),
            spaceAfter=6, leading=13,
        ),
        "small": ParagraphStyle(
            "small", parent=styles["Normal"], fontName=font,
            fontSize=8, textColor=SZARY, spaceAfter=4, leading=10,
        ),
        "footer": ParagraphStyle(
            "footer", parent=styles["Normal"], fontName=font,
            fontSize=7.5, textColor=SZARY, alignment=1,
        ),
        "font": font,
        "font_b": font_b,
    }


def _kolor_strefy(interpretacja: str):
    if "Zagroż" in interpretacja:
        return ZAGROZONY
    if "szar" in interpretacja.lower() or "Słaba" in interpretacja:
        return SZARA_STREFA
    if interpretacja in ("Brak danych do obliczenia", "—"):
        return SZARY
    return BEZPIECZNY


def _naglowek_stopka(canvas, doc, autor: str):
    """Rysuje stopkę na każdej stronie."""
    canvas.saveState()
    canvas.setFont("DejaVu" if _FONTS_REGISTERED else "Helvetica", 7.5)
    canvas.setFillColor(SZARY)
    # Linia
    canvas.setStrokeColor(ZLOTO)
    canvas.setLineWidth(0.8)
    canvas.line(20 * mm, 18 * mm, A4[0] - 20 * mm, 18 * mm)
    # Tekst
    canvas.drawString(
        20 * mm, 12 * mm,
        f"{autor}  ·  Kalkulator Zagrożenia Upadłością  ·  Projekt portfolio",
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
    """
    Generuje raport PDF.

    Args:
        tytul: tytuł nagłówka (np. nazwa spółki lub "Raport — pojedynczy okres")
        podtytul: opis okresu / źródła danych
        autor: imię i nazwisko autora aplikacji
        dane: słownik wartości finansowych {klucz: wartość}
        wyniki: wynik policz_wszystkie_modele(dane)
        pola_etykiety: lista (klucz, etykieta_pol) z POLA_FINANSOWE
        kontekst: opcjonalne dodatkowe informacje (sektor, kapitalizacja itd.)
    """
    _zarejestruj_czcionki()
    s = _style()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=24 * mm,
    )
    story = []

    # ----- Nagłówek -----
    story.append(Paragraph(tytul, s["title"]))
    story.append(Paragraph(podtytul, s["subtitle"]))

    if kontekst:
        kontekst_rows = [[k, v] for k, v in kontekst.items()]
        t = Table(kontekst_rows, colWidths=[55 * mm, 105 * mm])
        t.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, -1), s["font"], 9),
            ("TEXTCOLOR", (0, 0), (0, -1), GRANATOWY),
            ("FONT", (0, 0), (0, -1), s["font_b"], 9),
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

    # ----- Wyniki modeli -----
    story.append(Paragraph("Wyniki modeli dyskryminacyjnych", s["h2"]))

    rows = [["Model", "Z-score", "Klasyfikacja"]]
    kolory_wierszy = [None]
    for nazwa, info in wyniki.items():
        z = info["wynik"]
        z_str = "—" if z is None else f"{z:.4f}"
        rows.append([nazwa, z_str, info["interpretacja"]])
        kolory_wierszy.append(_kolor_strefy(info["interpretacja"]))

    t = Table(rows, colWidths=[55 * mm, 30 * mm, 75 * mm])
    style_cmds = [
        ("FONT", (0, 0), (-1, 0), s["font_b"], 9),
        ("BACKGROUND", (0, 0), (-1, 0), GRANATOWY),
        ("TEXTCOLOR", (0, 0), (-1, 0), BIALY),
        ("FONT", (0, 1), (-1, -1), s["font"], 9),
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
            style_cmds.append(("FONT", (2, i), (2, i), s["font_b"], 9))
    t.setStyle(TableStyle(style_cmds))
    story.append(t)

    # ----- Konsensus -----
    licz_zagr = sum(
        1 for v in wyniki.values()
        if v["wynik"] is not None and "Zagroż" in v["interpretacja"]
    )
    licz_obl = sum(1 for v in wyniki.values() if v["wynik"] is not None)
    konsensus = "ZAGROŻENIE" if licz_zagr > licz_obl / 2 else "BRAK ZAGROŻENIA"
    kolor_kons = ZAGROZONY if konsensus == "ZAGROŻENIE" else BEZPIECZNY

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f"<font name='{s['font_b']}'>Konsensus modeli: "
        f"<font color='{kolor_kons.hexval()}'>{konsensus}</font></font> "
        f"({licz_zagr} z {licz_obl} modeli sygnalizuje zagrożenie)",
        s["body"],
    ))

    # ----- Dane wejściowe -----
    story.append(Paragraph("Dane wejściowe (w tysiącach PLN)", s["h2"]))
    rows = [["Pozycja", "Wartość"]]
    for klucz, etyk in pola_etykiety:
        v = dane.get(klucz, 0)
        rows.append([etyk, f"{v:,.2f}".replace(",", " ")])
    t = Table(rows, colWidths=[100 * mm, 60 * mm])
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), s["font_b"], 9),
        ("BACKGROUND", (0, 0), (-1, 0), GRANATOWY),
        ("TEXTCOLOR", (0, 0), (-1, 0), BIALY),
        ("FONT", (0, 1), (-1, -1), s["font"], 8.5),
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

    # ----- Wskaźniki szczegółowe per model -----
    story.append(Paragraph("Wskaźniki szczegółowe per model", s["h2"]))
    for nazwa, info in wyniki.items():
        story.append(Paragraph(nazwa, s["h3"]))
        wsk = info.get("wskazniki") or {}
        if not wsk:
            story.append(Paragraph("Brak wskaźników do wyświetlenia.", s["small"]))
            continue
        rows = [["Wskaźnik", "Wartość"]]
        for k, v in wsk.items():
            rows.append([k, "—" if v is None else f"{v:.4f}"])
        t = Table(rows, colWidths=[40 * mm, 40 * mm])
        t.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, 0), s["font_b"], 8.5),
            ("BACKGROUND", (0, 0), (-1, 0), JASNY),
            ("TEXTCOLOR", (0, 0), (-1, 0), GRANATOWY),
            ("FONT", (0, 1), (-1, -1), s["font"], 8.5),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),
            ("BOX", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Paragraph(info.get("opis", ""), s["small"]))
        story.append(Spacer(1, 4))

    # ----- Disclaimer -----
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>Zastrzeżenie:</b> Raport został wygenerowany automatycznie przez "
        "aplikację „Kalkulator Zagrożenia Upadłością” w ramach projektu "
        "portfolio. Wartości wskaźników i klasyfikacji opierają się wyłącznie "
        "na danych wprowadzonych do formularza i nie uwzględniają jakościowych "
        "czynników ryzyka (jakość audytora, struktura wynagrodzenia zarządu, "
        "ryzyko sektorowe, czynniki makroekonomiczne). Raport nie stanowi "
        "rekomendacji inwestycyjnej w rozumieniu rozporządzenia MAR (UE 596/2014) "
        "ani Rozporządzenia Delegowanego Komisji (UE) 2017/565. Każda decyzja "
        "inwestycyjna lub kredytowa wymaga uzupełniającej analizy.",
        s["small"],
    ))

    # Render z stopką
    def _stopka(canvas, doc):
        _naglowek_stopka(canvas, doc, autor)

    doc.build(story, onFirstPage=_stopka, onLaterPages=_stopka)
    return buf.getvalue()
