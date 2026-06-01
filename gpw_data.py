"""
Pobieranie danych finansowych dla spółek notowanych na GPW
ze źródła Yahoo Finance (yfinance) z mapowaniem na pola modeli
dyskryminacyjnych.

Moduł zwraca nie tylko wartości, ale również:
- audit trail (z której pozycji yfinance pochodzi każda liczba)
- walidację spójności bilansu
- linki do źródeł weryfikacyjnych

UWAGA: Yahoo Finance jest darmowym źródłem danych, ale jakość
sprawozdań finansowych może odbiegać od oryginalnych raportów ESPI/ESEF.
Dla zastosowań produkcyjnych (KNF, due diligence) należy weryfikować
dane z raportami źródłowymi.
"""

from __future__ import annotations

import warnings
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus

import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore", category=FutureWarning)


WIG20: List[Tuple[str, str]] = [
    ("ALE.WA", "Allegro"),
    ("ALR.WA", "Alior Bank"),
    ("BDX.WA", "Budimex"),
    ("CDR.WA", "CD Projekt"),
    ("CPS.WA", "Cyfrowy Polsat"),
    ("DNP.WA", "Dino Polska"),
    ("JSW.WA", "Jastrzębska Spółka Węglowa"),
    ("KGH.WA", "KGHM Polska Miedź"),
    ("KRU.WA", "Kruk"),
    ("KTY.WA", "Grupa Kęty"),
    ("LPP.WA", "LPP"),
    ("MBK.WA", "mBank"),
    ("OPL.WA", "Orange Polska"),
    ("PCO.WA", "Pepco Group"),
    ("PEO.WA", "Bank Pekao"),
    ("PGE.WA", "PGE"),
    ("PKN.WA", "Orlen"),
    ("PKO.WA", "PKO BP"),
    ("PZU.WA", "PZU"),
    ("SPL.WA", "Santander Bank Polska"),
]

MWIG40: List[Tuple[str, str]] = [
    ("11B.WA", "11 bit studios"),
    ("ACP.WA", "Asseco Poland"),
    ("AMC.WA", "Amica"),
    ("ATT.WA", "Grupa Azoty"),
    ("BFT.WA", "Benefit Systems"),
    ("BHW.WA", "Bank Handlowy"),
    ("BNP.WA", "BNP Paribas Bank Polska"),
    ("CAR.WA", "Inter Cars"),
    ("CCC.WA", "CCC"),
    ("CIE.WA", "Ciech"),
    ("CIG.WA", "CI Games"),
    ("DOM.WA", "Dom Development"),
    ("DVL.WA", "Develia"),
    ("EAT.WA", "AmRest"),
    ("ENA.WA", "Enea"),
    ("EUR.WA", "Eurocash"),
    ("GPW.WA", "GPW"),
    ("GRX.WA", "Grupa Azoty Police"),
    ("HUG.WA", "Huuuge"),
    ("ING.WA", "ING Bank Śląski"),
    ("KER.WA", "Kernel Holding"),
    ("KGN.WA", "Kogeneracja"),
    ("LWB.WA", "LW Bogdanka"),
    ("MIL.WA", "Bank Millennium"),
    ("MRB.WA", "Mirbud"),
    ("MRC.WA", "Mercator Medical"),
    ("NEU.WA", "Neuca"),
    ("OPN.WA", "Oponeo.pl"),
    ("PEP.WA", "Polenergia"),
    ("PKP.WA", "PKP Cargo"),
    ("PLW.WA", "Playway"),
    ("PTW.WA", "Polski Holding Hotelowy"),
    ("R22.WA", "R22"),
    ("RBW.WA", "Rainbow Tours"),
    ("STH.WA", "Stalprodukt"),
    ("TPE.WA", "Tauron"),
    ("TXT.WA", "Text"),
    ("VRG.WA", "VRG"),
    ("XTB.WA", "XTB"),
]

