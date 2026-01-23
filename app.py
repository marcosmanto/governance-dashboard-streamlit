import streamlit as st
from charts.charts import grafico_evolucao
from data.loader import carregar_dados

st.set_page_config(page_title="Painel Evolutivo de Dados", layout="wide")

st.title("📊 Painel Evolutivo de Dados")

# --- dados ---
df = carregar_dados()

# --- filtros ---
categoria = st.selectbox("Selecione a categoria", options=df["categoria"].unique())

df_filtrado = df[df["categoria"] == categoria]

# --- visualizações ---
fig = grafico_evolucao(df_filtrado, categoria)
st.plotly_chart(fig, use_container_width=True)

st.dataframe(df_filtrado)
