import pandas as pd


def normalize_team_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize team name encoding and naming variations across seasons.

    Args:
        df: DataFrame with home_team and away_team columns.

    Returns:
        DataFrame with normalized team names.
    """
    df = df.copy()
    # TODO: map encoding variants to canonical names
    return df


def merge_seasons(seasons: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Merge multiple season DataFrames into one, adding a season column.

    Args:
        seasons: Dict mapping season key to DataFrame.

    Returns:
        Combined DataFrame with an added 'season' column.
    """
    frames = []
    for season_key, df in seasons.items():
        df = df.copy()
        df["season"] = season_key
        frames.append(df)
    return pd.concat(frames, ignore_index=True)