# sWIG80 — indeks 80 mniejszych spółek z GPW (Small WIG 80).
# Lista zweryfikowana pod kątem dostępności sprawozdań finansowych
# w Yahoo Finance — 57 spółek z minimum 2 latami historii BS+IS.
# UWAGA: nie wszystkie 80 spółek z indeksu sWIG80 jest dostępne na
# Yahoo (niektóre mają tylko wycenę, bez sprawozdań). Lista pomija
# spółki bez danych finansowych.
SWIG80: List[Tuple[str, str]] = [
    ("1AT.WA", "Atal"),
    ("ABE.WA", "AB"),
    ("ACT.WA", "Action"),
    ("AGO.WA", "Agora"),
    ("APR.WA", "Auto Partner"),
    ("ASB.WA", "Asbis"),
    ("ATC.WA", "Arctic Paper"),
    ("ATD.WA", "Atende"),
    ("BBT.WA", "Boombit"),
    ("BIO.WA", "Bioton"),
    ("BOS.WA", "BOŚ Bank"),
    ("BRS.WA", "Boryszew"),
    ("CLN.WA", "Clean&Carbon Energy"),
    ("CMP.WA", "Comp"),
    ("DAT.WA", "DataWalk"),
    ("DCR.WA", "Decora"),
    ("ECH.WA", "Echo Investment"),
    ("ELT.WA", "Elektrotim"),
    ("ENT.WA", "Enter Air"),
    ("ERB.WA", "Erbud"),
    ("FRO.WA", "Ferro"),
    ("FTE.WA", "Forte"),
    ("GTC.WA", "Globe Trade Centre"),
    ("IPO.WA", "iPos"),
    ("KGL.WA", "Kogeneracja Gliwice"),
    ("LBW.WA", "Lubawa"),
    ("MBR.WA", "Mabion"),
    ("MCI.WA", "MCI Capital"),
    ("MDG.WA", "Medicalgorithmics"),
    ("MGT.WA", "Mangata Holding"),
    ("MLG.WA", "MLP Group"),
    ("MOC.WA", "Mo-Bruk"),
    ("OND.WA", "Onde"),
    ("PCE.WA", "Polska Celuloza"),
    ("PCF.WA", "PCF Group"),
    ("PCR.WA", "PCC Rokita"),
    ("PEN.WA", "PCC Exol"),
    ("PHN.WA", "Polski Holding Nieruchomości"),
    ("PJP.WA", "PJP Makrum"),
    ("PLZ.WA", "Polna"),
    ("RVU.WA", "Ryvu Therapeutics"),
    ("SGN.WA", "Sygnity"),
    ("SKA.WA", "Skarbiec Holding"),
    ("SLV.WA", "Selvita"),
    ("SNK.WA", "Sanok Rubber"),
    ("STX.WA", "Stalexport Autostrady"),
    ("TOR.WA", "Toya"),
    ("TRN.WA", "Trans Polonia"),
    ("TRR.WA", "Trakcja"),
    ("UNI.WA", "Unimot"),
    ("VGO.WA", "Vigo Photonics"),
    ("VOX.WA", "Voxel"),
    ("VVD.WA", "Vivid Games"),
    ("WLT.WA", "Wielton"),
    ("WPL.WA", "Wirtualna Polska"),
    ("WWL.WA", "Wawel"),
    ("ZEP.WA", "ZE PAK"),
]


def lista_spolek() -> List[Tuple[str, str, str]]:
    """Zwraca listę krotek (ticker, nazwa, indeks) posortowaną po nazwie."""
    wynik: List[Tuple[str, str, str]] = []
    wynik.extend((t, n, "WIG20") for t, n in WIG20)
    wynik.extend((t, n, "mWIG40") for t, n in MWIG40)
    wynik.extend((t, n, "sWIG80") for t, n in SWIG80)
    wynik.sort(key=lambda x: x[1].lower())
    return wynik


