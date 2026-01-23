import pandas as pd
import streamlit as st

st.title("📊 Painel Evolutivo de Dados")

df = pd.DataFrame(
    {
        "data": pd.date_range("2025-01-01", periods=10),
        "categoria": ["A", "B"] * 5,
        "valor": range(10),
    }
)

st.dataframe(df)
