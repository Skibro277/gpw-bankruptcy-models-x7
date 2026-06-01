"""
Kalkulator Zagrożenia Upadłością Przedsiębiorstwa
Aplikacja Streamlit implementująca polskie i zagraniczne modele
dyskryminacyjne predykcji bankructwa.
"""

import json
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from gpw_data import lista_spolek, pobierz_spolke, podsumowanie_walidacji
from models import MODELE, policz_wszystkie_modele
from backtest_data import UPADLOSCI, lista_upadlosci, dane_w_tysiacach
from raport_pdf import generuj_raport
from walidacja import (
    metryki_wszystkich_modeli, ranking_po_metryce, zbierz_obserwacje,
)
from screening import skanuj_spolki, filtruj_uniwersum
from sesja import (
    WERSJA_APLIKACJI, zbuduj_snapshot, snapshot_jako_bytes,
    waliduj_snapshot, odczytaj_dane_ze_snapshotu,
)

st.set_page_config(
    page_title="Kalkulator Zagrożenia Upadłością",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------- Globalna szata graficzna (CSS) ---------
_GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+Pro:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
h1, h2, h3, h4 {
    font-family: 'Source Serif Pro', Georgia, serif !important;
    color: #0F2A47;
    letter-spacing: -0.01em;
}
.block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1280px; }

/* Hero header */
.hero {
    background: linear-gradient(135deg, #0F2A47 0%, #1E3A66 100%);
    color: #F8FAFC;
    padding: 28px 36px;
    border-radius: 10px;
    margin-bottom: 22px;
    border-left: 6px solid #C9A227;
    box-shadow: 0 2px 10px rgba(15,42,71,0.12);
}
.hero h1 {
    color: #FFFFFF !important;
    font-size: 30px !important;
    margin: 0 0 6px 0 !important;
    font-weight: 700;
}
.hero .hero-sub {
    color: #CBD5E1;
    font-size: 15px;
    margin-bottom: 12px;
    line-height: 1.45;
}
.hero .hero-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 18px;
    font-size: 13px;
    color: #E2E8F0;
    border-top: 1px solid rgba(201,162,39,0.35);
    padding-top: 12px;
}
.hero .hero-meta b { color: #C9A227; font-weight: 600; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #F8FAFC;
    border-right: 1px solid #E2E8F0;
}
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #0F2A47;
    font-size: 15px !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 8px;
}
.author-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #C9A227;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 6px;
}
.author-card .author-name {
    font-family: 'Source Serif Pro', Georgia, serif;
    font-weight: 700;
    font-size: 15px;
    color: #0F2A47;
    margin-bottom: 2px;
}
.author-card .author-role {
    font-size: 12.5px;
    color: #475569;
    line-height: 1.4;
}

/* Buttons */
.stButton > button[kind="primary"] {
    background: #0F2A47 !important;
    border-color: #0F2A47 !important;
    font-weight: 600;
    letter-spacing: 0.02em;
}
.stButton > button[kind="primary"]:hover {
    background: #1E3A66 !important;
    border-color: #C9A227 !important;
}

/* Section headers */
h3, h4 { padding-top: 6px; }

/* Tabs */
button[data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #0F2A47 !important;
    border-bottom-color: #C9A227 !important;
}

/* Metric */
[data-testid="stMetric"] {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 10px 14px;
}
[data-testid="stMetricLabel"] p {
    font-size: 12px !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748B !important;
}

/* Footer */
.app-footer {
    margin-top: 48px;
    padding: 22px 0 8px 0;
    border-top: 2px solid #C9A227;
    color: #475569;
    font-size: 12.5px;
    line-height: 1.5;
}
.app-footer .footer-name {
    color: #0F2A47;
    font-weight: 600;
    font-family: 'Source Serif Pro', Georgia, serif;
}

