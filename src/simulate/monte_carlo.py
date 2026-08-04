import numpy as np
import pandas as pd


def simulate_season(model, fixtures: pd.DataFrame, n_simulations: int = 10000) -> pd.DataFrame:
    """Simulate a full season using Monte Carlo with a fitted Dixon-Coles model.

    Args:
        model: A fitted DixonColes model instance.
        fixtures: DataFrame with columns: home_team, away_team.
                  Can optionally include round, HomeGoal, AwayGoal for matches
                  already played (those scores will be used directly).
        n_simulations: Number of simulated seasons.

    Returns:
        DataFrame with columns: team, avg_points, avg_position, champion_prob,
        top4_prob, relegation_prob.
    """
    teams = sorted(set(fixtures["home_team"].unique()) | set(fixtures["away_team"].unique()))
    n_teams = len(teams)

    # Separate played matches from unplayed ones
    played = fixtures.dropna(subset=["HomeGoal", "AwayGoal"]) if "HomeGoal" in fixtures.columns else pd.DataFrame()
    unplayed = fixtures[fixtures["HomeGoal"].isna() | fixtures["AwayGoal"].isna()] if "HomeGoal" in fixtures.columns else fixtures

    # Precompute played match results
    played_results = []
    for _, row in played.iterrows():
        hg, ag = int(row["HomeGoal"]), int(row["AwayGoal"])
        if hg > ag:
            played_results.append(("H", row["home_team"], row["away_team"]))
        elif hg == ag:
            played_results.append(("D", row["home_team"], row["away_team"]))
        else:
            played_results.append(("A", row["home_team"], row["away_team"]))

    # Precompute probability matrices for unplayed matches
    unplayed_probs = []
    for _, row in unplayed.iterrows():
        home, away = row["home_team"], row["away_team"]
        prob = model.predict_match(home, away)
        p_home = np.tril(prob, -1).sum()
        p_draw = np.trace(prob)
        unplayed_probs.append((home, away, p_home, p_draw))

    points_total = {team: 0 for team in teams}
    positions_total = {team: 0 for team in teams}
    champion_count = {team: 0 for team in teams}
    top4_count = {team: 0 for team in teams}
    relegation_count = {team: 0 for team in teams}
    position_counts = {team: [0] * n_teams for team in teams}

    for sim in range(n_simulations):
        points = {team: 0 for team in teams}

        # Apply played match results
        for outcome, home, away in played_results:
            if outcome == "H":
                points[home] += 3
            elif outcome == "D":
                points[home] += 1
                points[away] += 1
            else:
                points[away] += 3

        # Simulate unplayed matches
        for home, away, p_home, p_draw in unplayed_probs:
            r = np.random.random()
            if r < p_home:
                points[home] += 3
            elif r < p_home + p_draw:
                points[home] += 1
                points[away] += 1
            else:
                points[away] += 3

        table = sorted(points.items(), key=lambda x: -x[1])
        for pos, (team, pts) in enumerate(table):
            points_total[team] += pts
            positions_total[team] += pos + 1
            position_counts[team][pos] += 1
            if pos == 0:
                champion_count[team] += 1
            if pos < 4:
                top4_count[team] += 1
            if pos >= n_teams - 2:
                relegation_count[team] += 1

    results = []
    for team in teams:
        results.append({
            "team": team,
            "avg_points": points_total[team] / n_simulations,
            "avg_position": positions_total[team] / n_simulations,
            "champion_prob": champion_count[team] / n_simulations,
            "top4_prob": top4_count[team] / n_simulations,
            "relegation_prob": relegation_count[team] / n_simulations,
            "position_probs": [c / n_simulations for c in position_counts[team]],
        })

    df = pd.DataFrame(results).sort_values("avg_points", ascending=False)
    df.reset_index(drop=True, inplace=True)
    return df
