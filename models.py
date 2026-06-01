"""
Modele dyskryminacyjne predykcji upadłości przedsiębiorstw.

Implementacja zawiera klasyczne polskie i zagraniczne modele Z-score:
- Altman (1968) - oryginalny dla spółek notowanych
- Altman Z' (1983) - dla spółek nienotowanych (lepszy dla rynku polskiego)
- Mączyńska INE PAN (model 6-wskaźnikowy)
- Hołda (2001)
- Gajdki-Stosa
- Poznański (Hadasik, Hamrol, Czajka, Piechocki)

Każda funkcja zwraca krotkę: (wynik_z, interpretacja, kolor, szczegoly_wskaznikow)
"""

from typing import Dict, Tuple, Optional

KOLOR_BEZPIECZNY = "#16a34a"
KOLOR_SZARY = "#f59e0b"
KOLOR_ZAGROZONY = "#dc2626"
KOLOR_BLAD = "#6b7280"


def _bezpieczne_dzielenie(licznik: float, mianownik: float) -> Optional[float]:
    if mianownik is None or mianownik == 0:
        return None
    return licznik / mianownik


def model_altman_1968(d: Dict[str, float]) -> Tuple:
    """
    Model Altmana (1968) - dla spółek notowanych na giełdzie.
    Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5

    X1 = kapitał obrotowy / aktywa ogółem
    X2 = zysk zatrzymany (wynik brutto skumulowany 3 lata) / aktywa ogółem
    X3 = EBIT (wynik operacyjny) / aktywa ogółem
    X4 = wartość rynkowa kapitału własnego / zobowiązania ogółem
    X5 = przychody ze sprzedaży / aktywa ogółem

    Strefy: Z < 1.81 zagrożony | 1.81-2.99 strefa szara | Z > 2.99 bezpieczny
    """
    x1 = _bezpieczne_dzielenie(d["kapital_obrotowy"], d["aktywa_ogolem"])
    x2 = _bezpieczne_dzielenie(d["wynik_brutto_skumulowany"], d["aktywa_ogolem"])
    x3 = _bezpieczne_dzielenie(d["wynik_operacyjny"], d["aktywa_ogolem"])
    # X4: oryginalna definicja Altmana 1968 to WARTOŚĆ RYNKOWA kapitału
    # własnego (kapitalizacja giełdowa). Użyj jej, jeśli dostępna; w trybie
    # ręcznym lub dla starszych lat gdy brak ceny — fallback na wartość księgową
    # (i wtedy wynik zbliża się do interpretacji Altman Z' 1983).
    kw_rynk = d.get("kapital_wlasny_rynkowy") or 0
    kw_dla_x4 = kw_rynk if kw_rynk > 0 else d["kapital_wlasny"]
    x4 = _bezpieczne_dzielenie(kw_dla_x4, d["zobowiazania_ogolem"])
    x5 = _bezpieczne_dzielenie(d["przychody_sprzedazy"], d["aktywa_ogolem"])

    wskazniki = {"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5}

    if None in (x1, x2, x3, x4, x5):
        return None, "Brak danych do obliczenia", KOLOR_BLAD, wskazniki

    z = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5

    if z < 1.81:
        interp, kolor = "Zagrożony upadłością", KOLOR_ZAGROZONY
    elif z <= 2.99:
        interp, kolor = "Strefa niepewności (szara)", KOLOR_SZARY
    else:
        interp, kolor = "Sytuacja bezpieczna", KOLOR_BEZPIECZNY

    return round(z, 4), interp, kolor, wskazniki


def model_altman_z_prim(d: Dict[str, float]) -> Tuple:
    """
    Model Altmana Z' (1983) - dla spółek nienotowanych.
    Z' = 0.717*X1 + 0.847*X2 + 3.107*X3 + 0.420*X4 + 0.998*X5

    Różnica od oryginału: wartość księgowa zamiast rynkowej kapitału
    własnego w X4 oraz przeszacowane współczynniki.

    Strefy: Z' < 1.23 zagrożony | 1.23-2.90 szara | Z' > 2.90 bezpieczny
    """
    x1 = _bezpieczne_dzielenie(d["kapital_obrotowy"], d["aktywa_ogolem"])
    x2 = _bezpieczne_dzielenie(d["wynik_brutto_skumulowany"], d["aktywa_ogolem"])
    x3 = _bezpieczne_dzielenie(d["wynik_operacyjny"], d["aktywa_ogolem"])
    x4 = _bezpieczne_dzielenie(d["kapital_wlasny"], d["zobowiazania_ogolem"])
    x5 = _bezpieczne_dzielenie(d["przychody_sprzedazy"], d["aktywa_ogolem"])

    wskazniki = {"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5}

    if None in (x1, x2, x3, x4, x5):
        return None, "Brak danych do obliczenia", KOLOR_BLAD, wskazniki

    z = 0.717 * x1 + 0.847 * x2 + 3.107 * x3 + 0.420 * x4 + 0.998 * x5

    if z < 1.23:
        interp, kolor = "Zagrożony upadłością", KOLOR_ZAGROZONY
    elif z <= 2.90:
        interp, kolor = "Strefa niepewności (szara)", KOLOR_SZARY
    else:
        interp, kolor = "Sytuacja bezpieczna", KOLOR_BEZPIECZNY

    return round(z, 4), interp, kolor, wskazniki


def model_maczynskiej(d: Dict[str, float]) -> Tuple:
    """
    Model E. Mączyńskiej (wariant 6-wskaźnikowy, INE PAN).
    W = 1.5*X1 + 0.08*X2 + 10.0*X3 + 5.0*X4 + 0.3*X5 + 0.1*X6

    X1 = (wynik brutto + amortyzacja) / zobowiązania ogółem
    X2 = aktywa ogółem / zobowiązania ogółem
    X3 = wynik brutto / aktywa ogółem
    X4 = wynik netto / przychody ze sprzedaży
    X5 = kapitał obrotowy / przychody ze sprzedaży (proxy zapasów)
    X6 = przychody ze sprzedaży / aktywa ogółem

    Strefy: W < 0 zagrożony | 0-1 słaby | 1-2 dobry | W > 2 bardzo dobry
    """
    # Wynik brutto = zysk PRZED opodatkowaniem (Pretax Income). Dla danych z
    # Yahoo pole `wynik_brutto` jest pobierane bezpośrednio z RZiS. Dla danych
    # z formularza ręcznego (gdy pole nie zostało wypełnione) cofamy się do
    # przybliżenia `netto + koszty_finansowe` z wyraźną notką w UI.
    wynik_brutto = d.get("wynik_brutto") or (d["wynik_finansowy_netto"] + d["koszty_finansowe"])

    x1 = _bezpieczne_dzielenie(wynik_brutto + d["amortyzacja"], d["zobowiazania_ogolem"])
    x2 = _bezpieczne_dzielenie(d["aktywa_ogolem"], d["zobowiazania_ogolem"])
    x3 = _bezpieczne_dzielenie(wynik_brutto, d["aktywa_ogolem"])
    x4 = _bezpieczne_dzielenie(d["wynik_finansowy_netto"], d["przychody_sprzedazy"])
    x5 = _bezpieczne_dzielenie(d["kapital_obrotowy"], d["przychody_sprzedazy"])
    x6 = _bezpieczne_dzielenie(d["przychody_sprzedazy"], d["aktywa_ogolem"])

    wskazniki = {"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5, "X6": x6}

    if None in (x1, x2, x3, x4, x5, x6):
        return None, "Brak danych do obliczenia", KOLOR_BLAD, wskazniki

    w = 1.5 * x1 + 0.08 * x2 + 10.0 * x3 + 5.0 * x4 + 0.3 * x5 + 0.1 * x6

    if w < 0:
        interp, kolor = "Zagrożony upadłością", KOLOR_ZAGROZONY
    elif w <= 1:
        interp, kolor = "Słaba kondycja, brak zagrożenia", KOLOR_SZARY
    elif w <= 2:
        interp, kolor = "Dobra kondycja", KOLOR_BEZPIECZNY
    else:
        interp, kolor = "Bardzo dobra kondycja", KOLOR_BEZPIECZNY

    return round(w, 4), interp, kolor, wskazniki


def model_maczynska_e(d: Dict[str, float]) -> Tuple:
    """
    
    INE PAN, druga generacja modeli z serii A-G publikowanych
    w pracach Mączyńskiej & Zawadzkiego.

    W = 9.478*X1 + 3.613*X2 + 3.246*X3 + 0.455*X4 + 0.802*X5 − 2.478

    X1 = wynik operacyjny (EBIT) / aktywa ogółem
    X2 = kapitał własny / aktywa ogółem
    X3 = (wynik finansowy netto + amortyzacja) / zobowiązania ogółem
    X4 = przychody ze sprzedaży / aktywa ogółem
    X5 = aktywa obrotowe / zobowiązania krótkoterminowe (płynność bieżąca)

    Strefy: W < 0 zagrożony | W >= 0 bezpieczny
    Skuteczność predykcyjna na próbie INE PAN: ok. 92% (klasyfikacja
    poprawna na 1 rok przed upadłością).
    """
    x1 = _bezpieczne_dzielenie(d["wynik_operacyjny"], d["aktywa_ogolem"])
    x2 = _bezpieczne_dzielenie(d["kapital_wlasny"], d["aktywa_ogolem"])
    x3 = _bezpieczne_dzielenie(
        d["wynik_finansowy_netto"] + d["amortyzacja"],
        d["zobowiazania_ogolem"],
    )
    x4 = _bezpieczne_dzielenie(d["przychody_sprzedazy"], d["aktywa_ogolem"])
    x5 = _bezpieczne_dzielenie(d["aktywa_obrotowe"], d["zobowiazania_krotkoterm"])

    wskazniki = {"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5}

    if None in (x1, x2, x3, x4, x5):
        return None, "Brak danych do obliczenia", KOLOR_BLAD, wskazniki

    w = (
        9.478 * x1
        + 3.613 * x2
        + 3.246 * x3
        + 0.455 * x4
        + 0.802 * x5
        - 2.478
    )

    if w < 0:
        interp, kolor = "Zagrożony upadłością", KOLOR_ZAGROZONY
    else:
        interp, kolor = "Sytuacja bezpieczna", KOLOR_BEZPIECZNY

    return round(w, 4), interp, kolor, wskazniki


def model_holda(d: Dict[str, float]) -> Tuple:
    """
    Model A. Hołdy (2001) - opracowany na danych polskich spółek.
    Z = 0.605 + 0.681*X1 - 0.0196*X2 + 0.00969*X3 + 0.000672*X4 + 0.157*X5

    X1 = aktywa obrotowe / zobowiązania krótkoterminowe (płynność bieżąca)
    X2 = (zobowiązania ogółem / aktywa ogółem) * 100
    X3 = (wynik finansowy netto / aktywa ogółem) * 100
    X4 = (zobowiązania krótkoterminowe / koszty operacyjne) * 365
    X5 = przychody ze sprzedaży / aktywa ogółem

    Strefy: Z < 0 zagrożony | 0-0.1 strefa szara | Z > 0.1 bezpieczny
    """
    # Koszty operacyjne — preferuj wartość bezpośrednio z RZiS; jeśli brak,
    # przybliż jako Przychody − EBIT. Guard: gdy wynik <= 0 (firma deficytowa
    # operacyjnie lub ujemny EBIT większy od przychodów), użyj samych
    # przychodów jako mianownik X4 — żeby nie rozbić wskaźnika rotacji
    # zobowiązań krótkoterminowych.
    koszty_operacyjne = d.get("koszty_operacyjne")
    if not koszty_operacyjne or koszty_operacyjne <= 0:
        koszty_operacyjne = d["przychody_sprzedazy"] - d["wynik_operacyjny"]
    if koszty_operacyjne <= 0:
        koszty_operacyjne = max(d["przychody_sprzedazy"], 1e-9)

    x1 = _bezpieczne_dzielenie(d["aktywa_obrotowe"], d["zobowiazania_krotkoterm"])
    x2 = _bezpieczne_dzielenie(d["zobowiazania_ogolem"], d["aktywa_ogolem"])
    x2 = x2 * 100 if x2 is not None else None
    x3 = _bezpieczne_dzielenie(d["wynik_finansowy_netto"], d["aktywa_ogolem"])
    x3 = x3 * 100 if x3 is not None else None
    x4 = _bezpieczne_dzielenie(d["zobowiazania_krotkoterm"], koszty_operacyjne)
    x4 = x4 * 365 if x4 is not None else None
    x5 = _bezpieczne_dzielenie(d["przychody_sprzedazy"], d["aktywa_ogolem"])

    wskazniki = {"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5}

    if None in (x1, x2, x3, x4, x5):
        return None, "Brak danych do obliczenia", KOLOR_BLAD, wskazniki

    z = 0.605 + 0.681 * x1 - 0.0196 * x2 + 0.00969 * x3 + 0.000672 * x4 + 0.157 * x5

    if z < 0:
        interp, kolor = "Zagrożony upadłością", KOLOR_ZAGROZONY
    elif z <= 0.1:
        interp, kolor = "Strefa niepewności (szara)", KOLOR_SZARY
    else:
        interp, kolor = "Sytuacja bezpieczna", KOLOR_BEZPIECZNY

    return round(z, 4), interp, kolor, wskazniki


def model_gajdka_stos(d: Dict[str, float]) -> Tuple:
    """
    Model J. Gajdki i S. Stosa.
    Z = 0.7732059 - 0.0856425*X1 + 0.0007747*X2 + 0.9220985*X3 + 0.6535995*X4 - 0.594687*X5

    X1 = przychody ze sprzedaży / aktywa ogółem
    X2 = (zobowiązania krótkoterminowe / koszty operacyjne) * 365
    X3 = wynik finansowy netto / aktywa ogółem
    X4 = wynik brutto / przychody ze sprzedaży
    X5 = zobowiązania ogółem / aktywa ogółem

    Strefy: Z < 0.45 zagrożony | Z >= 0.45 bezpieczny
    """
    # Koszty operacyjne — preferuj z RZiS, fallback Przychody − EBIT, guard
    # gdy wynik <= 0 (firma deficytowa) → użyj samych przychodów.
    koszty_operacyjne = d.get("koszty_operacyjne")
    if not koszty_operacyjne or koszty_operacyjne <= 0:
        koszty_operacyjne = d["przychody_sprzedazy"] - d["wynik_operacyjny"]
    if koszty_operacyjne <= 0:
        koszty_operacyjne = max(d["przychody_sprzedazy"], 1e-9)
    # Wynik brutto = Pretax Income (zob. komentarz w model_maczynskiej).
    wynik_brutto = d.get("wynik_brutto") or (d["wynik_finansowy_netto"] + d["koszty_finansowe"])

    x1 = _bezpieczne_dzielenie(d["przychody_sprzedazy"], d["aktywa_ogolem"])
    x2 = _bezpieczne_dzielenie(d["zobowiazania_krotkoterm"], koszty_operacyjne)
    x2 = x2 * 365 if x2 is not None else None
    x3 = _bezpieczne_dzielenie(d["wynik_finansowy_netto"], d["aktywa_ogolem"])
    x4 = _bezpieczne_dzielenie(wynik_brutto, d["przychody_sprzedazy"])
    x5 = _bezpieczne_dzielenie(d["zobowiazania_ogolem"], d["aktywa_ogolem"])

    wskazniki = {"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5}

    if None in (x1, x2, x3, x4, x5):
        return None, "Brak danych do obliczenia", KOLOR_BLAD, wskazniki

    z = (0.7732059 - 0.0856425 * x1 + 0.0007747 * x2
         + 0.9220985 * x3 + 0.6535995 * x4 - 0.594687 * x5)

    if z < 0.45:
        interp, kolor = "Zagrożony upadłością", KOLOR_ZAGROZONY
    else:
        interp, kolor = "Sytuacja bezpieczna", KOLOR_BEZPIECZNY

    return round(z, 4), interp, kolor, wskazniki


def model_poznanski(d: Dict[str, float]) -> Tuple:
    """
    Model poznański (Hamrol, Czajka, Piechocki).
    FD = 3.562*X1 + 1.588*X2 + 4.288*X3 + 6.719*X4 - 2.368

    X1 = wynik finansowy netto / aktywa ogółem
    X2 = (aktywa obrotowe - zapasy proxy) / zobowiązania krótkoterminowe (płynność szybka)
    X3 = kapitał stały (kap. własny + zob. długoterm.) / aktywa ogółem
    X4 = wynik finansowy ze sprzedaży / przychody ze sprzedaży

    W braku zapasów używamy aktywów obrotowych (uproszczenie).
    Strefy: FD < 0 zagrożony | FD >= 0 bezpieczny
    """
    # Zobowiązania długoterminowe — pobieramy z bilansu (Total Non Current
    # Liabilities); dla danych ręcznych bez tego pola fallback na różnicę
    # zob. ogółem − zob. krótkoterm. zaszyty w gpw_data._mapuj_okres.
    zob_dlugoterm = d.get("zobowiazania_dlugoterm")
    if zob_dlugoterm is None:
        zob_dlugoterm = max(d["zobowiazania_ogolem"] - d["zobowiazania_krotkoterm"], 0)
    kapital_staly = d["kapital_wlasny"] + zob_dlugoterm

    # X2 to wskaźnik PŁYNNOŚCI SZYBKIEJ (quick ratio) — zapasy są wyłączone
    # bo są najmniej płynnym składnikiem aktywów obrotowych.
    aktywa_szybkie = d["aktywa_obrotowe"] - (d.get("zapasy") or 0)

    x1 = _bezpieczne_dzielenie(d["wynik_finansowy_netto"], d["aktywa_ogolem"])
    x2 = _bezpieczne_dzielenie(aktywa_szybkie, d["zobowiazania_krotkoterm"])
    x3 = _bezpieczne_dzielenie(kapital_staly, d["aktywa_ogolem"])
    x4 = _bezpieczne_dzielenie(d["wynik_operacyjny"], d["przychody_sprzedazy"])

    wskazniki = {"X1": x1, "X2": x2, "X3": x3, "X4": x4}

    if None in (x1, x2, x3, x4):
        return None, "Brak danych do obliczenia", KOLOR_BLAD, wskazniki

    fd = 3.562 * x1 + 1.588 * x2 + 4.288 * x3 + 6.719 * x4 - 2.368

    if fd < 0:
        interp, kolor = "Zagrożony upadłością", KOLOR_ZAGROZONY
    else:
        interp, kolor = "Sytuacja bezpieczna", KOLOR_BEZPIECZNY

    return round(fd, 4), interp, kolor, wskazniki


MODELE = {
    "Altman (1968)": {
        "func": model_altman_1968,
        "opis": "Klasyczny model Z-score dla spółek notowanych. 5 wskaźników.",
        "progi": {"zagrozony": 1.81, "bezpieczny": 2.99},
    },
    "Altman Z' (1983)": {
        "func": model_altman_z_prim,
        "opis": "Wersja Altmana dla spółek nienotowanych. Lepiej dopasowany do polskich realiów.",
        "progi": {"zagrozony": 1.23, "bezpieczny": 2.90},
    },
    "Mączyńska (INE PAN)": {
        "func": model_maczynskiej,
        "opis": "Polski model 6-wskaźnikowy E. Mączyńskiej (INE PAN, 1994).",
        "progi": {"zagrozony": 0.0, "bezpieczny": 1.0},
    },
    "Mączyńska Model E (2004)": {
        "func": model_maczynska_e,
        "opis": "Drugi wariant Mączyńskiej (INE PAN), 5-zmienny. Skuteczność ok. 92% na 1 rok przed upadłością.",
        "progi": {"zagrozony": 0.0, "bezpieczny": 0.0},
    },
    "Hołda (2001)": {
        "func": model_holda,
        "opis": "Polski model A. Hołdy oparty o dane polskich spółek z lat 90-tych.",
        "progi": {"zagrozony": 0.0, "bezpieczny": 0.1},
    },
    "Gajdka-Stos": {
        "func": model_gajdka_stos,
        "opis": "Polski model J. Gajdki i S. Stosa. Próg odcięcia 0.45.",
        "progi": {"zagrozony": 0.45, "bezpieczny": 0.45},
    },
    "Poznański (Hamrol)": {
        "func": model_poznanski,
        "opis": "Polski model poznański (Hamrol, Czajka, Piechocki). Próg odcięcia 0.0.",
        "progi": {"zagrozony": 0.0, "bezpieczny": 0.0},
    },
}


def policz_wszystkie_modele(dane: Dict[str, float]) -> Dict[str, Dict]:
    """Oblicza wszystkie zarejestrowane modele i zwraca słownik wyników."""
    wyniki = {}
    for nazwa, info in MODELE.items():
        wynik, interp, kolor, wskazniki = info["func"](dane)
        wyniki[nazwa] = {
            "wynik": wynik,
            "interpretacja": interp,
            "kolor": kolor,
            "wskazniki": wskazniki,
            "opis": info["opis"],
            "progi": info["progi"],
        }
    return wyniki
