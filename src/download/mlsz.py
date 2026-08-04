import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

SEASONS = {
    "26-27": {"league_id": 67, "season_id": 33586, "rounds": 33},
    "25-26": {"league_id": 65, "season_id": 31362, "rounds": 33},
    "24-25": {"league_id": 63, "season_id": 29213, "rounds": 33},
    "23-24": {"league_id": 61, "season_id": 27254, "rounds": 33},
}

NEXT_SEASON = "26-27"
HISTORICAL_SEASONS = [s for s in SEASONS if s != NEXT_SEASON]


def download_season(season: str, save: bool = True) -> pd.DataFrame:
    """Download all match results for a given NB1 season from MLSZ adatbank.

    Args:
        season: Season key, one of "25-26", "24-25", "23-24".
        save: If True, saves the results to an Excel file in the project root.

    Returns:
        DataFrame with columns: home_team, away_team, HomeGoal, AwayGoal
    """
    if season not in SEASONS:
        raise ValueError(f"Unknown season '{season}'. Available: {list(SEASONS.keys())}")

    cfg = SEASONS[season]
    results = []

    for i in range(cfg["rounds"]):
        url = f"https://adatbank.mlsz.hu/league/{cfg['league_id']}/0/{cfg['season_id']}/{i+1}.html"
        print(f"Fetching round {i+1}/{cfg['rounds']}: {url}")
        response = requests.get(url)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        box = soup.find("div", class_=["box", "box-1"])
        schedules = box.find_all("div", class_="schedule") if box else []
        for sched in schedules:
            home_team = sched.find("div", class_="home_team")
            home_team_name = home_team.get_text(strip=True) if home_team else None

            away_team = sched.find("div", class_="away_team")
            away_team_name = away_team.get_text(strip=True) if away_team else None

            result_span = sched.find("span", class_="schedule-points")
            result = result_span.get_text(strip=True) if result_span else None

            results.append({
                "home_team": home_team_name,
                "away_team": away_team_name,
                "result": result,
            })

    df = pd.DataFrame(results)
    df[["HomeGoal", "-", "AwayGoal"]] = df["result"].str.split(" ", expand=True)
    df.drop(columns=["-", "result"], inplace=True)
    df["HomeGoal"] = df["HomeGoal"].astype(int)
    df["AwayGoal"] = df["AwayGoal"].astype(int)

    if save:
        os.makedirs(DATA_DIR, exist_ok=True)
        filename = os.path.join(DATA_DIR, f"NB1_{season.replace('-', '_')}.xlsx")
        df.to_excel(filename)
        print(f"Saved {len(df)} matches to {filename}")

    return df


def download_fixtures(season: str, save: bool = True) -> pd.DataFrame:
    """Download the fixture schedule for a season (without requiring results).

    Works for seasons where the schedule is published but matches may not
    have been played yet. Matches that have been played will include scores.

    Args:
        season: Season key, e.g. "25-26", "26-27". If not in SEASONS, you must
                provide the URL params via add_season() first.
        save: If True, saves the fixtures to an Excel file.

    Returns:
        DataFrame with columns: round, home_team, away_team, HomeGoal, AwayGoal.
        HomeGoal/AwayGoal will be NaN for unplayed matches.
    """
    if season not in SEASONS:
        raise ValueError(f"Unknown season '{season}'. Available: {list(SEASONS.keys())}")

    cfg = SEASONS[season]
    fixtures = []

    for i in range(cfg["rounds"]):
        url = f"https://adatbank.mlsz.hu/league/{cfg['league_id']}/0/{cfg['season_id']}/{i+1}.html"
        print(f"Fetching round {i+1}/{cfg['rounds']}: {url}")
        response = requests.get(url)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        box = soup.find("div", class_=["box", "box-1"])
        schedules = box.find_all("div", class_="schedule") if box else []
        for sched in schedules:
            home_team = sched.find("div", class_="home_team")
            home_team_name = home_team.get_text(strip=True) if home_team else None

            away_team = sched.find("div", class_="away_team")
            away_team_name = away_team.get_text(strip=True) if away_team else None

            result_span = sched.find("span", class_="schedule-points")
            result = result_span.get_text(strip=True) if result_span else None

            home_goal = None
            away_goal = None
            if result and " " in result:
                parts = result.split(" ")
                if len(parts) >= 3:
                    try:
                        home_goal = int(parts[0])
                        away_goal = int(parts[2])
                    except ValueError:
                        pass

            fixtures.append({
                "round": i + 1,
                "home_team": home_team_name,
                "away_team": away_team_name,
                "HomeGoal": home_goal,
                "AwayGoal": away_goal,
            })

    df = pd.DataFrame(fixtures)

    if save:
        os.makedirs(DATA_DIR, exist_ok=True)
        filename = os.path.join(DATA_DIR, f"NB1_fixtures_{season.replace('-', '_')}.xlsx")
        df.to_excel(filename)
        print(f"Saved {len(df)} fixtures to {filename}")

    return df


def add_season(season: str, league_id: int, season_id: int, rounds: int):
    """Register a new season so download functions can use it.

    Args:
        season: Season key, e.g. "26-27".
        league_id: MLSZ league ID from the URL.
        season_id: MLSZ season ID from the URL.
        rounds: Number of rounds in the season.
    """
    SEASONS[season] = {"league_id": league_id, "season_id": season_id, "rounds": rounds}


def download_all_seasons(save: bool = True) -> dict[str, pd.DataFrame]:
    """Download all historical NB1 seasons (excludes next season).

    Returns:
        Dict mapping season key to DataFrame.
    """
    return {season: download_season(season, save=save) for season in HISTORICAL_SEASONS}
