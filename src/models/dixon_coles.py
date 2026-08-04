import numpy as np
import pandas as pd
from scipy.optimize import minimize


class DixonColes:
    """Dixon-Coles model for football match prediction.

    Models home goals and away goals as independent Poisson variables
    with a low-score correction term (tau) for 0-0, 1-0, 0-1, 1-1 results.
    """

    def __init__(self, xi: float = 0.0018):
        """Initialize the model.

        Args:
            xi: Time decay parameter. Higher values weight recent matches more.
        """
        self.xi = xi
        self.params = None
        self.teams = None

    def fit(self, df: pd.DataFrame, max_goals: int = 10):
        """Fit the Dixon-Coles model to historical match data.

        Args:
            df: DataFrame with columns: home_team, away_team, HomeGoal, AwayGoal.
                Optionally a 'date' column for time decay weighting.
            max_goals: Maximum number of goals to consider in the probability matrix.
        """
        self.max_goals = max_goals
        self.teams = sorted(set(df["home_team"].unique()) | set(df["away_team"].unique()))
        n_teams = len(self.teams)
        team_idx = {team: i for i, team in enumerate(self.teams)}

        # Time decay weights
        if "date" in df.columns:
            dates = pd.to_datetime(df["date"])
            days_since = (dates.max() - dates).dt.days
            weights = np.exp(-self.xi * days_since)
        else:
            weights = np.ones(len(df))

        home_idx = df["home_team"].map(team_idx).values
        away_idx = df["away_team"].map(team_idx).values
        home_goals = df["HomeGoal"].values
        away_goals = df["AwayGoal"].values

        # Initial parameters: attack, defense (per team), home advantage, rho
        init = np.concatenate([
            np.zeros(n_teams),       # attack
            np.zeros(n_teams),       # defense
            [0.3],                   # home advantage
            [-0.1],                  # rho (correction)
        ])

        def neg_log_likelihood(params):
            attack = params[:n_teams]
            defense = params[n_teams:2*n_teams]
            home_adv = params[2*n_teams]
            rho = params[2*n_teams + 1]

            lambda_home = np.exp(attack[home_idx] + defense[away_idx] + home_adv)
            lambda_away = np.exp(attack[away_idx] + defense[home_idx])

            log_lik = weights * self._log_likelihood(
                home_goals, away_goals, lambda_home, lambda_away, rho
            )
            return -np.sum(log_lik)

        # Sum-to-zero constraint for identifiability
        constraints = [
            {"type": "eq", "fun": lambda p: np.sum(p[:n_teams])},
            {"type": "eq", "fun": lambda p: np.sum(p[n_teams:2*n_teams])},
        ]

        result = minimize(
            neg_log_likelihood, init,
            constraints=constraints,
            method="SLSQP",
        )

        self.params = {
            "attack": result.x[:n_teams],
            "defense": result.x[n_teams:2*n_teams],
            "home_adv": result.x[2*n_teams],
            "rho": result.x[2*n_teams + 1],
        }
        return self

    def _log_likelihood(self, home_goals, away_goals, lambda_home, lambda_away, rho):
        """Compute log-likelihood with Dixon-Coles correction."""
        from scipy.stats import poisson

        log_p = poisson.logpmf(home_goals, lambda_home) + poisson.logpmf(away_goals, lambda_away)

        # Apply correction for low scores
        tau = self._tau(home_goals, away_goals, lambda_home, lambda_away, rho)
        log_p += np.log(tau)

        return log_p

    def _tau(self, home_goals, away_goals, lambda_home, lambda_away, rho):
        """Dixon-Coles correction term."""
        tau = np.ones_like(home_goals, dtype=float)
        mask_00 = (home_goals == 0) & (away_goals == 0)
        mask_10 = (home_goals == 1) & (away_goals == 0)
        mask_01 = (home_goals == 0) & (away_goals == 1)
        mask_11 = (home_goals == 1) & (away_goals == 1)

        tau[mask_00] = 1 - lambda_home[mask_00] * lambda_away[mask_00] * rho
        tau[mask_10] = 1 + lambda_away[mask_10] * rho
        tau[mask_01] = 1 + lambda_home[mask_01] * rho
        tau[mask_11] = 1 - rho

        return tau

    def _get_attack(self, team: str) -> float:
        if team in self.teams:
            return self.params["attack"][self.teams.index(team)]
        return 0.0

    def _get_defense(self, team: str) -> float:
        if team in self.teams:
            return self.params["defense"][self.teams.index(team)]
        return 0.0

    def predict_match(self, home_team: str, away_team: str) -> np.ndarray:
        """Predict the score probability matrix for a single match.

        Unknown teams (e.g. promoted teams not in training data) are assigned
        league-average parameters (attack=0, defense=0).

        Args:
            home_team: Name of the home team.
            away_team: Name of the away team.

        Returns:
            (max_goals+1, max_goals+1) matrix of goal probabilities.
        """
        if self.params is None:
            raise RuntimeError("Model must be fitted before prediction.")

        attack_home = self._get_attack(home_team)
        defense_home = self._get_defense(home_team)
        attack_away = self._get_attack(away_team)
        defense_away = self._get_defense(away_team)

        lambda_home = np.exp(attack_home + defense_away + self.params["home_adv"])
        lambda_away = np.exp(attack_away + defense_home)

        from scipy.stats import poisson

        prob = np.outer(
            poisson.pmf(np.arange(self.max_goals + 1), lambda_home),
            poisson.pmf(np.arange(self.max_goals + 1), lambda_away),
        )

        # Apply Dixon-Coles correction
        rho = self.params["rho"]
        prob[0, 0] *= (1 - lambda_home * lambda_away * rho)
        prob[1, 0] *= (1 + lambda_away * rho)
        prob[0, 1] *= (1 + lambda_home * rho)
        prob[1, 1] *= (1 - rho)

        prob /= prob.sum()
        return prob

    def get_score_matrix(self, home_team: str, away_team: str, max_goals: int = 5) -> pd.DataFrame:
        """Get a truncated score probability matrix as a labeled DataFrame.

        Args:
            home_team: Name of the home team.
            away_team: Name of the away team.
            max_goals: Maximum goals per team to show (matrix will be max_goals x max_goals).

        Returns:
            DataFrame with goal counts as index/columns and probabilities as values.
        """
        full_prob = self.predict_match(home_team, away_team)
        truncated = full_prob[:max_goals, :max_goals]
        truncated /= truncated.sum()

        return pd.DataFrame(
            truncated,
            index=[f"{i}" for i in range(max_goals)],
            columns=[f"{i}" for i in range(max_goals)],
        )

    def get_match_outcomes(self, home_team: str, away_team: str) -> dict[str, float]:
        """Get probability of home win, draw, and away win.

        Returns:
            Dict with keys 'home_win', 'draw', 'away_win'.
        """
        prob = self.predict_match(home_team, away_team)
        return {
            "home_win": float(np.tril(prob, -1).sum()),
            "draw": float(np.trace(prob)),
            "away_win": float(np.triu(prob, 1).sum()),
        }

    def get_team_strengths(self) -> pd.DataFrame:
        """Return attack and defense strengths for all teams.

        Returns:
            DataFrame with columns: team, attack, defense.
        """
        return pd.DataFrame({
            "team": self.teams,
            "attack": self.params["attack"],
            "defense": self.params["defense"],
        })
