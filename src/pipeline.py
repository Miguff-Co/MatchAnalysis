from src.download import download_all_seasons, download_fixtures, add_season, SEASONS, DATA_DIR, NEXT_SEASON, HISTORICAL_SEASONS
from src.preprocess.clean import merge_seasons, normalize_team_names
import pandas as pd
import os


def ingest_data(save: bool = True) -> dict:
    """Download and preprocess all historical season data.

    Args:
        save: If True, saves raw data to Excel files.

    Returns:
        Dict with 'matches' (combined DataFrame) and 'seasons' (dict of per-season DataFrames).
    """
    print("Downloading historical data...")
    raw = download_all_seasons(save=save)

    print("Preprocessing...")
    df = merge_seasons(raw)
    df = normalize_team_names(df)

    return {"matches": df, "seasons": raw}


def ingest_fixtures(season: str, save: bool = True) -> pd.DataFrame:
    """Download and preprocess fixtures for a specific season.

    Args:
        season: Season key, e.g. "26-27".
        save: If True, saves fixtures to Excel.

    Returns:
        Preprocessed fixtures DataFrame.
    """
    print(f"Downloading fixtures for season {season}...")
    fixtures = download_fixtures(season, save=save)
    fixtures = normalize_team_names(fixtures)
    return fixtures


def ingest_all(save: bool = True) -> dict:
    """Download all data: 3 past seasons of results + current season fixtures.

    Downloads everything needed for the Streamlit app to run without
    any network calls during the session.

    Args:
        save: If True, saves all data to Excel files.

    Returns:
        Dict with 'matches', 'seasons', and 'fixtures' (current season).
    """
    data = ingest_data(save=save)

    fixtures = ingest_fixtures(NEXT_SEASON, save=save)

    return {**data, "fixtures": fixtures, "current_season": NEXT_SEASON}


def load_from_disk() -> dict:
    """Load previously downloaded data from Excel files.

    Returns:
        Dict with 'matches', 'seasons', and 'fixtures'.
    """
    seasons = {}
    for season_key in HISTORICAL_SEASONS:
        filename = os.path.join(DATA_DIR, f"NB1_{season_key.replace('-', '_')}.xlsx")
        if os.path.exists(filename):
            seasons[season_key] = pd.read_excel(filename, index_col=0)
            print(f"Loaded {filename}: {len(seasons[season_key])} matches")

    if not seasons:
        raise FileNotFoundError(
            f"No data files found in {DATA_DIR}. Run `uv run python -m src.pipeline` first to download data."
        )

    df = merge_seasons(seasons)
    df = normalize_team_names(df)

    fixtures = None
    fixtures_file = os.path.join(DATA_DIR, f"NB1_fixtures_{NEXT_SEASON.replace('-', '_')}.xlsx")
    if os.path.exists(fixtures_file):
        fixtures = pd.read_excel(fixtures_file, index_col=0)
        fixtures = normalize_team_names(fixtures)
        print(f"Loaded {fixtures_file}: {len(fixtures)} fixtures")

    return {
        "matches": df,
        "seasons": seasons,
        "fixtures": fixtures,
        "current_season": NEXT_SEASON,
    }


if __name__ == "__main__":
    ingest_all()
