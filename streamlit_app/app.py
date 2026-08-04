import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="NB1 Match Analysis",
    page_icon="⚽",
    layout="wide",
)

st.title("NB1 Match Analysis")
st.sidebar.success("Select a page above.")

st.markdown("""
Welcome to the NB1 Match Analysis app.

Use the sidebar to navigate to the **Dixon-Coles** page where you can:
- Run the Dixon-Coles model on the last 3 seasons of Hungarian NB1
- View score probability matrices for any match
- Run Monte Carlo simulations for next season predictions
""")
