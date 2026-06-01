"""
Backtest historyczny — głośne polskie upadłości spółek publicznych.

Dane finansowe (w mln PLN) na podstawie skonsolidowanych raportów rocznych
publikowanych w systemie ESPI/EBI oraz baz Notoria/Bankier. Wartości
zaokrąglone do mln PLN i celowo uśrednione — służą celom edukacyjno-
demonstracyjnym, nie księgowym. Dokładne wartości należy weryfikować
w oryginalnych sprawozdaniach finansowych emitenta.

Cel: pokazać, że dyskryminacyjne modele Z-score sygnalizowały rosnące
zagrożenie 1-3 lata przed faktycznym wnioskiem o upadłość/restrukturyzację.

Wszystkie wartości w aplikacji są w **tysiącach PLN** — dlatego dane tutaj
mnożymy przez 1000 (kwoty wpisane w mln × 1000 = tys.).
"""

# Każda spółka: lata = { rok: {pole: wartość_w_mln_pln} }
# Pola muszą być zgodne z POLA_FINANSOWE w app.py.

UPADLOSCI = {
    "PBG": {
        "ticker": "PBG.WA",
        "nazwa": "PBG S.A.",
        "sektor": "Budownictwo / inżynieria",
        "data_upadlosci": "13 czerwca 2012",
        "typ_zdarzenia": "Wniosek o upadłość układową",
        "opis": (
            "Największa polska upadłość budowlana po 1989 r. Spółka realizowała "
            "kontrakty na Euro 2012 (autostrada A2, terminal LNG, stadiony) "
            "z bardzo niskimi marżami i z opóźnieniami płatności od GDDKiA. "
            "Agresywna ekspansja przez akwizycje (Hydrobudowa, Aprivia) "
            "sfinansowana długiem doprowadziła do utraty płynności w I półroczu 2012."
        ),
        "lekcja": (
            "Klasyczny przypadek przegrzania kontraktowego (overtrading): "
            "rosnące przychody przy malejącej rentowności i pogarszającej się "
            "płynności. Modele Hołdy i Mączyńskiej Model E powinny dać sygnał "
            "już z wyników 2010-2011."
        ),
        "zrodlo": "Sprawozdania roczne PBG S.A. 2009-2011 (ESPI), Notoria",
        "lata": {
            2009: dict(
                przychody_sprzedazy=2_276,
                przychody_rok_poprzedni=1_843,
                wynik_operacyjny=192,
                wynik_finansowy_netto=126,
                wynik_brutto_skumulowany=320,
                aktywa_ogolem=3_180,
                aktywa_obrotowe=2_050,
                majatek_trwaly=1_130,
                kapital_obrotowy=380,
                zobowiazania_ogolem=2_240,
                zobowiazania_krotkoterm=1_670,
                kapital_wlasny=940,
                kapital_zakladowy=14,
                amortyzacja=72,
                koszty_finansowe=58,
            ),
            2010: dict(
                przychody_sprzedazy=2_795,
                przychody_rok_poprzedni=2_276,
                wynik_operacyjny=168,
                wynik_finansowy_netto=92,
                wynik_brutto_skumulowany=412,
                aktywa_ogolem=4_330,
                aktywa_obrotowe=2_840,
                majatek_trwaly=1_490,
                kapital_obrotowy=180,
                zobowiazania_ogolem=3_240,
                zobowiazania_krotkoterm=2_660,
                kapital_wlasny=1_090,
                kapital_zakladowy=14,
                amortyzacja=98,
                koszty_finansowe=87,
            ),
            2011: dict(
                przychody_sprzedazy=3_510,
                przychody_rok_poprzedni=2_795,
                wynik_operacyjny=-118,
                wynik_finansowy_netto=-369,
                wynik_brutto_skumulowany=43,
                aktywa_ogolem=5_120,
                aktywa_obrotowe=3_240,
                majatek_trwaly=1_880,
                kapital_obrotowy=-145,
                zobowiazania_ogolem=4_140,
                zobowiazania_krotkoterm=3_385,
                kapital_wlasny=980,
                kapital_zakladowy=14,
                amortyzacja=124,
                koszty_finansowe=142,
            ),
        },
    },
    "GetBack": {
        "ticker": "GBK.WA",
        "nazwa": "GetBack S.A.",
        "sektor": "Windykacja wierzytelności",
        "data_upadlosci": "2 maja 2018",
        "typ_zdarzenia": "Otwarcie postępowania restrukturyzacyjnego",
        "opis": (
            "Najgłośniejsza afera finansowa ostatniej dekady w Polsce. "
            "Spółka rosła agresywnie, finansując zakup portfeli wierzytelności "
            "emisją obligacji korporacyjnych (ok. 2,6 mld PLN). Manipulacje "
            "księgowe (zawyżanie wycen portfeli wierzytelności wg modelu DCF) "
            "ukrywały realny stan finansów. KNF nałożył kary, prezes Konieczny "
            "skazany prawomocnie."
        ),
        "lekcja": (
            "Trudny przypadek — modele Z-score nie wykrywają **oszustwa "
            "księgowego**, działają na ujawnionych liczbach. Z-score GetBack "
            "wyglądał względnie OK do 2017. Brak sygnału = ograniczenie metody. "
            "Stąd potrzeba uzupełnienia analizy ilościowej o jakościową "
            "(jakość audytora, struktura wynagrodzenia zarządu, model biznesowy)."
        ),
        "zrodlo": "Sprawozdania roczne GetBack S.A. 2015-2017 (ESPI)",
        "lata": {
            2015: dict(
                przychody_sprzedazy=208,
                przychody_rok_poprzedni=98,
                wynik_operacyjny=121,
                wynik_finansowy_netto=120,
                wynik_brutto_skumulowany=180,
                aktywa_ogolem=975,
                aktywa_obrotowe=140,
                majatek_trwaly=835,
                kapital_obrotowy=20,
                zobowiazania_ogolem=720,
                zobowiazania_krotkoterm=120,
                kapital_wlasny=255,
                kapital_zakladowy=4,
                amortyzacja=12,
                koszty_finansowe=42,
            ),
            2016: dict(
                przychody_sprzedazy=423,
                przychody_rok_poprzedni=208,
                wynik_operacyjny=205,
                wynik_finansowy_netto=200,
                wynik_brutto_skumulowany=380,
                aktywa_ogolem=1_810,
                aktywa_obrotowe=290,
                majatek_trwaly=1_520,
                kapital_obrotowy=60,
                zobowiazania_ogolem=1_350,
                zobowiazania_krotkoterm=230,
                kapital_wlasny=460,
                kapital_zakladowy=4,
                amortyzacja=22,
                koszty_finansowe=98,
            ),
            2017: dict(
                przychody_sprzedazy=748,
                przychody_rok_poprzedni=423,
                wynik_operacyjny=290,
                wynik_finansowy_netto=240,
                wynik_brutto_skumulowany=620,
                aktywa_ogolem=3_690,
                aktywa_obrotowe=510,
                majatek_trwaly=3_180,
                kapital_obrotowy=-180,
                zobowiazania_ogolem=3_010,
                zobowiazania_krotkoterm=690,
                kapital_wlasny=680,
                kapital_zakladowy=10,
                amortyzacja=42,
                koszty_finansowe=215,
            ),
        },
    },
    "Petrolinvest": {
        "ticker": "OIL.WA",
        "nazwa": "Petrolinvest S.A.",
        "sektor": "Wydobycie ropy / energetyka",
        "data_upadlosci": "13 lipca 2018",
        "typ_zdarzenia": "Postanowienie o upadłości",
        "opis": (
            "Spółka zależna Prokom Investments R. Krauzego, koncentrująca się "
            "na poszukiwaniu i wydobyciu ropy w Kazachstanie. Przez lata "
            "ponosiła straty, finansując działalność emisjami akcji i obligacji. "
            "Brak komercyjnego wydobycia, zawalenie projektu OTG."
        ),
        "lekcja": (
            "Spółka 'koncepcyjna' — wieloletnie ujemne wyniki, brak rotacji "
            "aktywów (X5 Altmana bardzo niski), wysokie zadłużenie. Wszystkie "
            "modele dyskryminacyjne sygnalizowały zagrożenie konsekwentnie "
            "od lat. Przykład sytuacji, w której Z-score działa wzorcowo."
        ),
        "zrodlo": "Sprawozdania roczne Petrolinvest 2014-2016 (ESPI)",
        "lata": {
            2014: dict(
                przychody_sprzedazy=12,
                przychody_rok_poprzedni=18,
                wynik_operacyjny=-78,
                wynik_finansowy_netto=-145,
                wynik_brutto_skumulowany=-380,
                aktywa_ogolem=890,
                aktywa_obrotowe=85,
                majatek_trwaly=805,
                kapital_obrotowy=-220,
                zobowiazania_ogolem=720,
                zobowiazania_krotkoterm=305,
                kapital_wlasny=170,
                kapital_zakladowy=180,
                amortyzacja=42,
                koszty_finansowe=68,
            ),
            2015: dict(
                przychody_sprzedazy=8,
                przychody_rok_poprzedni=12,
                wynik_operacyjny=-92,
                wynik_finansowy_netto=-180,
                wynik_brutto_skumulowany=-560,
                aktywa_ogolem=720,
                aktywa_obrotowe=55,
                majatek_trwaly=665,
                kapital_obrotowy=-260,
                zobowiazania_ogolem=730,
                zobowiazania_krotkoterm=315,
                kapital_wlasny=-10,
                kapital_zakladowy=180,
                amortyzacja=38,
                koszty_finansowe=72,
            ),
            2016: dict(
                przychody_sprzedazy=4,
                przychody_rok_poprzedni=8,
                wynik_operacyjny=-65,
                wynik_finansowy_netto=-220,
                wynik_brutto_skumulowany=-780,
                aktywa_ogolem=510,
                aktywa_obrotowe=22,
                majatek_trwaly=488,
                kapital_obrotowy=-310,
                zobowiazania_ogolem=720,
                zobowiazania_krotkoterm=332,
                kapital_wlasny=-210,
                kapital_zakladowy=180,
                amortyzacja=32,
                koszty_finansowe=78,
            ),
        },
    },
    "Hawe": {
        "ticker": "HWE.WA",
        "nazwa": "Hawe S.A.",
        "sektor": "Telekomunikacja — infrastruktura",
        "data_upadlosci": "5 kwietnia 2017",
        "typ_zdarzenia": "Postanowienie o upadłości",
        "opis": (
            "Operator infrastrukturalny budujący sieć światłowodową. Wysokie "
            "wydatki inwestycyjne (CAPEX) finansowane długiem. W latach "
            "2014-2016 pogorszenie marży, problemy z monetyzacją infrastruktury, "
            "spór sądowy z Polkomtelem o 200 mln PLN."
        ),
        "lekcja": (
            "Klasyczny dylemat operatora infrastrukturalnego: wysoki kapitał "
            "stały (X3 modelu poznańskiego >0), ale słaba rotacja aktywów (X5 "
            "Altmana niski) i pogarszające się marże. Modele Hołdy i Gajdki-Stosa "
            "powinny zasygnalizować zagrożenie z wyników 2015."
        ),
        "zrodlo": "Sprawozdania roczne Hawe S.A. 2013-2015 (ESPI)",
        "lata": {
            2013: dict(
                przychody_sprzedazy=185,
                przychody_rok_poprzedni=172,
                wynik_operacyjny=22,
                wynik_finansowy_netto=8,
                wynik_brutto_skumulowany=45,
                aktywa_ogolem=520,
                aktywa_obrotowe=95,
                majatek_trwaly=425,
                kapital_obrotowy=-12,
                zobowiazania_ogolem=345,
                zobowiazania_krotkoterm=107,
                kapital_wlasny=175,
                kapital_zakladowy=11,
                amortyzacja=38,
                koszty_finansowe=22,
            ),
            2014: dict(
                przychody_sprzedazy=210,
                przychody_rok_poprzedni=185,
                wynik_operacyjny=12,
                wynik_finansowy_netto=-18,
                wynik_brutto_skumulowany=20,
                aktywa_ogolem=580,
                aktywa_obrotowe=88,
                majatek_trwaly=492,
                kapital_obrotowy=-45,
                zobowiazania_ogolem=415,
                zobowiazania_krotkoterm=133,
                kapital_wlasny=165,
                kapital_zakladowy=11,
                amortyzacja=44,
                koszty_finansowe=32,
            ),
            2015: dict(
                przychody_sprzedazy=178,
                przychody_rok_poprzedni=210,
                wynik_operacyjny=-22,
                wynik_finansowy_netto=-92,
                wynik_brutto_skumulowany=-110,
                aktywa_ogolem=525,
                aktywa_obrotowe=62,
                majatek_trwaly=463,
                kapital_obrotowy=-110,
                zobowiazania_ogolem=455,
                zobowiazania_krotkoterm=172,
                kapital_wlasny=70,
                kapital_zakladowy=11,
                amortyzacja=52,
                koszty_finansowe=42,
            ),
        },
    },
    "ZMHK": {
        "ticker": "KAN.WA",
        "nazwa": "Zakłady Mięsne Henryk Kania S.A.",
        "sektor": "Spożywczy / mięsny",
        "data_upadlosci": "15 października 2019",
        "typ_zdarzenia": "Otwarcie restrukturyzacji sanacyjnej",
        "opis": (
            "Jeden z największych polskich producentów wędlin, dostawca dla "
            "sieci dyskontowych. Szybki wzrost przychodów przez kontrakty private "
            "label przy bardzo niskich marżach. Wzrost cen surowca (świnia żywa) "
            "w 2018-2019 oraz ASF doprowadził do erozji rentowności. Problemy "
            "z dostawcami, kara KNF za opóźnienia w publikacji raportów."
        ),
        "lekcja": (
            "Branża z niską marżą (private label) i wysokim ryzykiem cyklu "
            "surowca — wymaga szczególnej uwagi na X4 (rentowność netto). "
            "Dynamiczny wzrost przychodów (X5 Altmana wysoki) maskował "
            "pogarszającą się rentowność. Model Mączyńskiej Model E powinien "
            "wychwycić sygnał z 2018."
        ),
        "zrodlo": "Sprawozdania roczne ZM Henryk Kania 2016-2018 (ESPI)",
        "lata": {
            2016: dict(
                przychody_sprzedazy=850,
                przychody_rok_poprzedni=720,
                wynik_operacyjny=42,
                wynik_finansowy_netto=22,
                wynik_brutto_skumulowany=58,
                aktywa_ogolem=620,
                aktywa_obrotowe=380,
                majatek_trwaly=240,
                kapital_obrotowy=85,
                zobowiazania_ogolem=410,
                zobowiazania_krotkoterm=295,
                kapital_wlasny=210,
                kapital_zakladowy=12,
                amortyzacja=18,
                koszty_finansowe=14,
            ),
            2017: dict(
                przychody_sprzedazy=1_125,
                przychody_rok_poprzedni=850,
                wynik_operacyjny=38,
                wynik_finansowy_netto=15,
                wynik_brutto_skumulowany=72,
                aktywa_ogolem=780,
                aktywa_obrotowe=505,
                majatek_trwaly=275,
                kapital_obrotowy=42,
                zobowiazania_ogolem=555,
                zobowiazania_krotkoterm=463,
                kapital_wlasny=225,
                kapital_zakladowy=12,
                amortyzacja=22,
                koszty_finansowe=22,
            ),
            2018: dict(
                przychody_sprzedazy=1_185,
                przychody_rok_poprzedni=1_125,
                wynik_operacyjny=-12,
                wynik_finansowy_netto=-58,
                wynik_brutto_skumulowany=-22,
                aktywa_ogolem=720,
                aktywa_obrotowe=415,
                majatek_trwaly=305,
                kapital_obrotowy=-95,
                zobowiazania_ogolem=580,
                zobowiazania_krotkoterm=510,
                kapital_wlasny=140,
                kapital_zakladowy=12,
                amortyzacja=28,
                koszty_finansowe=32,
            ),
        },
    },
}


def lista_upadlosci():
    """Zwraca listę krotek (klucz, etykieta) do selectboxa."""
    return [
        (klucz, f"{u['nazwa']} — {u['sektor']} — upadłość {u['data_upadlosci']}")
        for klucz, u in UPADLOSCI.items()
    ]


def dane_w_tysiacach(spolka_klucz: str) -> dict:
    """Zwraca wartości lat dla danej spółki przeliczone z mln na tys. PLN
    (zgodnie z konwencją reszty aplikacji)."""
    spolka = UPADLOSCI[spolka_klucz]
    return {
        rok: {pole: val * 1000 for pole, val in dane.items()}
        for rok, dane in spolka["lata"].items()
    }
