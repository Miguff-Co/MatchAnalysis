import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.pipeline import load_from_disk
from src.models.dixon_coles import DixonColes
from src.simulate.monte_carlo import simulate_season

st.set_page_config(page_title="Dixon-Coles", page_icon="⚽", layout="wide")

st.title("Dixon-Coles Model & Monte Carlo Simulation")

# --- Load data from disk (pre-downloaded via pipeline) ---
@st.cache_data
def load_data():
    return load_from_disk()

@st.cache_resource
def fit_model(matches_df):
    model = DixonColes()
    model.fit(matches_df)
    return model

try:
    data = load_data()
except FileNotFoundError as e:
    st.error(str(e))
    st.code("uv run python -m src.pipeline")
    st.stop()

# --- Session state initialization ---
if "model" not in st.session_state:
    st.session_state["model"] = None
if "mc_results" not in st.session_state:
    st.session_state["mc_results"] = None

# --- Button 1: Run Dixon-Coles ---
if st.button("Run Dixon-Coles", type="primary"):
    with st.spinner("Fitting Dixon-Coles model..."):
        st.session_state["model"] = fit_model(data["matches"])
        st.session_state["mc_results"] = None
    st.success("Dixon-Coles model fitted successfully!")

# --- Score matrix display (only after model is fitted) ---
if st.session_state["model"] is not None:
    model = st.session_state["model"]
    teams = model.teams
    if data["fixtures"] is not None:
        fixture_teams = sorted(
            set(data["fixtures"]["home_team"].unique()) | set(data["fixtures"]["away_team"].unique())
        )
        teams = sorted(set(teams) | set(fixture_teams))

    st.subheader("Score Probability Matrix")
    st.markdown("Select a match to view the probability of each scoreline.")

    col_home, col_away = st.columns(2)
    with col_home:
        home_team = st.selectbox("Home Team", teams, index=0)
    with col_away:
        away_options = [t for t in teams if t != home_team]
        away_team = st.selectbox("Away Team", away_options, index=0)

    max_goals = st.slider("Max goals to display", min_value=3, max_value=10, value=5)

    score_matrix = model.get_score_matrix(home_team, away_team, max_goals=max_goals)
    outcomes = model.get_match_outcomes(home_team, away_team)

    # Display outcome probabilities
    oc_col1, oc_col2, oc_col3 = st.columns(3)
    oc_col1.metric(f"{home_team} Win", f"{outcomes['home_win']:.1%}")
    oc_col2.metric("Draw", f"{outcomes['draw']:.1%}")
    oc_col3.metric(f"{away_team} Win", f"{outcomes['away_win']:.1%}")

    # Display score matrix as heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=score_matrix.values,
            x=score_matrix.columns,
            y=score_matrix.index,
            text=[[f"{v:.1%}" for v in row] for row in score_matrix.values],
            texttemplate="%{text}",
            colorscale="Blues",
            colorbar=dict(title="Probability"),
        )
    )
    fig.update_layout(
        title=f"Scoreline Probabilities: {home_team} vs {away_team}",
        xaxis_title=f"{away_team} Goals",
        yaxis_title=f"{home_team} Goals",
        yaxis=dict(autorange="reversed"),
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- Button 2: Run Monte Carlo ---
    st.divider()
    st.subheader("Monte Carlo Season Simulation")

    n_sims = st.number_input("Number of simulations", min_value=1000, max_value=100000, value=10000, step=1000)

    fixtures = data["fixtures"]
    if fixtures is None:
        st.warning("No fixtures file found. Run `uv run python -m src.pipeline` to download fixtures.")
    else:
        st.info(f"Using fixtures for season {data['current_season']} ({len(fixtures)} matches)")

        mc_disabled = st.session_state["model"] is None
        if st.button("Run Monte Carlo", type="primary", disabled=mc_disabled):
            with st.spinner(f"Running {n_sims} Monte Carlo simulations..."):
                st.session_state["mc_results"] = simulate_season(
                    st.session_state["model"], fixtures, n_simulations=int(n_sims)
                )
            st.success("Monte Carlo simulation complete!")

# --- Monte Carlo results display ---
if st.session_state["mc_results"] is not None:
    mc = st.session_state["mc_results"]

    st.divider()
    st.subheader("Season Predictions")

    # Summary table
    st.dataframe(
        mc[["team", "avg_points", "avg_position", "champion_prob", "top4_prob", "relegation_prob"]],
        use_container_width=True,
        hide_index=True,
    )

    # Position probability heatmap
    st.markdown("### Position Probability Matrix")
    st.markdown("Each cell shows the probability of a team finishing in that position.")

    n_teams = len(mc)
    position_matrix = pd.DataFrame(
        [row["position_probs"] for _, row in mc.iterrows()],
        index=mc["team"],
        columns=[f"{i+1}" for i in range(n_teams)],
    )

    fig_pos = go.Figure(
        data=go.Heatmap(
            z=position_matrix.values,
            x=position_matrix.columns,
            y=position_matrix.index,
            text=[[f"{v:.1%}" for v in row] for row in position_matrix.values],
            texttemplate="%{text}",
            colorscale="Viridis",
            colorbar=dict(title="Probability"),
        )
    )
    fig_pos.update_layout(
        title="Probability of Final Position by Team",
        xaxis_title="Final Position",
        yaxis_title="Team",
        yaxis=dict(autorange="reversed"),
        height=600,
    )
    st.plotly_chart(fig_pos, use_container_width=True)

    # Champion probability bar chart
    st.markdown("### Championship Probability")
    champ_df = mc[["team", "champion_prob"]].sort_values("champion_prob", ascending=True)
    fig_champ = px.bar(
        champ_df,
        x="champion_prob",
        y="team",
        orientation="h",
        labels={"champion_prob": "Probability", "team": ""},
        title="Probability of Winning the Championship",
    )
    fig_champ.update_layout(height=500, xaxis_tickformat=".0%")
    st.plotly_chart(fig_champ, use_container_width=True)