SEKTORY_NIEKOMPATYBILNE = {
    "Financial Services",
    "Financials",
}

BRANZE_BANKI_UBEZP = {
    "Banks", "Bank", "Banks—Regional", "Banks—Diversified",
    "Insurance", "Insurance—Diversified", "Insurance—Life",
    "Insurance—Property & Casualty", "Insurance Brokers",
    "Capital Markets", "Asset Management",
}


# ---------------------------------------------------------------------------
# Pobieranie wartości z DataFrame'ów yfinance + audit trail
# ---------------------------------------------------------------------------

def _pobierz(df: pd.DataFrame, kolumna, *nazwy: str) -> Tuple[Optional[float], Optional[str]]:
    """Zwraca (wartość, nazwę wiersza yfinance który zadziałał) lub (None, None)."""
    if df is None or df.empty or kolumna not in df.columns:
        return None, None
    for nazwa in nazwy:
        if nazwa in df.index:
            v = df.at[nazwa, kolumna]
            if pd.notna(v):
                return float(v), nazwa
    return None, None


def _w_tysiacach(v: Optional[float]) -> float:
    """Yahoo zwraca dane w jednostkach. Przeliczamy na tys. dla spójności z formularzem."""
    if v is None:
        return 0.0
    return round(v / 1_000.0, 2)


# ---------------------------------------------------------------------------
# Mapowanie pojedynczego okresu z opisem źródeł
# ---------------------------------------------------------------------------

