# MatchAnalysis

# NB1 Match Analysis

Magyar labdarúgó NB1 bajnokság elemzése Dixon-Coles modellel és Monte Carlo szimulációval.

## Áttekintés

Ez a projekt az utolsó 3 év NB1-es mérkőzésadatait használja fel egy Dixon-Coles statisztikai modell felépítéséhez, amely képes:

- **Mérkőzés kimenetelének predikciója** — gólmatrix valószínűségek (pl. 2-1 eredmény valószínűsége)
- **Szezon szimuláció** — Monte Carlo módszerrel a következő szezon végeredményének predikciója (bajnok, európai helyek, kiesők)

## Projekt struktúra

```
MatchAnalysis/
├── data/                          # Letöltött adatok (gitignored)
├── src/
│   ├── download/                  # MLSZ adatbank scraper
│   │   ├── __init__.py
│   │   └── mlsz.py               # download_season, download_fixtures
│   ├── preprocess/                # Adat tisztítás és összevonás
│   │   ├── __init__.py
│   │   └── clean.py              # merge_seasons, normalize_team_names
│   ├── models/                    # Dixon-Coles modell
│   │   ├── __init__.py
│   │   └── dixon_coles.py        # DixonColes osztály (fit, predict, score matrix)
│   ├── simulate/                  # Monte Carlo szimuláció
│   │   ├── __init__.py
│   │   └── monte_carlo.py        # simulate_season
│   └── pipeline.py               # Adatletöltés és előfeldolgozás
├── streamlit_app/                 # Streamlit webes alkalmazás
│   ├── app.py                    # Főoldal
│   └── pages/
│       └── dixson_coles.py       # Dixon-Coles oldal
├── pyproject.toml
└── .gitignore
```

## Telepítés

```bash
uv sync
```

## Használat

### 1. Adatok letöltése

A Streamlit alkalmazás futtatása előtt le kell tölteni az adatokat (3 történelmi szezon + következő szezon menetrendje):

```bash
uv run python -m src.pipeline
```

Ez a következő fájlokat hozza létre a `data/` mappában:

- `NB1_23_24.xlsx` — 2023/24 szezon eredmények
- `NB1_24_25.xlsx` — 2024/25 szezon eredmények
- `NB1_25_26.xlsx` — 2025/26 szezon eredmények
- `NB1_fixtures_26_27.xlsx` — 2026/27 szezon menetrendje

### 2. Streamlit alkalmazás indítása

```bash
uv run streamlit run streamlit_app/app.py
```

## Dixon-Coles modell

A Dixon-Coles modell a mérkőzés góljait független Poisson eloszlásként modellezi, a következő kiegészítésekkel:

- **Tau korrekciós tag** — a 0-0, 1-0, 0-1, 1-1 eredmények valószínűségét korrigálja, amelyeket az alap Poisson modell alulbecsül
- **Időbeli súlyozás (time decay)** — a frissebb mérkőzések nagyobb súllyal szerepelnek a modell illesztésében
- **Hazai pálya előny** — külön paraméter a hazai csapat előnyének modellezésére

A modell paraméterei:
- `attack` — támadóerő csapatonként
- `defense` — védekezőerő csapatonként
- `home_adv` — hazai pálya előny
- `rho` — Dixon-Coles korrekciós paraméter

### Promóciós csapatok kezelése

A feljutott csapatok (amelyek nem szerepeltek az elmúlt 3 szezonban) átlagos paramétereket kapnak (attack=0, defense=0), ami a ligaátlagnak felel meg.

## Monte Carlo szimuláció

A szimuláció a következő szezon menetrendjét használja:

1. A már lejátszott mérkőzések eredményei fixek
2. A még le nem játszott mérkőzéseket a Dixon-Coles modell predikciói alapján szimulálja (10 000 alkalommal)
3. Minden szimulációban kiszámolja a végső tabellát
4. Eredmény: valószínűség minden csapat számára minden pozícióra

## Szezonok és MLSZ azonosítók

| Szezon | League ID | Season ID | Fordulók |
|--------|-----------|-----------|----------|
| 2026/27 | 67 | 33586 | 33 |
| 2025/26 | 65 | 31362 | 33 |
| 2024/25 | 63 | 29213 | 33 |
| 2023/24 | 61 | 27254 | 33 |

## Függőségek

- `pandas` — adatkezelés
- `numpy` — numerikus számítások
- `scipy` — optimalizáció és Poisson eloszlás
- `requests` + `beautifulsoup4` — web scraping
- `streamlit` — webes alkalmazás
- `plotly` — interaktív vizualizáció
- `openpyxl` — Excel fájl kezelés