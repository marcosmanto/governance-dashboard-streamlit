import pandas as pd
import streamlit as st
from frontend.services.api import listar_registros


@st.cache_data
def carregar_registros():
    dados = listar_registros()
    df = pd.DataFrame(dados)

    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
        df["data"] = df["data"].dt.normalize()
    return df