def mapuj_okres(
    bs: pd.DataFrame, fin: pd.DataFrame, cf: pd.DataFrame,
    kolumna,
    rok_poprzedni_kol=None,
    market_cap: Optional[float] = None,
) -> Tuple[Dict[str, float], Dict[str, str]]:
    """Mapuje dane jednego roku na (dane, opis_zrodel).

    `dane` = słownik wartości (w tysiącach) gotowy dla modeli.
    `opis_zrodel` = słownik {pole: tekstowy opis skąd wzięta wartość}.
    """

    zrodla: Dict[str, str] = {}

    # --- Przychody ---
    przychody, src = _pobierz(fin, kolumna, "Total Revenue", "Operating Revenue")
    zrodla["przychody_sprzedazy"] = f"RZiS: {src}" if src else "BRAK"

    przychody_prev, src_prev = (None, None)
    if rok_poprzedni_kol is not None:
        przychody_prev, src_prev = _pobierz(
            fin, rok_poprzedni_kol, "Total Revenue", "Operating Revenue"
        )
    zrodla["przychody_rok_poprzedni"] = (
        f"RZiS rok poprzedni: {src_prev}" if src_prev else "BRAK"
    )

    # --- Bilans: aktywa ---
    aktywa_og, src = _pobierz(bs, kolumna, "Total Assets")
    zrodla["aktywa_ogolem"] = f"Bilans: {src}" if src else "BRAK"

    aktywa_obr, src = _pobierz(bs, kolumna, "Current Assets")
    zrodla["aktywa_obrotowe"] = f"Bilans: {src}" if src else "BRAK"

    aktywa_trw, src = _pobierz(bs, kolumna, "Total Non Current Assets")
    if aktywa_trw is None and aktywa_og is not None and aktywa_obr is not None:
        aktywa_trw = aktywa_og - aktywa_obr
        zrodla["majatek_trwaly"] = "WYLICZONE: Total Assets − Current Assets"
    else:
        zrodla["majatek_trwaly"] = f"Bilans: {src}" if src else "BRAK"

    # --- Bilans: zapasy (X2 Poznański: szybkie aktywa = obrotowe − zapasy) ---
    zapasy, src = _pobierz(bs, kolumna, "Inventory", "Inventories", "Other Inventories")
    zrodla["zapasy"] = f"Bilans: {src}" if src else "BRAK (przyjęto 0)"

    # --- Bilans: zobowiązania ---
    zob_og, src = _pobierz(
        bs, kolumna,
        "Total Liabilities Net Minority Interest", "Total Liab",
    )
    zrodla["zobowiazania_ogolem"] = f"Bilans: {src}" if src else "BRAK"

    zob_kt, src = _pobierz(bs, kolumna, "Current Liabilities")
    zrodla["zobowiazania_krotkoterm"] = f"Bilans: {src}" if src else "BRAK"

    zob_dt, src = _pobierz(
        bs, kolumna,
        "Total Non Current Liabilities Net Minority Interest",
        "Long Term Debt And Capital Lease Obligation",
    )
    if zob_dt is None and zob_og is not None and zob_kt is not None:
        zob_dt = max(zob_og - zob_kt, 0)
        zrodla["zobowiazania_dlugoterm"] = (
            "WYLICZONE: Total Liabilities − Current Liabilities"
        )
    else:
        zrodla["zobowiazania_dlugoterm"] = f"Bilans: {src}" if src else "BRAK"

    # --- Kapitał obrotowy (working capital) ---
    kap_obr, src = _pobierz(bs, kolumna, "Working Capital")
    if kap_obr is None and aktywa_obr is not None and zob_kt is not None:
        kap_obr = aktywa_obr - zob_kt
        zrodla["kapital_obrotowy"] = "WYLICZONE: Current Assets − Current Liabilities"
    else:
        zrodla["kapital_obrotowy"] = f"Bilans: {src}" if src else "BRAK"

    # --- Kapitał własny (księgowy) ---
    kap_wl, src = _pobierz(
        bs, kolumna,
        "Stockholders Equity", "Common Stock Equity",
        "Total Equity Gross Minority Interest",
    )
    zrodla["kapital_wlasny"] = f"Bilans: {src} (wartość księgowa)" if src else "BRAK"

    kap_zakl, src = _pobierz(bs, kolumna, "Common Stock", "Capital Stock")
    zrodla["kapital_zakladowy"] = f"Bilans: {src}" if src else "BRAK"

    # --- RZiS ---
    ebit, src = _pobierz(fin, kolumna, "EBIT", "Operating Income")
    zrodla["wynik_operacyjny"] = f"RZiS: {src}" if src else "BRAK"

    # Koszty operacyjne (Hołda X4, Gajdka-Stos X2 — wskaźnik rotacji zob. kt.)
    koszty_op, src = _pobierz(
        fin, kolumna, "Total Expenses", "Operating Expense", "Cost Of Revenue"
    )
    if koszty_op is None and przychody is not None and ebit is not None:
        koszty_op = przychody - ebit
        zrodla["koszty_operacyjne"] = "WYLICZONE: Przychody − EBIT"
    else:
        zrodla["koszty_operacyjne"] = f"RZiS: {src}" if src else "BRAK"

    netto, src = _pobierz(fin, kolumna, "Net Income", "Net Income Common Stockholders")
    zrodla["wynik_finansowy_netto"] = f"RZiS: {src}" if src else "BRAK"

    # Wynik brutto = zysk PRZED opodatkowaniem (= netto + podatek). Mączyńska
    # i Gajdka-Stos używają tego pola w X1/X3/X4. Wcześniej liczono je jako
    # `netto + koszty_finansowe`, co było matematycznie błędne — różnica
    # potrafiła sięgać 25-28% dla typowej polskiej spółki płacącej CIT.
    pretax, src = _pobierz(
        fin, kolumna, "Pretax Income", "Income Before Tax", "Pretax Income Reported"
    )
    zrodla["wynik_brutto"] = f"RZiS: {src} (zysk przed opodatkowaniem)" if src else "BRAK"

    # X2 Altmana: retained earnings — bezpośrednio z bilansu
    retained, src = _pobierz(bs, kolumna, "Retained Earnings")
    zrodla["wynik_brutto_skumulowany"] = (
        f"Bilans: {src} (zyski zatrzymane — X2 Altmana)" if src else "BRAK"
    )

    # --- Cash Flow / Amortyzacja ---
    # Yahoo zwraca amortyzację w CF często z minusem (przepływ ujemny lub
    # konwencja non-cash adjustment). W modelach traktujemy ją jako wartość
    # dodatnią (koszt non-cash dodawany z powrotem do zysku w X1 Mączyńskiej).
    amort, src = _pobierz(cf, kolumna, "Depreciation And Amortization", "Depreciation")
    if amort is None:
        amort, src = _pobierz(fin, kolumna, "Reconciled Depreciation")
        zrodla["amortyzacja"] = f"RZiS (fallback): {src}" if src else "BRAK"
    else:
        zrodla["amortyzacja"] = f"CF: {src}" if src else "BRAK"
    if amort is not None:
        amort = abs(amort)

    # Yahoo zwraca Interest Expense czasem jako wartość ujemną (zależnie od
    # spółki/standardu raportowania). W polskiej księgowości "koszty finansowe"
    # to wartość dodatnia. abs() zapobiega zaniżaniu fallbacka wynik_brutto
    # w trybie ręcznym.
    odsetki, src = _pobierz(
        fin, kolumna, "Interest Expense", "Interest Expense Non Operating"
    )
    zrodla["koszty_finansowe"] = f"RZiS: {src}" if src else "BRAK"
    if odsetki is not None:
        odsetki = abs(odsetki)

    # --- Kapitał własny: zawsze KSIĘGOWY (zgodnie z definicją Altman Z' 1983,
    #     Mączyńskiej, Hołdy, Gajdki-Stosa, Hamrola — wszystkie estymowane
    #     na wartości księgowej). Wartość RYNKOWA (kapitalizacja) idzie do
    #     osobnego pola `kapital_wlasny_rynkowy` i jest używana TYLKO przez
    #     Altmana 1968 w X4 (oryginalna definicja: market value of equity).
    #     UWAGA: wcześniejsza wersja podmieniała `kapital_wlasny` na market_cap
    #     dla najnowszego roku — dla CDR/KGH/DAT dawało to KW > Aktywa, co jest
    #     księgowym absurdem i psuło 6 z 7 modeli (wzrost o rząd wielkości).
    if market_cap is not None and market_cap > 0:
        kap_wl_rynkowy = market_cap
        zrodla["kapital_wlasny_rynkowy"] = (
            "Yahoo info.marketCap (kapitalizacja rynkowa — używana w X4 Altman 1968)"
        )
    else:
        kap_wl_rynkowy = None
        zrodla["kapital_wlasny_rynkowy"] = "BRAK (Altman 1968 użyje wartości księgowej)"

    dane = {
        "przychody_sprzedazy": _w_tysiacach(przychody),
        "przychody_rok_poprzedni": _w_tysiacach(przychody_prev),
        "wynik_operacyjny": _w_tysiacach(ebit),
        "koszty_operacyjne": _w_tysiacach(koszty_op),
        "wynik_finansowy_netto": _w_tysiacach(netto),
        "wynik_brutto": _w_tysiacach(pretax),
        "wynik_brutto_skumulowany": _w_tysiacach(retained),
        "aktywa_ogolem": _w_tysiacach(aktywa_og),
        "aktywa_obrotowe": _w_tysiacach(aktywa_obr),
        "majatek_trwaly": _w_tysiacach(aktywa_trw),
        "zapasy": _w_tysiacach(zapasy),
        "kapital_obrotowy": _w_tysiacach(kap_obr),
        "zobowiazania_ogolem": _w_tysiacach(zob_og),
        "zobowiazania_krotkoterm": _w_tysiacach(zob_kt),
        "zobowiazania_dlugoterm": _w_tysiacach(zob_dt),
        "kapital_wlasny": _w_tysiacach(kap_wl),
        "kapital_wlasny_rynkowy": _w_tysiacach(kap_wl_rynkowy),
        "kapital_zakladowy": _w_tysiacach(kap_zakl),
        "amortyzacja": _w_tysiacach(amort),
        "koszty_finansowe": _w_tysiacach(odsetki),
    }
    return dane, zrodla


