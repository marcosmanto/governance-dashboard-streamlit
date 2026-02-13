import pandas as pd
import streamlit as st
from fastapi import Response

from backend.core.config import settings
from frontend.services.api import APIClient


@st.cache_data
def carregar_registros():
    """
    _api começa com underscore:
    - NÃO entra no hash do cache
    - mas continua sendo usado
    """
    resp: Response = APIClient.listar_registros_publico(settings.API_BASE_URL)

    if resp.status_code != 200:
        raise RuntimeError(f"Erro ao carregar registros: {resp.status_code} - {resp.text}")

    dados = resp.json()
    df = pd.DataFrame(dados)

    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
        df["data"] = df["data"].dt.normalize()
    return df