/* Hide Streamlit default chrome niceties */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* Dataframe polish */
[data-testid="stDataFrame"] {
    border: 1px solid #E2E8F0;
    border-radius: 6px;
}
</style>
"""
st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)


AUTOR_IMIE = "Arkadiusz Oczkowski"
AUTOR_ROLA = "Licencjonowany Makler Papierów Wartościowych"

POLA_FINANSOWE = [
    ("przychody_sprzedazy", "Przychody ze sprzedaży", 100000.0),
    ("przychody_rok_poprzedni", "Przychody rok poprzedni", 95000.0),
    ("wynik_operacyjny", "Wynik operacyjny (EBIT)", 12000.0),
    ("koszty_operacyjne", "Koszty operacyjne (RZiS)", 88000.0),
    ("wynik_brutto", "Wynik brutto (przed opodatkowaniem)", 10000.0),
    ("wynik_finansowy_netto", "Wynik finansowy netto", 8000.0),
    ("wynik_brutto_skumulowany", "Zyski zatrzymane (retained earnings)", 20000.0),
    ("aktywa_ogolem", "Aktywa ogółem", 150000.0),
    ("aktywa_obrotowe", "Aktywa obrotowe", 60000.0),
    ("zapasy", "Zapasy (inventory)", 15000.0),
    ("majatek_trwaly", "Majątek trwały", 90000.0),
    ("kapital_obrotowy", "Kapitał obrotowy netto", 30000.0),
    ("zobowiazania_ogolem", "Zobowiązania ogółem", 70000.0),
    ("zobowiazania_krotkoterm", "Zobowiązania krótkoterminowe", 30000.0),
    ("kapital_wlasny", "Kapitał własny", 80000.0),
    ("kapital_zakladowy", "Kapitał zakładowy", 50000.0),
    ("amortyzacja", "Amortyzacja", 5000.0),
    ("koszty_finansowe", "Koszty finansowe", 2000.0),
]


def _puste_dane() -> dict:
    return {klucz: 0.0 for klucz, _, _ in POLA_FINANSOWE}


def formularz_wprowadzania(prefix: str, wartosci_domyslne: dict) -> dict:
    """Renderuje formularz danych finansowych. Zwraca słownik wartości."""
    dane = {}
    cols = st.columns(3)
    for i, (klucz, etykieta, _) in enumerate(POLA_FINANSOWE):
        with cols[i % 3]:
            dane[klucz] = st.number_input(
                etykieta,
                value=float(wartosci_domyslne.get(klucz, 0.0)),
                step=1000.0,
                format="%.2f",
                key=f"{prefix}_{klucz}",
            )
    return dane


def karta_wyniku(nazwa_modelu: str, wynik_info: dict) -> None:
    """Renderuje pojedynczą kartę z wynikiem modelu."""
    wynik = wynik_info["wynik"]
    kolor = wynik_info["kolor"]
    interp = wynik_info["interpretacja"]

    if wynik is None:
        st.markdown(
            f"""
            <div style="border-left: 6px solid {kolor}; padding: 14px 18px;
                        background: #f9fafb; border-radius: 6px; margin-bottom: 10px;">
                <div style="font-size: 13px; color: #6b7280; text-transform: uppercase;
                            letter-spacing: 0.05em;">{nazwa_modelu}</div>
                <div style="font-size: 28px; font-weight: 600; color: #374151; margin: 4px 0;">
                    —
                </div>
                <div style="font-size: 14px; color: {kolor};">{interp}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
        <div style="border-left: 6px solid {kolor}; padding: 14px 18px;
                    background: #f9fafb; border-radius: 6px; margin-bottom: 10px;">
            <div style="font-size: 13px; color: #6b7280; text-transform: uppercase;
                        letter-spacing: 0.05em;">{nazwa_modelu}</div>
            <div style="font-size: 28px; font-weight: 600; color: #111827; margin: 4px 0;">
                Z = {wynik}
            </div>
            <div style="font-size: 14px; color: {kolor}; font-weight: 500;">{interp}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def wykres_porownawczy(wyniki: dict) -> go.Figure:
    """Wykres słupkowy porównujący znormalizowane wyniki wszystkich modeli."""
    nazwy, wartosci, kolory, opisy = [], [], [], []

    for nazwa, info in wyniki.items():
        if info["wynik"] is None:
            continue
        nazwy.append(nazwa)
        wartosci.append(info["wynik"])
        kolory.append(info["kolor"])
        opisy.append(info["interpretacja"])

    fig = go.Figure(
        data=[
            go.Bar(
                x=nazwy,
                y=wartosci,
                marker_color=kolory,
                text=[f"{w:.3f}<br>{o}" for w, o in zip(wartosci, opisy)],
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Wynik: %{y:.4f}<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        title="Porównanie wyników wszystkich modeli (każdy w swojej skali)",
        yaxis_title="Wartość Z-score",
        xaxis_title="Model",
        height=480,
        showlegend=False,
        margin=dict(t=60, b=80, l=40, r=20),
    )
    fig.add_hline(y=0, line_dash="dot", line_color="#9ca3af", opacity=0.6)
    return fig


def wykres_trendu(historia: dict) -> go.Figure:
    """Wykres liniowy trendu wyników w czasie."""
    fig = go.Figure()
    lata = sorted(historia.keys())

    for nazwa_modelu in MODELE.keys():
        seria = []
        for rok in lata:
            wynik = historia[rok].get(nazwa_modelu, {}).get("wynik")
            seria.append(wynik)

        if all(v is None for v in seria):
            continue

        fig.add_trace(
            go.Scatter(
                x=lata,
                y=seria,
                mode="lines+markers",
                name=nazwa_modelu,
                line=dict(width=2.5),
                marker=dict(size=9),
                connectgaps=True,
            )
        )

    fig.update_layout(
        title="Trend wyników modeli w kolejnych okresach",
        xaxis_title="Rok",
        yaxis_title="Wartość Z-score",
        height=500,
        hovermode="x unified",
        margin=dict(t=60, b=60, l=40, r=20),
    )
    return fig


def panel_wskaznikow(wyniki: dict) -> None:
    """Tabela ze wszystkimi wskaźnikami pośrednimi."""
    rows = []
    for nazwa_modelu, info in wyniki.items():
        for ws_nazwa, ws_wartosc in info["wskazniki"].items():
            rows.append({
                "Model": nazwa_modelu,
                "Wskaźnik": ws_nazwa,
                "Wartość": round(ws_wartosc, 4) if ws_wartosc is not None else "—",
            })
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)


def init_state():
    if "tryb" not in st.session_state:
        st.session_state.tryb = "Pojedynczy okres"
    if "dane_pojedyncze" not in st.session_state:
        st.session_state.dane_pojedyncze = {
            klucz: domyslna for klucz, _, domyslna in POLA_FINANSOWE
        }
    if "lata_dane" not in st.session_state:
        st.session_state.lata_dane = {
            2023: {klucz: domyslna for klucz, _, domyslna in POLA_FINANSOWE},
            2024: {klucz: domyslna * 1.05 for klucz, _, domyslna in POLA_FINANSOWE},
        }
    if "gpw_pobrane" not in st.session_state:
        st.session_state.gpw_pobrane = None
        st.session_state.screening_wyniki = None
    if "gpw_lata_dane" not in st.session_state:
        st.session_state.gpw_lata_dane = {}
    if "gpw_aktywny_ticker" not in st.session_state:
        st.session_state.gpw_aktywny_ticker = None


def main():
    init_state()

    st.markdown(
        f"""
        <div class="hero">
            <h1>Kalkulator Zagrożenia Upadłością</h1>
            <div class="hero-sub">
                Analiza dyskryminacyjna Z-score dla przedsiębiorstw — modele
                polskie (INE PAN, Hołda, Gajdka-Stos, Poznański) oraz
                klasyczne modele Altmana z weryfikacją w czasie rzeczywistym
                na danych spółek z GPW.
            </div>
            <div class="hero-meta">
                <div><b>7</b> modeli dyskryminacyjnych</div>
                <div><b>116</b> spółek WIG20 + mWIG40 + sWIG80</div>
                <div><b>8</b> trybów analizy</div>
                <div>Walidacja na <b>5</b> historycznych upadłościach</div>
                <div>Autor: <b>{AUTOR_IMIE}</b> — {AUTOR_ROLA}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown(
            f"""
            <div class="author-card">
                <div class="author-name">{AUTOR_IMIE}</div>
                <div class="author-role">{AUTOR_ROLA}<br>
                Projekt portfolio — analiza ryzyka kredytowego</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()
        st.header("Tryb pracy")
        tryb = st.radio(
            "Wybierz tryb analizy",
            [
                "Pojedynczy okres",
                "Wieloletni (trend)",
                "Spółka z GPW (online)",
                "Screening WIG20/mWIG40",
                "Walidacja modeli",
                "Backtest upadłości",
                "Test wrażliwości",
                "Metodologia",
            ],
            key="tryb",
        )
        st.divider()
        st.header("Modele w aplikacji")
        for nazwa, info in MODELE.items():
            with st.expander(nazwa):
                st.caption(info["opis"])
                progi = info["progi"]
                st.markdown(
                    f"**Progi:** zagrożony &lt; **{progi['zagrozony']}** "
                    f"&lt; szara &lt; **{progi['bezpieczny']}** &lt; bezpieczny",
                    unsafe_allow_html=True,
                )
        st.divider()
        st.caption(
            "Modele bazują na publikacjach: Altman (1968, 1983), Mączyńska & "
            "Zawadzki (INE PAN), Hołda (2001), Gajdka & Stos, Hamrol-Czajka-"
            "Piechocki (model poznański)."
        )

    if tryb == "Pojedynczy okres":
        widok_pojedynczy()
    elif tryb == "Wieloletni (trend)":
        widok_wieloletni()
    elif tryb == "Spółka z GPW (online)":
        widok_gpw()
    elif tryb == "Screening WIG20/mWIG40":
        widok_screening()
    elif tryb == "Walidacja modeli":
        widok_walidacja()
    elif tryb == "Backtest upadłości":
        widok_backtest()
    elif tryb == "Test wrażliwości":
        widok_wrazliwosc()
    else:
        widok_metodologia()

    st.markdown(
        f"""
        <div class="app-footer">
            <span class="footer-name">{AUTOR_IMIE}</span> &nbsp;·&nbsp;
            {AUTOR_ROLA} &nbsp;·&nbsp; Projekt portfolio © 2026<br>
            Modele zaczerpnięte z publikacji: E. Altman (1968, 1983),
            E. Mączyńska &amp; M. Zawadzki (INE PAN), A. Hołda (2001),
            J. Gajdka &amp; D. Stos, Hamrol-Czajka-Piechocki (model poznański).
            Dane spółek: Yahoo Finance / GPW.
            Aplikacja ma charakter edukacyjno-portfolio'wy i nie stanowi
            rekomendacji inwestycyjnej w rozumieniu MAR / Rozp. 2017/565.
        </div>
        """,
        unsafe_allow_html=True,
    )


def widok_pojedynczy():
    st.subheader("Dane finansowe (jeden okres)")
    st.caption("Wprowadź wartości w jednolitej walucie (najczęściej PLN tys.).")

    dane = formularz_wprowadzania("pj", st.session_state.dane_pojedyncze)
    st.session_state.dane_pojedyncze = dane

    if st.button("Oblicz wyniki", type="primary", use_container_width=False):
        st.session_state.wyniki_pojedyncze = policz_wszystkie_modele(dane)

    wyniki = st.session_state.get("wyniki_pojedyncze")
    if not wyniki:
        wyniki = policz_wszystkie_modele(dane)

    st.divider()
    st.subheader("Wyniki modeli")

    cols = st.columns(2)
    for i, (nazwa, info) in enumerate(wyniki.items()):
        with cols[i % 2]:
            karta_wyniku(nazwa, info)

    st.divider()
    st.subheader("Porównanie modeli")
    st.plotly_chart(wykres_porownawczy(wyniki), use_container_width=True)

    licz_zagrozonych = sum(
        1 for info in wyniki.values()
        if info["wynik"] is not None and "Zagrożony" in info["interpretacja"]
    )
    licz_obliczonych = sum(1 for info in wyniki.values() if info["wynik"] is not None)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Modeli obliczonych", licz_obliczonych)
    col_b.metric("Sygnały zagrożenia", licz_zagrozonych)
    col_c.metric(
        "Konsensus",
        "Zagrożenie" if licz_zagrozonych > licz_obliczonych / 2 else "Brak zagrożenia",
    )

    with st.expander("Szczegółowe wskaźniki pośrednie (X1, X2, ...)"):
        panel_wskaznikow(wyniki)

    # ----- Eksport PDF + Snapshot sesji -----
    st.divider()
    przycisk_pdf(
        nazwa_pliku=f"raport_pojedynczy_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        tytul="Raport analizy ryzyka upadłości",
        podtytul=f"Tryb: pojedynczy okres · Wygenerowano {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        dane=dane,
        wyniki=wyniki,
        kontekst={"Tryb": "Pojedynczy okres", "Liczba modeli": str(len(MODELE))},
        klucz="pdf_pojedynczy",
    )
    przycisk_snapshot(
        dane=dane,
        wyniki=wyniki,
        tryb="Pojedynczy okres",
        klucz="snap_pojedynczy",
        kontekst={"Liczba modeli": len(MODELE)},
    )


def widok_wieloletni():
    st.subheader("Dane finansowe — wiele okresów")
    st.caption(
        "Dodaj dane dla kolejnych lat aby zobaczyć trend kondycji "
        "finansowej w czasie."
    )

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.write(f"**Aktualne lata w analizie:** {sorted(st.session_state.lata_dane.keys())}")
    with col2:
        nowy_rok = st.number_input(
            "Dodaj rok",
            min_value=1990,
            max_value=2100,
            value=max(st.session_state.lata_dane.keys()) + 1
            if st.session_state.lata_dane else 2025,
            step=1,
        )
    with col3:
        if st.button("Dodaj rok", use_container_width=True):
            if nowy_rok not in st.session_state.lata_dane:
                st.session_state.lata_dane[nowy_rok] = _puste_dane()
                st.rerun()

    if not st.session_state.lata_dane:
        st.info("Dodaj przynajmniej jeden rok aby rozpocząć analizę.")
        return

    lata_posortowane = sorted(st.session_state.lata_dane.keys())
    zakladki = st.tabs([str(rok) for rok in lata_posortowane])

    for tab, rok in zip(zakladki, lata_posortowane):
        with tab:
            col_h1, col_h2 = st.columns([4, 1])
            with col_h2:
                if st.button(f"Usuń rok {rok}", key=f"del_{rok}"):
                    del st.session_state.lata_dane[rok]
                    st.rerun()

            dane_roczne = formularz_wprowadzania(
                f"y{rok}", st.session_state.lata_dane[rok]
            )
            st.session_state.lata_dane[rok] = dane_roczne

    st.divider()
    historia = {
        rok: policz_wszystkie_modele(dane)
        for rok, dane in st.session_state.lata_dane.items()
    }

    st.subheader("Trend kondycji finansowej")
    st.plotly_chart(wykres_trendu(historia), use_container_width=True)

    st.subheader("Tabela wyników")
    tabela_rows = []
    for rok in sorted(historia.keys()):
        wiersz = {"Rok": rok}
        for nazwa_modelu in MODELE.keys():
            wynik = historia[rok][nazwa_modelu]["wynik"]
            interp = historia[rok][nazwa_modelu]["interpretacja"]
            wiersz[nazwa_modelu] = (
                f"{wynik} ({interp})" if wynik is not None else "—"
            )
        tabela_rows.append(wiersz)
    st.dataframe(pd.DataFrame(tabela_rows), use_container_width=True, hide_index=True)


@st.cache_data(show_spinner=False, ttl=3600)
def _cached_pobierz(ticker: str, max_lat: int):
    return pobierz_spolke(ticker, max_lat=max_lat)


_ETYKIETY_POL = {k: e for k, e, _ in POLA_FINANSOWE}


def panel_walidacji(rok: int, walidacja: list) -> None:
    """Sekcja 'Kontrola jakości danych' z tickerami ✓/⚠/❌."""
    ok, warn, err = podsumowanie_walidacji(walidacja)

    if err > 0:
        kolor_naglowka = "#dc2626"
        ikona = "❌"
        status = f"{err} błąd(ów) krytycznych"
    elif warn > 0:
        kolor_naglowka = "#f59e0b"
        ikona = "⚠️"
        status = f"{warn} ostrzeżenie(ń)"
    else:
        kolor_naglowka = "#16a34a"
        ikona = "✅"
        status = "Wszystkie kontrole zaliczone"

    st.markdown(
        f"<h4 style='margin-top:18px;'>{ikona} Kontrola jakości danych "
        f"({rok}) — <span style='color:{kolor_naglowka};'>{status}</span></h4>",
        unsafe_allow_html=True,
    )

    rows = []
    for t in walidacja:
        if t["status"] == "ok":
            ikona_t = "✅"
        elif t["status"] == "err":
            ikona_t = "❌"
        else:
            ikona_t = "⚠️"
        rows.append({
            "": ikona_t,
            "Test": t["test"],
            "Wynik": t["wiadomosc"],
            "Szczegóły": t.get("szczegol", ""),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def panel_audit_trail(pobrane: dict, lata: list) -> None:
    """Sekcja 'Audyt mapowania' — pokazuje skąd pochodzi każda wartość."""
    with st.expander(
        "🔍 Audyt mapowania — z której pozycji Yahoo pochodzi każda liczba",
        expanded=False,
    ):
        st.caption(
            "Każda wartość wprowadzona do modeli pochodzi z konkretnego "
            "wiersza sprawozdania finansowego. Poniżej widzisz precyzyjne "
            "mapowanie. Adnotacja **WYLICZONE** oznacza, że dana pozycja "
            "nie była dostępna bezpośrednio i została wyprowadzona ze wzoru."
        )

        zakladki = st.tabs([str(r) for r in lata])
        for tab, rok in zip(zakladki, lata):
            with tab:
                dane = pobrane["lata"][rok]["dane"]
                zrodla = pobrane["lata"][rok]["zrodla"]
                rows = []
                for klucz, etykieta, _ in POLA_FINANSOWE:
                    rows.append({
                        "Pole modelu": etykieta,
                        "Wartość (tys.)": f"{dane.get(klucz, 0):,.2f}",
                        "Źródło Yahoo Finance": zrodla.get(klucz, "—"),
                    })
                st.dataframe(
                    pd.DataFrame(rows),
                    use_container_width=True,
                    hide_index=True,
                )


def panel_linki(linki: dict) -> None:
    """Sekcja 'Linki weryfikacyjne' — porównaj dane z innymi źródłami."""
    if not linki:
        return
    with st.expander(
        "🔗 Linki do źródeł — zweryfikuj dane w innych serwisach",
        expanded=False,
    ):
        st.caption(
            "Aplikacja korzysta z Yahoo Finance. Poniższe linki pozwalają "
            "porównać te same dane w innych polskich i międzynarodowych "
            "serwisach finansowych oraz w komunikatach giełdowych ESPI/EBI."
        )
        cols = st.columns(2)
        for i, (etyk, url) in enumerate(linki.items()):
            with cols[i % 2]:
                st.markdown(f"- [{etyk}]({url})")


def widok_gpw():
    st.subheader("Analiza spółki notowanej na GPW")
    st.caption(
        "Pobiera roczne sprawozdania finansowe z Yahoo Finance i automatycznie "
        "uruchamia analizę dyskryminacyjną dla ostatnich kilku lat. "
        "Dane mogą odbiegać od raportów ESPI/ESEF — przed użyciem profesjonalnym "
        "zweryfikuj wartości z oryginalnymi sprawozdaniami emitenta."
    )

    spolki = lista_spolek()
    etykiety = [f"{nazwa} ({ticker}) — {indeks}" for ticker, nazwa, indeks in spolki]
    mapa = {etyk: spolki[i][0] for i, etyk in enumerate(etykiety)}

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        wybor = st.selectbox(
            "Spółka",
            etykiety,
            index=etykiety.index(next(e for e in etykiety if "Orlen" in e)),
            help="WIG20 + mWIG40 + sWIG80 — łącznie 116 spółek",
        )
    with col2:
        max_lat = st.number_input(
            "Liczba lat", min_value=2, max_value=4, value=4, step=1
        )
    with col3:
        st.write("")
        st.write("")
        pobierz_btn = st.button(
            "Pobierz i analizuj", type="primary", use_container_width=True
        )

    if pobierz_btn:
        ticker = mapa[wybor]
        with st.spinner(f"Pobieram dane dla {ticker}..."):
            st.session_state.gpw_pobrane = _cached_pobierz(ticker, int(max_lat))
        # Reset edytowanych wartości i widżetów formularza, gdy zmienia się
        # spółka — bez tego wpisy z poprzedniej spółki dla tego samego roku
        # (np. „2024”) nadpisywałyby świeżo pobrane dane (klucze widżetów
        # `gpw_<rok>_<pole>` przeżywają rerun).
        if st.session_state.gpw_aktywny_ticker != ticker:
            st.session_state.gpw_lata_dane = {}
            for klucz in list(st.session_state.keys()):
                if klucz.startswith("gpw_") and "_" in klucz[4:]:
                    fragment = klucz[4:].split("_", 1)[0]
                    if fragment.isdigit():
                        del st.session_state[klucz]
            st.session_state.gpw_aktywny_ticker = ticker

    pobrane = st.session_state.gpw_pobrane
    if not pobrane:
        st.info("Wybierz spółkę i kliknij **Pobierz i analizuj**.")
        return

    if pobrane.get("blad"):
        st.error(pobrane["blad"])
        return

    st.divider()

    info_col1, info_col2, info_col3, info_col4 = st.columns(4)
    info_col1.metric("Spółka", pobrane["nazwa"] or pobrane["ticker"])
    info_col2.metric("Sektor", pobrane.get("sektor") or "—")
    info_col3.metric("Branża", pobrane.get("branza") or "—")
    if pobrane.get("kapitalizacja"):
        kap_mld = pobrane["kapitalizacja"] / 1e9
        info_col4.metric("Kapitalizacja", f"{kap_mld:.2f} mld {pobrane.get('waluta') or ''}")
    else:
        info_col4.metric("Kapitalizacja", "—")

    if pobrane.get("ostrzezenie"):
        st.warning(
            f"⚠️ **Uwaga metodologiczna:** {pobrane['ostrzezenie']}",
            icon="⚠️",
        )

    lata = sorted(pobrane["lata"].keys(), reverse=True)
    if not lata:
        st.error("Brak danych rocznych do analizy.")
        return

    najnowszy_rok = max(lata)

    st.caption(
        f"Pobrane lata sprawozdawcze: {', '.join(str(r) for r in sorted(lata))}. "
        f"Wszystkie wartości w **tysiącach {pobrane.get('waluta') or 'PLN'}**. "
        "Dla najświeższego okresu w polu „kapitał własny” użyto wartości "
        "rynkowej (kapitalizacji) — zgodnie z definicją X4 modelu Altmana 1968."
    )

    # ----- Sekcja: Kontrola jakości danych (B) -----
    walidacja_najnowsza = pobrane["lata"][najnowszy_rok]["walidacja"]
    panel_walidacji(najnowszy_rok, walidacja_najnowsza)

    # ----- Sekcja: Audit trail (A) -----
    panel_audit_trail(pobrane, lata)

    # ----- Sekcja: Linki źródłowe (C) -----
    panel_linki(pobrane.get("linki", {}))

    with st.expander("Pobrane dane finansowe — możesz je edytować", expanded=False):
        st.caption(
            "Edycje są lokalne — wpłyną na obliczenia poniżej, ale nie nadpiszą "
            "danych w cache."
        )
        zakladki = st.tabs([str(r) for r in lata])
        for tab, rok in zip(zakladki, lata):
            with tab:
                bazowe = pobrane["lata"][rok]["dane"]
                if rok not in st.session_state.gpw_lata_dane:
                    aktualne = bazowe
                else:
                    aktualne = st.session_state.gpw_lata_dane[rok]
                edytowane = formularz_wprowadzania(f"gpw_{rok}", aktualne)
                st.session_state.gpw_lata_dane[rok] = edytowane

    # Wyniki dla każdego roku — scalamy oryginalne dane z Yahoo z ewentualnymi
    # edycjami użytkownika. Scalanie (a nie zastąpienie) gwarantuje, że klucze
    # spoza POLA_FINANSOWE (kapital_wlasny_rynkowy, zobowiazania_dlugoterm itp.)
    # nie przepadają — bez tego Altman 1968 X4 traciłby market cap i używał
    # wartości księgowej zamiast rynkowej, dając wynik inny niż Screening.
    historia = {}
    for rok in lata:
        bazowe = pobrane["lata"][rok]["dane"]
        edycje = st.session_state.gpw_lata_dane.get(rok) or {}
        dane = {**bazowe, **edycje}
        historia[rok] = policz_wszystkie_modele(dane)

    wyniki_najnowsze = historia[najnowszy_rok]

    st.divider()
    st.subheader(f"Wyniki dla najnowszego okresu ({najnowszy_rok})")

    cols = st.columns(2)
    for i, (nazwa, info) in enumerate(wyniki_najnowsze.items()):
        with cols[i % 2]:
            karta_wyniku(nazwa, info)

    licz_zagrozonych = sum(
        1 for info in wyniki_najnowsze.values()
        if info["wynik"] is not None and "Zagrożony" in info["interpretacja"]
    )
    licz_obliczonych = sum(
        1 for info in wyniki_najnowsze.values() if info["wynik"] is not None
    )
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Modeli obliczonych", licz_obliczonych)
    col_b.metric("Sygnały zagrożenia", licz_zagrozonych)
    col_c.metric(
        "Konsensus",
        "Zagrożenie" if licz_zagrozonych > licz_obliczonych / 2 else "Brak zagrożenia",
    )

    st.divider()
    st.subheader("Trend kondycji finansowej w czasie")
    st.plotly_chart(wykres_trendu(historia), use_container_width=True)

    st.subheader("Tabela wyników po latach")
    tabela_rows = []
    for rok in sorted(historia.keys()):
        wiersz = {"Rok": rok}
        for nazwa_modelu in MODELE.keys():
            wynik = historia[rok][nazwa_modelu]["wynik"]
            interp = historia[rok][nazwa_modelu]["interpretacja"]
            wiersz[nazwa_modelu] = (
                f"{wynik} ({interp})" if wynik is not None else "—"
            )
        tabela_rows.append(wiersz)
    st.dataframe(pd.DataFrame(tabela_rows), use_container_width=True, hide_index=True)

    with st.expander("Szczegółowe wskaźniki pośrednie (najnowszy rok)"):
        panel_wskaznikow(wyniki_najnowsze)

    st.caption(
        "Źródło danych: Yahoo Finance (yfinance). Dla zastosowań produkcyjnych "
        "zalecana weryfikacja z raportami rocznymi spółki publikowanymi w ESPI/ESEF."
    )

    # ----- Eksport PDF + Snapshot sesji -----
    st.divider()
    _dane_naj = {
        **pobrane["lata"][najnowszy_rok]["dane"],
        **(st.session_state.gpw_lata_dane.get(najnowszy_rok) or {}),
    }
    przycisk_snapshot(
        dane=_dane_naj,
        wyniki=wyniki_najnowsze,
        tryb="Spółka z GPW",
        klucz=f"snap_gpw_{pobrane['ticker']}_{najnowszy_rok}",
        kontekst={
            "ticker": pobrane["ticker"],
            "nazwa": pobrane["nazwa"],
            "rok_sprawozdawczy": najnowszy_rok,
            "sektor": pobrane.get("sektor"),
            "branza": pobrane.get("branza"),
            "kapitalizacja": pobrane.get("kapitalizacja"),
            "zrodlo": "Yahoo Finance (yfinance)",
        },
    )
    przycisk_pdf(
        nazwa_pliku=f"raport_{pobrane['ticker']}_{najnowszy_rok}.pdf",
        tytul=f"{pobrane['nazwa']} — Analiza ryzyka upadłości",
        podtytul=(
            f"Najnowszy okres sprawozdawczy: {najnowszy_rok} · "
            f"Wygenerowano {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ),
        dane=_dane_naj,
        wyniki=wyniki_najnowsze,
        kontekst={
            "Spółka": pobrane["nazwa"],
            "Ticker": pobrane["ticker"],
            "Sektor": pobrane.get("sektor") or "—",
            "Branża": pobrane.get("branza") or "—",
            "Kapitalizacja": (
                f"{(pobrane['kapitalizacja'] or 0)/1e9:.2f} mld "
                f"{pobrane.get('waluta') or ''}"
                if pobrane.get("kapitalizacja") else "—"
            ),
            "Źródło": "Yahoo Finance (yfinance)",
        },
        klucz=f"pdf_gpw_{pobrane['ticker']}",
    )


def widok_wrazliwosc():
    """Test wrażliwości — interaktywne slidery pokazujące jak Z-score
    reaguje na zmiany kluczowych pozycji sprawozdania finansowego."""
    st.subheader("Test wrażliwości — analiza scenariuszowa")
    st.caption(
        "Standardowe narzędzie analityka kredytowego: o ile spadnie/wzrośnie "
        "Z-score gdy pojedyncza pozycja sprawozdania zmieni się o ±X%? "
        "Pomaga zidentyfikować, który składnik bilansu jest „najbardziej "
        "krytyczny” dla wskaźnika zagrożenia upadłością danej spółki."
    )

    # Wybór scenariusza bazowego
    col1, col2 = st.columns([2, 1])
    with col1:
        zrodlo = st.selectbox(
            "Scenariusz bazowy",
            [
                "Dane z trybu „Pojedynczy okres”",
                "Najnowszy rok z trybu „Spółka z GPW”",
                "Wartości przykładowe",
            ],
            help="Z którego zestawu danych wziąć punkt wyjścia.",
        )
    with col2:
        zakres = st.slider(
            "Zakres zmian (±%)",
            min_value=10, max_value=50, value=20, step=5,
            help="Maksymalna amplituda suwaków poniżej.",
        )

    if zrodlo == "Dane z trybu „Pojedynczy okres”":
        bazowe = dict(st.session_state.dane_pojedyncze)
    elif zrodlo == "Najnowszy rok z trybu „Spółka z GPW”":
        pobrane = st.session_state.gpw_pobrane
        if not pobrane or not pobrane.get("lata"):
            st.warning(
                "Najpierw pobierz dane spółki w trybie „Spółka z GPW (online)”."
            )
            return
        rok = max(pobrane["lata"].keys())
        bazowe = dict(pobrane["lata"][rok]["dane"])
    else:
        bazowe = {k: w for k, _, w in POLA_FINANSOWE}

    # Suwaki dla najistotniejszych pozycji
    KLUCZOWE = [
        ("przychody_sprzedazy", "Przychody"),
        ("wynik_operacyjny", "EBIT"),
        ("wynik_finansowy_netto", "Zysk netto"),
        ("aktywa_ogolem", "Aktywa"),
        ("aktywa_obrotowe", "Aktywa obrotowe"),
        ("kapital_obrotowy", "Kapitał obrotowy"),
        ("zobowiazania_ogolem", "Zobowiązania ogółem"),
        ("zobowiazania_krotkoterm", "Zob. krótkoterminowe"),
        ("kapital_wlasny", "Kapitał własny"),
    ]

    st.divider()
    st.markdown("**Suwaki — zmiana procentowa względem wartości bazowej:**")

    przesuniecia = {}
    cols = st.columns(3)
    for i, (klucz, etyk) in enumerate(KLUCZOWE):
        with cols[i % 3]:
            przesuniecia[klucz] = st.slider(
                etyk,
                min_value=-int(zakres),
                max_value=int(zakres),
                value=0,
                step=1,
                format="%+d%%",
                key=f"sens_{klucz}",
            )

    # Symulowane dane
    symulowane = dict(bazowe)
    for klucz, pct in przesuniecia.items():
        symulowane[klucz] = bazowe.get(klucz, 0) * (1 + pct / 100.0)

    # Przelicz
    wyniki_bazowe = policz_wszystkie_modele(bazowe)
    wyniki_sym = policz_wszystkie_modele(symulowane)

    st.divider()
    st.subheader("Reakcja modeli na zmianę")

    # Tabela porównawcza wyników
    rows = []
    for nazwa in MODELE.keys():
        z0 = wyniki_bazowe[nazwa]["wynik"]
        z1 = wyniki_sym[nazwa]["wynik"]
        if z0 is None or z1 is None:
            delta = None
            delta_str = "—"
            stan_baz = wyniki_bazowe[nazwa]["interpretacja"]
            stan_sym = wyniki_sym[nazwa]["interpretacja"]
        else:
            delta = z1 - z0
            delta_str = f"{delta:+.4f}"
            stan_baz = wyniki_bazowe[nazwa]["interpretacja"]
            stan_sym = wyniki_sym[nazwa]["interpretacja"]
        zmiana_klasy = "🔴 ZMIANA" if stan_baz != stan_sym else "—"
        rows.append({
            "Model": nazwa,
            "Z bazowe": "—" if z0 is None else f"{z0:.4f}",
            "Z scenariusz": "—" if z1 is None else f"{z1:.4f}",
            "Δ": delta_str,
            "Klasyfikacja bazowa": stan_baz,
            "Klasyfikacja scenariusz": stan_sym,
            "Migracja": zmiana_klasy,
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Tornado chart — wpływ pojedynczych zmian na Altman Z' (model PL)
    st.divider()
    st.subheader("Wykres tornado — wrażliwość Altman Z' (1983)")
    st.caption(
        "Każda zmienna jest indywidualnie zmieniana o ±{:d}% (przy "
        "pozostałych równych) i mierzymy wpływ na Altman Z'. "
        "Im dłuższy słupek tym większa wrażliwość modelu na daną pozycję.".format(int(zakres))
    )

    nazwy = []
    wplyw_minus = []
    wplyw_plus = []
    z_baz_altman = wyniki_bazowe["Altman Z' (1983)"]["wynik"]
    if z_baz_altman is not None:
        for klucz, etyk in KLUCZOWE:
            d_minus = dict(bazowe)
            d_minus[klucz] = bazowe.get(klucz, 0) * (1 - zakres / 100.0)
            d_plus = dict(bazowe)
            d_plus[klucz] = bazowe.get(klucz, 0) * (1 + zakres / 100.0)
            z_minus = policz_wszystkie_modele(d_minus)["Altman Z' (1983)"]["wynik"]
            z_plus = policz_wszystkie_modele(d_plus)["Altman Z' (1983)"]["wynik"]
            if z_minus is None or z_plus is None:
                continue
            nazwy.append(etyk)
            wplyw_minus.append(z_minus - z_baz_altman)
            wplyw_plus.append(z_plus - z_baz_altman)

        # Sortuj po amplitudzie
        amp = [abs(p) + abs(m) for p, m in zip(wplyw_plus, wplyw_minus)]
        sortowanie = sorted(range(len(amp)), key=lambda i: amp[i])
        nazwy = [nazwy[i] for i in sortowanie]
        wplyw_minus = [wplyw_minus[i] for i in sortowanie]
        wplyw_plus = [wplyw_plus[i] for i in sortowanie]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=nazwy, x=wplyw_minus, orientation="h",
            name=f"−{int(zakres)}%", marker_color="#dc2626",
            hovertemplate="%{y}: ΔZ = %{x:.3f}<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            y=nazwy, x=wplyw_plus, orientation="h",
            name=f"+{int(zakres)}%", marker_color="#16a34a",
            hovertemplate="%{y}: ΔZ = %{x:.3f}<extra></extra>",
        ))
        fig.update_layout(
            barmode="overlay",
            height=420,
            margin=dict(l=10, r=10, t=20, b=20),
            xaxis_title="Zmiana wartości Altman Z' względem bazy",
            yaxis_title="",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
        )
        fig.add_vline(x=0, line=dict(color="#0F2A47", width=1))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(
            "Wartość Altman Z' nie została obliczona dla danych bazowych — "
            "wykres tornado niedostępny."
        )


def przycisk_pdf(
    nazwa_pliku: str,
    tytul: str,
    podtytul: str,
    dane: dict,
    wyniki: dict,
    kontekst: dict,
    klucz: str,
) -> None:
    """Renderuje przycisk pobrania raportu PDF z bieżącej analizy.

    Generowanie raportu (kilkaset KB) odbywa się dopiero po kliknięciu —
    używamy lazy-callbacka st.download_button który wymaga gotowych
    bajtów; generujemy je na każdym renderze, ale operacja zajmuje <0.5 s.
    """
    pola_etykiety = [(klucz_, etykieta) for klucz_, etykieta, _ in POLA_FINANSOWE]
    try:
        pdf_bytes = generuj_raport(
            tytul=tytul,
            podtytul=podtytul,
            autor="Arkadiusz Oczkowski — Licencjonowany Makler PW",
            dane=dane,
            wyniki=wyniki,
            pola_etykiety=pola_etykiety,
            kontekst=kontekst,
        )
    except Exception as e:  # pragma: no cover - guard
        st.warning(f"Nie udało się wygenerować raportu PDF: {e}")
        return

    col_pdf, col_info = st.columns([1, 3])
    with col_pdf:
        st.download_button(
            label="📄 Pobierz raport PDF",
            data=pdf_bytes,
            file_name=nazwa_pliku,
            mime="application/pdf",
            key=klucz,
            use_container_width=True,
        )
    with col_info:
        st.caption(
            "Raport zawiera dane wejściowe, wyniki wszystkich modeli, "
            "interpretacje i obowiązkowe zastrzeżenia (MAR/edukacyjny "
            "charakter analizy). Format A4, czcionka DejaVu Sans z pełną "
            "obsługą polskich znaków."
        )


def przycisk_snapshot(
    dane: dict,
    wyniki: dict,
    tryb: str,
    klucz: str,
    kontekst: dict | None = None,
) -> None:
    """Przycisk pobrania snapshotu sesji w formacie JSON.

    Snapshot zawiera dane wejściowe, wyniki, hash SHA-256 i wersje modeli —
    pozwala odtworzyć analizę 1:1 za miesiąc/rok (audyt due diligence)."""
    snap = zbuduj_snapshot(
        dane=dane,
        wyniki=wyniki,
        tryb=tryb,
        autor=f"{AUTOR_IMIE} — {AUTOR_ROLA}",
        kontekst=kontekst or {},
    )
    bajty = snapshot_jako_bytes(snap)
    nazwa_pliku = (
        f"snapshot_{tryb.replace(' ', '_').lower()}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    )

    col_a, col_b = st.columns([1, 3])
    with col_a:
        st.download_button(
            label="💾 Pobierz snapshot sesji (JSON)",
            data=bajty,
            file_name=nazwa_pliku,
            mime="application/json",
            key=klucz,
            use_container_width=True,
        )
    with col_b:
        st.caption(
            f"Snapshot zawiera dane wejściowe + wyniki + **hash SHA-256** "
            f"`{snap['hash_danych_sha256'][:16]}…` + wersje modeli "
            f"({len(snap['wersje_modeli'])} szt.). Format JSON v"
            f"{snap['wersja_formatu_snapshotu']}, app v{snap['wersja_aplikacji']}. "
            "Pozwala odtworzyć analizę 1:1 (reprodukowalność dla DM/TFI/audytu)."
        )


def widok_screening():
    """Masowy screening WIG20 / mWIG40 — ranking ryzyka spółek z GPW."""
    st.subheader("Screening — ranking ryzyka spółek z GPW")
    st.caption(
        "Jednym kliknięciem oblicza wszystkie modele dyskryminacyjne dla "
        "wybranego uniwersum i tworzy ranking konsensusu sygnałów zagrożenia. "
        "Spółki finansowe (banki, ubezpieczyciele) są oznaczane jako "
        "**Sektor wykluczony** — modele dyskryminacyjne nie są dla nich właściwe."
    )

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        uniwersum = st.selectbox(
            "Uniwersum",
            [
                "WIG20",
                "mWIG40",
                "sWIG80",
                "WIG20 + mWIG40",
                "WIG20 + mWIG40 + sWIG80",
            ],
            index=0,
            help="WIG20 = 20 spółek (najszybsze, ~30 s). "
                 "mWIG40 = 40 spółek (~1 min). "
                 "sWIG80 = 57 spółek z dostępnymi sprawozdaniami (~1.5 min). "
                 "Pełne uniwersum = 116 spółek (~3 min przy pierwszym "
                 "uruchomieniu, kolejne natychmiastowe dzięki cache).",
        )
    with col2:
        st.write("")
        st.write("")
        skanuj_btn = st.button(
            "🔍 Uruchom screening", type="primary", use_container_width=True
        )
    with col3:
        st.write("")
        st.write("")
        if st.button("Wyczyść wyniki", use_container_width=True):
            st.session_state.screening_wyniki = None
            st.rerun()

    if skanuj_btn:
        tickery = filtruj_uniwersum(uniwersum)
        progress_bar = st.progress(0.0)
        status_txt = st.empty()

        def _cb(idx: int, total: int, ticker: str):
            progress_bar.progress(idx / total)
            status_txt.caption(f"Pobieram {idx}/{total}: **{ticker}**")

        wyniki = skanuj_spolki(
            tickery,
            pobierz_func=_cached_pobierz,
            progress_callback=_cb,
            max_lat=1,
        )
        progress_bar.empty()
        status_txt.empty()
        st.session_state.screening_wyniki = {
            "uniwersum": uniwersum,
            "wyniki": wyniki,
            "wygenerowano": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

    if not st.session_state.get("screening_wyniki"):
        st.info(
            "Wybierz uniwersum i kliknij **Uruchom screening**. "
            "Pierwsze pobranie 20 spółek WIG20 zajmuje ok. 30–60 sekund "
            "(dane są cache'owane, kolejne uruchomienia są natychmiastowe)."
        )
        return

    paczka = st.session_state.screening_wyniki
    st.caption(
        f"Uniwersum: **{paczka['uniwersum']}** · "
        f"Wygenerowano: **{paczka['wygenerowano']}** · "
        f"Spółek: **{len(paczka['wyniki'])}**"
    )

    # Statystyki
    konsens_count = {}
    for w in paczka["wyniki"]:
        konsens_count[w["konsensus"]] = konsens_count.get(w["konsensus"], 0) + 1
    cols = st.columns(5)
    cols[0].metric("✅ Bezpieczne", konsens_count.get("BEZPIECZNY", 0))
    cols[1].metric("⚠️ Neutralne", konsens_count.get("NEUTRALNY", 0))
    cols[2].metric("🔴 Zagrożenie", konsens_count.get("ZAGROŻENIE", 0))
    cols[3].metric("🚫 Wykluczone", konsens_count.get("SEKTOR WYKLUCZONY", 0))
    cols[4].metric("❓ Brak danych", konsens_count.get("BRAK DANYCH", 0))

    st.divider()

    # Ranking
    st.markdown("#### Ranking ryzyka — sortowanie po liczbie sygnałów zagrożenia")

    rows = []
    for w in paczka["wyniki"]:
        ikona = {
            "ZAGROŻENIE": "🔴", "NEUTRALNY": "⚠️", "BEZPIECZNY": "🟢",
            "SEKTOR WYKLUCZONY": "🚫", "BRAK DANYCH": "❓",
        }[w["konsensus"]]
        wiersz = {
            "": ikona,
            "Spółka": w["nazwa"],
            "Ticker": w["ticker"],
            "Sektor": (w["sektor"] or "—")[:25],
            "Rok": w["rok"] or "—",
            "Sygnały": (
                f"{w['sygnaly_zagrozenia']}/{w['modele_obliczone']}"
                if w["modele_obliczone"] else "—"
            ),
            "Konsensus": w["konsensus"],
        }
        # Skrócone wartości per model
        for nazwa_m in MODELE.keys():
            v = w["wyniki_per_model"].get(nazwa_m)
            zagr = w["zagrozenia_per_model"].get(nazwa_m)
            if v is None:
                wiersz[nazwa_m.split(" (")[0][:12]] = "—"
            else:
                marker = "🔴 " if zagr else ""
                wiersz[nazwa_m.split(" (")[0][:12]] = f"{marker}{v:.2f}"
        rows.append(wiersz)

    df = pd.DataFrame(rows)
    # Sortuj: najpierw zagrożenia, potem neutralne, potem bezpieczne
    porzadek = {
        "ZAGROŻENIE": 0, "NEUTRALNY": 1, "BEZPIECZNY": 2,
        "SEKTOR WYKLUCZONY": 3, "BRAK DANYCH": 4,
    }
    df["_sort"] = df["Konsensus"].map(porzadek)
    df["_zagr"] = -df["Sygnały"].map(
        lambda s: int(s.split("/")[0]) if s != "—" else -1
    )
    df = df.sort_values(by=["_sort", "_zagr"], kind="stable").drop(
        columns=["_sort", "_zagr"]
    )

    st.dataframe(df, use_container_width=True, hide_index=True, height=600)

    # CSV export
    st.divider()
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    col_csv, col_info = st.columns([1, 3])
    with col_csv:
        st.download_button(
            label="📊 Pobierz ranking (CSV)",
            data=csv_bytes,
            file_name=f"screening_{paczka['uniwersum'].replace(' + ', '_')}_"
                      f"{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_info:
        st.caption(
            "CSV nadaje się do dalszej analizy w Excelu / wklejenia do "
            "raportu klienta. Zawiera wartości każdego modelu i konsensus."
        )

    # Błędy / brak danych
    bledne = [w for w in paczka["wyniki"] if w.get("blad")]
    if bledne:
        with st.expander(f"❓ Spółki z błędem pobrania ({len(bledne)})"):
            for w in bledne:
                st.write(f"- **{w['nazwa']}** (`{w['ticker']}`): {w['blad']}")


def widok_walidacja():
    """Walidacja statystyczna — ROC/AUC, macierz pomyłek, błędy I/II."""
    st.subheader("Walidacja statystyczna modeli")
    st.caption(
        "Empiryczna ocena skuteczności predykcyjnej każdego modelu na próbie "
        "polskich upadłości giełdowych (PBG, GetBack, Petrolinvest, Hawe, "
        "ZM Henryk Kania) zestawionej ze zdrowymi spółkami referencyjnymi "
        "(Dino, KGHM, LPP, CD Projekt, Inter Cars, Kęty, Budimex, Asseco)."
    )

    obs = zbierz_obserwacje()
    n_pos = sum(1 for o in obs if o["label"] == 1)
    n_neg = sum(1 for o in obs if o["label"] == 0)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Próba pozytywna (upadłe)", n_pos)
    col2.metric("Próba negatywna (zdrowe)", n_neg)
    col3.metric("Łącznie obserwacji", n_pos + n_neg)
    col4.metric("Modele oceniane", len(MODELE))

    st.warning(
        "**Ograniczenia metodologiczne.** Próba jest niewielka "
        f"(15 obserwacji upadłych × {n_neg} zdrowych) — wyniki traktować "
        "jako orientacyjne. Pełna walidacja wymagałaby setek obserwacji "
        "per klasa, stratyfikacji sektorowej i podziału train/test. "
        "Zdrowe spółki to lata, w których emitenci NIE złożyli wniosku "
        "o upadłość/restrukturyzację w ciągu 3 lat po."
    )

    metryki = metryki_wszystkich_modeli(obs)

    # ----- Tabela zbiorcza -----
    st.divider()
    st.markdown("#### Tabela skuteczności per model")

    rows = []
    for nazwa, m in metryki.items():
        def _fmt_pct(v):
            return f"{v*100:.1f}%" if v is not None else "—"

        def _fmt_auc(v):
            return f"{v:.3f}" if v is not None else "—"

        rows.append({
            "Model": nazwa,
            "AUC": _fmt_auc(m["auc"]),
            "Czułość (recall)": _fmt_pct(m["czulosc"]),
            "Specyficzność": _fmt_pct(m["specyficznosc"]),
            "Trafność": _fmt_pct(m["trafnosc"]),
            "Błąd typu I": _fmt_pct(m["blad_typu_I"]),
            "Błąd typu II": _fmt_pct(m["blad_typu_II"]),
            "TP": m["tp"], "FN": m["fn"], "FP": m["fp"], "TN": m["tn"],
            "Brak": m["n_brak"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.caption(
        "**Czułość** = % wykrytych upadłości · "
        "**Specyficzność** = % poprawnie zaklasyfikowanych zdrowych · "
        "**Błąd typu I** = fałszywy alarm (FP/N) · "
        "**Błąd typu II** = przeoczona upadłość (FN/P) — najgroźniejszy dla DM/TFI. "
        "**AUC** = pole pod krzywą ROC, 1.0 = klasyfikator idealny, 0.5 = losowy."
    )

    # ----- Krzywe ROC -----
    st.divider()
    st.markdown("#### Krzywe ROC — porównanie modeli")
    st.caption(
        "Im bliżej lewego górnego rogu, tym lepszy klasyfikator. "
        "Linia diagonalna = klasyfikator losowy (AUC = 0.5)."
    )

    fig_roc = go.Figure()
    for nazwa, m in metryki.items():
        if m["auc"] is None:
            continue
        fig_roc.add_trace(
            go.Scatter(
                x=m["roc_fpr"], y=m["roc_tpr"],
                mode="lines",
                name=f"{nazwa} (AUC={m['auc']:.3f})",
                line=dict(width=2.2),
                hovertemplate=(
                    f"<b>{nazwa}</b><br>"
                    "FPR: %{x:.3f}<br>TPR: %{y:.3f}<extra></extra>"
                ),
            )
        )
    fig_roc.add_trace(
        go.Scatter(
            x=[0, 1], y=[0, 1],
            mode="lines",
            name="Klasyfikator losowy",
            line=dict(color="#9ca3af", width=1, dash="dot"),
            hoverinfo="skip",
        )
    )
    fig_roc.update_layout(
        height=520,
        xaxis_title="False Positive Rate (1 − specyficzność)",
        yaxis_title="True Positive Rate (czułość)",
        legend=dict(orientation="v", yanchor="bottom", y=0.0, x=0.55, bgcolor="rgba(255,255,255,0.85)"),
        margin=dict(l=10, r=10, t=20, b=10),
        hovermode="closest",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        xaxis=dict(range=[-0.02, 1.02], gridcolor="#E5E7EB"),
        yaxis=dict(range=[-0.02, 1.02], gridcolor="#E5E7EB", scaleanchor="x", scaleratio=1),
    )
    st.plotly_chart(fig_roc, use_container_width=True)

    # ----- Ranking AUC -----
    st.divider()
    st.markdown("#### Ranking modeli wg AUC")
    ranking = ranking_po_metryce(metryki, "auc")
    if ranking:
        nazwy = [r[0] for r in ranking]
        wartosci = [r[1] for r in ranking]
        kolory = [
            "#16a34a" if v >= 0.9 else "#C9A227" if v >= 0.7 else "#dc2626"
            for v in wartosci
        ]
        fig_rank = go.Figure(go.Bar(
            x=wartosci, y=nazwy, orientation="h",
            marker_color=kolory,
            text=[f"{v:.3f}" for v in wartosci],
            textposition="outside",
            hovertemplate="%{y}: AUC = %{x:.3f}<extra></extra>",
        ))
        fig_rank.add_vline(x=0.5, line_dash="dot", line_color="#6b7280",
                           annotation_text="Klasyfikator losowy")
        fig_rank.add_vline(x=0.9, line_dash="dot", line_color="#16a34a",
                           annotation_text="Bardzo dobry (≥0.9)")
        fig_rank.update_layout(
            height=380,
            xaxis_title="AUC",
            yaxis_title="",
            margin=dict(l=10, r=10, t=20, b=10),
            xaxis=dict(range=[0, 1.1]),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
        )
        st.plotly_chart(fig_rank, use_container_width=True)

    # ----- Macierze pomyłek per model -----
    st.divider()
    with st.expander("📊 Macierze pomyłek per model", expanded=False):
        st.caption(
            "TP = trafnie wykryta upadłość · FN = przeoczona upadłość · "
            "FP = fałszywy alarm · TN = trafnie wskazana zdrowa spółka."
        )
        for nazwa, m in metryki.items():
            st.markdown(f"**{nazwa}**")
            macierz = pd.DataFrame(
                [
                    [m["tp"], m["fn"]],
                    [m["fp"], m["tn"]],
                ],
                index=["Faktycznie UPADŁA (P)", "Faktycznie ZDROWA (N)"],
                columns=["Predykcja: zagrożenie", "Predykcja: bezpieczna"],
            )
            st.dataframe(macierz, use_container_width=False)

    # ----- Wnioski -----
    st.divider()
    st.markdown("#### Wnioski analityczne")
    if ranking:
        najlepszy_nazwa, najlepszy_auc = ranking[0]
        najgorszy_nazwa, najgorszy_auc = ranking[-1]
        st.markdown(
            f"- **Najlepszy klasyfikator (AUC):** {najlepszy_nazwa} "
            f"({najlepszy_auc:.3f}). Najwyższy stosunek wykrywalności do "
            "fałszywych alarmów na próbie polskich upadłości giełdowych.\n"
            f"- **Najsłabszy:** {najgorszy_nazwa} ({najgorszy_auc:.3f}) — "
            "warto skonfrontować z innymi modelami przed wnioskowaniem.\n"
            "- **Konsensus modeli** jest mocniejszą podstawą decyzji "
            "niż pojedynczy wynik (zalecenie: użyć trybu "
            "**Pojedynczy okres** lub **Spółka z GPW** które liczą "
            "wszystkie modele jednocześnie)."
        )


def widok_backtest():
    """Backtest historyczny — sprawdzenie czy modele wykryły zagrożenie
    u faktycznie upadłych spółek z GPW na 1–3 lata przed upadłością."""
    st.subheader("Backtest — historyczne upadłości na GPW")
    st.caption(
        "Sprawdź skuteczność modeli dyskryminacyjnych na realnych "
        "przypadkach upadłości polskich spółek giełdowych. Dla każdej "
        "spółki obliczamy Z-score na danych z lat t-3, t-2 i t-1 przed "
        "ogłoszeniem upadłości."
    )

    st.warning(
        "**Zastrzeżenie metodologiczne.** Dane finansowe w tym module "
        "to przybliżenia oparte na publicznie dostępnych raportach "
        "i opracowaniach prasowych. Backtest ma charakter **wyłącznie "
        "edukacyjny** — pokazuje mechanikę modeli i ich behawiorystykę "
        "na klasycznych polskich casusach (PBG, GetBack, Petrolinvest, "
        "Hawe, ZM Henryk Kania). Pełny audyt skuteczności wymagałby "
        "odtworzenia oryginalnych sprawozdań finansowych z ESPI/KRS."
    )

    spolki = lista_upadlosci()  # [(klucz, etykieta), ...]
    klucze = [k for k, _ in spolki]
    klucz = st.selectbox(
        "Wybierz spółkę",
        klucze,
        format_func=lambda k: dict(spolki)[k],
        key="backtest_spolka",
    )
    rec = UPADLOSCI[klucz]

    # Karta spółki
    col1, col2, col3 = st.columns([2, 1, 1])
    col1.markdown(f"### {rec['nazwa']}")
    col1.caption(f"Sektor: **{rec.get('sektor', '—')}** · Ticker: `{rec['ticker']}`")
    col2.metric("Data zdarzenia", rec.get("data_upadlosci", "—"))
    col3.metric("Typ zdarzenia", rec.get("typ_zdarzenia", "upadłość"))

    st.markdown(f"_{rec.get('opis', '')}_")
    st.divider()

    # Oblicz Z-score dla każdego roku (sorted ascending = t-3, t-2, t-1)
    lata_dane = dane_w_tysiacach(klucz)
    lata_sorted = sorted(lata_dane.keys())
    n_lat = len(lata_sorted)
    # Etykieta t-N gdzie N = lat-przed-upadłością
    oznaczenia_map = {
        rok: f"t-{n_lat - i}" for i, rok in enumerate(lata_sorted)
    }
    oznaczenia = [f"{rok} ({oznaczenia_map[rok]})" for rok in lata_sorted]

    lata_wyniki: dict = {}
    for rok in lata_sorted:
        pelne = {pole: 0.0 for pole, _, _ in POLA_FINANSOWE}
        pelne.update(lata_dane[rok])
        lata_wyniki[rok] = {
            "dane": pelne,
            "wyniki": policz_wszystkie_modele(pelne),
        }

    def _czy_zagrozony(interp: str) -> bool:
        s = interp.lower()
        return "zagroż" in s or "upadł" in s or "słaba" in s

    # Tabela wyników: wiersze = modele, kolumny = lata
    st.markdown(f"#### Wyniki Z-score — {n_lat} lata poprzedzające upadłość")
    rows = []
    for nazwa_modelu in MODELE.keys():
        wiersz = {"Model": nazwa_modelu}
        zagrozenia = 0
        obliczone = 0
        for rok, ozn in zip(lata_sorted, oznaczenia):
            wyn = lata_wyniki[rok]["wyniki"][nazwa_modelu]
            v = wyn["wynik"]
            interp = wyn["interpretacja"]
            if v is None:
                wiersz[ozn] = "—"
            else:
                obliczone += 1
                czy_zagr = _czy_zagrozony(interp)
                if czy_zagr:
                    zagrozenia += 1
                emoji = "🔴" if czy_zagr else "🟢"
                wiersz[ozn] = f"{emoji} {v:.2f}"
        if obliczone > 0:
            wiersz["Trafność"] = (
                f"✓ {zagrozenia}/{obliczone}"
                if zagrozenia >= max(2, obliczone // 2 + 1)
                else f"✗ {zagrozenia}/{obliczone}"
            )
        else:
            wiersz["Trafność"] = "—"
        rows.append(wiersz)

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(
        "🔴 = wartość Z w strefie zagrożenia/słabej kondycji · 🟢 = poza strefą "
        "zagrożenia · **Trafność** = liczba lat, w których model zasygnalizował "
        "ryzyko (✓ = większość lat trafnie wskazana)."
    )

    # Wykres trendu Z
    st.markdown("#### Trend wartości Z-score przed upadłością")
    fig = go.Figure()
    for nazwa_modelu in MODELE.keys():
        ys = [
            lata_wyniki[rok]["wyniki"][nazwa_modelu]["wynik"]
            for rok in lata_sorted
        ]
        if any(y is not None for y in ys):
            fig.add_trace(
                go.Scatter(
                    x=oznaczenia,
                    y=ys,
                    mode="lines+markers",
                    name=nazwa_modelu,
                    line=dict(width=2),
                    marker=dict(size=8),
                )
            )
    fig.update_layout(
        height=420,
        xaxis_title="Rok sprawozdawczy",
        yaxis_title="Wartość Z-score",
        legend=dict(orientation="h", yanchor="bottom", y=-0.35, x=0),
        margin=dict(l=10, r=10, t=10, b=10),
        hovermode="x unified",
    )
    fig.add_hline(
        y=0, line_dash="dot", line_color="#888",
        annotation_text="Z=0 (granica neutralna)",
        annotation_position="right",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Podsumowanie skuteczności
    st.divider()
    st.markdown("#### Skuteczność detekcji per model")
    skutecznosci = []
    for nazwa_modelu in MODELE.keys():
        zagr = 0
        obl = 0
        for rok in lata_sorted:
            wyn = lata_wyniki[rok]["wyniki"][nazwa_modelu]
            if wyn["wynik"] is not None:
                obl += 1
                if _czy_zagrozony(wyn["interpretacja"]):
                    zagr += 1
        if obl > 0:
            skutecznosci.append((nazwa_modelu, zagr, obl))

    if skutecznosci:
        n_cols = min(len(skutecznosci), 4)
        cols = st.columns(n_cols)
        for i, (nazwa, zagr, obl) in enumerate(skutecznosci):
            with cols[i % n_cols]:
                trafny = zagr >= max(2, obl // 2 + 1)
                st.metric(
                    nazwa.split(" — ")[0].split(" (")[0],
                    f"{zagr}/{obl} lat",
                    delta="trafna" if trafny else "słaba",
                    delta_color="normal" if trafny else "inverse",
                )

    # Lekcja
    if rec.get("lekcja"):
        st.divider()
        st.info(f"**Lekcja z casusu:** {rec['lekcja']}")

    # Źródło
    if rec.get("zrodlo"):
        st.caption(f"Źródło danych: {rec['zrodlo']}")


def widok_metodologia():
    """Strona metodologii — szczegółowy opis każdego modelu z wzorami,
    bibliografią i krytyczną oceną ograniczeń."""
    st.subheader("Metodologia — modele dyskryminacyjne predykcji upadłości")
    st.caption(
        "Pełna dokumentacja matematyczna i bibliograficzna modeli zaimplementowanych "
        "w aplikacji. Wzory zapisane w notacji LaTeX; każdy model opatrzony "
        "źródłem, próbą treningową i komentarzem metodologicznym."
    )

    st.markdown("### 1. Wprowadzenie")
    st.markdown(
        "**Analiza dyskryminacyjna** (Multiple Discriminant Analysis, MDA) "
        "to klasyczna metoda statystyczna wykorzystywana w predykcji "
        "bankructwa od pracy E. Altmana (1968). Funkcja dyskryminacyjna "
        "$Z = \\sum_{i=1}^{n} \\beta_i X_i$ jest liniową kombinacją "
        "wskaźników finansowych $X_i$, ważoną współczynnikami $\\beta_i$ "
        "oszacowanymi tak, by maksymalizować rozdział między grupą spółek "
        "zbankrutowanych a kontynuujących działalność. Wartość $Z$ "
        "porównywana jest z **progiem odcięcia (cutoff point)** — niższy "
        "$Z$ oznacza wyższe prawdopodobieństwo upadłości."
    )
    st.markdown(
        "**Ograniczenia:** modele są wrażliwe na: (1) próbę treningową — "
        "współczynniki estymowane na danych z lat 90-tych mogą tracić moc "
        "predykcyjną w odmiennym otoczeniu makroekonomicznym; (2) sektor — "
        "klasyczne modele słabo działają dla banków, ubezpieczycieli i firm "
        "inwestycyjnych; (3) standard rachunkowości — przejście z PSR na "
        "MSSF zmienia definicje pozycji bilansowych."
    )

    st.divider()

    # ----- Altman 1968 -----
    st.markdown("### 2. Altman Z-score (1968)")
    st.markdown(
        "**Autor:** Edward I. Altman (NYU Stern). "
        "**Próba:** 66 spółek przemysłowych z USA (33 zbankrutowane "
        "1946–1965 + 33 zdrowe). **Skuteczność oryginalna:** 95% na "
        "1 rok przed upadłością, 72% na 2 lata. "
        "**Zastosowanie:** spółki **notowane** na giełdzie."
    )
    st.latex(r"Z = 1{,}2\,X_1 + 1{,}4\,X_2 + 3{,}3\,X_3 + 0{,}6\,X_4 + 1{,}0\,X_5")
    st.markdown(
        "- $X_1 = \\dfrac{\\text{kapitał obrotowy}}{\\text{aktywa ogółem}}$ — płynność\n"
        "- $X_2 = \\dfrac{\\text{zysk zatrzymany}}{\\text{aktywa ogółem}}$ — historia rentowności\n"
        "- $X_3 = \\dfrac{\\text{EBIT}}{\\text{aktywa ogółem}}$ — efektywność operacyjna\n"
        "- $X_4 = \\dfrac{\\text{wartość rynkowa kap. własnego}}{\\text{zobowiązania ogółem}}$ — dźwignia (rynkowa)\n"
        "- $X_5 = \\dfrac{\\text{przychody}}{\\text{aktywa ogółem}}$ — rotacja aktywów"
    )
    st.markdown(
        "**Interpretacja:** $Z < 1{,}81$ — strefa zagrożenia · "
        "$1{,}81 \\le Z \\le 2{,}99$ — strefa szara · $Z > 2{,}99$ — bezpieczeństwo."
    )
    st.markdown(
        "**Źródło:** Altman E.I. (1968), *Financial Ratios, Discriminant "
        "Analysis and the Prediction of Corporate Bankruptcy*, "
        "Journal of Finance, Vol. 23, No. 4."
    )

    st.divider()

    # ----- Altman Z' 1983 -----
    st.markdown("### 3. Altman Z' (1983) — dla spółek nienotowanych")
    st.markdown(
        "**Autor:** E. Altman. **Modyfikacja:** $X_4$ używa wartości "
        "**księgowej** zamiast rynkowej kapitału własnego, pozostałe "
        "współczynniki przeszacowane na próbie spółek nienotowanych. "
        "**Lepiej dopasowany do polskich realiów** dla większości spółek "
        "spoza GPW."
    )
    st.latex(r"Z' = 0{,}717\,X_1 + 0{,}847\,X_2 + 3{,}107\,X_3 + 0{,}420\,X_4 + 0{,}998\,X_5")
    st.markdown(
        "**Interpretacja:** $Z' < 1{,}23$ — zagrożenie · "
        "$1{,}23 \\le Z' \\le 2{,}90$ — strefa szara · $Z' > 2{,}90$ — bezpieczeństwo."
    )
    st.markdown(
        "**Źródło:** Altman E.I. (1983), *Corporate Financial Distress*, "
        "John Wiley & Sons, New York."
    )

    st.divider()

    # ----- Mączyńska 6-wsk -----
    st.markdown("### 4. Mączyńska — model 6-wskaźnikowy (INE PAN, 1994)")
    st.markdown(
        "**Autor:** prof. Elżbieta Mączyńska (INE PAN, SGH). "
        "**Próba:** polskie spółki z lat transformacji 1990–1994. "
        "**Cel:** zaadaptować podejście Altmana do specyfiki polskiej "
        "rachunkowości (PSR) i polskiej gospodarki transformacyjnej."
    )
    st.latex(r"W = 1{,}5\,X_1 + 0{,}08\,X_2 + 10\,X_3 + 5\,X_4 + 0{,}3\,X_5 + 0{,}1\,X_6")
    st.markdown(
        "- $X_1 = \\dfrac{\\text{wynik brutto + amortyzacja}}{\\text{zobowiązania}}$\n"
        "- $X_2 = \\dfrac{\\text{aktywa}}{\\text{zobowiązania}}$\n"
        "- $X_3 = \\dfrac{\\text{wynik brutto}}{\\text{aktywa}}$\n"
        "- $X_4 = \\dfrac{\\text{wynik netto}}{\\text{przychody}}$\n"
        "- $X_5 = \\dfrac{\\text{kapitał obrotowy}}{\\text{przychody}}$\n"
        "- $X_6 = \\dfrac{\\text{przychody}}{\\text{aktywa}}$"
    )
    st.markdown(
        "**Interpretacja:** $W < 0$ zagrożenie · $0 \\le W \\le 1$ słaba · "
        "$1 < W \\le 2$ dobra · $W > 2$ bardzo dobra kondycja."
    )
    st.markdown(
        "**Źródło:** Mączyńska E. (1994), *Ocena kondycji przedsiębiorstwa. "
        "Uproszczone metody*, Życie Gospodarcze nr 38."
    )

    st.divider()

    # ----- Mączyńska Model E 2004 -----
    st.markdown("### 5. Mączyńska — Model E (2004, INE PAN)")
    st.markdown(
        "**Autorzy:** E. Mączyńska, M. Zawadzki. **Próba:** 80 polskich "
        "przedsiębiorstw (40 zbankrutowanych + 40 zdrowych) z lat 1997–2002. "
        "**Skuteczność:** ok. 92% na 1 rok przed upadłością. "
        "**Cechy:** uproszczona forma 5-zmienna, wyższe współczynniki przy "
        "$X_1$ i $X_3$ — większa waga rentowności operacyjnej i zdolności "
        "do generowania gotówki na obsługę zobowiązań."
    )
    st.latex(r"W = 9{,}478\,X_1 + 3{,}613\,X_2 + 3{,}246\,X_3 + 0{,}455\,X_4 + 0{,}802\,X_5 - 2{,}478")
    st.markdown(
        "- $X_1 = \\dfrac{\\text{EBIT}}{\\text{aktywa}}$\n"
        "- $X_2 = \\dfrac{\\text{kapitał własny}}{\\text{aktywa}}$\n"
        "- $X_3 = \\dfrac{\\text{wynik netto + amortyzacja}}{\\text{zobowiązania}}$\n"
        "- $X_4 = \\dfrac{\\text{przychody}}{\\text{aktywa}}$\n"
        "- $X_5 = \\dfrac{\\text{aktywa obrotowe}}{\\text{zob. krótkoterminowe}}$ (płynność bieżąca)"
    )
    st.markdown("**Interpretacja:** $W < 0$ zagrożenie · $W \\geq 0$ bezpieczeństwo.")
    st.markdown(
        "**Źródło:** Mączyńska E., Zawadzki M. (2006), *Dyskryminacyjne "
        "modele predykcji bankructwa przedsiębiorstw*, "
        "Ekonomista nr 2."
    )

    st.divider()

    # ----- Hołda -----
    st.markdown("### 6. Model A. Hołdy (2001)")
    st.markdown(
        "**Autor:** Artur Hołda (UEK Kraków). "
        "**Próba:** 80 polskich spółek (40 zbankrutowanych + 40 zdrowych) "
        "z lat 1993–1996. **Cecha charakterystyczna:** wzór zawiera **wyraz "
        "wolny** ($+0{,}605$) — nietypowe w modelach Altmanowskich, daje "
        "dodatni „bias” strefy bezpiecznej."
    )
    st.latex(r"Z = 0{,}605 + 0{,}681\,X_1 - 0{,}0196\,X_2 + 0{,}00969\,X_3 + 0{,}000672\,X_4 + 0{,}157\,X_5")
    st.markdown(
        "- $X_1 = $ wsk. płynności bieżącej = aktywa obrotowe / zob. krótkoterm.\n"
        "- $X_2 = $ ogólne zadłużenie (%) = zobowiązania / aktywa × 100\n"
        "- $X_3 = $ ROA (%) = wynik netto / aktywa × 100\n"
        "- $X_4 = $ rotacja zob. krótkoterm. (dni) = zob. kr. / koszty op. × 365\n"
        "- $X_5 = $ rotacja aktywów = przychody / aktywa"
    )
    st.markdown(
        "**Interpretacja:** $Z < 0$ zagrożenie · $0 \\le Z \\le 0{,}1$ "
        "strefa szara · $Z > 0{,}1$ bezpieczeństwo."
    )
    st.markdown(
        "**Źródło:** Hołda A. (2001), *Prognozowanie bankructwa "
        "jednostki w warunkach gospodarki polskiej z wykorzystaniem "
        "funkcji dyskryminacyjnej Z<sub>H</sub>*, Rachunkowość nr 5."
    )

    st.divider()

    # ----- Gajdka-Stos -----
    st.markdown("### 7. Model J. Gajdki i S. Stosa")
    st.markdown(
        "**Autorzy:** J. Gajdka, D. Stos (UŁ). "
        "**Próba:** polskie spółki notowane z lat 1994–1995. "
        "**Cecha:** stosunkowo prosty (5 zmiennych, próg odcięcia $0{,}45$). "
        "Często przywoływany w polskiej literaturze obok modelu Hołdy."
    )
    st.latex(r"Z = 0{,}7732 - 0{,}0856\,X_1 + 0{,}0008\,X_2 + 0{,}9221\,X_3 + 0{,}6536\,X_4 - 0{,}5947\,X_5")
    st.markdown(
        "- $X_1 = $ przychody / aktywa\n"
        "- $X_2 = $ rotacja zob. kr. (dni) = zob. kr. / koszty op. × 365\n"
        "- $X_3 = $ wynik netto / aktywa\n"
        "- $X_4 = $ wynik brutto / przychody (marża brutto)\n"
        "- $X_5 = $ ogólne zadłużenie = zobowiązania / aktywa"
    )
    st.markdown("**Interpretacja:** $Z < 0{,}45$ zagrożenie · $Z \\geq 0{,}45$ bezpieczeństwo.")
    st.markdown(
        "**Źródło:** Gajdka J., Stos D. (1996), *Wykorzystanie analizy "
        "dyskryminacyjnej w ocenie kondycji finansowej przedsiębiorstw*, "
        "Restrukturyzacja w procesie przekształceń i rozwoju "
        "przedsiębiorstw (red. R. Borowiecki), AE Kraków."
    )

    st.divider()

    # ----- Poznański -----
    st.markdown("### 8. Model poznański (Hamrol-Czajka-Piechocki, 2004)")
    st.markdown(
        "**Autorzy:** M. Hamrol, B. Czajka, M. Piechocki (UE Poznań). "
        "**Próba:** 100 polskich spółek (50/50) z lat 1999–2002. "
        "**Cecha:** najbardziej współczesny z polskich modeli "
        "Altmanowskich, używa kapitału stałego (kap. własny + zob. "
        "długoterm.) jako miary trwałej bazy finansowania."
    )
    st.latex(r"FD = 3{,}562\,X_1 + 1{,}588\,X_2 + 4{,}288\,X_3 + 6{,}719\,X_4 - 2{,}368")
    st.markdown(
        "- $X_1 = $ wynik netto / aktywa (ROA)\n"
        "- $X_2 = $ płynność szybka ≈ aktywa obrotowe / zob. krótkoterm.\n"
        "- $X_3 = $ kapitał stały / aktywa (struktura kapitału)\n"
        "- $X_4 = $ wynik ze sprzedaży / przychody (marża operacyjna)"
    )
    st.markdown("**Interpretacja:** $FD < 0$ zagrożenie · $FD \\geq 0$ bezpieczeństwo.")
    st.markdown(
        "**Źródło:** Hamrol M., Czajka B., Piechocki M. (2004), "
        "*Upadłość przedsiębiorstwa — model analizy dyskryminacyjnej*, "
        "Przegląd Organizacji nr 6."
    )

    st.divider()

    st.markdown("### 9. Tabela porównawcza modeli")
    porownanie = pd.DataFrame([
        {"Model": "Altman 1968", "Rok": 1968, "Próba": "66 spółek US", "Wskaźniki": 5, "Próg": "1.81 / 2.99", "Zastosowanie": "Notowane"},
        {"Model": "Altman Z' 1983", "Rok": 1983, "Próba": "Spółki US nienotowane", "Wskaźniki": 5, "Próg": "1.23 / 2.90", "Zastosowanie": "Nienotowane (zalecany dla PL)"},
        {"Model": "Mączyńska 6-wsk.", "Rok": 1994, "Próba": "PL transformacja", "Wskaźniki": 6, "Próg": "0 / 1 / 2", "Zastosowanie": "PL — wszystkie"},
        {"Model": "Mączyńska Model E", "Rok": 2004, "Próba": "80 PL spółek", "Wskaźniki": 5, "Próg": "0", "Zastosowanie": "PL — wszystkie"},
        {"Model": "Hołda", "Rok": 2001, "Próba": "80 PL spółek", "Wskaźniki": 5, "Próg": "0 / 0.1", "Zastosowanie": "PL — wszystkie"},
        {"Model": "Gajdka-Stos", "Rok": 1996, "Próba": "PL notowane", "Wskaźniki": 5, "Próg": "0.45", "Zastosowanie": "PL — głównie notowane"},
        {"Model": "Poznański", "Rok": 2004, "Próba": "100 PL spółek", "Wskaźniki": 4, "Próg": "0", "Zastosowanie": "PL — wszystkie"},
    ])
    st.dataframe(porownanie, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### 10. Krytyka i ograniczenia metodologiczne")
    st.markdown(
        "1. **Stacjonarność współczynników.** Wszystkie modele zakładają, "
        "że relacje wskaźnik → upadłość ustalone na próbie historycznej "
        "pozostaną stabilne. Po kryzysie 2008, pandemii 2020 i kryzysie "
        "energetycznym 2022 założenie to jest dyskusyjne.\n"
        "2. **Sektory wykluczone.** Banki, ubezpieczyciele, firmy "
        "leasingowe i inwestycyjne mają fundamentalnie inną strukturę "
        "bilansu (wysoki udział aktywów finansowych) — Altman 1968 "
        "i polskie modele zwracają dla nich „artefaktowe” wyniki.\n"
        "3. **Wpływ MSSF.** Pozycje takie jak prawo do użytkowania (MSSF 16), "
        "instrumenty pochodne, aktywa z tytułu odroczonego podatku "
        "zniekształcają wskaźniki względem definicji oryginalnych.\n"
        "4. **Polityka rachunkowości.** Window dressing końca okresu "
        "(zwłaszcza kapitał obrotowy, wynik finansowy) potrafi "
        "podnieść Z-score o 0.3–0.5 bez realnej poprawy kondycji.\n"
        "5. **Brak modelu „all-in-one”.** Konsensus literatury: stosować "
        "**wiele modeli równolegle** (jak w tej aplikacji) i interpretować "
        "rozbieżności jako sygnał niepewności.\n"
        "6. **Model logitowy.** Najnowsza literatura (od lat 2000) "
        "preferuje **regresję logistyczną** (Ohlson 1980, Hołda-logit, "
        "Wędzki) nad MDA — zwraca prawdopodobieństwo, nie tylko "
        "klasyfikację. Implementacja modelu logitowego planowana w "
        "kolejnej iteracji aplikacji."
    )

    st.divider()

    st.markdown("### 11. Bibliografia")
    st.markdown(
        "- Altman E.I. (1968), *Financial Ratios, Discriminant Analysis "
        "and the Prediction of Corporate Bankruptcy*, **Journal of "
        "Finance** 23(4), 589–609.\n"
        "- Altman E.I. (1983), *Corporate Financial Distress*, **John "
        "Wiley & Sons**.\n"
        "- Mączyńska E. (1994), *Ocena kondycji przedsiębiorstwa. "
        "Uproszczone metody*, **Życie Gospodarcze** 38.\n"
        "- Mączyńska E., Zawadzki M. (2006), *Dyskryminacyjne modele "
        "predykcji bankructwa przedsiębiorstw*, **Ekonomista** 2.\n"
        "- Hołda A. (2001), *Prognozowanie bankructwa jednostki w "
        "warunkach gospodarki polskiej z wykorzystaniem funkcji "
        "dyskryminacyjnej Z_H*, **Rachunkowość** 5.\n"
        "- Gajdka J., Stos D. (1996), *Wykorzystanie analizy "
        "dyskryminacyjnej w ocenie kondycji finansowej "
        "przedsiębiorstw*, w: R. Borowiecki (red.), AE Kraków.\n"
        "- Hamrol M., Czajka B., Piechocki M. (2004), *Upadłość "
        "przedsiębiorstwa — model analizy dyskryminacyjnej*, "
        "**Przegląd Organizacji** 6.\n"
        "- Wędzki D. (2009), *Analiza wskaźnikowa sprawozdania "
        "finansowego*, **Wolters Kluwer**.\n"
        "- Ohlson J.A. (1980), *Financial Ratios and the Probabilistic "
        "Prediction of Bankruptcy*, **Journal of Accounting Research** "
        "18(1), 109–131."
    )


if __name__ == "__main__":
    main()
