import pandas as pd
import requests
import streamlit as st

API_URL = "http://localhost:8000"


@st.cache_data
def carregar_dados():
    resp = requests.get(f"{API_URL}/registros")
    resp.raise_for_status()
    df = pd.DataFrame(resp.json())

    if "data" in df.columns:
        df.loc[:, "data"] = pd.to_datetime(df["data"], errors="coerce")

    return df
