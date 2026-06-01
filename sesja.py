"""
Snapshot sesji — eksport/import pełnego stanu analizy do JSON.

Zapisuje:
- dane wejściowe (słownik POLA_FINANSOWE → wartości),
- wyniki wszystkich modeli (wartości + interpretacje + wskaźniki pośrednie),
- metadane: znacznik czasowy, wersja aplikacji, wersje modeli, hash danych,
- kontekst (tryb pracy, źródło danych, ticker spółki itp.).

Cel: REPRODUKOWALNOŚĆ. Snapshot pozwala odtworzyć dokładnie tę samą analizę
za miesiąc/rok (audyt due diligence, przeglądy KNF, raporty wewnętrzne TFI/DM).
Hash SHA-256 danych pozwala wykryć modyfikację po fakcie.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional


WERSJA_APLIKACJI = "1.1.0"

# Wersjonowanie modeli — istotne, żeby raport sprzed roku był identyfikowalny
# nawet po zmianie współczynników/progów.
WERSJE_MODELI: Dict[str, str] = {
    "Altman (1968)": "1968.v1",
    "Altman Z' (1983)": "1983.v1",
    "Mączyńska (INE PAN)": "1994.v1",
    "Mączyńska Model E (2004)": "2004.v1",
    "Hołda (2001)": "2001.v1",
    "Gajdka-Stos": "1996.v1",
    "Poznański (Hamrol)": "2004.v1",
}


def _hash_danych(dane: Dict[str, float]) -> str:
    """Deterministyczny SHA-256 hash z posortowanych par klucz=wartość.

    Hash obejmuje WYŁĄCZNIE dane wejściowe (nie metadane), żeby ten sam
    bilans zawsze dawał ten sam hash niezależnie od daty wygenerowania."""
    norm = json.dumps(
        {k: round(float(v), 6) for k, v in sorted(dane.items())},
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def _serializuj_wyniki(wyniki: Dict[str, Dict]) -> Dict[str, Dict]:
    """Konwertuje słownik wyników modeli na typowy JSON-compatible dict."""
    out: Dict[str, Dict] = {}
    for nazwa, info in wyniki.items():
        out[nazwa] = {
            "wersja_modelu": WERSJE_MODELI.get(nazwa, "nieznana"),
            "wynik": info.get("wynik"),
            "interpretacja": info.get("interpretacja"),
            "wskazniki": {
                k: (round(v, 6) if isinstance(v, (int, float)) else None)
                for k, v in (info.get("wskazniki") or {}).items()
            },
            "progi": info.get("progi"),
        }
    return out


def zbuduj_snapshot(
    dane: Dict[str, float],
    wyniki: Dict[str, Dict],
    tryb: str,
    autor: str,
    kontekst: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Tworzy snapshot sesji jako słownik gotowy do serializacji JSON.

    Argumenty:
    - dane     — słownik wejściowy {pole_finansowe: wartość_w_tys_PLN}
    - wyniki   — wynik `policz_wszystkie_modele(dane)`
    - tryb     — opisowa nazwa trybu pracy ("Pojedynczy okres" itp.)
    - autor    — kto wygenerował snapshot
    - kontekst — dodatkowe metadane (ticker, rok sprawozdawczy, źródło danych)
    """
    teraz = datetime.now(timezone.utc).isoformat(timespec="seconds")
    h = _hash_danych(dane)
    snapshot = {
        "wersja_formatu_snapshotu": "1.0",
        "wersja_aplikacji": WERSJA_APLIKACJI,
        "wygenerowano_utc": teraz,
        "tryb_pracy": tryb,
        "autor": autor,
        "kontekst": dict(kontekst or {}),
        "hash_danych_sha256": h,
        "wersje_modeli": dict(WERSJE_MODELI),
        "dane_wejsciowe": {k: float(v) for k, v in dane.items()},
        "wyniki": _serializuj_wyniki(wyniki),
    }
    return snapshot


def snapshot_jako_bytes(snapshot: Dict[str, Any]) -> bytes:
    """Serializuje snapshot do bajtów JSON (UTF-8, wcięcia 2)."""
    return json.dumps(
        snapshot, ensure_ascii=False, indent=2, sort_keys=False
    ).encode("utf-8")


def waliduj_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Sprawdza spójność wczytanego snapshotu.

    Zwraca słownik:
    {
        "ok": bool,
        "powod": str,
        "hash_zgadza_sie": bool,
        "obecny_hash": str,
        "oryginalny_hash": str,
        "ostrzezenia_wersji": [str],
    }
    """
    rec = {
        "ok": True,
        "powod": "OK",
        "hash_zgadza_sie": False,
        "obecny_hash": "",
        "oryginalny_hash": snapshot.get("hash_danych_sha256", ""),
        "ostrzezenia_wersji": [],
    }

    if not isinstance(snapshot, dict) or "dane_wejsciowe" not in snapshot:
        rec["ok"] = False
        rec["powod"] = "Brak pola 'dane_wejsciowe' — to nie jest snapshot."
        return rec

    obecny = _hash_danych(snapshot["dane_wejsciowe"])
    rec["obecny_hash"] = obecny
    rec["hash_zgadza_sie"] = (obecny == rec["oryginalny_hash"])
    if not rec["hash_zgadza_sie"]:
        rec["powod"] = (
            "Hash danych wejściowych nie zgadza się z zapisanym w snapshocie — "
            "dane mogły zostać zmodyfikowane po wygenerowaniu raportu."
        )
        rec["ok"] = False

    # Sprawdź zgodność wersji modeli
    zapisane = snapshot.get("wersje_modeli") or {}
    for nazwa, wersja in WERSJE_MODELI.items():
        zapisana_wersja = zapisane.get(nazwa)
        if zapisana_wersja and zapisana_wersja != wersja:
            rec["ostrzezenia_wersji"].append(
                f"Model '{nazwa}': snapshot v{zapisana_wersja}, aplikacja v{wersja}"
            )
        elif not zapisana_wersja:
            rec["ostrzezenia_wersji"].append(
                f"Model '{nazwa}': brak wersji w snapshocie"
            )

    return rec


def odczytaj_dane_ze_snapshotu(snapshot: Dict[str, Any]) -> Dict[str, float]:
    """Wyciąga sam słownik danych wejściowych — gotowe do użycia w widoku."""
    return {k: float(v) for k, v in (snapshot.get("dane_wejsciowe") or {}).items()}
