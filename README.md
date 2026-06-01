# Bankruptcy Risk Calculator for Polish Listed Companies

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.56+-red?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

A Streamlit application implementing seven Polish and international discriminant bankruptcy prediction models (Z-score family). Built as a professional portfolio project targeting Polish brokerage houses and investment funds (TFI).

---

## Features

- **Live data from Yahoo Finance** — automatic fetching of financial statements for 116 companies from WIG20, mWIG40, and sWIG80 indices
- **Audit trail** — every fetched value shows its exact source row from Yahoo Finance (balance sheet, income statement, or cash flow)
- **Balance sheet validation** — automatic consistency checks with warnings for data quality issues
- **Manual entry & editing** — all financial fields are editable in the UI; changes immediately recalculate all models
- **Multi-year trend analysis** — up to 4 years of historical data with trend charts
- **Mass screening** — one-click scoring of up to 116 companies, ranked by risk consensus
- **Model validation** — empirical accuracy assessment (confusion matrix, ROC curves, AUC) on a sample of 31 observations (15 bankruptcies + 16 healthy)
- **Bankruptcy backtests** — historical case studies: PBG, GetBack, Petrolinvest, Hawe, ZM Henryk Kania — Z-scores 3 years before bankruptcy
- **Sensitivity analysis** — interactive sliders ±X%, tornado chart showing impact of individual balance sheet items on Altman Z'
- **PDF reports** — downloadable A4 reports with full methodology, source audit, and MAR/Regulation 2017/565 disclaimer
- **Session snapshots** — reproducible JSON exports with SHA-256 data hash for audit/due diligence purposes

---

## Implemented Models

| Model | Author(s) | Year | Variables | Cut-off |
|---|---|---|---|---|
| Altman Z-score | Edward I. Altman | 1968 | 5 | Z < 1.81 → distress |
| Altman Z' (private firms) | Edward I. Altman | 1983 | 5 | Z' < 1.23 → distress |
| Mączyńska INE PAN | Elżbieta Mączyńska | 1994 | 6 | W < 0 → distress |
| Mączyńska Model E | Elżbieta Mączyńska | 2004 | 5 | EM < 0 → distress |
| Hołda | Artur Hołda | 2001 | 5 | Z < 0 → distress |
| Gajdka-Stos | Jerzy Gajdka, Daniel Stos | 1996 | 5 | Z < 0.45 → distress |
| Poznański (Hamrol-Czajka-Piechocki) | Hamrol, Czajka, Piechocki | 2004 | 4 | FD < 0 → distress |

### Model Notes

- **Altman (1968)** — original Z-score for publicly traded manufacturing firms; X4 uses market capitalisation.
- **Altman Z' (1983)** — revised version for private firms; X4 uses book value of equity.
- **Mączyńska INE PAN (1994)** — estimated on Polish firms by the Institute of Economics, Polish Academy of Sciences; 6-variable model.
- **Mączyńska Model E (2004)** — second-generation Polish model, 5 variables, improved for Polish accounting standards.
- **Hołda (2001)** — estimated on Polish firms by Artur Hołda; X4 uses operating cost turnover ratio.
- **Gajdka-Stos (1996)** — Polish model using pretax income in X4; requires operating expenses for X2.
- **Poznański / Hamrol-Czajka-Piechocki (2004)** — 4-variable Polish model; X2 is the quick ratio (current assets minus inventory).

---

## Work Modes

The application offers 8 independent analysis modes accessible from the sidebar:

1. **Single period** — manual data entry for one fiscal year + PDF report + JSON snapshot
2. **Multi-year trend** — analysis across multiple years with trend charts
3. **GPW listed company (online)** — automatic data fetching for WIG20/mWIG40/sWIG80 companies
4. **WIG20/mWIG40/sWIG80 screening** — mass scanner with risk ranking and CSV export
5. **Model validation** — empirical accuracy assessment with ROC curves and AUC
6. **Bankruptcy backtest** — historical Polish bankruptcy case studies
7. **Sensitivity analysis** — interactive tornado chart for Altman Z'
8. **Methodology** — mathematical documentation (LaTeX), bibliography, and model limitations

---

## Installation & Running

```bash
# 1. Clone the repository
git clone https://github.com/your-username/bankruptcy-risk-calculator.git
cd bankruptcy-risk-calculator

# 2. Create a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
.venv\Scripts\activate.bat     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
streamlit run app.py
```

The application will open at `http://localhost:8501`.

No API keys or additional configuration are required.

---

## Data Source

Financial data is fetched from **Yahoo Finance** via the [`yfinance`](https://github.com/ranaroussi/yfinance) library.

**Important limitations:**

- Data quality for Polish companies may differ from official ESPI/ESEF filings. Always cross-check critical figures with the original annual reports.
- Banks, insurance companies, and other financial institutions are automatically flagged and excluded from the analysis — discriminant models were estimated on manufacturing and trading companies.
- Yahoo Finance occasionally returns missing or inconsistent rows (especially for smaller sWIG80 companies). The audit trail panel shows exactly which source row each value was taken from, or whether a fallback calculation was used.
- All monetary values are denominated in thousands (PLN or the company's reporting currency).

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Web framework | Streamlit |
| Financial data | yfinance |
| Data processing | pandas, numpy |
| Charts | Plotly |
| PDF generation | ReportLab (DejaVu Sans for Polish characters) |

---

## Project Structure

```
├── app.py               — Streamlit UI (forms, charts, 8 work modes)
├── models.py            — Calculation core; all 7 models registered in MODELE dict
├── gpw_data.py          — Yahoo Finance integration; XBRL-to-model field mapping; audit trail
├── screening.py         — Mass scanner with consensus scoring
├── walidacja.py         — Statistical validation: confusion matrix, ROC, AUC
├── backtest_data.py     — Historical bankruptcy case data (PBG, GetBack, etc.)
├── kontrole_zdrowe.py   — Healthy reference companies (Dino, KGHM, LPP, etc.)
├── sesja.py             — Session snapshot: JSON export with SHA-256 hash
├── raport_pdf.py        — PDF report generator (ReportLab + DejaVu Sans)
└── .streamlit/
    └── config.toml      — Streamlit server configuration
```

---

## Author

Arkadiusz Oczkowski
Licensed Securities Broker

- LinkedIn: www.linkedin.com/in/arkadiusz-o-12275639a
- GitHub: [github.com/your-username](https://github.com/your-username)

---

## Disclaimer

This application is for **educational and research purposes only**. Results should not be interpreted as investment advice or recommendations. The author is not liable for any decisions made on the basis of the outputs of this tool. See the in-app disclaimer for full MAR / Regulation (EU) 2017/565 notice.
