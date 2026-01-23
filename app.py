import pandas as pd
import plotly.express as px
import streamlit as st

st.title("📊 Painel Evolutivo de Dados")


@st.cache_data
def carregar_dados():
    return pd.DataFrame(
        {
            "data": pd.date_range("2025-01-01", periods=10),
            "categoria": ["A", "B"] * 5,
            "valor": range(10),
        }
    )


df = carregar_dados()
categoria = st.selectbox("Categoria", df["categoria"].unique())
df_filtrado = df[df["categoria"] == categoria]

fig = px.line(
    df_filtrado, x="data", y="valor", title=f"Evolução da categoria {categoria}"
)

st.plotly_chart(fig, use_container_width=True)
st.dataframe(df_filtrado)
