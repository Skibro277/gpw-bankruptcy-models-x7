"""
Walidacja statystyczna modeli dyskryminacyjnych predykcji upadłości.

Liczy dla każdego modelu, używając próby:
- POZYTYWNYCH (label=1): obserwacji rok-spółka z `backtest_data.UPADLOSCI`,
- NEGATYWNYCH (label=0): obserwacji z `kontrole_zdrowe.KONTROLE_ZDROWE`,

następujące miary diagnostyczne:
- Macierz pomyłek (TP / FN / FP / TN),
- Czułość (sensitivity / recall) = TP / (TP + FN) — % wykrytych upadłości,
- Specyficzność (specificity) = TN / (TN + FP) — % poprawnie sklasyf. zdrowych,
- Trafność (accuracy) = (TP+TN) / wszystkie,
- Błąd typu I (false positive rate) = FP / (FP+TN) — fałszywy alarm,
- Błąd typu II (false negative rate) = FN / (FN+TP) — przeoczona upadłość,
- AUC (Area Under ROC Curve) — z empirycznej krzywej ROC bez dodatkowych
  zależności (algorytm trapezoidalny + statystyka Manna-Whitneya).

Konwencja oceniania (czy model sygnalizuje zagrożenie):
- używamy progu odcięcia z `MODELE[nazwa]['progi']['zagrozony']`,
- spółka klasyfikowana jako "zagrożona" gdy `wynik < próg_zagrozony`,
- dla AUC interpretujemy NIŻSZY wynik = WIĘKSZE ryzyko upadłości
  (mnożymy score × −1, tak by wyższy = wyższe prawdopodobieństwo P=1).

UWAGA metodologiczna: liczność próby (15 upadłości × 16 zdrowych obserwacji)
jest niewielka — wyniki traktować jako orientacyjne. Pełna walidacja
wymagałaby setek obserwacji per klasa.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from backtest_data import UPADLOSCI, dane_w_tysiacach
from kontrole_zdrowe import KONTROLE_ZDROWE, dane_w_tysiacach_zdrowe
from models import MODELE


# ---------------------------------------------------------------------------
# Zbieranie obserwacji
# ---------------------------------------------------------------------------

def zbierz_obserwacje() -> List[Dict]:
    """Zwraca listę obserwacji do walidacji.

    Każda obserwacja: {
        "spolka": str, "rok": int, "label": 1|0,
        "klasa": "upadla"|"zdrowa", "dane": {pole: wartość_w_tys_PLN}
    }
    """
    obs: List[Dict] = []

    # Upadłości — label = 1
    for klucz, rec in UPADLOSCI.items():
        dane_lata = dane_w_tysiacach(klucz)
        for rok, d in dane_lata.items():
            obs.append({
                "spolka": rec["nazwa"],
                "ticker": rec["ticker"],
                "rok": rok,
                "label": 1,
                "klasa": "upadla",
                "dane": d,
            })

    # Zdrowe — label = 0
    for klucz, rec in KONTROLE_ZDROWE.items():
        dane_lata = dane_w_tysiacach_zdrowe(klucz)
        for rok, d in dane_lata.items():
            obs.append({
                "spolka": rec["nazwa"],
                "ticker": rec["ticker"],
                "rok": rok,
                "label": 0,
                "klasa": "zdrowa",
                "dane": d,
            })

    return obs


# ---------------------------------------------------------------------------
# Liczenie ROC / AUC bez zewnętrznych zależności
# ---------------------------------------------------------------------------

def krzywa_roc(scores_pos: List[float], scores_neg: List[float]) -> Tuple[List[float], List[float]]:
    """Empiryczna krzywa ROC.

    `scores_pos` — wartości score dla obserwacji upadłych (label=1),
    `scores_neg` — wartości score dla obserwacji zdrowych (label=0).
    KONWENCJA: WYŻSZY score = WYŻSZE prawdopodobieństwo upadłości.

    Zwraca (FPR_list, TPR_list) posortowane po rosnącym progu.
    """
    if not scores_pos or not scores_neg:
        return [0.0, 1.0], [0.0, 1.0]

    progi = sorted(set(scores_pos + scores_neg), reverse=True)
    fpr_list = [0.0]
    tpr_list = [0.0]

    n_pos = len(scores_pos)
    n_neg = len(scores_neg)

    for prog in progi:
        tp = sum(1 for s in scores_pos if s >= prog)
        fp = sum(1 for s in scores_neg if s >= prog)
        tpr_list.append(tp / n_pos)
        fpr_list.append(fp / n_neg)

    fpr_list.append(1.0)
    tpr_list.append(1.0)

    # Sortuj po FPR rosnąco (na potrzeby trapezowego AUC)
    pary = sorted(zip(fpr_list, tpr_list))
    fpr_sorted = [p[0] for p in pary]
    tpr_sorted = [p[1] for p in pary]
    return fpr_sorted, tpr_sorted


def auc_z_roc(fpr: List[float], tpr: List[float]) -> float:
    """AUC metodą trapezów."""
    if len(fpr) < 2:
        return 0.5
    area = 0.0
    for i in range(1, len(fpr)):
        dx = fpr[i] - fpr[i - 1]
        srednia_tpr = (tpr[i] + tpr[i - 1]) / 2.0
        area += dx * srednia_tpr
    return max(0.0, min(1.0, area))


# ---------------------------------------------------------------------------
# Metryki klasyfikacyjne dla pojedynczego modelu
# ---------------------------------------------------------------------------

def _czy_zagrozony_per_model(nazwa_modelu: str, wynik: Optional[float]) -> Optional[bool]:
    """True/False jeśli model uznałby spółkę za zagrożoną przy progu z MODELE.
    None gdy wynik niemożliwy do obliczenia."""
    if wynik is None:
        return None
    prog = MODELE[nazwa_modelu]["progi"]["zagrozony"]
    return wynik < prog


def metryki_modelu(
    nazwa_modelu: str, obserwacje: List[Dict]
) -> Dict:
    """Liczy macierz pomyłek + miary diagnostyczne dla pojedynczego modelu.

    Zwraca:
    {
        "model": str,
        "n_pozytywnych": int, "n_negatywnych": int,
        "tp": int, "fn": int, "fp": int, "tn": int, "n_brak": int,
        "czulosc": float (0..1) | None,
        "specyficznosc": float (0..1) | None,
        "trafnosc": float | None,
        "blad_typu_I": float | None,
        "blad_typu_II": float | None,
        "auc": float (0..1) | None,
        "roc_fpr": [float], "roc_tpr": [float],
        "scores_pos": [float], "scores_neg": [float],
    }
    """
    func = MODELE[nazwa_modelu]["func"]

    tp = fn = fp = tn = brak = 0
    scores_pos: List[float] = []
    scores_neg: List[float] = []

    for o in obserwacje:
        wynik, _interp, _kolor, _wsk = func(o["dane"])
        decyzja = _czy_zagrozony_per_model(nazwa_modelu, wynik)
        if decyzja is None:
            brak += 1
            continue

        # Zbieramy do ROC (transformacja: WYŻSZY score → WYŻSZE p(upadłość))
        score_dla_roc = -wynik  # niższy wynik modelu = większe ryzyko
        if o["label"] == 1:
            scores_pos.append(score_dla_roc)
            if decyzja:
                tp += 1
            else:
                fn += 1
        else:
            scores_neg.append(score_dla_roc)
            if decyzja:
                fp += 1
            else:
                tn += 1

    n_pos = tp + fn
    n_neg = fp + tn

    czulosc = tp / n_pos if n_pos else None
    specyficznosc = tn / n_neg if n_neg else None
    trafnosc = (tp + tn) / (n_pos + n_neg) if (n_pos + n_neg) else None
    blad_I = fp / n_neg if n_neg else None
    blad_II = fn / n_pos if n_pos else None

    fpr, tpr = krzywa_roc(scores_pos, scores_neg)
    auc = auc_z_roc(fpr, tpr) if scores_pos and scores_neg else None

    return {
        "model": nazwa_modelu,
        "n_pozytywnych": n_pos,
        "n_negatywnych": n_neg,
        "tp": tp, "fn": fn, "fp": fp, "tn": tn,
        "n_brak": brak,
        "czulosc": czulosc,
        "specyficznosc": specyficznosc,
        "trafnosc": trafnosc,
        "blad_typu_I": blad_I,
        "blad_typu_II": blad_II,
        "auc": auc,
        "roc_fpr": fpr,
        "roc_tpr": tpr,
        "scores_pos": scores_pos,
        "scores_neg": scores_neg,
    }


def metryki_wszystkich_modeli(obserwacje: Optional[List[Dict]] = None) -> Dict[str, Dict]:
    """Liczy metryki dla każdego zarejestrowanego modelu z `MODELE`."""
    if obserwacje is None:
        obserwacje = zbierz_obserwacje()
    return {
        nazwa: metryki_modelu(nazwa, obserwacje) for nazwa in MODELE.keys()
    }


# ---------------------------------------------------------------------------
# Pomocniczy: ranking modeli po wybranej metryce
# ---------------------------------------------------------------------------

def ranking_po_metryce(
    metryki: Dict[str, Dict], metryka: str = "auc"
) -> List[Tuple[str, float]]:
    """Zwraca listę (model, wartość) posortowaną malejąco po metryce."""
    pary = []
    for nazwa, m in metryki.items():
        v = m.get(metryka)
        if v is not None:
            pary.append((nazwa, v))
    pary.sort(key=lambda x: x[1], reverse=True)
    return pary
