import pandas as pd
import streamlit as st

# from frontend.services.api import listar_registros


@st.cache_data
def carregar_registros(_api):
    """
    _api começa com underscore:
    - NÃO entra no hash do cache
    - mas continua sendo usado
    """
    resp = _api.listar_registros()

    if not resp.ok:
        raise RuntimeError(f"Erro ao carregar registros: {resp.status_code} - {resp.text}")

    dados = resp.json()
    df = pd.DataFrame(dados)

    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
        df["data"] = df["data"].dt.normalize()
    return df