# ---------------------------------------------------------------------------
# Walidacja spójności bilansu i danych
# ---------------------------------------------------------------------------

def waliduj_dane(dane: Dict[str, float], tolerancja: float = 0.02) -> List[Dict]:
    """Sprawdza spójność księgową pobranych danych. Zwraca listę testów:
    [{"test": str, "status": "ok"|"warn"|"err", "wiadomosc": str, "szczegol": str}]
    Tolerancja 2% jest dopuszczalna ze względu na zaokrąglenia i Yahoo.
    """
    testy: List[Dict] = []

    aktywa = dane.get("aktywa_ogolem", 0)
    aktywa_obr = dane.get("aktywa_obrotowe", 0)
    aktywa_trw = dane.get("majatek_trwaly", 0)
    zob_og = dane.get("zobowiazania_ogolem", 0)
    zob_kt = dane.get("zobowiazania_krotkoterm", 0)
    kap_obr = dane.get("kapital_obrotowy", 0)
    kap_wl_ksieg = dane.get("kapital_wlasny", 0)  # zawsze wartość księgowa z bilansu
    przychody = dane.get("przychody_sprzedazy", 0)
    netto = dane.get("wynik_finansowy_netto", 0)

    # Test 1: aktywa = aktywa obrotowe + majątek trwały
    if aktywa > 0 and aktywa_obr > 0 and aktywa_trw > 0:
        suma = aktywa_obr + aktywa_trw
        diff = abs(suma - aktywa) / aktywa
        if diff <= tolerancja:
            testy.append({
                "test": "Aktywa obrotowe + majątek trwały = Aktywa ogółem",
                "status": "ok",
                "wiadomosc": f"Spójne (różnica {diff*100:.2f}%)",
                "szczegol": f"{aktywa_obr:,.0f} + {aktywa_trw:,.0f} = {suma:,.0f} vs {aktywa:,.0f}",
            })
        else:
            testy.append({
                "test": "Aktywa obrotowe + majątek trwały = Aktywa ogółem",
                "status": "warn",
                "wiadomosc": f"Niezgodność {diff*100:.2f}% (próg {tolerancja*100:.0f}%)",
                "szczegol": f"{aktywa_obr:,.0f} + {aktywa_trw:,.0f} = {suma:,.0f} vs {aktywa:,.0f}",
            })
    else:
        testy.append({
            "test": "Aktywa obrotowe + majątek trwały = Aktywa ogółem",
            "status": "warn",
            "wiadomosc": "Niesprawdzone (brak wartości)",
            "szczegol": "",
        })

    # Test 2: zob_kt <= zob_og
    if zob_og > 0:
        if zob_kt <= zob_og + 1e-6:
            testy.append({
                "test": "Zobowiązania krótkoterm. ≤ Zobowiązania ogółem",
                "status": "ok",
                "wiadomosc": "Spójne",
                "szczegol": f"{zob_kt:,.0f} ≤ {zob_og:,.0f}",
            })
        else:
            testy.append({
                "test": "Zobowiązania krótkoterm. ≤ Zobowiązania ogółem",
                "status": "err",
                "wiadomosc": "BŁĄD: zob. krótkoterm. > zob. ogółem",
                "szczegol": f"{zob_kt:,.0f} > {zob_og:,.0f}",
            })
    else:
        testy.append({
            "test": "Zobowiązania krótkoterm. ≤ Zobowiązania ogółem",
            "status": "warn",
            "wiadomosc": "Niesprawdzone (brak zobowiązań ogółem)",
            "szczegol": "",
        })

    # Test 3: kapitał obrotowy = aktywa obrotowe - zob krótkoterm.
    if aktywa_obr > 0 and zob_kt > 0:
        oczekiwany = aktywa_obr - zob_kt
        if abs(kap_obr - oczekiwany) < 1e-3 * max(abs(oczekiwany), 1) + 1:
            testy.append({
                "test": "Kapitał obrotowy = Akt. obr. − Zob. krótkoterm.",
                "status": "ok",
                "wiadomosc": "Spójne",
                "szczegol": f"{aktywa_obr:,.0f} − {zob_kt:,.0f} = {oczekiwany:,.0f}",
            })
        else:
            testy.append({
                "test": "Kapitał obrotowy = Akt. obr. − Zob. krótkoterm.",
                "status": "warn",
                "wiadomosc": "Yahoo Working Capital ≠ wyliczeniu",
                "szczegol": f"Yahoo: {kap_obr:,.0f}, wyliczone: {oczekiwany:,.0f}",
            })

    # Test 4: aktywa > 0 (warunek konieczny dla wszystkich modeli)
    if aktywa <= 0:
        testy.append({
            "test": "Aktywa ogółem > 0",
            "status": "err",
            "wiadomosc": "BŁĄD: brak aktywów — modele nie zadziałają",
            "szczegol": "",
        })
    else:
        testy.append({
            "test": "Aktywa ogółem > 0",
            "status": "ok",
            "wiadomosc": "OK",
            "szczegol": f"{aktywa:,.0f}",
        })

    # Test 5: przychody > 0
    if przychody <= 0:
        testy.append({
            "test": "Przychody ze sprzedaży > 0",
            "status": "err",
            "wiadomosc": "BŁĄD: brak przychodów — większość modeli nie zadziała",
            "szczegol": "",
        })
    else:
        testy.append({
            "test": "Przychody ze sprzedaży > 0",
            "status": "ok",
            "wiadomosc": "OK",
            "szczegol": f"{przychody:,.0f}",
        })

    # Test 6: rentowność netto sanity check (-100% .. +100% przychodów)
    if przychody > 0:
        marza = netto / przychody
        if -1 <= marza <= 1:
            testy.append({
                "test": "Marża netto w typowym zakresie (−100% do +100%)",
                "status": "ok",
                "wiadomosc": f"Marża netto = {marza*100:.2f}%",
                "szczegol": f"{netto:,.0f} / {przychody:,.0f}",
            })
        else:
            testy.append({
                "test": "Marża netto w typowym zakresie (−100% do +100%)",
                "status": "warn",
                "wiadomosc": f"Marża netto = {marza*100:.2f}% — sprawdź dane!",
                "szczegol": f"{netto:,.0f} / {przychody:,.0f}",
            })

    return testy


