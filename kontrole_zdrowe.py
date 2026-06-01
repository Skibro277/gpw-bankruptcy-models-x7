"""
Kontrolne dane finansowe — zdrowe spółki giełdowe (próba referencyjna
do walidacji statystycznej modeli dyskryminacyjnych).

Dobór: spółki notowane na GPW, które w okresach pokazanych poniżej:
- nie złożyły wniosku o upadłość/restrukturyzację w 3 latach po,
- miały dodatni wynik netto, dodatni kapitał własny i rosnące przychody,
- nie były objęte sankcjami audytora.

Wartości zaokrąglone do mln PLN (zgodnie z konwencją modułu
backtest_data.py — w aplikacji mnożone × 1000 → tysiące PLN).

Cel: dostarczyć "klasę negatywną" (label = 0, NIE upadłość) do liczenia
specyficzności, błędu typu I oraz krzywej ROC modeli.

Źródło: skonsolidowane sprawozdania roczne emitentów (ESPI), Notoria.
Wartości celowo uśrednione/zaokrąglone — służą walidacji metodologicznej,
nie księgowej.
"""

# Schemat identyczny jak w backtest_data.UPADLOSCI:
# klucz: { ticker, nazwa, sektor, lata: { rok: {pole: wartość_w_mln_pln} } }

