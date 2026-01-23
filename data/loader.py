from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "dados.csv"


@st.cache_data
def carregar_dados():
    df = pd.read_csv(DATA_DIR, parse_dates=["data"])
    return df