def podsumowanie_walidacji(testy: List[Dict]) -> Tuple[int, int, int]:
    """Zwraca (liczba_ok, liczba_warn, liczba_err)."""
    return (
        sum(1 for t in testy if t["status"] == "ok"),
        sum(1 for t in testy if t["status"] == "warn"),
        sum(1 for t in testy if t["status"] == "err"),
    )


# ---------------------------------------------------------------------------
# Linki do źródeł weryfikacyjnych
# ---------------------------------------------------------------------------

def linki_zrodlowe(ticker: str, nazwa: Optional[str] = None) -> Dict[str, str]:
    """Zwraca słownik {etykieta: URL} z linkami pozwalającymi zweryfikować dane."""
    ticker_no_wa = ticker.replace(".WA", "")
    nazwa_q = quote_plus(nazwa or ticker_no_wa)
    links = {
        "Yahoo Finance — sprawozdania (źródło aplikacji)":
            f"https://finance.yahoo.com/quote/{ticker}/financials",
        "Yahoo Finance — bilans":
            f"https://finance.yahoo.com/quote/{ticker}/balance-sheet",
        "Bankier.pl — profil i sprawozdania":
            f"https://www.bankier.pl/inwestowanie/profile/quote.html?symbol={ticker_no_wa}",
        "Stooq.pl — notowania i podstawy":
            f"https://stooq.pl/q/?s={ticker_no_wa.lower()}",
        "Biznesradar — analizy":
            f"https://www.biznesradar.pl/raporty-finansowe-bilans/{nazwa_q}",
        "Komunikaty ESPI/EBI (GPW)":
            f"https://www.gpw.pl/komunikaty?searchedPhrase={nazwa_q}",
    }
    return links