KONTROLE_ZDROWE = {
    "Dino": {
        "ticker": "DNP.WA",
        "nazwa": "Dino Polska S.A.",
        "sektor": "Handel detaliczny — spożywczy",
        "uwagi": "Dynamiczny wzrost organiczny, dodatnia rentowność, "
                 "konserwatywne finansowanie.",
        "lata": {
            2021: dict(
                przychody_sprzedazy=13_356, przychody_rok_poprzedni=10_011,
                wynik_operacyjny=1_018, wynik_finansowy_netto=805,
                wynik_brutto_skumulowany=2_640,
                aktywa_ogolem=6_240, aktywa_obrotowe=2_120, majatek_trwaly=4_120,
                kapital_obrotowy=210,
                zobowiazania_ogolem=3_580, zobowiazania_krotkoterm=1_910,
                kapital_wlasny=2_660, kapital_zakladowy=10,
                amortyzacja=412, koszty_finansowe=72,
            ),
            2022: dict(
                przychody_sprzedazy=19_801, przychody_rok_poprzedni=13_356,
                wynik_operacyjny=1_530, wynik_finansowy_netto=1_171,
                wynik_brutto_skumulowany=3_810,
                aktywa_ogolem=8_280, aktywa_obrotowe=2_690, majatek_trwaly=5_590,
                kapital_obrotowy=380,
                zobowiazania_ogolem=4_490, zobowiazania_krotkoterm=2_310,
                kapital_wlasny=3_790, kapital_zakladowy=10,
                amortyzacja=560, koszty_finansowe=118,
            ),
        },
    },
    "KGHM": {
        "ticker": "KGH.WA",
        "nazwa": "KGHM Polska Miedź S.A.",
        "sektor": "Górnictwo / metale przemysłowe",
        "uwagi": "Stabilny duży gracz; pokazane lata ze średnimi cenami miedzi.",
        "lata": {
            2021: dict(
                przychody_sprzedazy=29_803, przychody_rok_poprzedni=23_632,
                wynik_operacyjny=8_120, wynik_finansowy_netto=6_177,
                wynik_brutto_skumulowany=14_280,
                aktywa_ogolem=46_500, aktywa_obrotowe=14_120, majatek_trwaly=32_380,
                kapital_obrotowy=4_120,
                zobowiazania_ogolem=22_310, zobowiazania_krotkoterm=10_050,
                kapital_wlasny=24_190, kapital_zakladowy=2_000,
                amortyzacja=2_780, koszty_finansowe=420,
            ),
            2022: dict(
                przychody_sprzedazy=33_847, przychody_rok_poprzedni=29_803,
                wynik_operacyjny=5_840, wynik_finansowy_netto=4_786,
                wynik_brutto_skumulowany=18_950,
                aktywa_ogolem=49_120, aktywa_obrotowe=14_810, majatek_trwaly=34_310,
                kapital_obrotowy=4_320,
                zobowiazania_ogolem=22_680, zobowiazania_krotkoterm=10_490,
                kapital_wlasny=26_440, kapital_zakladowy=2_000,
                amortyzacja=3_120, koszty_finansowe=510,
            ),
        },
    },
    "LPP": {
        "ticker": "LPP.WA",
        "nazwa": "LPP S.A.",
        "sektor": "Odzież / handel detaliczny",
        "uwagi": "Silna marka, ekspansja zagraniczna; rentowność netto >5%.",
        "lata": {
            2022: dict(
                przychody_sprzedazy=15_960, przychody_rok_poprzedni=14_031,
                wynik_operacyjny=1_485, wynik_finansowy_netto=920,
                wynik_brutto_skumulowany=3_410,
                aktywa_ogolem=10_580, aktywa_obrotowe=4_240, majatek_trwaly=6_340,
                kapital_obrotowy=820,
                zobowiazania_ogolem=6_980, zobowiazania_krotkoterm=3_420,
                kapital_wlasny=3_600, kapital_zakladowy=4,
                amortyzacja=520, koszty_finansowe=212,
            ),
            2023: dict(
                przychody_sprzedazy=17_410, przychody_rok_poprzedni=15_960,
                wynik_operacyjny=2_140, wynik_finansowy_netto=1_480,
                wynik_brutto_skumulowany=4_890,
                aktywa_ogolem=11_320, aktywa_obrotowe=4_810, majatek_trwaly=6_510,
                kapital_obrotowy=1_120,
                zobowiazania_ogolem=6_640, zobowiazania_krotkoterm=3_690,
                kapital_wlasny=4_680, kapital_zakladowy=4,
                amortyzacja=580, koszty_finansowe=198,
            ),
        },
    },
    "CDProjekt": {
        "ticker": "CDR.WA",
        "nazwa": "CD Projekt S.A.",
        "sektor": "Gry komputerowe / IT",
        "uwagi": "Niskie zadłużenie, wysokie rezerwy gotówki, wysoka marża netto.",
        "lata": {
            2021: dict(
                przychody_sprzedazy=888, przychody_rok_poprzedni=2_139,
                wynik_operacyjny=237, wynik_finansowy_netto=209,
                wynik_brutto_skumulowany=1_780,
                aktywa_ogolem=2_310, aktywa_obrotowe=1_540, majatek_trwaly=770,
                kapital_obrotowy=1_310,
                zobowiazania_ogolem=290, zobowiazania_krotkoterm=230,
                kapital_wlasny=2_020, kapital_zakladowy=100,
                amortyzacja=88, koszty_finansowe=8,
            ),
            2022: dict(
                przychody_sprzedazy=953, przychody_rok_poprzedni=888,
                wynik_operacyjny=362, wynik_finansowy_netto=350,
                wynik_brutto_skumulowany=2_130,
                aktywa_ogolem=2_640, aktywa_obrotowe=1_780, majatek_trwaly=860,
                kapital_obrotowy=1_490,
                zobowiazania_ogolem=320, zobowiazania_krotkoterm=260,
                kapital_wlasny=2_320, kapital_zakladowy=100,
                amortyzacja=98, koszty_finansowe=10,
            ),
        },
    },
    "InterCars": {
        "ticker": "CAR.WA",
        "nazwa": "Inter Cars S.A.",
        "sektor": "Dystrybucja części samochodowych",
        "uwagi": "Konsekwentny wzrost przychodów, dobra rotacja aktywów.",
        "lata": {
            2021: dict(
                przychody_sprzedazy=12_080, przychody_rok_poprzedni=10_117,
                wynik_operacyjny=802, wynik_finansowy_netto=586,
                wynik_brutto_skumulowany=2_180,
                aktywa_ogolem=8_120, aktywa_obrotowe=5_810, majatek_trwaly=2_310,
                kapital_obrotowy=1_580,
                zobowiazania_ogolem=5_290, zobowiazania_krotkoterm=4_230,
                kapital_wlasny=2_830, kapital_zakladowy=28,
                amortyzacja=210, koszty_finansowe=98,
            ),
            2022: dict(
                przychody_sprzedazy=14_618, przychody_rok_poprzedni=12_080,
                wynik_operacyjny=1_080, wynik_finansowy_netto=820,
                wynik_brutto_skumulowany=3_010,
                aktywa_ogolem=9_640, aktywa_obrotowe=6_910, majatek_trwaly=2_730,
                kapital_obrotowy=1_810,
                zobowiazania_ogolem=6_010, zobowiazania_krotkoterm=5_100,
                kapital_wlasny=3_630, kapital_zakladowy=28,
                amortyzacja=240, koszty_finansowe=148,
            ),
        },
    },
    "Kety": {
        "ticker": "KTY.WA",
        "nazwa": "Grupa Kęty S.A.",
        "sektor": "Aluminium / przetwórstwo",
        "uwagi": "Stabilna rentowność EBIT >10%, konserwatywne zadłużenie.",
        "lata": {
            2021: dict(
                przychody_sprzedazy=4_750, przychody_rok_poprzedni=3_606,
                wynik_operacyjny=712, wynik_finansowy_netto=556,
                wynik_brutto_skumulowany=1_280,
                aktywa_ogolem=3_320, aktywa_obrotowe=1_810, majatek_trwaly=1_510,
                kapital_obrotowy=620,
                zobowiazania_ogolem=1_620, zobowiazania_krotkoterm=1_190,
                kapital_wlasny=1_700, kapital_zakladowy=68,
                amortyzacja=160, koszty_finansowe=42,
            ),
            2022: dict(
                przychody_sprzedazy=5_644, przychody_rok_poprzedni=4_750,
                wynik_operacyjny=820, wynik_finansowy_netto=638,
                wynik_brutto_skumulowany=1_580,
                aktywa_ogolem=3_780, aktywa_obrotowe=2_080, majatek_trwaly=1_700,
                kapital_obrotowy=720,
                zobowiazania_ogolem=1_840, zobowiazania_krotkoterm=1_360,
                kapital_wlasny=1_940, kapital_zakladowy=68,
                amortyzacja=180, koszty_finansowe=58,
            ),
        },
    },
    "Budimex": {
        "ticker": "BDX.WA",
        "nazwa": "Budimex S.A.",
        "sektor": "Budownictwo (kontraktor generalny)",
        "uwagi": "Lider polskiego budownictwa drogowego, dodatnia rentowność.",
        "lata": {
            2021: dict(
                przychody_sprzedazy=7_926, przychody_rok_poprzedni=7_870,
                wynik_operacyjny=565, wynik_finansowy_netto=420,
                wynik_brutto_skumulowany=1_120,
                aktywa_ogolem=5_740, aktywa_obrotowe=4_230, majatek_trwaly=1_510,
                kapital_obrotowy=580,
                zobowiazania_ogolem=4_540, zobowiazania_krotkoterm=3_650,
                kapital_wlasny=1_200, kapital_zakladowy=145,
                amortyzacja=130, koszty_finansowe=58,
            ),
            2022: dict(
                przychody_sprzedazy=8_628, przychody_rok_poprzedni=7_926,
                wynik_operacyjny=465, wynik_finansowy_netto=336,
                wynik_brutto_skumulowany=1_320,
                aktywa_ogolem=6_180, aktywa_obrotowe=4_580, majatek_trwaly=1_600,
                kapital_obrotowy=620,
                zobowiazania_ogolem=4_910, zobowiazania_krotkoterm=3_960,
                kapital_wlasny=1_270, kapital_zakladowy=145,
                amortyzacja=148, koszty_finansowe=82,
            ),
        },
    },
    "Asseco": {
        "ticker": "ACP.WA",
        "nazwa": "Asseco Poland S.A.",
        "sektor": "IT / oprogramowanie",
        "uwagi": "Stabilne przychody powtarzalne (utrzymanie SLA), dobra struktura kap.",
        "lata": {
            2021: dict(
                przychody_sprzedazy=14_528, przychody_rok_poprzedni=12_190,
                wynik_operacyjny=1_460, wynik_finansowy_netto=460,
                wynik_brutto_skumulowany=3_120,
                aktywa_ogolem=15_320, aktywa_obrotowe=5_120, majatek_trwaly=10_200,
                kapital_obrotowy=1_180,
                zobowiazania_ogolem=8_910, zobowiazania_krotkoterm=3_940,
                kapital_wlasny=6_410, kapital_zakladowy=83,
                amortyzacja=520, koszty_finansowe=130,
            ),
            2022: dict(
                przychody_sprzedazy=17_117, przychody_rok_poprzedni=14_528,
                wynik_operacyjny=1_780, wynik_finansowy_netto=510,
                wynik_brutto_skumulowany=3_540,
                aktywa_ogolem=16_810, aktywa_obrotowe=5_580, majatek_trwaly=11_230,
                kapital_obrotowy=1_240,
                zobowiazania_ogolem=9_780, zobowiazania_krotkoterm=4_340,
                kapital_wlasny=7_030, kapital_zakladowy=83,
                amortyzacja=590, koszty_finansowe=210,
            ),
        },
    },
}


def lista_zdrowych():
    """Zwraca listę krotek (klucz, etykieta) — analogiczna do lista_upadlosci()."""
    return [
        (k, f"{v['nazwa']} — {v['sektor']}")
        for k, v in KONTROLE_ZDROWE.items()
    ]


def dane_w_tysiacach_zdrowe(spolka_klucz: str) -> dict:
    """Zwraca słownik {rok: {pole: wartość_w_tys_PLN}} dla zdrowej spółki."""
    spolka = KONTROLE_ZDROWE[spolka_klucz]
    return {
        rok: {pole: val * 1000 for pole, val in dane.items()}
        for rok, dane in spolka["lata"].items()
    }


def wszystkie_obserwacje_zdrowe():
    """Generator (klucz_spolki, rok, dict_dane_w_tys) dla wszystkich kontrol."""
    for klucz in KONTROLE_ZDROWE:
        dane = dane_w_tysiacach_zdrowe(klucz)
        for rok, d in dane.items():
            yield klucz, rok, d
