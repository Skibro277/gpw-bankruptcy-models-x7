"""
Screening — masowa analiza Z-score dla wielu spółek z GPW jednocześnie.

Pobiera dane z Yahoo Finance dla każdego tickera z WIG20 / mWIG40 (lub
wybranej listy), oblicza wszystkie modele dyskryminacyjne i tworzy ranking
ryzyka. Wynik to tabela z konsensusem modeli + flagi sektorów wykluczonych.

Wykorzystuje cachowane pobieranie z app.py poprzez parametr `pobierz_func`.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from gpw_data import (
    WIG20, MWIG40, SWIG80,
    SEKTORY_NIEKOMPATYBILNE, BRANZE_BANKI_UBEZP,
)
from models import MODELE, policz_wszystkie_modele


def _czy_zagrozony(interp: str) -> bool:
    """Czy interpretacja modelu wskazuje zagrożenie upadłością.

    Wszystkie modele w `models.py` zwracają DOKŁADNIE string
    'Zagrożony upadłością' jako sygnał zagrożenia. Dopasowanie podstring-owe
    z dużej litery jest jedynym poprawnym podejściem — wcześniej używana
    forma 'lower() in [zagroż, słaba, upadł]' dawała FAŁSZYWE POZYTYWY na
    interpretacjach typu 'Słaba kondycja, BRAK zagrożenia' (Mączyńska INE
    PAN, strefa szara) — bo zarówno 'słaba' jak i 'zagroż' (z 'zagrożenia')
    matchowały. To dawało rozbieżne wyniki konsensusu między widokiem GPW
    a Screeningiem dla tej samej spółki.
    """
    return "Zagrożony" in (interp or "")


def _sektor_niekompatybilny(sektor: str, branza: str) -> bool:
    if (sektor or "") in SEKTORY_NIEKOMPATYBILNE:
        return True
    if not branza:
        return False
    return any(b.lower() in branza.lower() for b in BRANZE_BANKI_UBEZP if b)


def skanuj_spolki(
    tickery_nazwy: List[Tuple[str, str]],
    pobierz_func: Callable[[str, int], Dict],
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    max_lat: int = 1,
) -> List[Dict]:
    """Skanuje listę spółek i zwraca listę wierszy z wynikami.

    `tickery_nazwy` — [(ticker, nazwa), ...]
    `pobierz_func(ticker, max_lat)` — funkcja pobierająca (najczęściej cachowana).
    `progress_callback(idx, total, ticker)` — opcjonalny callback dla paska postępu.
    `max_lat` — ile lat pobrać; do screeningu wystarczy 1 (najnowszy).

    Zwraca listę słowników:
    {
        ticker, nazwa, sektor, branza, rok, kapitalizacja,
        modele_obliczone (int), sygnaly_zagrozenia (int),
        konsensus ("ZAGROŻENIE"|"NEUTRALNY"|"BEZPIECZNY"|"SEKTOR WYKLUCZONY"|"BRAK DANYCH"),
        wyniki_per_model {nazwa: float|None},
        zagrozenia_per_model {nazwa: bool|None},
        blad: str|None,
    }
    """
    rezultaty: List[Dict] = []
    total = len(tickery_nazwy)

    for idx, (ticker, nazwa) in enumerate(tickery_nazwy, start=1):
        if progress_callback:
            progress_callback(idx, total, ticker)

        wiersz = {
            "ticker": ticker,
            "nazwa": nazwa,
            "sektor": "—",
            "branza": "—",
            "rok": None,
            "kapitalizacja": None,
            "modele_obliczone": 0,
            "sygnaly_zagrozenia": 0,
            "konsensus": "BRAK DANYCH",
            "wyniki_per_model": {n: None for n in MODELE.keys()},
            "zagrozenia_per_model": {n: None for n in MODELE.keys()},
            "blad": None,
        }

        try:
            pobrane = pobierz_func(ticker, max_lat)
        except Exception as e:
            wiersz["blad"] = f"Błąd pobierania: {e}"
            rezultaty.append(wiersz)
            continue

        if pobrane.get("blad"):
            wiersz["blad"] = pobrane["blad"]
            rezultaty.append(wiersz)
            continue

        wiersz["sektor"] = pobrane.get("sektor") or "—"
        wiersz["branza"] = pobrane.get("branza") or "—"
        wiersz["kapitalizacja"] = pobrane.get("kapitalizacja")

        if _sektor_niekompatybilny(pobrane.get("sektor"), pobrane.get("branza")):
            wiersz["konsensus"] = "SEKTOR WYKLUCZONY"
            rezultaty.append(wiersz)
            continue

        lata = pobrane.get("lata") or {}
        if not lata:
            wiersz["blad"] = "Brak danych rocznych"
            rezultaty.append(wiersz)
            continue

        rok = max(lata.keys())
        wiersz["rok"] = rok
        dane = lata[rok]["dane"]

        wyniki = policz_wszystkie_modele(dane)

        obliczone = 0
        zagr = 0
        for nazwa_m, info in wyniki.items():
            wiersz["wyniki_per_model"][nazwa_m] = info["wynik"]
            if info["wynik"] is None:
                wiersz["zagrozenia_per_model"][nazwa_m] = None
                continue
            obliczone += 1
            czy_zagr = _czy_zagrozony(info["interpretacja"])
            wiersz["zagrozenia_per_model"][nazwa_m] = czy_zagr
            if czy_zagr:
                zagr += 1

        wiersz["modele_obliczone"] = obliczone
        wiersz["sygnaly_zagrozenia"] = zagr
        if obliczone == 0:
            wiersz["konsensus"] = "BRAK DANYCH"
        elif zagr == 0:
            wiersz["konsensus"] = "BEZPIECZNY"
        elif zagr >= max(2, obliczone // 2 + 1):
            wiersz["konsensus"] = "ZAGROŻENIE"
        else:
            wiersz["konsensus"] = "NEUTRALNY"

        rezultaty.append(wiersz)

    return rezultaty


def filtruj_uniwersum(uniwersum: str) -> List[Tuple[str, str]]:
    """Zwraca listę (ticker, nazwa) dla wybranego uniwersum.

    `uniwersum` ∈ {
        "WIG20", "mWIG40", "sWIG80",
        "WIG20 + mWIG40", "WIG20 + mWIG40 + sWIG80"
    }.
    """
    if uniwersum == "WIG20":
        return list(WIG20)
    if uniwersum == "mWIG40":
        return list(MWIG40)
    if uniwersum == "sWIG80":
        return list(SWIG80)
    if uniwersum == "WIG20 + mWIG40 + sWIG80":
        return list(WIG20) + list(MWIG40) + list(SWIG80)
    return list(WIG20) + list(MWIG40)