# ---------------------------------------------------------------------------
# Główna funkcja pobierająca
# ---------------------------------------------------------------------------

def pobierz_spolke(ticker: str, max_lat: int = 4) -> Dict:
    """Pobiera dane finansowe spółki z GPW i zwraca słownik:
    {
        "ticker": str, "nazwa": str, "sektor": str, "branza": str,
        "waluta": str, "kapitalizacja": float | None,
        "ostrzezenie": str | None,
        "lata": {rok: {"dane": dict, "zrodla": dict, "walidacja": list}},
        "linki": dict,
        "blad": str | None,
    }
    """
    wynik = {
        "ticker": ticker,
        "nazwa": None,
        "sektor": None,
        "branza": None,
        "waluta": None,
        "kapitalizacja": None,
        "ostrzezenie": None,
        "lata": {},
        "linki": {},
        "blad": None,
    }

    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        bs = t.balance_sheet
        fin = t.financials
        cf = t.cashflow
    except Exception as e:
        wynik["blad"] = f"Nie udało się pobrać danych z Yahoo Finance: {e}"
        return wynik

    if bs is None or bs.empty or fin is None or fin.empty:
        wynik["blad"] = (
            "Yahoo Finance nie udostępnia sprawozdań finansowych dla tego "
            "tickera. Spróbuj innej spółki lub wprowadź dane ręcznie."
        )
        return wynik

    wynik["nazwa"] = info.get("longName") or info.get("shortName") or ticker
    wynik["sektor"] = info.get("sector")
    wynik["branza"] = info.get("industry")
    wynik["waluta"] = info.get("financialCurrency") or info.get("currency")
    market_cap = info.get("marketCap")
    wynik["kapitalizacja"] = market_cap
    wynik["linki"] = linki_zrodlowe(ticker, wynik["nazwa"])

    sektor = wynik["sektor"] or ""
    branza = wynik["branza"] or ""
    if sektor in SEKTORY_NIEKOMPATYBILNE or any(
        b.lower() in branza.lower() for b in BRANZE_BANKI_UBEZP if b
    ):
        wynik["ostrzezenie"] = (
            f"Sektor: **{sektor}** / Branża: **{branza}**. "
            "Modele dyskryminacyjne Altmana, Mączyńskiej, Hołdy i Gajdki-Stosa "
            "były estymowane na próbach przedsiębiorstw produkcyjnych i "
            "handlowych. Nie są właściwe dla banków, ubezpieczycieli, TFI "
            "ani innych instytucji finansowych — wyniki będą mylące."
        )

    kolumny_bs = list(bs.columns)[:max_lat]
    for i, kol in enumerate(kolumny_bs):
        rok = pd.Timestamp(kol).year
        rok_poprzedni_kol = (
            kolumny_bs[i + 1] if i + 1 < len(kolumny_bs) else None
        )
        mc = market_cap if i == 0 else None
        dane, zrodla = mapuj_okres(
            bs, fin, cf, kol,
            rok_poprzedni_kol=rok_poprzedni_kol,
            market_cap=mc,
        )
        walidacja = waliduj_dane(dane)
        wynik["lata"][rok] = {
            "dane": dane,
            "zrodla": zrodla,
            "walidacja": walidacja,
        }

    if not wynik["lata"]:
        wynik["blad"] = "Brak danych rocznych w Yahoo Finance dla tego tickera."

    return wynik
